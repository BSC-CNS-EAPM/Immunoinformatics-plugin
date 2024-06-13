from HorusAPI import PluginConfig, PluginVariable, VariableTypes

noahPathVariable = PluginVariable(
    id="noah_path",
    name="NOAH path",
    description="Path to the NOAH executable",
    type=VariableTypes.FILE,
    defaultValue="NOAH/main_NOAH.py",
)


def checkNOAHInstallation(block: PluginConfig):
    import os

    print("verifying NOAH installation")

    # Get the path to the noah executable
    noahPath = block.variables.get("noah_path")

    # Check if the path is valid
    if not os.path.isfile(noahPath):
        raise Exception("The NOAH executable path is not valid")


# Create a plugin configuration for the noah executable
noahExecutableConfig = PluginConfig(
    name="NOAH executable",
    description="Configure the path to the NOAH executables for performing protein alignments",
    variables=[noahPathVariable],
    action=checkNOAHInstallation,
)
