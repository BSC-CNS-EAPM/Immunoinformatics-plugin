"""
Structure/energy based TCoaRse predictor.

Port of the `predictor_tcoarse` process of tcoarse_prediction.nf.
"""


from HorusAPI import PluginVariable, SlurmBlock, VariableTypes

from slurm_utils import BSC_JOB_VARIABLES  # type: ignore
from tcoarse_steps import predictor_tcoarse_command  # type: ignore

from tcoarse_utils import (  # type: ignore
    TCOARSE_CATEGORY,
    TCOARSE_COLOR,
    output_prefix,
    ensure_produced,
    finish,
    launch,
    required_input,
    show_results,
    stage,
    tcoarse_model,
    variable_or,
)

# ==========================#
# Inputs
# ==========================#
merged_csv_variable = PluginVariable(
    id="merged_csv",
    name="Merged features",
    description="Feature table produced by the 'Merge Energies' block.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
    required=True,
)

# ==========================#
# Outputs
# ==========================#
predictions_output = PluginVariable(
    id="tcoarse_predictions_csv",
    name="TCoaRse predictions",
    description="Predicted binding of every TCR-pMHC model.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)

# ==========================#
# Other variables
# ==========================#
model_variable = PluginVariable(
    id="model",
    name="Model",
    description="Overrides the TCoaRse model configured in the plugin settings.",
    type=VariableTypes.FILE,
    allowedValues=["json"],
    placeholder="Optional",
)

open_results_variable = PluginVariable(
    id="open_results",
    name="Show results",
    description="Load the predictions in the results page.",
    type=VariableTypes.BOOLEAN,
    defaultValue=True,
)


def initial_predictor_tcoarse(block: SlurmBlock):
    """
    Score the models with the TCoaRse model.
    """

    merged_csv = stage(required_input(block, merged_csv_variable))
    prefix = output_prefix(block)

    predictions = f"{prefix}_tcoarse_predictions.csv"
    model = variable_or(block, model_variable, None) or tcoarse_model(block)

    command = predictor_tcoarse_command(block, merged_csv, predictions, str(model))

    block.extraData["tcoarse_predictions_csv"] = predictions

    print("Running the TCoaRse predictor")

    launch(block, command, upload=[merged_csv])


def final_predictor_tcoarse(block: SlurmBlock):
    """
    Publish the predictions.
    """

    finish(block)

    predictions = ensure_produced(
        block.extraData["tcoarse_predictions_csv"], "The TCoaRse predictions"
    )

    if variable_or(block, open_results_variable, True):
        show_results(block, predictions, "TCoaRse predictions")

    block.setOutput(predictions_output.id, predictions)


predictorTCoaRseBlock = SlurmBlock(
    id="tcoarse_predictor_tcoarse",
    name="TCoaRse Predictor",
    description=(
        "Predict TCR-pMHC binding from the coarse-grained and pyDock energies "
        "of the AlphaFold3 models."
    ),
    initialAction=initial_predictor_tcoarse,
    finalAction=final_predictor_tcoarse,
    inputs=[merged_csv_variable],
    variables=BSC_JOB_VARIABLES + [model_variable, open_results_variable],
    outputs=[predictions_output],
    category=TCOARSE_CATEGORY,
    color=TCOARSE_COLOR,
)
