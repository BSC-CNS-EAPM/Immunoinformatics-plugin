from HorusAPI import PluginConfig, PluginVariable, VariableTypes

netCleavePathVariable = PluginVariable(
    id="cleave_path",
    name="NetCleave path",
    description="Path to the NetCleave executable",
    type=VariableTypes.FILE,
    defaultValue="NetCleave.py",
)


def checkNetCleaveInstallation(block: PluginConfig):
    import os

    print("verifying NetCleave installation")

    # Get the path to the netCleave executable
    cleavePath = block.variables.get("cleave_path")

    # Check if the path is valid
    if not os.path.isfile(cleavePath):
        raise Exception("The NetCleave executable path is not valid")


# Create a plugin configuration for the NetCleave executable
netClaveExecutableConfig = PluginConfig(
    name="NetCleave executable",
    description="Configure the path to the NetCleave executable for performing protein alignments",
    variables=[netCleavePathVariable],
    action=checkNetCleaveInstallation,
)