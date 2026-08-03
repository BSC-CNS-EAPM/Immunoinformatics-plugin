from HorusAPI import PluginConfig, PluginVariable, VariableTypes

predigNeoAModelVariable = PluginVariable(
    id="predig_neoa_model_path",
    name="PredIG-NeoA model path",
    description="Path to the PredIG-NeoA XGBoost model file (spw_xtreme_predig_model.model)",
    type=VariableTypes.FILE,
    defaultValue="/home/perry/data/Programs/Immuno/Predig/spw_xtreme_predig_model.model",
)

predigNonCanModelVariable = PluginVariable(
    id="predig_noncan_model_path",
    name="PredIG-NonCan model path",
    description="Path to the PredIG-NonCan XGBoost model file (spw_indep2_rescale_predig_model.model)",
    type=VariableTypes.FILE,
    defaultValue="/home/perry/data/Programs/Immuno/Predig/spw_indep2_rescale_predig_model.model",
)

predigPathModelVariable = PluginVariable(
    id="predig_path_model_path",
    name="PredIG-Path model path",
    description="Path to the PredIG-Path XGBoost model file (spw_indep1_rescale_predig_model.model)",
    type=VariableTypes.FILE,
    defaultValue="/home/perry/data/Programs/Immuno/Predig/spw_indep1_rescale_predig_model.model",
)


def checkPredigModels(block: PluginConfig):
    import os

    print("Verifying PredIG model files")

    for var in [predigNeoAModelVariable, predigNonCanModelVariable, predigPathModelVariable]:
        path = block.variables.get(var.id)
        if path and not os.path.isfile(path):
            raise Exception(f"The PredIG model path is not valid: {path}")


predigModelsConfig = PluginConfig(
    name="PredIG models",
    description="Configure the paths to the PredIG XGBoost model files",
    variables=[predigNeoAModelVariable, predigNonCanModelVariable, predigPathModelVariable],
    action=checkPredigModels,
)
