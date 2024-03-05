"""
Module containing the PredIG block for the Immunoinformatics plugin 
"""

import pandas as pd

from HorusAPI import PluginBlock, PluginVariable, VariableGroup, VariableTypes

# ==========================#
# Variable inputs
# ==========================#
inputNetCleave = PluginVariable(
    name="NetCleave CSV",
    id="netCleave_csv",
    description="The output csv from NetCleave.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)
inputNOAH = PluginVariable(
    name="NOAH CSV",
    id="noah_csv",
    description="The output csv from Noah.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)
inputPCH = PluginVariable(
    name="PredIGPCH CSV",
    id="pch_csv",
    description="The output csv from PredIGPCH.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)


# ==========================#
# Variable outputs
# ==========================#
outputFinal = PluginVariable(
    name="Output CSV",
    id="output_final",
    description="The output csv with the final output.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)


# Align action block
def runPredIGMerge(block: PluginBlock):
    """
    Run the PredIG block
    """
    import os

    df_merge = pd.DataFrame()

    # NetCleave
    if os.path.exists(block.inputs["netCleave_csv"]):
        df_netcleave = pd.read_csv(block.inputs["pch_csv"])
        df_merge = pd.merge(df_merge, df_netcleave, on="epitope", how='outer')
    else:
        raise Exception("The csv file of NetCleave does not exist.")

    # NOAH
    if os.path.exists(block.inputs["noah_csv"]):
        df_noah = pd.read_csv(block.inputs["noah_csv"])
        df_merge = pd.merge(df_merge, df_noah, on="id", how='outer')
    else:
        raise Exception("The csv file of NetCleave does not exist.")

    # PCH
    if os.path.exists(block.inputs["pch_csv"]):
        df_pch = pd.read_csv(block.inputs["pch_csv"])
        df_merge = pd.merge(df_merge, df_pch, on="epitope", how='outer')
    else:
        raise Exception("The csv file of PCH does not exist.")
    
    # MHCflurry
    if os.path.exists(block.inputs["mhcflurry_csv"]):
        df_flurry = pd.read_csv(block.inputs["mhcflurry_csv"])
        df_merge = pd.merge(df_merge, df_flurry, on="id", how='outer')
    else:
        raise Exception("The csv file of MHCflurry does not exist.")

    # peptide, mw_peptide, mw_tcr_contact, "
    # hydroph_peptide, hydroph_tcr_contact, charge_peptide, charge_tcr_contact, stab_peptide"
    output_final = "output_merge.csv"

    block.outputs["output_final"] = output_final


predigBlock = PluginBlock(
    name="PredIG",
    description="Predicts the binding affinity of an epitope to an HLA-I allele.",
    action=runPredIGMerge,
    variables=[],
    inputs=[inputNetCleave, inputNOAH, inputPCH],
    outputs=[outputFinal],
)
