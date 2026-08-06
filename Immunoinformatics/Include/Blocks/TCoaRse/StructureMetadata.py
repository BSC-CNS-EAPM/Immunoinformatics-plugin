"""
Extract the TCR / peptide / MHC sequences and annotations from the structures.

Port of the `metadata_from_str` process of tcoarse_prediction.nf.
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
pdb_dir_variable = PluginVariable(
    id="pdb_dir",
    name="PDB folder",
    description="Folder with the merged PDB models.",
    type=VariableTypes.FOLDER,
    required=True,
)

# ==========================#
# Outputs
# ==========================#
metadata_csv_output = PluginVariable(
    id="metadata_csv",
    name="Metadata CSV",
    description="Sequences and annotations of every TCR-pMHC model.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)


def initial_structure_metadata(block: SlurmBlock):
    """
    Build the metadata table out of the structures.
    """

    pdb_dir = stage(required_input(block, pdb_dir_variable))
    prefix = output_prefix(block)

    metadata_csv = f"{prefix}_metadata.csv"

    command = (
        f"{python_exec(block)} {shlex.quote(script_path(block, 'metadata_from_str.py'))}"
        f" {pdb_dir}"
        f" -o {metadata_csv}"
    )

    block.extraData["metadata_csv"] = metadata_csv

    print("Extracting the metadata from the structures")

    launch(block, command, upload=[pdb_dir])


def final_structure_metadata(block: SlurmBlock):
    """
    Publish the metadata CSV.
    """

    finish(block)

    metadata_csv = ensure_produced(block.extraData["metadata_csv"], "The metadata CSV")

    print(f"Metadata written to '{metadata_csv}'")

    block.setOutput(metadata_csv_output.id, metadata_csv)


structureMetadataBlock = SlurmBlock(
    id="tcoarse_structure_metadata",
    name="Structure Metadata",
    description=(
        "Extract the TCR (CDR3s, V/J genes), peptide and MHC sequences of "
        "every model from its structure."
    ),
    initialAction=initial_structure_metadata,
    finalAction=final_structure_metadata,
    inputs=[pdb_dir_variable],
    variables=BSC_JOB_VARIABLES,
    outputs=[metadata_csv_output],
    category=TCOARSE_CATEGORY,
    color=TCOARSE_COLOR,
)
