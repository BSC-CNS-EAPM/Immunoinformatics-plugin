from HorusAPI import PluginConfig, PluginVariable, VariableTypes

columns_to_delete = PluginVariable(
    id="columns_to_delete",
    name="Columns to remove",
    description="List of columns to remove from the CSV results file. This will drop the columns from the dataframe.",
    type=VariableTypes.LIST,
)

columns_to_delete_config = PluginConfig(
    name="Columns to remove",
    description="List of columns to remove from the CSV results file. This will drop the columns from the dataframe.",
    variables=[columns_to_delete],
)
