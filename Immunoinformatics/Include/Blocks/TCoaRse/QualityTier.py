"""
Assign a quality tier to every model with the pretrained random forest.

Port of the `quality_tier` process of tcoarse_prediction.nf.
"""

import shlex

from HorusAPI import PluginVariable, SlurmBlock, VariableTypes

from slurm_utils import BSC_JOB_VARIABLES  # type: ignore
from tcoarse_utils import (  # type: ignore
    TCOARSE_CATEGORY,
    TCOARSE_COLOR,
    output_prefix,
    ensure_produced,
    finish,
    launch,
    python_exec,
    quality_model,
    required_input,
    script_path,
    show_results,
    stage,
    variable_or,
)

# ==========================#
# Inputs
# ==========================#
metrics_csv_variable = PluginVariable(
    id="metrics_csv",
    name="Metrics CSV",
    description="Quality metrics produced by the 'Quality Metrics' block.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
    required=True,
)

# ==========================#
# Outputs
# ==========================#
quality_csv_output = PluginVariable(
    id="quality_csv",
    name="Quality CSV",
    description="The metrics with the predicted quality tier of every model.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)

# ==========================#
# Other variables
# ==========================#
thresholds_variable = PluginVariable(
    id="thresholds",
    name="Thresholds",
    description=(
        "Optional thresholds passed to quality_tier.py "
        "(leave empty to use the ones of the model)."
    ),
    type=VariableTypes.STRING,
    placeholder="Optional",
)

open_results_variable = PluginVariable(
    id="open_results",
    name="Show results",
    description="Load the resulting CSV in the results page.",
    type=VariableTypes.BOOLEAN,
    defaultValue=False,
)


def initial_quality_tier(block: SlurmBlock):
    """
    Classify the models into quality tiers.
    """

    metrics_csv = stage(required_input(block, metrics_csv_variable))
    prefix = output_prefix(block)

    # The Nextflow pipeline wrote this file with the same name as the metrics
    # CSV, which overwrote it in the results folder. Use a dedicated name.
    quality_csv = f"{prefix}_quality.csv"

    command = (
        f"{python_exec(block)} {shlex.quote(script_path(block, 'quality_tier.py'))}"
        f" --test {metrics_csv}"
        f" --model {shlex.quote(quality_model(block))}"
        f" --output {quality_csv}"
    )

    thresholds = variable_or(block, thresholds_variable, None)
    if thresholds:
        command += f" --thresholds {shlex.quote(str(thresholds))}"

    block.extraData["quality_csv"] = quality_csv

    print("Assigning the quality tiers")

    launch(block, command, upload=[metrics_csv])


def final_quality_tier(block: SlurmBlock):
    """
    Publish the quality CSV.
    """

    finish(block)

    quality_csv = ensure_produced(block.extraData["quality_csv"], "The quality CSV")

    if variable_or(block, open_results_variable, False):
        show_results(block, quality_csv, "TCoaRse quality tiers")

    block.setOutput(quality_csv_output.id, quality_csv)


qualityTierBlock = SlurmBlock(
    id="tcoarse_quality_tier",
    name="Quality Tier",
    description=(
        "Classify the AlphaFold3 models into quality tiers using the "
        "pretrained random forest (rf_quality.pkl)."
    ),
    initialAction=initial_quality_tier,
    finalAction=final_quality_tier,
    inputs=[metrics_csv_variable],
    variables=BSC_JOB_VARIABLES + [thresholds_variable, open_results_variable],
    outputs=[quality_csv_output],
    category=TCOARSE_CATEGORY,
    color=TCOARSE_COLOR,
)
