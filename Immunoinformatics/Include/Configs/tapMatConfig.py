from HorusAPI import PluginConfig, PluginVariable, VariableTypes

tapMatPathVariable = PluginVariable(
    id="tapmap_mat_path",
    name="TAP matrix path",
    description="Path to the TAP logodds matrix file (tap.logodds.mat) used by tapmat_pred_fsa",
    type=VariableTypes.FILE,
    defaultValue="/home/perry/data/Programs/Immuno/netCTLpan-1.1/data/tap.logodds.mat",
)


def checkTapMatInstallation(block: PluginConfig):
    import os

    print("Verifying TAP matrix file")

    mat_path = block.variables.get(tapMatPathVariable.id)
    if mat_path is None or not os.path.isfile(mat_path):
        raise Exception("The TAP matrix file path is not valid")


tapMatConfig = PluginConfig(
    name="TAP matrix",
    description="Configure the path to the TAP logodds matrix file used for TAP transport prediction",
    variables=[tapMatPathVariable],
    action=checkTapMatInstallation,
)
