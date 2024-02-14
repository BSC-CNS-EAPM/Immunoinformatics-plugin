"""
Module containing the PredIG block for the Immunoinformatics plugin 
"""

from HorusAPI import PluginVariable, VariableTypes, PluginBlock, VariableGroup

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
    type=VariableTypes.STRING,
)
InputFolderVariableGroup = VariableGroup(
    id="file_variable_group",
    name="File variable group",
    description="Input with the csv file format.",
    variables=[inputCSV],
)
InputTxtVariableGroup = VariableGroup(
    id="txt_variable_group",
    name="TxtBox variable group",
    description="Input with the txt format.",
    variables=[inputTxtbox],
)

# ==========================#
# Variable outputs
# ==========================#
outputTSV = PluginVariable(
    name="Output TSV",
    id="output_csv",
    description="The output tsv with the predicted binding affinity.",
    type=VariableTypes.FILE,
    allowedValues=["tsv"],
)

##############################
#       Other variables      #
##############################
jobName = PluginVariable(
    name="Job name",
    id="job_name",
    description="The name of the job.",
    type=VariableTypes.STRING,
    defaultValue="PredIG Job",
)



# Align action block
def runPredIG(block: PluginBlock):
    pass


predigBlock = PluginBlock(
    name="PredIG",
    description="Predicts the binding affinity of an epitope to an HLA-I allele.",
    action=runPredIG,
    variables=[jobName],
    inputs=[InputFolderVariableGroup, InputTxtVariableGroup],
    outputs=[outputTSV],
)
