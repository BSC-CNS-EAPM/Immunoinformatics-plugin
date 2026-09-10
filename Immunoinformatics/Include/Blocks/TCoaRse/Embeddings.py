"""
ESMC embeddings of the TCR-pMHC sequences.

Port of the `generate_embeddings` process of tcoarse_prediction.nf. This is the
only GPU step of the pipeline: request the GPUs with the shared "GPUs" Slurm
variable and an 'acc_*' partition.
"""

import shlex

from HorusAPI import PluginVariable, SlurmBlock, VariableTypes

from slurm_utils import BSC_JOB_VARIABLES, gpusVariable  # type: ignore
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
    variable_or,
)

# ==========================#
# Inputs
# ==========================#
metadata_csv_variable = PluginVariable(
    id="metadata_csv",
    name="Metadata CSV",
    description="Metadata with the sequences to embed.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
    required=True,
)

# ==========================#
# Outputs
# ==========================#
embeddings_output = PluginVariable(
    id="embeddings_h5",
    name="Embeddings",
    description="HDF5 file with the ESMC embeddings.",
    type=VariableTypes.FILE,
    allowedValues=["h5"],
)

# ==========================#
# Other variables
# ==========================#
device_variable = PluginVariable(
    id="device",
    name="Device",
    description="Device used to run ESMC.",
    type=VariableTypes.STRING_LIST,
    allowedValues=["cuda", "cpu", "mps"],
    defaultValue="cuda",
)

normalized_variable = PluginVariable(
    id="normalized",
    name="Normalize",
    description="Normalize the embeddings.",
    type=VariableTypes.BOOLEAN,
    defaultValue=True,
)

no_compile_variable = PluginVariable(
    id="no_compile",
    name="Disable torch.compile",
    description="Disable torch.compile (useful when it stalls or errors).",
    type=VariableTypes.BOOLEAN,
    defaultValue=True,
)

batch_size_variable = PluginVariable(
    id="batch_size",
    name="Batch size",
    description="Batch size (leave empty to let the script decide).",
    type=VariableTypes.INTEGER,
    placeholder="Optional",
)


def initial_embeddings(block: SlurmBlock):
    """
    Generate the ESMC embeddings of every model.
    """

    metadata_csv = stage(required_input(block, metadata_csv_variable))
    prefix = output_prefix(block)

    device = str(variable_or(block, device_variable, "cuda"))
    embeddings = f"{prefix}_embeddings.h5"

    command = (
        f"{python_exec(block)} {shlex.quote(script_path(block, 'emb_generator.py'))}"
        f" -i {metadata_csv}"
        f" -o {embeddings}"
        f" -d {shlex.quote(device)}"
    )

    if variable_or(block, normalized_variable, True):
        command += " -norm"

    if variable_or(block, no_compile_variable, True):
        command += " --no-compile"

    batch_size = variable_or(block, batch_size_variable, None)
    if batch_size:
        command += f" -b {int(batch_size)}"

    block.extraData["embeddings_h5"] = embeddings

    print(f"Generating the ESMC embeddings on '{device}'")

    if device == "cuda" and not variable_or(block, gpusVariable, 0):
        print(
            "Warning: the device is 'cuda' but no GPUs were requested. "
            "Set the 'GPUs' variable and an 'acc_*' partition."
        )

    launch(block, command, upload=[metadata_csv])


def final_embeddings(block: SlurmBlock):
    """
    Publish the embeddings file.
    """

    finish(block)

    embeddings = ensure_produced(
        block.extraData["embeddings_h5"], "The embeddings file"
    )

    print(f"Embeddings written to '{embeddings}'")

    block.setOutput(embeddings_output.id, embeddings)


embeddingsBlock = SlurmBlock(
    id="tcoarse_embeddings",
    name="ESMC Embeddings",
    description=(
        "Generate the ESMC embeddings of the TCR-pMHC sequences. Requires a "
        "GPU when the device is set to 'cuda'."
    ),
    initialAction=initial_embeddings,
    finalAction=final_embeddings,
    inputs=[metadata_csv_variable],
    variables=BSC_JOB_VARIABLES
    + [
        gpusVariable,
        device_variable,
        normalized_variable,
        no_compile_variable,
        batch_size_variable,
    ],
    outputs=[embeddings_output],
    category=TCOARSE_CATEGORY,
    color=TCOARSE_COLOR,
)
