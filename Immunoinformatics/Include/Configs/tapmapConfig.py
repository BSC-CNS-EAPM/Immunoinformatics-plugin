from HorusAPI import PluginConfig, PluginVariable, VariableTypes

tapmapPathVariable = PluginVariable(
    id="tapmap_path",
    name="tapmap path",
    description="Path to the tapmap_pred_fsa executable",
    type=VariableTypes.FILE,
    defaultValue="/home/perry/data/Programs/Immuno/netCTLpan-1.1/Linux_x86_64/bin/tapmat_pred_fsa",
)


def checkInstallation(block: PluginConfig):
    import os

    print("verifying tapmap_pred_fsa installation")

    tapmap_pred_fsa_path = block.variables.get(tapmapPathVariable.id)
    # Check if the path is valid
    # Warn instead of raising: an exception here aborts the save of every
    # config that comes after this one (see noahConfig for the details).
    if tapmap_pred_fsa_path is None or not os.path.isfile(tapmap_pred_fsa_path):
        print("Warning: the tapmap_pred_fsa executable path is not valid on this machine.")


# Create a plugin configuration for the noah executable
tapmatExecutableConfig = PluginConfig(
    name="tapmap_pred_fsa executable",
    description="Configure the path to the tapmap_pred_fsa executables",
    variables=[tapmapPathVariable],
    action=checkInstallation,
)
