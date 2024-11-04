"""
Module containing the PredIG block for the Immunoinformatics plugin 
"""

import pandas as pd

import random

from typing import Union, cast

from HorusAPI import (
    Extensions,
    PluginBlock,
    PluginVariable,
    CustomVariable,
    VariableTypes,
    InputBlock,
)
from utils import (
    run_Predig_tapmap,
    runPredigMHCflurry,
    runPredigNetCleave,
    runPredigNOAH,
    runPredigPCH,
)


from Pages.setup_predig import setup_predig_page

setup_predig_variable = CustomVariable(
    id="setup_predig",
    name="Setup PredIG",
    description="Setup the PredIG simulation",
    customPage=setup_predig_page,
    type=VariableTypes.ANY,  # type: ignore
)


# ==========================#
# Variable inputs
# ==========================#
# inputCSV = PluginVariable(
#     name="Input CSV",
#     id="input_csv",
#     description="The input csv with the epitope and presenting HLA-I allele.",
#     type=VariableTypes.FILE,
#     allowedValues=["csv"],
# )
# inputTxtbox = PluginVariable(
#     name="Input txtbox",
#     id="input_txtbox",
#     description="The input txt with the epitope and presenting HLA-I allele.",
#     type=VariableTypes.TEXT_AREA,
# )
# modelXGVar = PluginVariable(
#     name="PredIG model",
#     id="modelXGvar",
#     description="The PredIG model.",
#     type=VariableTypes.STRING_LIST,
#     defaultValue="/home/perry/data/Programs/Immuno/Predig/spw_xtreme_predig_model.model",
# )
# input_csv_group = VariableGroup(
#     id="file_variable_group",
#     name="File variable group",
#     description="Input with the csv file format.",
#     variables=[inputCSV, modelXGVar],
# )
# input_txt_group = VariableGroup(
#     id="txt_variable_group",
#     name="TxtBox variable group",
#     description="Input with the txt format.",
#     variables=[inputTxtbox, modelXGVar],
# )


# ==========================#
# Variable outputs
# ==========================#
outputPredIG = PluginVariable(
    name="Output CSV",
    id="output_predig",
    description="The output csv",
    type=VariableTypes.FILE,  # type: ignore
    allowedValues=["csv"],
)


##############################
#       Other variables      #
##############################
# seedVar = PluginVariable(
#     name="Seed",
#     id="seed",
#     description="The seed for the random number generator.",
#     type=VariableTypes.INTEGER,
#     defaultValue=1234,
# )
# modelVar = PluginVariable(
#     name="Model",
#     id="model",
#     description="The model to use.",
#     type=VariableTypes.FILE,
#     defaultValue="/home/perry/data/Programs/Immuno/Neoantigens-NOAH/models/model.pkl",
# )
# hlaVar = PluginVariable(
#     name="HLA allele",
#     id="HLA_allele",
#     description="The HLA allele to use.",
#     type=VariableTypes.STRING,
#     defaultValue="HLA-A02:01",
# )
# peptideLenVar = PluginVariable(
#     name="Peptide length",
#     id="peptide_len",
#     description="The length of the peptide. Give a list of sizes",
#     type=VariableTypes.NUMBER_LIST,
#     defaultValue=None,
# )
# matVar = PluginVariable(
#     name="Matrix",
#     id="mat",
#     description="The matrix to use.",
#     type=VariableTypes.FILE,
#     defaultValue="/home/perry/data/Programs/Immuno/netCTLpan-1.1/data/tap.logodds.mat",
# )
# alphaVar = PluginVariable(
#     name="Alpha",
#     id="alpha",
#     description="The alpha value to use.",
#     type=VariableTypes.FLOAT,
#     defaultValue=None,
# )
# precursorLenVar = PluginVariable(
#     name="Precursor length",
#     id="precursor_len",
#     description="The precursor length to use.",
#     type=VariableTypes.INTEGER,
#     defaultValue=None,
# )


# Align action block
def runPredIG(block: PluginBlock):
    """
    Run the PredIG block
    """

    import os

    import xgboost as xgb

    # Get the input file from group
    # if block.selectedInputGroup == input_txt_group.id:
    #     inputFile = str(block.inputs.get(inputTxtbox.id))
    #     with open("input.csv", "w", encoding="utf-8") as file:
    #         file.write(inputFile)
    #     inputFile = "input.csv"
    # else:
    #     inputFile = block.inputs.get(inputCSV.id, None)

    # Get the input from the setup
    input_setup: Union[dict, None] = block.variables.get(setup_predig_variable.id, None)

    if not input_setup:
        raise ValueError(
            "No input setup was provided. Please click on the 'Configure' button and save the setup."
        )

    input_text: Union[str, None] = input_setup.get("input_text")
    if input_text is None or input_text == "":
        raise ValueError("No input CSV was provided.")
    input_text = cast(str, input_text)

    simulation = input_setup.get("simulation")

    if simulation is None:
        raise ValueError("No simulation mode was provided.")

    simulation = int(simulation)

    alleles = ""
    if simulation != 1:
        # If the file contains tab spaces, save a .tsv file
        if "\t" in input_text:
            input_text = input_text.replace("\t", ",")
        elif "," in input_text:
            pass
        else:
            raise ValueError(
                "The input file must contain tab or comma separated values."
            )
        input_file = "input.csv"
    else:
        alleles = input_setup.get("HLA_alleles", "")
        if not alleles or alleles == "":
            raise ValueError(
                "No HLA alleles were provided. Those are required when running PredIG with fasta files."
            )

        import re

        wrong_alleles = []
        for allele in alleles.split("\n"):
            match = re.match(r"^HLA-[ABC]\*[0-9]{1,3}:[0-9]{1,3}$", allele)
            if not match:
                wrong_alleles.append(allele)

        if len(wrong_alleles) > 0:

            raise ValueError(
                "Please modify or remove the alleles in your list that are not part of the HLA 4-digits resolution format established by IMGT. e.g HLA-A*02:01 or HLA-A*100:101. Binding predictions within PredIG can not interpret other allelic nomenclatures correctly: \n{}".format(
                    "\n".join(wrong_alleles)
                )
            )
        alleles = "\n".join(
            [allele for allele in alleles.split("\n") if allele.strip() != ""]
        )

        input_file = "input.fasta"

    simulation_map = {
        1: "FASTA",
        2: "UNIPROT",
        3: "RECOMBINANT",
    }

    print("====================INPUTS======================")
    print("Input file: ", input_file)
    print("Input text: ", input_text)
    if alleles:
        print("HLA alleles: ", alleles)
    print(f"Simulation type: {simulation_map[simulation]} ({simulation})")
    print("==========================================")

    with open(input_file, "w", encoding="utf-8") as file:
        # Clean the input CSV by removing unnedded quotes "" before writting
        file.write(input_text)

    # Get the seed
    seed = int(input_setup.get("seed", random.randint(0, 10000)))

    # TODO have changed the paths for the lavane, need to be chenged back for perry
    model = input_setup.get(
        "model",
        "/home/perry/data/Programs/Immuno/Neoantigens-NOAH/models/model.pkl",
    )

    # HLA_allele = block.variables.get(hlaVar.id, "HLA-A02:01")
    peptide_len = input_setup.get("peptide_len", None)
    if peptide_len is not None and isinstance(peptide_len, str):
        raise ValueError("The peptide length must be a list of integers")

    peptide_len = [int(p) for p in peptide_len]

    modelXG_name = input_setup.get("modelXG", "PredIG-NeoA")
    if modelXG_name == "PredIG-NonCan":
        modelXG = "/home/perry/data/Programs/Immuno/Predig/spw_indep2_rescale_predig_model.model"
    elif modelXG_name == "PredIG-Path":
        modelXG = "/home/perry/data/Programs/Immuno/Predig/spw_indep1_rescale_predig_model.model"
    else:  # "PredIG-NeoA"
        modelXG = (
            "/home/perry/data/Programs/Immuno/Predig/spw_xtreme_predig_model.model"
        )

    mat = input_setup.get(
        "mat", "/home/perry/data/Programs/Immuno/netCTLpan-1.1/data/tap.logodds.mat"
    )

    if mat is None or mat == "":
        mat = "/home/perry/data/Programs/Immuno/netCTLpan-1.1/data/tap.logodds.mat"

    alpha = input_setup.get("alpha")

    precursor_len = input_setup.get("precursor_len")

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
    if not os.path.isfile(input_file):
        raise ValueError("The input file is not valid")

    df = None
    fasta = None
    if simulation == 1:
        fasta = input_file.replace('"', "").replace("'", "")
    else:
        df = pd.read_csv(input_file)

        # Replace cells that have "" or ''
        df = df.replace('"', "")
        df = df.replace("'", "")

        # Verify that each row has the correct number of columns (all are filled)
        column_lenght = df.shape[1]

        for i, row in df.iterrows():
            if len(row) != column_lenght:
                raise ValueError("The input CSV file must contain the same number of columns in each row.")

        if df.shape[0] > 500:
            raise ValueError("The input CSV file must contain less than 500 rows.")

    print("Running NetCleave")
    # Run the NetCleave / can be placed before to generate csv when case of Fasta
    # When fasta set Hallele in input
    output_netcleave = runPredigNetCleave(
        df_csv=df, predigNetcleave_path=netCleavePath, mode=simulation, fasta=fasta
    )

    # If we are runnign with a fasta, concatenate the results of netcleave with HLA alleles
    if simulation == 1:
        df = output_netcleave

        # Add a new column to the dataframe, the HLA alleles
        alleles: str = input_setup.get("HLA_alleles", "")

        list_alleles = alleles.split("\n")

        # Initialize an empty list to hold DataFrames
        df_list = []

        # Loop through the list of values and create a DataFrame for each one
        for value in list_alleles:
            df_copy = df.copy()
            df_copy["HLA_allele"] = value.strip()
            df_list.append(df_copy)

        df = pd.concat(df_list, ignore_index=True)

        # Remove the index colum (does not have names)
        df = df.reset_index(drop=True)

        # Save as csv
        df.to_csv("input_fasta.csv", index=False)

    else:
        df = cast(pd.DataFrame, df)

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

    print("Running NOAH")

    python_exect = block.config.get("python_exec", "python")
    # Run the NOAH, ["HLA", "epitope", "NOAH_score"] id="HLA", "epitope"
    output_noah = runPredigNOAH(
        df_csv=df, predigNOAH_path=noahPath, model=model, python_exec=python_exect
    )

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
    # df_joined = output_pch.merge(output_flurry, on="epitope", how="inner")
    # df_joined = df_joined.merge(output_netcleave, on="epitope", how="inner")
    # df_joined = df_joined.merge(output_tapmap, on="epitope", how="inner")
    # df_joined = df_joined.merge(output_noah, on="epitope", how="inner")

    df_joined = output_pch.merge(
        output_flurry, left_index=True, right_index=True, how="inner"
    )
    df_joined = df_joined.merge(
        output_netcleave, left_index=True, right_index=True, how="inner"
    )
    df_joined = df_joined.merge(
        output_tapmap,
        left_index=True,
        right_index=True,
        how="inner",
        suffixes=("", "_tapmap"),
    )

    df_joined["id"] = df_joined["hla_allele"] + "_" + df_joined["epitope"]
    output_noah["id"] = output_noah["hla_allele"] + "_" + output_noah["epitope"]
    df_joined = df_joined.merge(
        output_noah, on="id", how="inner", suffixes=("", "_noah")
    )

    print("Launching the XGBoost model")
    if "hla_allele_y" in df_joined.columns:
        df_joined = df_joined.drop(columns=["hla_allele_y"])
    if "hla_allele_x" in df_joined.columns:
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

    # Rename and sort the columns
    name_mapping = {
        "Id": "ID",
        "Epitope": "epitope",
        "Hla_allele": "HLA_allele",
        "Predig": "PredIG",
        "NOAH": "NOAH",
        "TAP": "TAP",
        "Netcleave": "NetCleave",
        "Mhcflurry_affinity": "mhcflurry_affinity",
        "Mhcflurry_affinity_percentile": "mhcflurry_affinity_percentile",
        "Mhcflurry_presentation_score": "mhcflurry_presentation_score",
        "Mhcflurry_processing_score": "mhcflurry_processing_score",
        "Hydroph_peptide": "Hydrophobicity_peptide",
        "Mw_peptide": "MW_peptide",
        "Charge_peptide": "Charge_peptide",
        "Stab_peptide": "Stab_peptide",
        "Tcr_contact": "TCR_contact",
        "Hydroph_tcr_contact": "Hydrophobicity_tcr_contact",
        "Mw_tcr_contact": "MW_tcr_contact",
        "Charge_tcr_contact": "Charge_tcr_contact",
    }

    name_mapping = {key.lower(): value for key, value in name_mapping.items()}

    df_joined = df_joined.rename(str.lower, axis="columns")

    # Sort based on the mapping
    df_joined = df_joined[name_mapping.keys()]

    # Rename
    df_joined = df_joined.rename(columns=name_mapping)

    # Remove unwanted columns
    columns_to_delete: list[str] = block.config.get("columns_to_delete", [])

    columns_to_delete = [c.lower() for c in columns_to_delete]

    for col in df_joined.columns:
        if col.lower() in columns_to_delete:
            df_joined = df_joined.drop(columns=col)

    # Remove any *_output.csv file to prevent other programs messing the folder
    import glob

    for file in glob.glob("*output*.csv"):
        os.remove(file)

    # Save the results as a CSV
    filename = block.flow.name + "_output.csv"
    df_joined.to_csv(filename, index=False)

    print("PredIG simulations finished")

    safe_path = os.path.abspath(filename)

    from App import AppDelegate  # type: ignore

    if AppDelegate().mode == "webapp":

        # Get only the last 3 components of the path /flo_dir/flow_results/results.csv
        safe_path = "/".join(safe_path.split("/")[-3:])

    print(f"Results are at: '{safe_path}'")

    Extensions().open(
        "immuno",
        "results",
        data={"csv": safe_path},
        title="PredIG results",
    )

    Extensions().storeExtensionResults(
        "immuno",
        "results",
        data={"csv": safe_path},
        title="PredIG results",
    )

    # Save the blocklogs to a file
    with open("predig.log", "w") as f:
        f.write(block.blockLogs)

    block.setOutput(outputPredIG.id, filename)


predigBlock = InputBlock(
    name="PredIG",
    description="An interpretable predictor of CD8+ T-cell epitope immunogenicity.\nPredIG predicts the immunogenicity of given pairs of epitope and HLA-I alleles.\nPredIG predicts the immunogenicity of full proteins vs. a list of HLA-I alleles.\nPredIG score is a probability from 0 to 1, being 1 the max likelihood for pHLA-I immunogenicity.\n\nNote: Max 500 queries per submission.",
    action=runPredIG,
    variable=setup_predig_variable,
    # variables=[
    #     seedVar,
    #     modelVar,
    #     hlaVar,
    #     peptideLenVar,
    #     matVar,
    #     alphaVar,
    #     precursorLenVar,
    # ],
    # inputs=[inputCSV, inputTxtbox, modelXGVar],
    output=outputPredIG,
)
