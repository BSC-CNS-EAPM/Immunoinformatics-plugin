"""
Module containing the PredIG block for the Immunoinformatics plugin 
"""

import os

import pandas as pd
from HorusAPI import PluginBlock, PluginVariable, VariableGroup, VariableTypes
from utils import (
    run_Predig_netCTLpan,
    runPredigMHCflurry,
    runPredigNetCleave,
    runPredigNOAH,
    runPredigPCH,
)

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
outputPredIG = PluginVariable(
    name="Output CSV",
    id="output_predig",
    description="The output csv",
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
modelVar = PluginVariable(
    name="Model",
    id="model",
    description="The model to use.",
    type=VariableTypes.FILE,
    defaultValue="/home/perry/data/Programs/Immuno/Neoantigens-NOAH/models/model.pkl",
)
hlaVar = PluginVariable(
    name="HLA allele",
    id="HLA_allele",
    description="The HLA allele to use.",
    type=VariableTypes.STRING,
    defaultValue="HLA-A02:01",
)
peptideLenVar = PluginVariable(
    name="Peptide length",
    id="peptide_len",
    description="The length of the peptide.",
    type=VariableTypes.INTEGER,
    defaultValue=9,
)
modelXGVar = PluginVariable(
    name="XGBoost model",
    id="modelXG",
    description="The XGBoost model to use.",
    type=VariableTypes.FILE,
    defaultValue="/home/perry/data/Programs/Immuno/Predig/spw_xtreme_predig_model.model",
)


# Align action block
def runPredIG(block: PluginBlock):
    """
    Run the PredIG block
    """

    import subprocess

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
    seed = int(block.variables.get(seedVar.id, 123))
    model = block.variables.get(
        modelVar.id,
        "/home/perry/data/Programs/Immuno/Neoantigens-NOAH/models/model.pkl",
    )
    HLA_allele = block.variables.get(hlaVar.id, "HLA-A02:01")
    peptide_len = block.variables.get(peptideLenVar.id, 9)
    modelXG = block.variables.get(modelXGVar.id)

    # Get the PCH path
    pchPath = block.config.get(
        "PCH_path", "/home/albertcs/Projects/ROC/pch_inout/predig_pch_calc.R"
    )
    # Get the MHCflurry path
    mhcflurryPath = block.config.get("MHC_path", "mhcflurry-predict")
    # Get the NetCleave path
    netCleavePath = block.config.get(
        "cleave_path", "/home/perry/data/Github/NetCleave/NetCleave.py"
    )
    # Get the NOah path
    noahPath = block.config.get(
        "noah_path", "/home/perry/data/Github/Neoantigens-NOAH/noah/main_NOAH.py"
    )
    # Get the netCTLpan path
    netCTLpanPath = block.config.get(
        "netCTLpan_path", "/home/perry/data/Programs/Immuno/netCTLpan-1.1/netCTLpan"
    )
    predig_script_path = block.config.get(
        "spwindep_path",
        "/home/perry/data/Programs/Immuno/Predig/predig_spwindep_calc.R",
    )

    # /home/perry/data/Github/Neoantigens-NOAH/noah/main_NOAH.py
    # Check if the input file is valid
    if not os.path.isfile(inputFile):
        raise Exception("The input file is not valid")

    df = pd.read_csv(inputFile)

    # Run the PCH ["epitope"]
    print("Running PCH")
    output_pch = runPredigPCH(
        df_csv=df,
        seed=int(seed),
        predigPCH_path=pchPath,
    )

    print("Running MHCflurry")
    # Run the MHCflurry ["epitope", "hla_allele"]
    output_flurry = runPredigMHCflurry(
        df_csv=df,
        predigMHCflurry_path=mhcflurryPath,
    )

    print("Running NetCleave")
    # Run the NetCleave
    output_netcleave = runPredigNetCleave(df_csv=df, predigNetcleave_path=netCleavePath)

    print("Running NOAH")
    # Run the NOAH, ["HLA", "epitope", "NOAH_score"] id="HLA", "epitope"
    output_noah = runPredigNOAH(df_csv=df, predigNOAH_path=noahPath, model=model)

    print("Running netCTLpan")
    output_netCTLpan = run_Predig_netCTLpan(
        df_csv=df,
        predignetCTLpan_path=netCTLpanPath,
        HLA_allele=HLA_allele,
        peptide_len=peptide_len,
    )

    print("Joining the outputs")
    # join all the outputs dataframes by index
    df_joined = pd.concat(
        [output_noah, output_flurry, output_pch, output_netcleave, output_netCTLpan],
        axis=1,
        join="inner",
    )

    print("Launching the XGBoost model")
    df_joined.to_csv("outputs_parsed.csv", index=False)

    try:
        proc = subprocess.Popen(
            [
                "Rscript",
                predig_script_path,
                "--input",
                "outputs_parsed.csv",
                "--seed",
                str(seed),
                "--model",
                str(modelXG),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate()
        print("Output:", stdout.decode())
        print("Error:", stderr.decode())
    except Exception as e:
        raise Exception(f"An error occurred while running the predig XGBoost: {e}")

    print("PredIG simulations finished")
    output = "outputs_parsed_predig.csv"
    # Set the output
    block.setOutput(outputPredIG.id, df_joined.to_csv(output, index=False))


predigBlock = PluginBlock(
    name="PredIG",
    description="Predicts the binding affinity of an epitope to an HLA-I allele.",
    action=runPredIG,
    variables=[seedVar, modelVar, hlaVar, peptideLenVar],
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
    outputs=[outputPredIG],
)
