"""
Sequence and structure similarity of the new models against the training set.

Port of the `similarities_af3` process of tcoarse_prediction.nf.
"""

import shlex

from HorusAPI import PluginVariable, SlurmBlock, VariableTypes

from slurm_utils import BSC_JOB_VARIABLES  # type: ignore
from tcoarse_utils import (  # type: ignore
    TCOARSE_CATEGORY,
    TCOARSE_COLOR,
    af3_training_csv,
    af3_training_pdbs,
    ensure_produced,
    finish,
    launch,
    python_exec,
    required_input,
    script_path,
    stage,
    variable_or,
)

# ==========================#
# Inputs
# ==========================#
metadata_csv_variable = PluginVariable(
    id="metadata_csv",
    name="Metadata CSV",
    description="Metadata of the models to compare.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
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
sim_seq_output = PluginVariable(
    id="sim_seq_csv",
    name="Sequence similarity",
    description="Sequence similarity against the AF3 training set.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)

sim_str_output = PluginVariable(
    id="sim_str_csv",
    name="Structure similarity",
    description="Structural similarity against the AF3 training set.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)

# ==========================#
# Other variables
# ==========================#
n_jobs_variable = PluginVariable(
    id="n_jobs",
    name="Jobs",
    description="Parallel jobs used by the comparison (-1 uses every core).",
    type=VariableTypes.INTEGER,
    defaultValue=-1,
)


def initial_similarities(block: SlurmBlock):
    """
    Compare the new models with the AF3 training set.
    """

    metadata_csv = stage(required_input(block, metadata_csv_variable))
    pdb_dir = stage(required_input(block, pdb_dir_variable))

    sim_seq_csv = "sim_seq.csv"
    sim_str_csv = "sim_str.csv"

    command = (
        f"{python_exec(block)} {shlex.quote(script_path(block, 'similarities_af3.py'))}"
        f" -pre {shlex.quote(af3_training_csv(block))}"
        f" -post {metadata_csv}"
        f" -pre_pdb {shlex.quote(af3_training_pdbs(block))}"
        f" -post_pdb {pdb_dir}"
        f" -o_seq {sim_seq_csv}"
        f" -o_str {sim_str_csv}"
        f" -n_jobs {int(variable_or(block, n_jobs_variable, -1))}"
    )

    block.extraData["sim_seq_csv"] = sim_seq_csv
    block.extraData["sim_str_csv"] = sim_str_csv

    print("Computing the similarities with the training set")

    launch(block, command, upload=[metadata_csv, pdb_dir])


def final_similarities(block: SlurmBlock):
    """
    Publish both similarity tables.
    """

    finish(block)

    sim_seq_csv = ensure_produced(
        block.extraData["sim_seq_csv"], "The sequence similarity CSV"
    )
    sim_str_csv = ensure_produced(
        block.extraData["sim_str_csv"], "The structure similarity CSV"
    )

    block.setOutput(sim_seq_output.id, sim_seq_csv)
    block.setOutput(sim_str_output.id, sim_str_csv)


similaritiesBlock = SlurmBlock(
    id="tcoarse_similarities",
    name="AF3 Similarities",
    description=(
        "Compute how similar the new TCR-pMHC models are to the complexes used "
        "to train the models, both in sequence and in structure."
    ),
    initialAction=initial_similarities,
    finalAction=final_similarities,
    inputs=[metadata_csv_variable, pdb_dir_variable],
    variables=BSC_JOB_VARIABLES + [n_jobs_variable],
    outputs=[sim_seq_output, sim_str_output],
    category=TCOARSE_CATEGORY,
    color=TCOARSE_COLOR,
)
