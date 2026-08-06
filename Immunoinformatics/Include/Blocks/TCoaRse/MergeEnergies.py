"""
Merge the TCoaRse energies, the pyDock energies and the metadata into the
feature table used by the predictors.

Port of the `merge_energies` process of tcoarse_prediction.nf.
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
    required_input,
    script_path,
    stage,
)

# ==========================#
# Inputs
# ==========================#
energies_csv_variable = PluginVariable(
    id="energies_csv",
    name="TCoaRse energies",
    description="Energies produced by the 'Energetic Scorer' block.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
    required=True,
)

metadata_csv_variable = PluginVariable(
    id="metadata_csv",
    name="Metadata CSV",
    description="Metadata produced by the 'Structure Metadata' block.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
    required=True,
)

pydock_tar_variable = PluginVariable(
    id="pydock_tar",
    name="pyDock energies",
    description="Archive produced by the 'pyDock Energies' block.",
    type=VariableTypes.FILE,
    allowedValues=["tar"],
    required=True,
)

metrics_csv_variable = PluginVariable(
    id="metrics_csv",
    name="Metrics CSV",
    description=(
        "Optional quality metrics to merge into the feature table "
        "(not used by the Nextflow pipeline)."
    ),
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)

# ==========================#
# Outputs
# ==========================#
merged_csv_output = PluginVariable(
    id="merged_csv",
    name="Merged features",
    description="Feature table used by the TCoaRse and bimodal predictors.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)


def initial_merge_energies(block: SlurmBlock):
    """
    Build the feature table of the predictors.
    """

    energies_csv = stage(required_input(block, energies_csv_variable))
    metadata_csv = stage(required_input(block, metadata_csv_variable))
    pydock_tar = stage(required_input(block, pydock_tar_variable))

    uploads = [energies_csv, metadata_csv, pydock_tar]

    prefix = output_prefix(block)
    merged_csv = f"{prefix}_tcoarse_pydock_energies.csv"

    command = (
        f"{python_exec(block)} {shlex.quote(script_path(block, 'merge_energies.py'))}"
        f" -tcoarse {energies_csv}"
        f" -metadata {metadata_csv}"
        f" -tar {pydock_tar}"
        f" -o {merged_csv}"
    )

    metrics_csv = block.inputs.get(metrics_csv_variable.id)
    if metrics_csv:
        metrics_csv = stage(str(metrics_csv))
        uploads.append(metrics_csv)
        command += f" -metrics {metrics_csv}"

    block.extraData["merged_csv"] = merged_csv

    print("Merging the energies with the metadata")

    launch(block, command, upload=uploads)


def final_merge_energies(block: SlurmBlock):
    """
    Publish the feature table.
    """

    finish(block)

    merged_csv = ensure_produced(
        block.extraData["merged_csv"], "The merged features CSV"
    )

    print(f"Feature table written to '{merged_csv}'")

    block.setOutput(merged_csv_output.id, merged_csv)


mergeEnergiesBlock = SlurmBlock(
    id="tcoarse_merge_energies",
    name="Merge Energies",
    description=(
        "Merge the coarse-grained energies, the pyDock energies and the "
        "metadata into the feature table used by the predictors."
    ),
    initialAction=initial_merge_energies,
    finalAction=final_merge_energies,
    inputs=[
        energies_csv_variable,
        metadata_csv_variable,
        pydock_tar_variable,
        metrics_csv_variable,
    ],
    variables=BSC_JOB_VARIABLES,
    outputs=[merged_csv_output],
    category=TCOARSE_CATEGORY,
    color=TCOARSE_COLOR,
)
