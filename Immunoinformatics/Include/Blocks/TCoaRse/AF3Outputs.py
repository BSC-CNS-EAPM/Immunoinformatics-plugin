"""
Entry point of the TCoaRse pipeline: the folder with the AlphaFold3 predictions.

Equivalent to the `params.af3_outputs` parameter of tcoarse_prediction.nf.
"""

import os

from HorusAPI import PluginBlock, PluginVariable, VariableTypes

from tcoarse_utils import (  # type: ignore
    TCOARSE_CATEGORY,
    TCOARSE_COLOR,
    output_prefix,
    variable_or,
)

# ==========================#
# Variables
# ==========================#
af3_folder_variable = PluginVariable(
    id="af3_outputs",
    name="AF3 outputs folder",
    description=(
        "Folder containing one subfolder per TCR-pMHC complex, as produced by "
        "AlphaFold3 (each with its *_model.cif, *_confidences.json and seed-* "
        "subfolders). It is never uploaded: the path must be valid on the "
        "machine that runs the jobs (the cluster when a remote is selected)."
    ),
    type=VariableTypes.FOLDER,
    showInCanvas=True,
)

# ==========================#
# Outputs
# ==========================#
af3_dir_output = PluginVariable(
    id="af3_dir",
    name="AF3 outputs",
    description="The folder with the AlphaFold3 predictions.",
    type=VariableTypes.FOLDER,
)


def run_af3_outputs(block: PluginBlock):
    """
    Validate the AF3 outputs folder and pass it downstream.
    """

    af3_dir = variable_or(block, af3_folder_variable, None)

    if not af3_dir:
        raise Exception("Please select the folder with the AlphaFold3 outputs.")

    af3_dir = os.path.normpath(str(af3_dir))

    # The check runs on the machine that will execute the jobs
    print(f"Checking '{af3_dir}'")

    output = block.remote.command(f"ls -1 '{af3_dir}' | wc -l")

    try:
        entries = int(output.strip().splitlines()[0])
    except (ValueError, IndexError):
        entries = 0

    if entries == 0:
        raise Exception(f"The AF3 outputs folder is empty or does not exist: {af3_dir}")

    print(f"Found {entries} entries in '{af3_dir}'")
    print(f"The results will be named after the flow: '{output_prefix(block)}_*'")

    block.setOutput(af3_dir_output.id, af3_dir)


af3OutputsBlock = PluginBlock(
    id="tcoarse_af3_outputs",
    name="AF3 Outputs",
    description=(
        "Folder with the AlphaFold3 TCR-pMHC predictions. Starting point of the "
        "TCoaRse pipeline; the name of the folder is used to name every result."
    ),
    action=run_af3_outputs,
    variables=[af3_folder_variable],
    outputs=[af3_dir_output],
    category=TCOARSE_CATEGORY,
    color=TCOARSE_COLOR,
)
