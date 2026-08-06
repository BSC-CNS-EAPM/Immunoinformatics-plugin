"""
Bimodal predictor: energies + ESMC embeddings.

Port of the `predictor_bimodal` process of tcoarse_prediction.nf.
"""

import shlex

from HorusAPI import PluginVariable, SlurmBlock, VariableTypes

from slurm_utils import BSC_JOB_VARIABLES  # type: ignore
from tcoarse_utils import (  # type: ignore
    TCOARSE_CATEGORY,
    TCOARSE_COLOR,
    output_prefix,
    bimodal_model,
    ensure_produced,
    finish,
    launch,
    python_exec,
    required_input,
    script_path,
    show_results,
    stage,
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

embeddings_variable = PluginVariable(
    id="embeddings_h5",
    name="Embeddings",
    description="ESMC embeddings of the same models.",
    type=VariableTypes.FILE,
    allowedValues=["h5"],
    required=True,
)

# ==========================#
# Outputs
# ==========================#
predictions_output = PluginVariable(
    id="bimodal_predictions_csv",
    name="Bimodal predictions",
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
    description="Overrides the bimodal model configured in the plugin settings.",
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


def initial_predictor_bimodal(block: SlurmBlock):
    """
    Score the models with the bimodal model.
    """

    merged_csv = stage(required_input(block, merged_csv_variable))
    embeddings = stage(required_input(block, embeddings_variable))
    prefix = output_prefix(block)

    predictions = f"{prefix}_bimodal_predictions.csv"
    model = variable_or(block, model_variable, None) or bimodal_model(block)

    command = (
        f"{python_exec(block)} {shlex.quote(script_path(block, 'predictor_bimodal.py'))}"
        f" -df {merged_csv}"
        f" -emb {embeddings}"
        f" -m {shlex.quote(str(model))}"
        f" -out {predictions}"
    )

    block.extraData["bimodal_predictions_csv"] = predictions

    print("Running the bimodal predictor")

    launch(block, command, upload=[merged_csv, embeddings])


def final_predictor_bimodal(block: SlurmBlock):
    """
    Publish the predictions.
    """

    finish(block)

    predictions = ensure_produced(
        block.extraData["bimodal_predictions_csv"], "The bimodal predictions"
    )

    if variable_or(block, open_results_variable, True):
        show_results(block, predictions, "TCoaRse bimodal predictions")

    block.setOutput(predictions_output.id, predictions)


predictorBimodalBlock = SlurmBlock(
    id="tcoarse_predictor_bimodal",
    name="Bimodal Predictor",
    description=(
        "Predict TCR-pMHC binding combining the energetic features with the "
        "ESMC sequence embeddings."
    ),
    initialAction=initial_predictor_bimodal,
    finalAction=final_predictor_bimodal,
    inputs=[merged_csv_variable, embeddings_variable],
    variables=BSC_JOB_VARIABLES + [model_variable, open_results_variable],
    outputs=[predictions_output],
    category=TCOARSE_CATEGORY,
    color=TCOARSE_COLOR,
)
