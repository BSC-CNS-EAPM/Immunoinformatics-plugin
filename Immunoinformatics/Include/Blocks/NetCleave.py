"""
Module containing the NetCleave block for the Immunoinformatics plugin 
"""

from HorusAPI import (
    Extensions,
    PluginBlock,
    PluginVariable,
    VariableGroup,
    VariableTypes,
)

# ==========================#
# Variable inputs
# ==========================#
inputFileVar = PluginVariable(
    name="Input CSV peptides",
    id="input_csv",
    description="File with the peptides to Predict. The file must have the following structure; peptide  HLA",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)
inputFastaVar = PluginVariable(
    name="Input fasta",
    id="input_fasta",
    description="FASTA file of a single protein, from which epitopes will be generated and scored.",
    type=VariableTypes.FILE,
    allowedValues=["fasta"],
)
csvVariableGroup = VariableGroup(
    id="csv_variable_group",
    name="Csv variable group",
    description="Input csv file.",
    variables=[inputFileVar],
)
fastaVariableGroup = VariableGroup(
    id="fasta_variable_group",
    name="Fasta file group",
    description="Input Fasta file.",
    variables=[inputFastaVar],
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
    import os
    import shutil
    import subprocess

    import pandas as pd

    if block.selectedInputGroup == csvVariableGroup.id:
        inputFile = block.inputs.get(inputFileVar.id, None)
        try:
            os.path.exists(inputFile)
        except Exception as e:
            raise Exception(f"An error occurred while checking the input file: {e}")

        # Load the csv file
        df_csv = pd.read_csv(inputFile)

        if df_csv.shape[0] > 500:
            raise ValueError("The input CSV file must contain less than 500 rows.")

        # Check if 'peptide' and 'epitope' columns exist
        if "peptide" not in df_csv.columns and "epitope" not in df_csv.columns:
            raise ValueError(
                "The input CSV file must contain 'peptide' or 'epitope' column."
            )
        # Rename 'peptide' column to 'epitope'
        if "peptide" in df_csv.columns:
            df_csv = df_csv.rename(columns={"peptide": "epitope"})

        # Check if 'uniprot_id' or 'protein_seq' columns exist to define the input type
        if "uniprot_id" not in df_csv.columns:
            if "protein_seq" not in df_csv.columns:
                raise ValueError(
                    "The input CSV file must contain 'uniprot_id' or 'protein_seq' column."
                )
            else:
                input_type = 3
                df_csv = df_csv[["epitope", "protein_name", "protein_seq"]]
        else:
            input_type = 2
            df_csv = df_csv[["epitope", "uniprot_id"]]

        df_csv.to_csv(".input_NetCleave.csv", index=False)
        in_netcleave = ".input_NetCleave.csv"
    else:
        in_netcleave = block.inputs.get(inputFastaVar.id, None)
        with open(in_netcleave, "rbU") as f:
            num_lines = sum(1 for _ in f)
        if num_lines > 1000:
            raise ValueError("The input FASTA file must contain less than 500 FASTAs.")
        try:
            os.path.exists(in_netcleave)
        except Exception as e:
            raise Exception(f"An error occurred while checking the input file: {e}")
        in_name = os.path.basename(in_netcleave).split(".")[0]
        input_type = 1

    netCleavePath = block.config.get(
        "cleave_path", "/home/perry/data/Github/NetCleave/NetCleave.py"
    )

    # Run the NetCleave
    try:
        proc = subprocess.Popen(
            [
                "/home/perry/miniconda3/envs/horus/bin/python",
                netCleavePath,
                "--predict",
                in_netcleave,
                "--pred_input",
                str(input_type),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate()
        print("Output:", stdout.decode())
        print("Error:", stderr.decode())
    except Exception as e:
        raise Exception(f"An error occurred while running the NetCleave: {e}")

    output = "output_NetCleave.csv"
    if input_type != 1:
        df = pd.read_csv("output/_NetCleave.csv")
        os.remove(".input_NetCleave.csv")
    else:
        df = pd.read_csv(f"output/{in_name}_NetCleave.csv")

    df = df.rename(columns={"Unnamed: 0": "n"})
    df.to_csv(output, index=False)

    shutil.rmtree("output")

    print("NetCleave finished")

    # Generate HTML from template.
    from itables import to_html_datatable

    html = to_html_datatable(df, display_logo_when_loading=False)
    with open("interactive_table.html", "w", encoding="utf-8") as filehtml:
        filehtml.write(html)

    Extensions().storeExtensionResults(
        "immuno",
        "load_tables",
        data={"path": os.path.abspath("interactive_table.html")},
        title="NetCleave results",
    )

    # Set output
    block.setOutput(outputCSVVar.id, output)


# ==========================#
# Block definition
# ==========================#
netCleaveBlock = PluginBlock(
    name="NetCleave",
    description="NetCleave allows the prediction of C-terminal peptide processing of MHC pathways. Max 500 queries.",
    inputGroups=[csvVariableGroup, fastaVariableGroup],
    outputs=[outputCSVVar],
    variables=[],
    action=runNetCleave,
)
