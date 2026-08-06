"""
Contact maps of the TCR-pMHC models.

Port of the `contact_maps` process of tcoarse_prediction.nf.
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
cm_dir_output = PluginVariable(
    id="cm_dir",
    name="Contact maps folder",
    description="Folder with the contact map of every model.",
    type=VariableTypes.FOLDER,
)

# ==========================#
# Other variables
# ==========================#
chain_map_variable = PluginVariable(
    id="chain_map",
    name="Chain map",
    description="Chain mapping (TCRa:TCRb:peptide:MHC...).",
    type=VariableTypes.STRING,
    defaultValue="D:E:C:B:A",
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


def initial_contact_maps(block: SlurmBlock):
    """
    Compute the contact maps of every model.
    """

    pdb_dir = stage(required_input(block, pdb_dir_variable))
    prefix = output_prefix(block)

    cm_dir = f"{prefix}_cm"

    command = (
        f"{python_exec(block)} {shlex.quote(script_path(block, 'contact_maps.py'))}"
        f" -pdb {pdb_dir}"
        f" -out {cm_dir}"
        f" -cm {shlex.quote(str(variable_or(block, chain_map_variable, 'D:E:C:B:A')))}"
        f" -workers {job_cpus(block)}"
    )

    if variable_or(block, not_experimental_variable, True):
        command += " -notexp"

    block.extraData["cm_dir"] = cm_dir

    print("Computing the contact maps")

    launch(block, command, upload=[pdb_dir])


def final_contact_maps(block: SlurmBlock):
    """
    Publish the contact maps folder.
    """

    finish(block)

    cm_dir = ensure_produced(block.extraData["cm_dir"], "The contact maps folder")

    print(f"Contact maps written to '{cm_dir}'")

    block.setOutput(cm_dir_output.id, cm_dir)


contactMapsBlock = SlurmBlock(
    id="tcoarse_contact_maps",
    name="Contact Maps",
    description="Compute the residue contact maps of every TCR-pMHC model.",
    initialAction=initial_contact_maps,
    finalAction=final_contact_maps,
    inputs=[pdb_dir_variable],
    variables=BSC_JOB_VARIABLES + [chain_map_variable, not_experimental_variable],
    outputs=[cm_dir_output],
    category=TCOARSE_CATEGORY,
    color=TCOARSE_COLOR,
)
