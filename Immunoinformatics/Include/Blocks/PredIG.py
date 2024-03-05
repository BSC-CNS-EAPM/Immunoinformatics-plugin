"""
Module containing the PredIG block for the Immunoinformatics plugin 
"""

import os

import pandas as pd
from utils import runPredigMHCflurry, runPredigPCH

from HorusAPI import PluginBlock, PluginVariable, VariableGroup, VariableTypes

# ==========================#
# Variable inputs
# ==========================#
inputCSV = PluginVariable(
    name="Input CSV",
    id="input_csv",
    description="The input csv with the epitope and presenting HLA-I allele.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)
inputTxtbox = PluginVariable(
    name="Input txtbox",
    id="input_txtbox",
    description="The input txt with the epitope and presenting HLA-I allele.",
    type=VariableTypes.TEXT_AREA,
)


# ==========================#
# Variable outputs
# ==========================#
outputPCH = PluginVariable(
    name="Output CSV",
    id="output_pch",
    description="The output csv with the PCH output.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)
outputFlurry = PluginVariable(
    name="Output CSV",
    id="output_flurry",
    description="The output tsv with the predicted binding affinity.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)

##############################
#       Other variables      #
##############################
seedVar = PluginVariable(
    name="Seed",
    id="seed",
    description="The seed for the random number generator.",
    type=VariableTypes.INTEGER,
    defaultValue=123,
)


# Align action block
def runPredIG(block: PluginBlock):
    """
    Run the PredIG block
    """

    # Get the input file
    inputFile = block.inputs.get("input_csv")
    if inputFile is None:
        inputFile = str(block.inputs.get("input_txtbox"))
        with open("input.csv", "w") as file:
            file.write(inputFile)
        inputFile = "input.csv"
    if inputFile is None:
        raise Exception("No input file was provided")

    # Get the seed
    seed = int(block.variables.get("seed", 123))

    # Get the PCH path
    pchPath = block.config.get(
        "PCH_path", "/home/albertcs/Projects/ROC/pch_inout/predig_pch_calc.R"
    )

    # Get the MHCflurry path
    mhcflurryPath = block.config.get("MHC_path", "mhcflurry-predict")

    # Check if the input file is valid
    if not os.path.isfile(inputFile):
        raise Exception("The input file is not valid")

    df = pd.read_csv(inputFile)

    # Run the PCH
    print("Running PCH")
    outputpch = runPredigPCH(
        df_csv=df,
        input_name=inputFile.split("/")[-1],
        seed=int(seed),
        predigPCH_path=pchPath,
    )
    print("Running MHCflurry")
    # Run the MHCflurry
    outputflurry = runPredigMHCflurry(
        df_csv=df,
        input_name=inputFile.split("/")[-1],
        predigMHCflurry_path=mhcflurryPath,
    )

    print("PCH and MHCflurry finished")
    # Set the output
    block.outputs["output_pch"] = outputpch
    block.outputs["output_flurry"] = outputflurry


predigBlock = PluginBlock(
    name="PredIG",
    description="Predicts the binding affinity of an epitope to an HLA-I allele.",
    action=runPredIG,
    variables=[seedVar],
    inputGroups=[
        VariableGroup(
            id="file_variable_group",
            name="File variable group",
            description="Input with the csv file format.",
            variables=[inputCSV],
        ),
        VariableGroup(
            id="txt_variable_group",
            name="TxtBox variable group",
            description="Input with the txt format.",
            variables=[inputTxtbox],
        ),
    ],
    outputs=[outputPCH, outputFlurry],
)
