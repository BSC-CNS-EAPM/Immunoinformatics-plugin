"""
Module containing the NetCleave block for the Immunoinformatics plugin 
"""
import os
import subprocess
from HorusAPI import PluginVariable, VariableTypes, PluginBlock, VariableGroup

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
    
    import pandas as pd
    
    try:
        os.path.exists(inputFile)
    except Exception as e:
        raise(f"An error occurred while checking the input file: {e}")

    # Run the NetCleave
    try:
        subprocess.Popen(["python", netCleave_path, "--predict", inputFile, "--pred_input", 2])
    except Exception as e:
        raise(f"An error occurred while running the NetCleave: {e}")
    
    # Set output
    block.outputs["output_csv"] = "out.csv"
    

# ==========================#
# Block definition
# ==========================#
netCleaveBlock = PluginBlock(
    name="NOAH",
    description="Predict the binding affinity of peptides to HLA-I alleles",
    inputs=[inputFileVar],
    outputs=[outputCSVVar],
    variables=[],
    action=runNetCleave,
)