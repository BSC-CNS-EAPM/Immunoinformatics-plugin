from HorusAPI import PluginConfig, PluginVariable, VariableTypes

noah_model_variable = PluginVariable(
    id="noah_model_path",
    name="NOAH model path",
    description="Path to the NOAH model file",
    type=VariableTypes.FILE,
)

# Create a plugin configuration for the noah model
noah_model = PluginConfig(
    name="NOAH model",
    description="Configure the path to the NOAH model file",
    variables=[noah_model_variable],
)
