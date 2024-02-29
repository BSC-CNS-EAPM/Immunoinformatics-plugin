"""
Module containing the NetCleave block for the Immunoinformatics plugin 
"""

import os
import subprocess
import pandas as pd
from HorusAPI import PluginVariable, VariableTypes, PluginBlock

# ==========================#
# Variable inputs
# ==========================#
inputFileVar = PluginVariable(
    name="Input CSV peptides",
    id="input_csv",
    description=" File with the peptides to Predict. The file must have the following structure; peptide  HLA",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)

# ==========================#
# Variable outputs
# ==========================#
outputCSVVar = PluginVariable(
    name="Output CSV",
    id="output_csv",
    description="Output file. (with file extension) the output is always a csv.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)


def runNetCleave(block: PluginBlock):
    """
    Run the NetCleave block
    """
    inputFile = block.inputs["input_csv"]

    netCleave_path = block.config.get("netCleave_path", "NetCleave.py")

    try:
        os.path.exists(inputFile)
    except Exception as e:
        raise Exception(f"An error occurred while checking the input file: {e}")

    # Run the NetCleave
    try:
        subprocess.Popen(
            ["python", netCleave_path, "--predict", inputFile, "--pred_input", str(2)]
        )
    except Exception as e:
        raise Exception(f"An error occurred while running the NetCleave: {e}")

    output = inputFile.replace(".fasta", "_netcleave.csv")

    # Set output
    # Columns epitope,uniprot_id, cleavage_site, netcleave, netc_warning
    block.outputs["output_csv"] = output


# ==========================#
# Block definition
# ==========================#
netCleaveBlock = PluginBlock(
    name="NetCleave",
    description="NetCleave allows the prediction of C-terminal peptide processing of MHC pathways",
    inputs=[inputFileVar],
    outputs=[outputCSVVar],
    variables=[],
    action=runNetCleave,
)
