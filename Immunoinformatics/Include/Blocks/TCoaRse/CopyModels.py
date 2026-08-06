"""
Gather the best AlphaFold3 models into a single folder of merged PDBs.

Port of the `cp_models` process of tcoarse_prediction.nf.
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
)

# ==========================#
# Inputs
# ==========================#
af3_dir_variable = PluginVariable(
    id="af3_dir",
    name="AF3 outputs",
    description="Folder with the AlphaFold3 predictions (not uploaded).",
    type=VariableTypes.FOLDER,
    required=True,
)

# ==========================#
# Outputs
# ==========================#
pdb_dir_output = PluginVariable(
    id="pdb_dir",
    name="PDB folder",
    description="Folder with one merged PDB per model.",
    type=VariableTypes.FOLDER,
)


def initial_copy_models(block: SlurmBlock):
    """
    Convert the AF3 predictions into merged PDB files.
    """

    af3_dir = required_input(block, af3_dir_variable)
    prefix = output_prefix(block)

    pdb_dir = f"{prefix}_pdb"

    command = (
        f"{python_exec(block)} {shlex.quote(script_path(block, 'cp_models.py'))}"
        f" {shlex.quote(af3_dir)}"
        f" {pdb_dir}"
        f" --workers {job_cpus(block, 4)}"
    )

    block.extraData["pdb_dir"] = pdb_dir

    print("Copying the AF3 models as merged PDBs")

    launch(block, command)


def final_copy_models(block: SlurmBlock):
    """
    Publish the folder of merged PDBs.
    """

    finish(block)

    pdb_dir = ensure_produced(block.extraData["pdb_dir"], "The PDB folder")

    print(f"Merged PDBs written to '{pdb_dir}'")

    block.setOutput(pdb_dir_output.id, pdb_dir)


copyModelsBlock = SlurmBlock(
    id="tcoarse_copy_models",
    name="Copy Models",
    description=(
        "Collect the AlphaFold3 predictions of every seed/sample into a single "
        "folder of merged PDB structures."
    ),
    initialAction=initial_copy_models,
    finalAction=final_copy_models,
    inputs=[af3_dir_variable],
    variables=BSC_JOB_VARIABLES,
    outputs=[pdb_dir_output],
    category=TCOARSE_CATEGORY,
    color=TCOARSE_COLOR,
)
