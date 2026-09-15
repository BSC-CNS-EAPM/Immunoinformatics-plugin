"""
TCoaRse coarse-grained energies from the contact maps and the statistical
potentials.

Port of the `energetic_scorer` process of tcoarse_prediction.nf.
"""


from HorusAPI import PluginVariable, SlurmBlock, VariableTypes

from slurm_utils import BSC_JOB_VARIABLES  # type: ignore
from tcoarse_steps import energetic_scorer_command  # type: ignore

from tcoarse_utils import (  # type: ignore
    TCOARSE_CATEGORY,
    TCOARSE_COLOR,
    output_prefix,
    ensure_produced,
    finish,
    job_cpus,
    launch,
    required_input,
    stage,
    variable_or,
)

# ==========================#
# Inputs
# ==========================#
cm_dir_variable = PluginVariable(
    id="cm_dir",
    name="Contact maps folder",
    description="Contact maps produced by the 'Contact Maps' block.",
    type=VariableTypes.FOLDER,
    required=True,
)

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
energies_csv_output = PluginVariable(
    id="energies_csv",
    name="TCoaRse energies",
    description="Coarse-grained energies of every model.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)

# ==========================#
# Other variables
# ==========================#
chain_map_variable = PluginVariable(
    id="chain_map",
    name="Chain map",
    description="Chain mapping used by the scorer.",
    type=VariableTypes.STRING,
    defaultValue="D:E:C:A:B",
)

threshold_variable = PluginVariable(
    id="threshold",
    name="Contact threshold",
    description="Distance threshold (A) used to define a contact.",
    type=VariableTypes.INTEGER,
    defaultValue=7,
)

io_workers_variable = PluginVariable(
    id="io_workers",
    name="IO workers",
    description="Threads used to read the contact maps.",
    type=VariableTypes.INTEGER,
    defaultValue=8,
)

not_experimental_variable = PluginVariable(
    id="not_experimental",
    name="Predicted structures",
    description=(
        "The structures are predicted (AlphaFold3) instead of experimental. "
        "Keep it enabled for the standard pipeline."
    ),
    type=VariableTypes.BOOLEAN,
    defaultValue=True,
)


def initial_energetic_scorer(block: SlurmBlock):
    """
    Score the contacts of every model with the statistical potentials.
    """

    cm_dir = stage(required_input(block, cm_dir_variable))
    pdb_dir = stage(required_input(block, pdb_dir_variable))
    prefix = output_prefix(block)

    energies_csv = f"{prefix}_tcoarse_energies.csv"

    command = energetic_scorer_command(
        block,
        pdb_dir,
        cm_dir,
        energies_csv,
        str(variable_or(block, chain_map_variable, "D:E:C:A:B")),
        int(variable_or(block, threshold_variable, 7)),
        job_cpus(block),
        int(variable_or(block, io_workers_variable, 8)),
        bool(variable_or(block, not_experimental_variable, True)),
    )

    block.extraData["energies_csv"] = energies_csv

    print("Computing the coarse-grained energies")

    launch(block, command, upload=[cm_dir, pdb_dir])


def final_energetic_scorer(block: SlurmBlock):
    """
    Publish the energies CSV.
    """

    finish(block)

    energies_csv = ensure_produced(
        block.extraData["energies_csv"], "The energies CSV"
    )

    print(f"Energies written to '{energies_csv}'")

    block.setOutput(energies_csv_output.id, energies_csv)


energeticScorerBlock = SlurmBlock(
    id="tcoarse_energetic_scorer",
    name="Energetic Scorer",
    description=(
        "Score the TCR-pMHC contacts with the TCoaRse statistical potentials "
        "(TCR-peptide, TCR-MHC and peptide-MHC)."
    ),
    initialAction=initial_energetic_scorer,
    finalAction=final_energetic_scorer,
    inputs=[cm_dir_variable, pdb_dir_variable],
    variables=BSC_JOB_VARIABLES
    + [
        chain_map_variable,
        threshold_variable,
        io_workers_variable,
        not_experimental_variable,
    ],
    outputs=[energies_csv_output],
    category=TCOARSE_CATEGORY,
    color=TCOARSE_COLOR,
)
