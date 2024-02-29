"""
Module containing the PredIG block for the Immunoinformatics plugin 
"""

from HorusAPI import PluginVariable, VariableTypes, PluginBlock, VariableGroup
from utils import runPredigPCH, runPredigMHCflurry
import pandas as pd

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
seed = PluginVariable(
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
    import os
    
    df_merge = pd.DataFrame()
    
    if os.path.exists(block.inputs["netCleave_csv"]):
        df_merge['netcleave'] = pd.read_csv(block.inputs["netCleave_csv"])[['netcleave']]
    else:
        raise Exception("The csv file of NetCleave does not exist.")
    
    if os.path.exists(block.inputs["noah_csv"]):
        df_noah = pd.read_csv(block.inputs["noah_csv"])
        df_merge['Peptide_Allele'] = df_noah[['Peptide_Allele']]
        df_merge['NOAH'] = df_noah[['NOAH']]
    else:
        raise Exception("The csv file of NetCleave does not exist.")
    
    if os.path.exists(block.inputs["pch_csv"]):
        df_pch = pd.read_csv(block.inputs["pch_csv"])
        df_merge['Peptide'] = df_pch[['peptide']]
    else:
        raise Exception("The csv file of NetCleave does not exist.")
    
    # peptide, mw_peptide, mw_tcr_contact, "
    # hydroph_peptide, hydroph_tcr_contact, charge_peptide, charge_tcr_contact, stab_peptide"
    
    
    
    
    block.outputs["output_flurry"] = outputflurry

predigBlock = PluginBlock(
    name="PredIG",
    description="Predicts the binding affinity of an epitope to an HLA-I allele.",
    action=runPredIG,
    variables=[seed],
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
            )
    ],
    outputs=[outputPCH, outputFlurry],
)
