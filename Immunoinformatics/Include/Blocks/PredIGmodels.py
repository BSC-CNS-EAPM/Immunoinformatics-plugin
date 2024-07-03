"""
Module containing the mmodule selection block for the Immunoinformatics plugin 
"""

from HorusAPI import InputBlock, PluginVariable, VariableTypes

# ==========================#
# Variable inputs
# ==========================#
modelVar = PluginVariable(
    name="PredIG Model",
    id="model",
    description="The model to use for the prediction",
    type=VariableTypes.STRING_LIST,
    defaultValue="PredIG-NeoA",
    allowedValues=["PredIG-NeoA", "PredIG-NonCan", "PredIG-Path"],
)

predig_modelsBlock = InputBlock(
    name="PredIG Models",
    description="Selection of the PredIG model to use.",
    action=None,
    variable=modelVar,
    id="predig_models",
)
