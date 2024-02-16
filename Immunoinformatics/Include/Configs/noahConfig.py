from HorusAPI import PluginConfig, PluginVariable, VariableTypes

noahPathVariable = PluginVariable(
    id="noah_path",
    name="NOAH path",
    description="Path to the NOAH executable",
    type=VariableTypes.FILE,
    defaultValue="NOAH/main_NOAH.py",
)
noahParserPathVariable = PluginVariable(
    id="noah_parser_path",
    name="NOAH parser path",
    description="Path to the NOAH parser executable",
    type=VariableTypes.FILE,
    defaultValue="noah_output_parser.R",
)


def checkNOAHInstallation(block: PluginConfig):
    import os

    print("verifying NOAH installation")

    # Get the path to the noah executable
    noahPath = block.variables.get("noah_path")
    # Get the path to the noah parser executable
    noahParserPath = block.variables.get("noah_parser_path")

    # Check if the path is valid
    if not os.path.isfile(noahPath):
        raise Exception("The NOAH executable path is not valid")
    # Check if the path is valid
    if not os.path.isfile(noahParserPath):
        raise Exception("The NOAH parser executable path is not valid")


# Create a plugin configuration for the mffa executable
noahExecutableConfig = PluginConfig(
    name="NOAH executable",
    description="Configure the path to the NOAH executables for performing protein alignments",
    variables=[noahPathVariable, noahParserPathVariable],
    action=checkNOAHInstallation,
)