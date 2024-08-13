from HorusAPI import PluginConfig, PluginVariable, VariableTypes

PCHPathVariable = PluginVariable(
    id="PCH_path",
    name="PCH path",
    description="Path to the PCH executable",
    type=VariableTypes.FILE,
    defaultValue="/home/lavane/sda/Users/acanella/Immuno/predig_pch_calc.R",
)


def checkInstallations(block: PluginConfig):
    import os

    print("verifying PCH installation")

    # Get the path to the noah executable
    predig_PCH = block.variables.get(PCHPathVariable.id)
    # Get the path to the noah parser executable

    # Check if the path is valid
    if predig_PCH is None or not os.path.isfile(predig_PCH):
        raise Exception("The PCH executable path is not valid")


# Create a plugin configuration for the PredIG executables
pchExecutableConfig = PluginConfig(
    name="PCH executables",
    description="Configure the path to the PCH executables.",
    variables=[PCHPathVariable],
    action=checkInstallations,
)
