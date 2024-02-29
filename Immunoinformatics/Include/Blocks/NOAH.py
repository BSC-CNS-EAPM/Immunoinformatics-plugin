"""
Module containing the NOAH block for the Immunoinformatics plugin 
"""

import os
import subprocess

from HorusAPI import PluginBlock, PluginVariable, VariableGroup, VariableTypes

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
modelVar = PluginVariable(
    name="Model",
    id="model",
    description="The model path to use for the prediction",
    type=VariableTypes.FILE,
    allowedValues=["pkl"],
)

# ==========================#
# Variable outputs
# ==========================#
outputTSVVar = PluginVariable(
    name="Output CSV",
    id="output_csv",
    description="Output file. (with file extension) the output is always a csv.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)

##############################
#       Other variables      #
##############################
seqVar = PluginVariable(
    name="Sequences file",
    id="sequences",
    description="File with the proteic sequences for the unknown HLAs (Selex format) (right now you must give a selex file if there is any HLA not modelled in your list, pending to be changed)",
    type=VariableTypes.FILE,
)
cpusVar = PluginVariable(
    name="CPUs",
    id="cpus",
    description="Number of CPUs to use",
    type=VariableTypes.INTEGER,
    defaultValue=1,
)


def runNOAH(block: PluginBlock):
    """
    Run the NOAH block
    """
    inputFile = block.inputs["input_csv"]
    model = block.inputs["model"]

    noah_path = block.config.get("noah_path", "NOAH/main_NOAH.py")
    noah_parser_path = block.config.get("noah_parser_path", "noah_output_parser.R")

    import pandas as pd

    try:
        os.path.exists(inputFile)
    except Exception as e:
        raise Exception(f"An error occurred while checking the input file: {e}")

    # Load the csv file
    df = pd.read_csv(inputFile)

    # Check if 'peptide' and 'allele' columns exist
    if "peptide" not in df.columns or "allele" not in df.columns:
        raise ValueError("The input CSV file must contain 'peptide' and 'allele' columns.")

    df = df[["peptide", "allele"]]
    df = df.rename(columns={"allele": "HLA"})
    df.to_csv("input_noah.csv", index=False)

    # Run the NOAH
    print("Running NOAH")
    try:
        with subprocess.Popen(
            [
                "python",
                noah_path,
                "-i",
                "input_noah.csv",
                "-m",
                model,
                "-o",
                "output_noah.csv",
            ]
        ) as proc:
            proc.wait()
    except Exception as e:
        raise Exception(f"An error occurred while running the NOAH: {e}")
    print("Parsing NOAH output")

    # try:
    #     subprocess.Popen(
    #         [
    #             "Rscript",
    #             noah_parser_path,
    #             "--input",
    #             "output_noah.csv",
    #         ]
    #     )
    #     proc.wait()
    # except Exception as e:
    #     raise Exception(f"An error occurred while running the NOAH parser: {e}")

    df = pd.read_csv("output_noah.csv", delimiter="\t")

    df.columns = ["allele", "peptide", "NOAH_score"]
    df.to_csv("noah_output_parsed.csv", index=False)

    output = "noah_output_parsed.csv"
    # df = pd.read_csv(output)
    # df = df.rename(columns={"NOAH_score": "NOAH"})
    # df["Peptide_Allele"] = df["peptide"] + "_" + df["allele"]
    # df.to_csv(output, index=False)

    print("NOAH finished")

    # Set output
    block.outputs["output_csv"] = output


# ==========================#
# Block definition
# ==========================#
noahBlock = PluginBlock(
    name="NOAH",
    description="Peptide prediction",
    inputs=[inputFileVar, modelVar],
    outputs=[outputTSVVar],
    variables=[seqVar, cpusVar],
    action=runNOAH,
)
