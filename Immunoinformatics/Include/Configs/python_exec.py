from HorusAPI import PluginConfig, PluginVariable, VariableTypes

python_exect_var = PluginVariable(
    id="python_exec",
    name="Python executable",
    description="Path to the python executable",
    type=VariableTypes.FILE,  # type: ignore
    defaultValue="python",
)

# Create a plugin configuration for the noah executable
python_exec_config = PluginConfig(
    name="Python executable",
    description="Configure the path to the python executable",
    variables=[python_exect_var],
)
