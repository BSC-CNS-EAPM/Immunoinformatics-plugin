from HorusAPI import PluginConfig, PluginVariable, VariableTypes

netCTLpanPathVariable = PluginVariable(
    id="netCTLpan_path",
    name="netCTLpan path",
    description="Path to the netCTLpan executable",
    type=VariableTypes.FILE,
    defaultValue="/home/perry/data/Programs/Immuno/netCTLpan-1.1/netCTLpan",
)


def checkInstallation(block: PluginConfig):
    import os

    print("verifying netCTLpan installation")

    netCTLpan_path = block.variables.get(netCTLpanPathVariable.id)
    # Check if the path is valid
    if netCTLpan_path is None or not os.path.isfile(netCTLpan_path):
        raise Exception("The netCTLpan executable path is not valid")


# Create a plugin configuration for the noah executable
netCTLpanExecutableConfig = PluginConfig(
    name="netCTLpan executable",
    description="Configure the path to the netCTLpan executables",
    variables=[netCTLpanPathVariable],
    action=checkInstallation,
)
