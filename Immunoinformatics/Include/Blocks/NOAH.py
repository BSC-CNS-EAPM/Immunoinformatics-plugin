"""
Module containing the NOAH block for the Immunoinformatics plugin 
"""

from HorusAPI import Extensions, PluginBlock, PluginVariable, VariableTypes

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
# seqVar = PluginVariable(
#     name="Sequences file",
#     id="sequences",
#     description="File with the proteic sequences for the unknown HLAs (Selex format) (right now you must give a selex file if there is any HLA not modelled in your list, pending to be changed)",
#     type=VariableTypes.FILE,
# )
# cpusVar = PluginVariable(
#     name="CPUs",
#     id="cpus",
#     description="Number of CPUs to use",
#     type=VariableTypes.INTEGER,
#     defaultValue=1,
# )
modelVar = PluginVariable(
    name="Model",
    id="model",
    description="The model path to use for the prediction",
    type=VariableTypes.FILE,
    allowedValues=["pkl"],
    defaultValue="/home/perry/data/Programs/Immuno/Neoantigens-NOAH/models/model.pkl",
)


def runNOAH(block: PluginBlock):
    """
    Run the NOAH block
    """

    import os
    import subprocess

    import pandas as pd

    inputFile = block.inputs.get(inputFileVar.id, None)
    model = block.variables.get(
        modelVar.id,
        "/home/perry/data/Programs/Immuno/Neoantigens-NOAH/models/model.pkl",
    )

    # Get the Noah path
    noahPath = block.config.get(
        "noah_path", "/home/perry/data/Github/Neoantigens-NOAH/noah/main_NOAH.py"
    )

    try:
        os.path.exists(inputFile)
    except Exception as e:
        raise Exception(f"An error occurred while checking the input file: {e}")

    # Load the csv file
    df_csv = pd.read_csv(inputFile)

    # Check if 'peptide' and 'allele' columns exist
    if "peptide" not in df_csv.columns or "allele" not in df_csv.columns:
        if not "peptide" in df_csv.columns and "HLA" not in df_csv.columns:
            raise ValueError(
                "The input CSV file must contain 'peptide' and 'allele' or HLA columns."
            )

    df_csv = df_csv[["peptide", "allele"]]
    df_csv = df_csv.rename(columns={"allele": "HLA"})
    df_csv.to_csv(".input_noah.csv", index=False)

    # Run the NOAH
    try:
        with subprocess.Popen(
            [
                "python",
                noahPath,
                "-i",
                ".input_noah.csv",
                "-m",
                model,
                "-o",
                ".output_noah.csv",
            ]
        ) as proc:
            proc.wait()
    except Exception as e:
        raise Exception(f"An error occurred while running the NOAH: {e}")
    print("Parsing NOAH output")

    output = "output_noah_parsed.csv"

    df = pd.read_csv(
        ".output_noah.csv",
        delimiter="\t",
        header=None,
    )
    df.to_csv(output, index=True)

    os.remove(".input_noah.csv")
    os.remove(".output_noah.csv")

    print("NOAH finished")

    from itables import to_html_datatable

    html = to_html_datatable(
        df, display_logo_when_loading=False, maxRows=501, showIndex=True
    )
    with open("interactive_table.html", "w", encoding="utf-8") as filehtml:
        filehtml.write(html)

    Extensions().storeExtensionResults(
        "immuno",
        "load_tables",
        data={"path": os.path.abspath("interactive_table.html")},
        title="NetCleave results",
    )

    # Set output
    block.setOutput(outputTSVVar.id, output)


# ==========================#
# Block definition
# ==========================#
noahBlock = PluginBlock(
    name="NOAH",
    description="Peptide prediction",
    inputs=[inputFileVar],
    outputs=[outputTSVVar],
    variables=[modelVar],
    action=runNOAH,
)
