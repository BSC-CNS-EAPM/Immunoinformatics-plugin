"""
Module containing the PredIG block for the Immunoinformatics plugin 
"""

import pandas as pd
from utils import (
    run_Predig_tapmap,
    runPredigMHCflurry,
    runPredigNetCleave,
    runPredigNOAH,
    runPredigPCH,
)

from HorusAPI import Extensions, PluginBlock, PluginVariable, VariableGroup, VariableTypes

# TODO modify the modul as input from the model selection block
# TODO create the template flow


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
modelXGVar = PluginVariable(
    name="PredIG model",
    id="modelXGvar",
    description="The PredIG model.",
    type=VariableTypes.STRING_LIST,
    defaultValue="/home/perry/data/Programs/Immuno/Predig/spw_xtreme_predig_model.model",
)
input_csv_group = VariableGroup(
    id="file_variable_group",
    name="File variable group",
    description="Input with the csv file format.",
    variables=[inputCSV, modelXGVar],
)
input_txt_group = VariableGroup(
    id="txt_variable_group",
    name="TxtBox variable group",
    description="Input with the txt format.",
    variables=[inputTxtbox, modelXGVar],
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
    defaultValue=1234,
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
    description="The length of the peptide. Give a list of sizes",
    type=VariableTypes.NUMBER_LIST,
    defaultValue=None,
)
matVar = PluginVariable(
    name="Matrix",
    id="mat",
    description="The matrix to use.",
    type=VariableTypes.FILE,
    defaultValue="/home/perry/data/Programs/Immuno/netCTLpan-1.1/data/tap.logodds.mat",
)
alphaVar = PluginVariable(
    name="Alpha",
    id="alpha",
    description="The alpha value to use.",
    type=VariableTypes.FLOAT,
    defaultValue=None,
)
precursorLenVar = PluginVariable(
    name="Precursor length",
    id="precursor_len",
    description="The precursor length to use.",
    type=VariableTypes.INTEGER,
    defaultValue=None,
)


# Align action block
def runPredIG(block: PluginBlock):
    """
    Run the PredIG block
    """

    import os

    import xgboost as xgb

    # Get the input file
    if block.selectedInputGroup == input_txt_group.id:
        inputFile = str(block.inputs.get(inputTxtbox.id))
        with open("input.csv", "w") as file:
            file.write(inputFile)
        inputFile = "input.csv"
    else:
        inputFile = block.inputs.get(inputCSV.id, None)

    if inputFile is None:
        raise Exception("No input file was provided")

    # Get the seed
    seed = int(block.variables.get(seedVar.id, 123))
    model = block.inputs.get(
        modelVar.id,
        "/home/perry/data/Programs/Immuno/Neoantigens-NOAH/models/model.pkl",
    )

    HLA_allele = block.variables.get(hlaVar.id, "HLA-A02:01")
    peptide_len = block.variables.get(peptideLenVar.id, None)  # 8..14
    if peptide_len is not None and type(peptide_len) == str:
        raise ValueError("The peptide length must be a list of integers")

    modelXG_name = block.variables.get(modelXGVar.id, None)
    if modelXG_name == "PredIG-NonCan":
        modelXG = "/home/perry/data/Programs/Immuno/Predig/spw_indep2_rescale_predig_model.model"
    elif modelXG_name == "PredIG-Path":
        modelXG = "/home/perry/data/Programs/Immuno/Predig/spw_indep1_rescale_predig_model.model"
    else:  # "PredIG-NeoA"
        modelXG = "/home/perry/data/Programs/Immuno/Predig/spw_xtreme_predig_model.model"

    mat = block.variables.get(matVar.id, None)
    alpha = block.variables.get(alphaVar.id, None)
    precursor_len = block.variables.get(precursorLenVar.id, None)

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
    tapmat_pred_fsa_path = block.config.get(
        "tapmap_path",
        "/home/perry/data/Programs/Immuno/netCTLpan-1.1/Linux_x86_64/bin/tapmat_pred_fsa",
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

    print("Running tapmat_pred_fsa")
    output_tapmap = run_Predig_tapmap(
        df_csv=df,
        tapmap_path=tapmat_pred_fsa_path,
        mat=mat,
        peptide_len=peptide_len,
        alpha=alpha,
        precursor_len=precursor_len,
    )

    print("Joining the outputs")

    # Sequentially merge the DataFrames on a common non-overlapping column, for example 'epitope'
    df_joined = output_noah.merge(output_flurry, on="epitope", how="inner")
    df_joined = df_joined.merge(output_pch, on="epitope", how="inner")
    df_joined = df_joined.merge(output_netcleave, on="epitope", how="inner")
    df_joined = df_joined.merge(output_tapmap, on="epitope", how="inner")

    print("Launching the XGBoost model")
    df_joined = df_joined.drop(columns=["hla_allele_y"])
    df_joined = df_joined.rename(columns={"hla_allele_x": "hla_allele"})
    # df_joined.to_csv("outputs_parsed.csv", index=False)

    df_xgboost = df_joined[
        [
            "netcleave",
            "NOAH",
            "mw_peptide",
            "mw_tcr_contact",
            "hydroph_peptide",
            "hydroph_tcr_contact",
            "charge_peptide",
            "charge_tcr_contact",
            "stab_peptide",
            "mhcflurry_affinity",
            "mhcflurry_affinity_percentile",
            "mhcflurry_processing_score",
            "mhcflurry_presentation_score",
        ]
    ]

    # df_xgboost.to_csv("df_xgboost.csv", index=False)
    predig_model = xgb.Booster()
    predig_model.load_model(modelXG)
    predig_input_matrix = xgb.DMatrix(df_xgboost)
    predig_score = predig_model.predict(predig_input_matrix)
    df_joined = pd.concat([df_joined, pd.Series(predig_score, name="predig")], axis=1)

    df_joined["id"] = df_joined["hla_allele"] + "_" + df_joined["epitope"]
    df_joined.to_csv("predig_output.csv", index=False)

    print("PredIG simulations finished")

    html = df_joined.to_html(index=False)
    Extensions().loadHTML(html, title="PredIG results")

    # Set the output
    block.setOutput(outputPredIG.id, "predig_output.csv")


predigBlock = PluginBlock(
    name="PredIG",
    description="Predicts Predicts T-cell immunogenicity of given epitope and HLA-I allele pairs (pHLAs).",
    action=runPredIG,
    variables=[
        seedVar,
        modelVar,
        hlaVar,
        peptideLenVar,
        matVar,
        alphaVar,
        precursorLenVar,
    ],
    inputGroups=[input_csv_group, input_txt_group],
    outputs=[outputPredIG],
)
