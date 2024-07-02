"""
Module containing the mmodule selection block for the Immunoinformatics plugin 
"""

from HorusAPI import PluginBlock, PluginVariable, VariableTypes

# ==========================#
# Variable inputs
# ==========================#
modelVar = PluginVariable(
    name="Model",
    id="model",
    description="The model path to use for the prediction",
    type=VariableTypes.STRING_LIST,
    defaultValue="model1",
    allowedValues=["model1", "model2", "model3"],
)


# ==========================#
# Variable outputs
# ==========================#
outputModel = PluginVariable(
    name="Output model",
    id="output_model",
    description="Output model.",
    type=VariableTypes.FILE,
)

##############################
#       Other variables      #
##############################


def model_selection(block: PluginBlock):
    """
    Run the model block
    """

    model = block.inputs.get(modelVar.id, None)
    if model is None:
        raise ValueError("Model not found")

    if model == "model1":
        model_path = "/home/perry/data/Programs/Immuno/Predig/spw_xtreme_predig_model.model"
    elif model == "model2":
        model_path = "/home/perry/data/Programs/Immuno/Predig/spw_xtreme_predig_model.model"
    elif model == "model3":
        model_path = "/home/perry/data/Programs/Immuno/Predig/spw_xtreme_predig_model.model"

    # Set output
    block.setOutput(outputModel.id, model_path)


# ==========================#
# Block definition
# ==========================#
predigModelsBlock = PluginBlock(
    name="PredIGModels",
    description="PredIG input models",
    inputs=[modelVar],
    outputs=[outputModel],
    action=model_selection,
)
