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
    type=VariableTypes.TEXT_AREA,
)
modelVar = PluginVariable(
    name="Model",
    id="model",
    description="The model path to use for the prediction",
    type=VariableTypes.FILE,
    allowedValues=["model"],
)

# ==========================#
# Variable outputs
# ==========================#
outputTSV = PluginVariable(
    name="Output CSV",
    id="output_csv",
    description="The output tsv with the predicted binding affinity.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
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
seed = PluginVariable(
    name="Seed",
    id="seed",
    description="The seed for the random number generator.",
    type=VariableTypes.INTEGER,
    defaultValue=123,
)

# Align action block
def runPredIG(block: PluginBlock):
    pass


predigBlock = PluginBlock(
    name="PredIG",
    description="Predicts the binding affinity of an epitope to an HLA-I allele.",
    action=runPredIG,
    variables=[jobName],
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
    outputs=[outputTSV],
)
