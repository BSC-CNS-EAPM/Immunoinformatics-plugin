"""
Sequence-only (ESMC) predictor of TCR-pMHC binding.

Port of the `predictor_esmc` process of tcoarse_prediction.nf.
"""

import shlex

from HorusAPI import PluginVariable, SlurmBlock, VariableTypes

from slurm_utils import BSC_JOB_VARIABLES  # type: ignore
from tcoarse_utils import (  # type: ignore
    TCOARSE_CATEGORY,
    TCOARSE_COLOR,
    output_prefix,
    ensure_produced,
    esmc_model,
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
metadata_csv_variable = PluginVariable(
    id="metadata_csv",
    name="Metadata CSV",
    description="Metadata of the models to score.",
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
    id="esmc_predictions_csv",
    name="ESMC predictions",
    description="Predicted binding of every TCR-pMHC pair.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)

# ==========================#
# Other variables
# ==========================#
model_variable = PluginVariable(
    id="model",
    name="Model",
    description="Overrides the ESMC model configured in the plugin settings.",
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


def initial_predictor_esmc(block: SlurmBlock):
    """
    Score the models with the sequence-only model.
    """

    metadata_csv = stage(required_input(block, metadata_csv_variable))
    embeddings = stage(required_input(block, embeddings_variable))
    prefix = output_prefix(block)

    predictions = f"{prefix}_esmc_predictions.csv"
    model = variable_or(block, model_variable, None) or esmc_model(block)

    command = (
        f"{python_exec(block)} {shlex.quote(script_path(block, 'predictor_esmc.py'))}"
        f" -df {metadata_csv}"
        f" -emb {embeddings}"
        f" -m {shlex.quote(str(model))}"
        f" -out {predictions}"
    )

    block.extraData["esmc_predictions_csv"] = predictions

    print("Running the ESMC predictor")

    launch(block, command, upload=[metadata_csv, embeddings])


def final_predictor_esmc(block: SlurmBlock):
    """
    Publish the predictions.
    """

    finish(block)

    predictions = ensure_produced(
        block.extraData["esmc_predictions_csv"], "The ESMC predictions"
    )

    if variable_or(block, open_results_variable, True):
        show_results(block, predictions, "TCoaRse ESMC predictions")

    block.setOutput(predictions_output.id, predictions)


predictorESMCBlock = SlurmBlock(
    id="tcoarse_predictor_esmc",
    name="ESMC Predictor",
    description=(
        "Predict TCR-pMHC binding from the ESMC embeddings alone (no "
        "structural or energetic features)."
    ),
    initialAction=initial_predictor_esmc,
    finalAction=final_predictor_esmc,
    inputs=[metadata_csv_variable, embeddings_variable],
    variables=BSC_JOB_VARIABLES + [model_variable, open_results_variable],
    outputs=[predictions_output],
    category=TCOARSE_CATEGORY,
    color=TCOARSE_COLOR,
)
