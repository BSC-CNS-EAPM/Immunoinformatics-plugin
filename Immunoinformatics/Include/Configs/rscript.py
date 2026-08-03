from HorusAPI import PluginConfig, PluginVariable, VariableTypes

rscript_var = PluginVariable(
    id="rscript_path",
    name="Rscript executable",
    description="Path to the Rscript executable",
    type=VariableTypes.FILE,  # type: ignore
    defaultValue="Rscript",
)

# Create a plugin configuration for the Rscript executable
rscript_config = PluginConfig(
    name="Rscript executable",
    description="Configure the path to the Rscript executable",
    variables=[rscript_var],
)
