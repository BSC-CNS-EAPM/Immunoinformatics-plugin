"""
Module containing the NetCleave block for the Immunoinformatics plugin 
"""

from utils import run_Predig_tapmap

from HorusAPI import Extensions, PluginBlock, PluginVariable, VariableGroup, VariableTypes

# ==========================#
# Variable inputs
# ==========================#
inputFileVar = PluginVariable(
    name="Input FASTA peptides",
    id="input_fasta",
    description="File with the peptides to Predict. The file must have the following structure; peptide  HLA",
    type=VariableTypes.FILE,
    allowedValues=["fasta"],
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

##############################
#       Other variables      #
##############################
matVar = PluginVariable(
    name="Matrix",
    id="mat",
    description="The matrix to use.",
    type=VariableTypes.FILE,
    defaultValue="/home/perry/data/Programs/Immuno/netCTLpan-1.1/data/tap.logodds.mat",
)
peptideLenVar = PluginVariable(
    name="Peptide length",
    id="peptide_len",
    description="The length of the peptide. Give a list of sizes",
    type=VariableTypes.NUMBER_LIST,
    defaultValue=None,
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


def runTAP(block: PluginBlock):
    """
    Run the NetCleave block
    """
    import os
    import shutil
    import subprocess

    import pandas as pd

    inputFile = block.inputs.get(inputFileVar.id, None)
    try:
        os.path.exists(inputFile)
    except Exception as e:
        raise Exception(f"An error occurred while checking the input file: {e}")

    # Load the csv file
    tapmat_pred_fsa_path = block.config.get(
        "tapmap_path",
        "/home/perry/data/Programs/Immuno/netCTLpan-1.1/Linux_x86_64/bin/tapmat_pred_fsa",
    )
    mat = block.variables.get(matVar.id, None)

    peptide_len = block.variables.get(peptideLenVar.id, None)  # 8..14
    if peptide_len is not None and isinstance(peptide_len, str):
        raise ValueError("The peptide length must be a list of integers")

    alpha = block.variables.get(alphaVar.id, None)
    precursor_len = block.variables.get(precursorLenVar.id, None)

    # Run the TAP

    dict_sizes = {}
    with open(inputFile, "r") as f:
        for line in f:
            if line.startswith(">"):
                continue
            peptide = line.strip()
            if len(peptide) not in dict_sizes:
                dict_sizes[len(peptide)] = []
            dict_sizes[len(peptide)].append(peptide)

    for size in dict_sizes:
        with open(f".input_tapmap_{size}.fasta", "w") as f:
            for i, peptide in enumerate(dict_sizes[size]):
                f.write(f">{i}\n")
                f.write(peptide + "\n")

    for size in dict_sizes:
        print(f"Running tapmap for peptides of size {size}")
        command = tapmat_pred_fsa_path
        if mat:
            command += f" -mat {mat} "
        if alpha:
            command += f"-a {alpha} "
        command += f"-l {size} "
        if precursor_len:
            command += f"-pl {precursor_len} "
        command += f".input_tapmap_{size}.fasta > .output_tapmap_{size}.txt"
        try:
            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
            )
            stdout, stderr = proc.communicate()
            print("Output:", stdout.decode())
            print("Error:", stderr.decode())
        except Exception as e:
            raise Exception(f"An error occurred while running the tapmap size={size}: {e}")

    print("Parsing tapmap output")

    epitope = []
    tap = []
    for size in dict_sizes:
        with open(f".output_tapmap_{size}.txt", "r") as infile:
            for line in infile:
                if not line.startswith("#"):
                    parts = line.split()
                    if len(parts) >= 3:  # Ensure there are at least three parts in the line
                        epitope.append(parts[1])
                        tap.append(parts[2])

    for size in dict_sizes:
        os.remove(f".input_tapmap_{size}.fasta")
        os.remove(f".output_tapmap_{size}.txt")

    df = pd.DataFrame({"epitope": epitope, "TAP": tap})
    df.to_csv("output_tapmap.csv", index=False)

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
    block.setOutput(outputCSVVar.id, "output_tapmap.csv")


# ==========================#
# Block definition
# ==========================#
tapBlock = PluginBlock(
    name="TAP",
    description="TAP. Max 500 queries.",
    inputs=[inputFileVar],
    outputs=[outputCSVVar],
    variables=[matVar, peptideLenVar, alphaVar, precursorLenVar],
    action=runTAP,
)
