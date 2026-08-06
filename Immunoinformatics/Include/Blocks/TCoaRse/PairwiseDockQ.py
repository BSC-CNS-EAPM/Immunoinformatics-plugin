"""
Pairwise DockQ between the models of the same complex.

Port of the `pairwise_dockq` process of tcoarse_prediction.nf.
"""

import shlex

from HorusAPI import PluginVariable, SlurmBlock, VariableTypes

from slurm_utils import BSC_JOB_VARIABLES  # type: ignore
from tcoarse_utils import (  # type: ignore
    TCOARSE_CATEGORY,
    TCOARSE_COLOR,
    output_prefix,
    ensure_produced,
    finish,
    job_cpus,
    launch,
    python_exec,
    required_input,
    script_path,
    stage,
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
dockq_csv_output = PluginVariable(
    id="pairwise_dockq_csv",
    name="Pairwise DockQ",
    description="DockQ between every pair of models of the same complex.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)


def initial_pairwise_dockq(block: SlurmBlock):
    """
    Compute the pairwise DockQ of the models.
    """

    pdb_dir = stage(required_input(block, pdb_dir_variable))
    prefix = output_prefix(block)

    dockq_csv = f"{prefix}_pairwise_dockq.csv"

    command = (
        f"{python_exec(block)} {shlex.quote(script_path(block, 'pw_sim.py'))}"
        f" --folder {pdb_dir}"
        f" --output {dockq_csv}"
        f" --workers {job_cpus(block, 8)}"
    )

    block.extraData["pairwise_dockq_csv"] = dockq_csv

    print("Computing the pairwise DockQ")

    launch(block, command, upload=[pdb_dir])


def final_pairwise_dockq(block: SlurmBlock):
    """
    Publish the pairwise DockQ table.
    """

    finish(block)

    dockq_csv = ensure_produced(
        block.extraData["pairwise_dockq_csv"], "The pairwise DockQ CSV"
    )

    block.setOutput(dockq_csv_output.id, dockq_csv)


pairwiseDockQBlock = SlurmBlock(
    id="tcoarse_pairwise_dockq",
    name="Pairwise DockQ",
    description=(
        "Compute the DockQ between the different models of the same complex, "
        "as a measure of the convergence of the prediction."
    ),
    initialAction=initial_pairwise_dockq,
    finalAction=final_pairwise_dockq,
    inputs=[pdb_dir_variable],
    variables=BSC_JOB_VARIABLES,
    outputs=[dockq_csv_output],
    category=TCOARSE_CATEGORY,
    color=TCOARSE_COLOR,
)
