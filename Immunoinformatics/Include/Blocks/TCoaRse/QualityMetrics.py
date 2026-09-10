"""
Quality metrics of the AlphaFold3 models (pDockQ, pDockQ2, ipSAE, PAE...).

Port of the `process_folder` process of tcoarse_prediction.nf.
"""

import os
import shlex

from HorusAPI import PluginVariable, SlurmBlock, VariableTypes

from slurm_utils import BSC_JOB_VARIABLES  # type: ignore
from tcoarse_utils import (  # type: ignore
    TCOARSE_CATEGORY,
    TCOARSE_COLOR,
    output_prefix,
    ensure_produced,
    finish,
    job_cpus,
    launch,
    python_exec,
    required_input,
    script_path,
    src_dir,
    variable_or,
)

# ==========================#
# Inputs
# ==========================#
af3_dir_variable = PluginVariable(
    id="af3_dir",
    name="AF3 outputs",
    description="Folder with the AlphaFold3 predictions (not uploaded).",
    type=VariableTypes.FOLDER,
    required=True,
)

# ==========================#
# Outputs
# ==========================#
metrics_csv_output = PluginVariable(
    id="metrics_csv",
    name="Metrics CSV",
    description="Per model quality metrics (pDockQ, pDockQ2, ipSAE, PAE...).",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)

# ==========================#
# Other variables
# ==========================#
threshold_variable = PluginVariable(
    id="threshold",
    name="pLDDT threshold",
    description="pLDDT threshold used to filter residues.",
    type=VariableTypes.INTEGER,
    defaultValue=70,
)

fast_variable = PluginVariable(
    id="fast",
    name="Fast mode",
    description=(
        "Skip the most expensive steps and reuse the metrics already present "
        "in the AF3 folders."
    ),
    type=VariableTypes.BOOLEAN,
    defaultValue=False,
)

verbose_variable = PluginVariable(
    id="verbose",
    name="Verbose",
    description="Print the metrics of every model while they are computed.",
    type=VariableTypes.BOOLEAN,
    defaultValue=False,
)

seed_workers_variable = PluginVariable(
    id="seed_workers",
    name="Seed workers",
    description="Threads used to process the seeds of a single TCR folder.",
    type=VariableTypes.INTEGER,
    defaultValue=4,
)


def initial_quality_metrics(block: SlurmBlock):
    """
    Compute the quality metrics of every AF3 model.
    """

    af3_dir = required_input(block, af3_dir_variable)
    prefix = output_prefix(block)

    metrics_csv = f"{prefix}_metrics.csv"
    src = src_dir(block)

    command = (
        f"{python_exec(block)} {shlex.quote(script_path(block, 'process_folder.py'))}"
        f" {shlex.quote(af3_dir)}"
        f" --output {metrics_csv}"
        f" --threshold {int(variable_or(block, threshold_variable, 70))}"
        f" --workers {job_cpus(block)}"
        f" --seed-workers {int(variable_or(block, seed_workers_variable, 4))}"
        f" --pdockq-script {shlex.quote(os.path.join(src, 'pdockq.py'))}"
        f" --pdockq2-script {shlex.quote(os.path.join(src, 'pdockq2_pae.py'))}"
        # The Nextflow pipeline passed a file here, but process_folder.py joins
        # "ipsae.py" to this value, so it must be the folder holding the script.
        f" --ipsae-scripts-dir {shlex.quote(src)}"
    )

    if variable_or(block, fast_variable, False):
        command += " --fast"

    if variable_or(block, verbose_variable, False):
        command += " --verbose"

    block.extraData["metrics_csv"] = metrics_csv

    print("Computing the quality metrics of the AF3 models")

    launch(block, command)


def final_quality_metrics(block: SlurmBlock):
    """
    Publish the metrics CSV.
    """

    finish(block)

    metrics_csv = ensure_produced(block.extraData["metrics_csv"], "The metrics CSV")

    print(f"Quality metrics written to '{metrics_csv}'")

    block.setOutput(metrics_csv_output.id, metrics_csv)


qualityMetricsBlock = SlurmBlock(
    id="tcoarse_quality_metrics",
    name="Quality Metrics",
    description=(
        "Compute the quality metrics of every AlphaFold3 model (pDockQ, "
        "pDockQ2, ipSAE, PAE and contact based metrics)."
    ),
    initialAction=initial_quality_metrics,
    finalAction=final_quality_metrics,
    inputs=[af3_dir_variable],
    variables=BSC_JOB_VARIABLES
    + [
        threshold_variable,
        seed_workers_variable,
        fast_variable,
        verbose_variable,
    ],
    outputs=[metrics_csv_output],
    category=TCOARSE_CATEGORY,
    color=TCOARSE_COLOR,
)
