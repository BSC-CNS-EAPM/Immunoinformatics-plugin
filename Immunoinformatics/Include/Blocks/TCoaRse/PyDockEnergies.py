"""
pyDock binding energies of the TCR-pMHC models.

Port of the `pydock` process of tcoarse_prediction.nf. The Nextflow version
copied `pydock/config.yaml` and patched it with `sed` (against placeholders
that the shipped config no longer has) and only ever processed the first chunk.
Here the config is generated from scratch and every chunk is processed.
"""


from HorusAPI import PluginVariable, SlurmBlock, VariableTypes

from slurm_utils import BSC_JOB_VARIABLES  # type: ignore
from tcoarse_steps import (  # type: ignore
    PYDOCK_CONFIG_NAME,
    PYDOCK_OUTPUT_DIR,
    PYDOCK_STAGING_DIR,
    parse_pydock_modules,
    pydock_command,
    write_pydock_config,
)

from tcoarse_utils import (  # type: ignore
    TCOARSE_CATEGORY,
    TCOARSE_COLOR,
    output_prefix,
    ensure_produced,
    finish,
    job_cpus,
    launch,
    pydock_dir,
    pydock_sif,
    python_exec,
    required_input,
    stage,
    variable_or,
)

# ==========================#
# Inputs
# ==========================#
pdb_dir_variable = PluginVariable(
    id="pdb_dir",
    name="PDB folder",
    description="Folder with the merged PDB models.",
    type=VariableTypes.FOLDER,
    required=True,
)

# ==========================#
# Outputs
# ==========================#
pydock_tar_output = PluginVariable(
    id="pydock_tar",
    name="pyDock energies",
    description="TAR archive with the .ene files of every model.",
    type=VariableTypes.FILE,
    allowedValues=["tar"],
)

# ==========================#
# Other variables
# ==========================#
chunk_size_variable = PluginVariable(
    id="complexes_per_chunk",
    name="Complexes per chunk",
    description="Number of complexes processed by each pyDock chunk.",
    type=VariableTypes.INTEGER,
    defaultValue=5000,
)

modules_variable = PluginVariable(
    id="pydock_modules",
    name="pyDock modules",
    description="pyDock modules to run, one per line.",
    type=VariableTypes.TEXT_AREA,
    defaultValue="bindEy",
)

# Kept as aliases so the rest of the block (and anything importing them) still
# reads the same names; the values live with the commands in tcoarse_steps.
CONFIG_NAME = PYDOCK_CONFIG_NAME
OUTPUT_DIR = PYDOCK_OUTPUT_DIR
STAGING_DIR = PYDOCK_STAGING_DIR


def _write_config(block: SlurmBlock, pdb_dir: str) -> str:
    """
    Write the pyDock config.yaml in the run folder and return its name.
    """
    return write_pydock_config(
        pdb_dir,
        pydock_sif(block),
        parse_pydock_modules(variable_or(block, modules_variable, "bindEy")),
        int(variable_or(block, chunk_size_variable, 5000)),
    )


def initial_pydock(block: SlurmBlock):
    """
    Run the pyDock scoring of every model.
    """

    pdb_dir = stage(required_input(block, pdb_dir_variable))
    prefix = output_prefix(block)

    cpus = job_cpus(block)
    tar_path = f"{prefix}_pydock_ene.tar"

    config = _write_config(block, pdb_dir)


    command = pydock_command(block, config, tar_path, cpus)

    block.extraData["pydock_tar"] = tar_path

    print("Scoring the models with pyDock")

    launch(block, command, upload=[pdb_dir, config])


def final_pydock(block: SlurmBlock):
    """
    Publish the archive with the pyDock energies.
    """

    finish(block)

    tar_path = ensure_produced(block.extraData["pydock_tar"], "The pyDock archive")

    print(f"pyDock energies written to '{tar_path}'")

    block.setOutput(pydock_tar_output.id, tar_path)


pydockEnergiesBlock = SlurmBlock(
    id="tcoarse_pydock",
    name="pyDock Energies",
    description=(
        "Score every TCR-pMHC model with pyDock (inside its Singularity "
        "container) and pack the resulting .ene files into a single archive."
    ),
    initialAction=initial_pydock,
    finalAction=final_pydock,
    inputs=[pdb_dir_variable],
    variables=BSC_JOB_VARIABLES + [chunk_size_variable, modules_variable],
    outputs=[pydock_tar_output],
    category=TCOARSE_CATEGORY,
    color=TCOARSE_COLOR,
)
