from HorusAPI import PluginConfig, PluginVariable, VariableTypes

noahPathVariable = PluginVariable(
    id="noah_path",
    name="NOAH path",
    description="Path to the NOAH executable",
    type=VariableTypes.FILE,
    defaultValue="/home/perry/data/Programs/Immuno/Neoantigens-NOAH/noah/main_NOAH.py",
)


def checkNOAHInstallation(block: PluginConfig):
    import os

    print("verifying NOAH installation")

    # Get the path to the noah executable
    noahPath = block.variables.get(noahPathVariable.id)

    # Check if the path is valid
    # Warn instead of raising: Horus saves every plugin config in a single loop
    # and aborts it on the first exception, which would silently discard the
    # configs saved after this one. The blocks re-check the path when they run.
    if noahPath is None or not os.path.isfile(noahPath):
        print("Warning: the NOAH executable path is not valid on this machine.")


# Create a plugin configuration for the noah executable
noahExecutableConfig = PluginConfig(
    name="NOAH executable",
    description="Configure the path to the NOAH executables",
    variables=[noahPathVariable],
    action=checkNOAHInstallation,
)
