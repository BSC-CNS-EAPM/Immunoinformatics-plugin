from HorusAPI import PluginConfig, PluginVariable, VariableTypes

netCleavePathVariable = PluginVariable(
    id="cleave_path",
    name="NetCleave path",
    description="Path to the NetCleave executable",
    type=VariableTypes.FILE,
    defaultValue="/home/perry/data/Programs/Immuno/NetCleave/NetCleave.py",
)


def checkNetCleaveInstallation(block: PluginConfig):
    import os

    print("verifying NetCleave installation")

    # Get the path to the netCleave executable
    cleavePath = block.variables.get(netCleavePathVariable.id)

    # Check if the path is valid
    # Warn instead of raising: an exception here aborts the save of every
    # config that comes after this one (see noahConfig for the details).
    if cleavePath is None or not os.path.isfile(cleavePath):
        print("Warning: the NetCleave executable path is not valid on this machine.")


# Create a plugin configuration for the NetCleave executable
netClaveExecutableConfig = PluginConfig(
    name="NetCleave executable",
    description="Configure the path to the NetCleave executable for performing protein alignments",
    variables=[netCleavePathVariable],
    action=checkNetCleaveInstallation,
)
