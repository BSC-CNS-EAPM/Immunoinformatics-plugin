"""
The whole TCoaRse pipeline as a single block.

The individual TCoaRse blocks stay in place and keep working on their own; this
block is the "run everything" shortcut, configured from the setup page instead
of by wiring a flow by hand. It covers the branch of the pipeline that ends in
the TCoaRse predictor:

    Copy Models -> Structure Metadata
                -> Contact Maps
                -> pyDock Energies
                -> Pairwise DockQ
    Contact Maps + Copy Models -> Energetic Scorer
    Energetic Scorer + Structure Metadata + pyDock -> Merge Energies
    Merge Energies -> TCoaRse Predictor

Every step is a shell command, so the eight of them are concatenated into a
single job script and submitted once. That keeps a cluster run to one SLURM job
and behaves the same locally, and it is the reason the steps have to be listed
here rather than reusing the blocks' own actions, which each submit a job of
their own.

Nothing is cleaned up between steps: every intermediate output stays in the run
folder, and each step appends a line to <prefix>_pipeline_status.tsv as it
completes, so a failed run shows exactly how far it got.
"""

import os
import typing

from slurm_utils import BSC_JOB_VARIABLES  # type: ignore

from HorusAPI import (
    CustomVariable,
    PluginVariable,
    SlurmBlock,
    VariableTypes,
)

from tcoarse_steps import (  # type: ignore
    contact_maps_command,
    copy_models_command,
    energetic_scorer_command,
    merge_energies_command,
    pairwise_dockq_command,
    parse_pydock_modules,
    predictor_tcoarse_command,
    pydock_command,
    structure_metadata_command,
    write_pydock_config,
)

from tcoarse_utils import (  # type: ignore
    ensure_produced,
    finish,
    job_cpus,
    launch,
    output_prefix,
    pydock_sif,
    python_exec,
    show_results,
    tcoarse_model,
    variable_or,
)

from Pages.setup_tcoarse import setup_tcoarse_page  # type: ignore


# ==========================#
# Setup page
# ==========================#
setup_tcoarse_variable = CustomVariable(
    id="setup_tcoarse",
    name="Setup TCoaRse",
    description="Configure the TCoaRse pipeline",
    customPage=setup_tcoarse_page,
    showInCanvas=True,
    type=VariableTypes.ANY,  # type: ignore
)

# ==========================#
# Inputs
# ==========================#
af3_dir_variable = PluginVariable(
    id="af3_dir",
    name="AF3 outputs",
    description=(
        "Folder with the AlphaFold3 predictions. Overrides the folder set in "
        "the setup page."
    ),
    type=VariableTypes.FOLDER,
)

# ==========================#
# Outputs
# ==========================#
predictions_output = PluginVariable(
    id="predictions",
    name="TCoaRse predictions",
    description="Immunogenicity probability of every TCR.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)

merged_csv_output = PluginVariable(
    id="merged_csv",
    name="Merged features",
    description="Feature table the predictor was run on.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)

dockq_csv_output = PluginVariable(
    id="dockq_csv",
    name="Pairwise DockQ",
    description="Pairwise DockQ of the models.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)

metadata_csv_output = PluginVariable(
    id="metadata_csv",
    name="Metadata CSV",
    description="Metadata extracted from the structures.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)

energies_csv_output = PluginVariable(
    id="energies_csv",
    name="TCoaRse energies",
    description="Coarse-grained energies of every model.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)

pydock_tar_output = PluginVariable(
    id="pydock_tar",
    name="pyDock energies",
    description="Archive with the pyDock .ene files.",
    type=VariableTypes.FILE,
    allowedValues=["tar"],
)

pdb_dir_output = PluginVariable(
    id="pdb_dir",
    name="PDB models",
    description="Folder with the merged PDB models.",
    type=VariableTypes.FOLDER,
)

# ==========================#
# Other variables
# ==========================#
chain_map_variable = PluginVariable(
    id="chain_map",
    name="Chain map",
    description="Chain mapping passed to the contact maps and the scorer.",
    type=VariableTypes.STRING,
    defaultValue="D:E:C:B:A",
)

not_experimental_variable = PluginVariable(
    id="not_experimental",
    name="Predicted structures",
    description="The models are predictions, not experimental structures.",
    type=VariableTypes.BOOLEAN,
    defaultValue=True,
)

energy_threshold_variable = PluginVariable(
    id="energy_threshold",
    name="Contact threshold",
    description="Distance threshold of the energetic scorer, in angstrom.",
    type=VariableTypes.INTEGER,
    defaultValue=7,
)

io_workers_variable = PluginVariable(
    id="io_workers",
    name="IO workers",
    description="Workers reading the contact maps of the energetic scorer.",
    type=VariableTypes.INTEGER,
    defaultValue=8,
)

chunk_size_variable = PluginVariable(
    id="chunk_size",
    name="Complexes per chunk",
    description="Complexes scored by each pyDock chunk.",
    type=VariableTypes.INTEGER,
    defaultValue=5000,
)

pydock_modules_variable = PluginVariable(
    id="pydock_modules",
    name="pyDock modules",
    description="pyDock modules to run, one per line.",
    type=VariableTypes.TEXT_AREA,
    defaultValue="bindEy",
)

model_variable = PluginVariable(
    id="model",
    name="TCoaRse model",
    description="Overrides the model set in the TCoaRse configuration.",
    type=VariableTypes.FILE,
    allowedValues=["json"],
)


def _setup(block: SlurmBlock) -> dict:
    """
    The dictionary written by the setup page, empty when it was never opened.
    """
    setup = block.variables.get(setup_tcoarse_variable.id)

    return setup if isinstance(setup, dict) else {}


def _setting(
    block: SlurmBlock,
    key: str,
    variable: PluginVariable,
    default: typing.Any,
) -> typing.Any:
    """
    A pipeline setting, taken from the setup page when it set one.

    The block variables stay usable on their own so the block still works when
    the page was never opened, and so the flow can be driven from a script.
    """
    setup = _setup(block)

    value = setup.get(key)
    if value not in (None, ""):
        return value

    return variable_or(block, variable, default)


def _af3_dir(block: SlurmBlock) -> str:
    """
    The AF3 outputs folder, from the input socket or from the setup page.
    """
    af3_dir = block.inputs.get(af3_dir_variable.id) or _setup(block).get("af3_dir")

    if not af3_dir:
        raise Exception(
            "No AF3 outputs folder. Set one in the setup page or wire the "
            "'AF3 outputs' input."
        )

    return str(af3_dir)


def _write_pydock_config(block: SlurmBlock, pdb_dir: str) -> str:
    """
    Write the pyDock config.yaml in the run folder and return its name.
    """
    return write_pydock_config(
        pdb_dir,
        pydock_sif(block),
        parse_pydock_modules(
            _setting(block, "pydock_modules", pydock_modules_variable, "bindEy")
        ),
        int(_setting(block, "chunk_size", chunk_size_variable, 5000)),
    )


def _step(number: int, total: int, name: str, body: str, status_file: str) -> str:
    """
    Wrap a step of the pipeline with its banner and its status line.

    The script runs under `set -e`, so it stops at the first failing step and
    the banner right above the error names it. The status file is what is left
    behind afterwards: it lists the steps that did complete, which is the same
    information once the console has scrolled away.
    """
    return "\n".join(
        [
            f'echo ""',
            f'echo "########## [{number}/{total}] {name} ##########"',
            body,
            f'echo "{number}/{total}\t{name}\tOK" >> {status_file}',
            f'echo "[{number}/{total}] {name}: done"',
        ]
    )


def initial_tcoarse_pipeline(block: SlurmBlock):
    """
    Build the script of the whole pipeline and submit it as a single job.
    """

    af3_dir = _af3_dir(block)
    prefix = output_prefix(block)

    cpus = job_cpus(block)

    # Every intermediate of the run, kept so a failure can be picked apart
    pdb_dir = f"{prefix}_pdb"
    metadata_csv = f"{prefix}_metadata.csv"
    cm_dir = f"{prefix}_cm"
    pydock_tar = f"{prefix}_pydock_ene.tar"
    dockq_csv = f"{prefix}_pairwise_dockq.csv"
    energies_csv = f"{prefix}_tcoarse_energies.csv"
    merged_csv = f"{prefix}_tcoarse_pydock_energies.csv"
    predictions = f"{prefix}_tcoarse_predictions.csv"
    status_file = f"{prefix}_pipeline_status.tsv"

    chain_map = str(_setting(block, "chain_map", chain_map_variable, "D:E:C:B:A"))
    not_experimental = bool(
        _setting(block, "not_experimental", not_experimental_variable, True)
    )

    config = _write_pydock_config(block, pdb_dir)
    model = _setting(block, "model", model_variable, None) or tcoarse_model(block)

    total = 8

    copy_models = copy_models_command(block, af3_dir, pdb_dir, job_cpus(block, 4))

    metadata = structure_metadata_command(block, pdb_dir, metadata_csv)

    contact_maps = contact_maps_command(
        block, pdb_dir, cm_dir, chain_map, cpus, not_experimental
    )

    pydock = pydock_command(block, config, pydock_tar, cpus)

    dockq = pairwise_dockq_command(block, pdb_dir, dockq_csv, job_cpus(block, 8))

    scorer = energetic_scorer_command(
        block,
        pdb_dir,
        cm_dir,
        energies_csv,
        chain_map,
        int(_setting(block, "energy_threshold", energy_threshold_variable, 7)),
        cpus,
        int(_setting(block, "io_workers", io_workers_variable, 8)),
        not_experimental,
    )

    merge = merge_energies_command(
        block, energies_csv, metadata_csv, pydock_tar, merged_csv
    )

    predictor = predictor_tcoarse_command(block, merged_csv, predictions, str(model))

    steps = [
        ("Copy Models", copy_models),
        ("Structure Metadata", metadata),
        ("Contact Maps", contact_maps),
        ("pyDock Energies", pydock),
        ("Pairwise DockQ", dockq),
        ("Energetic Scorer", scorer),
        ("Merge Energies", merge),
        ("TCoaRse Predictor", predictor),
    ]

    command = "\n".join(
        ["set -e", f"rm -f {status_file}"]
        + [
            _step(number, total, name, body, status_file)
            for number, (name, body) in enumerate(steps, start=1)
        ]
        + [f'echo ""', f'echo "The TCoaRse pipeline finished the {total} steps"']
    )

    block.extraData.update(
        {
            "pdb_dir": pdb_dir,
            "metadata_csv": metadata_csv,
            "cm_dir": cm_dir,
            "pydock_tar": pydock_tar,
            "dockq_csv": dockq_csv,
            "energies_csv": energies_csv,
            "merged_csv": merged_csv,
            "predictions": predictions,
            "status_file": status_file,
        }
    )

    print(f"Running the TCoaRse pipeline on '{af3_dir}'")
    print(f"{total} steps: " + ", ".join(name for name, _ in steps))

    launch(block, command, upload=[af3_dir, config])


def final_tcoarse_pipeline(block: SlurmBlock):
    """
    Publish every output the pipeline produced.
    """

    finish(block)

    data = block.extraData

    # The predictions are the point of the run, so they are the only output
    # that is required to exist
    predictions = ensure_produced(data["predictions"], "The TCoaRse predictions")

    print(f"Predictions written to '{predictions}'")

    block.setOutput(predictions_output.id, predictions)

    # The rest are published when they are there. A step that was reached is
    # worth handing downstream even if a later one failed.
    optional = [
        (merged_csv_output, "merged_csv"),
        (dockq_csv_output, "dockq_csv"),
        (metadata_csv_output, "metadata_csv"),
        (energies_csv_output, "energies_csv"),
        (pydock_tar_output, "pydock_tar"),
        (pdb_dir_output, "pdb_dir"),
    ]

    for variable, key in optional:
        path = data.get(key)
        if path and os.path.exists(path):
            block.setOutput(variable.id, path)
        else:
            print(f"Note: '{path}' was not produced, leaving '{variable.name}' unset.")

    show_results(block, predictions, "TCoaRse predictions")


tcoarsePipelineBlock = SlurmBlock(
    id="tcoarse_pipeline",
    name="TCoaRse Pipeline",
    description=(
        "Run the whole TCoaRse pipeline on a folder of AlphaFold3 predictions: "
        "copy models, structure metadata, contact maps, pyDock energies, "
        "pairwise DockQ, energetic scorer, merge energies and the TCoaRse "
        "predictor. Configure it from the setup page."
    ),
    initialAction=initial_tcoarse_pipeline,
    finalAction=final_tcoarse_pipeline,
    inputs=[af3_dir_variable],
    variables=BSC_JOB_VARIABLES
    + [
        setup_tcoarse_variable,
        chain_map_variable,
        not_experimental_variable,
        energy_threshold_variable,
        io_workers_variable,
        chunk_size_variable,
        pydock_modules_variable,
        model_variable,
    ],
    outputs=[
        predictions_output,
        merged_csv_output,
        dockq_csv_output,
        metadata_csv_output,
        energies_csv_output,
        pydock_tar_output,
        pdb_dir_output,
    ],
    category="TCoaRse",
)
