from HorusAPI import PluginConfig, PluginVariable, VariableTypes

spwindepPathVariable = PluginVariable(
    id="spwindep_path",
    name="Predig XGBoost script",
    description="Predig XGBoost script path",
    type=VariableTypes.FILE,
    defaultValue="/home/perry/data/Programs/Immuno/Predig/predig_spwindep_calc.R",
)


def checkInstallations(block: PluginConfig):
    import os

    print("verifying Predig XGBoost script installation")

    spwindep_path = block.variables.get(spwindepPathVariable.id)

    # Check if the path is valid
    if spwindep_path is None or not os.path.isfile(spwindep_path):
        raise Exception("The Predig XGBoost script executable path is not valid")


# Create a plugin configuration for the PredIG executables
pchExecutableConfig = PluginConfig(
    name="Predig XGBoost script executables",
    description="Configure the path to the Predig XGBoost script executables.",
    variables=[spwindepPathVariable],
    action=checkInstallations,
)
