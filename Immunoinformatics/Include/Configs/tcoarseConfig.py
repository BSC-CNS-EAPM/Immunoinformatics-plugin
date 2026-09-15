"""
Configuration for the TCoaRse blocks.

The TCoaRse blocks are a Horus port of the `tcoarse_prediction.nf` Nextflow
pipeline (https://github.com/BSC-CNS-EAPM/TCoaRse-nf). Every path that the
pipeline resolved through `${projectDir}` is configured here.

Only the "TCoaRse installation folder" is mandatory: the rest of the paths are
derived from it unless explicitly overridden.
"""

from HorusAPI import PluginConfig, PluginVariable, VariableTypes

tcoarse_dir_variable = PluginVariable(
    id="tcoarse_dir",
    name="TCoaRse installation folder",
    description=(
        "Path to the TCoaRse-nf checkout. All the other paths default to this "
        "folder (scripts/, src/, pretrained_models/, data/, pydock/)."
    ),
    type=VariableTypes.FOLDER,
)

tcoarse_python_variable = PluginVariable(
    id="tcoarse_python",
    name="TCoaRse python executable",
    description=(
        "Python interpreter of the TCoaRse environment (the one with torch, "
        "transformers, DockQ, tcrdist, anarci...). It is used to run every "
        "script of the pipeline."
    ),
    type=VariableTypes.STRING,
    defaultValue="python",
)

tcoarse_conda_env_variable = PluginVariable(
    id="tcoarse_conda_env",
    name="Cluster conda environment",
    description=(
        "Conda environment activated by the jobs on the cluster, as a name or a "
        "path. Leave it empty when the configured python executable is enough."
    ),
    type=VariableTypes.STRING,
    placeholder="/gpfs/projects/bsc72/conda_envs/tcoarse",
)

tcoarse_modules_variable = PluginVariable(
    id="tcoarse_modules",
    name="Cluster modules",
    description=(
        "Comma-separated modules loaded by the jobs before activating the "
        "environment (singularity is needed by the pyDock block, cuda by the "
        "embeddings one)."
    ),
    type=VariableTypes.STRING,
    placeholder="bsc/1.0, anaconda, singularity, cuda/12.6",
)

tcoarse_scripts_dir_variable = PluginVariable(
    id="tcoarse_scripts_dir",
    name="Scripts folder",
    description="Overrides <TCoaRse folder>/scripts",
    type=VariableTypes.FOLDER,
    placeholder="Optional",
)

tcoarse_src_dir_variable = PluginVariable(
    id="tcoarse_src_dir",
    name="Src folder",
    description=(
        "Folder holding pdockq.py, pdockq2_pae.py and ipsae.py. "
        "Overrides <TCoaRse folder>/src"
    ),
    type=VariableTypes.FOLDER,
    placeholder="Optional",
)

tcoarse_pydock_dir_variable = PluginVariable(
    id="tcoarse_pydock_dir",
    name="pyDock folder",
    description=(
        "Folder holding the pyDock driver scripts (01_make_manifest.py, "
        "02_make_chunks.py, 03_validate_chain_mapping.py, worker_chunk.py). "
        "Overrides <TCoaRse folder>/pydock"
    ),
    type=VariableTypes.FOLDER,
    placeholder="Optional",
)

tcoarse_model_variable = PluginVariable(
    id="tcoarse_model",
    name="TCoaRse model",
    description="Overrides <TCoaRse folder>/pretrained_models/tcoarse.json",
    type=VariableTypes.FILE,
    allowedValues=["json"],
    placeholder="Optional",
)

tcoarse_bimodal_model_variable = PluginVariable(
    id="tcoarse_bimodal_model",
    name="Bimodal model",
    description="Overrides <TCoaRse folder>/pretrained_models/bimodal.json",
    type=VariableTypes.FILE,
    allowedValues=["json"],
    placeholder="Optional",
)

tcoarse_esmc_model_variable = PluginVariable(
    id="tcoarse_esmc_model",
    name="ESMC model",
    description="Overrides <TCoaRse folder>/pretrained_models/esmc.json",
    type=VariableTypes.FILE,
    allowedValues=["json"],
    placeholder="Optional",
)

tcoarse_quality_model_variable = PluginVariable(
    id="tcoarse_quality_model",
    name="Quality classifier",
    description="Overrides <TCoaRse folder>/pretrained_models/rf_quality.pkl",
    type=VariableTypes.FILE,
    allowedValues=["pkl"],
    placeholder="Optional",
)

tcoarse_potential_dir_variable = PluginVariable(
    id="tcoarse_potential_dir",
    name="Statistical potentials folder",
    description="Overrides <TCoaRse folder>/pretrained_models/potential",
    type=VariableTypes.FOLDER,
    placeholder="Optional",
)

tcoarse_af3_training_variable = PluginVariable(
    id="tcoarse_af3_training",
    name="AF3 training CSV",
    description=(
        "Reference set used to compute the similarity of the new predictions. "
        "Overrides <TCoaRse folder>/data/af3_training.csv"
    ),
    type=VariableTypes.FILE,
    allowedValues=["csv"],
    placeholder="Optional",
)

tcoarse_af3_training_pdbs_variable = PluginVariable(
    id="tcoarse_af3_training_pdbs",
    name="AF3 training PDBs folder",
    description="Overrides <TCoaRse folder>/data/pdbs",
    type=VariableTypes.FOLDER,
    placeholder="Optional",
)

tcoarse_pydock_sif_variable = PluginVariable(
    id="tcoarse_pydock_sif",
    name="pyDock Singularity image",
    description=(
        "Absolute path (on the machine that runs the job) to the pyDock "
        "singularity image, e.g. pydock3_cythonize_20260622.sif"
    ),
    type=VariableTypes.STRING,
    placeholder="/path/to/pydock3_cythonize_20260622.sif",
)


def check_tcoarse_config(block: PluginConfig):
    """
    Report on the TCoaRse installation folder.

    This never raises. Horus saves every plugin config in a single loop and
    aborts it on the first exception, which would silently discard the configs
    saved after this one. On top of that, a config saved for a cluster remote
    holds paths that do not exist on the machine running Horus, so a local
    existence check is only ever a hint. The blocks raise a clear error at run
    time when something is missing.
    """

    import os

    root = block.variables.get(tcoarse_dir_variable.id)

    if not root:
        print("Warning: the TCoaRse installation folder is not set.")
        return

    if not os.path.isdir(root):
        print(
            f"Note: '{root}' does not exist on this machine. "
            "That is expected when configuring a cluster remote."
        )
        return

    expected = {
        "scripts": tcoarse_scripts_dir_variable.id,
        "src": tcoarse_src_dir_variable.id,
        "pydock": tcoarse_pydock_dir_variable.id,
    }

    for relative, override_id in expected.items():
        path = block.variables.get(override_id) or os.path.join(root, relative)
        if not os.path.isdir(path):
            print(f"Warning: '{path}' does not exist on this machine.")

    print("TCoaRse configuration saved")


tcoarseConfig = PluginConfig(
    id="tcoarse_config",
    name="TCoaRse",
    description="Paths of the TCoaRse (TCR-pMHC) pipeline",
    action=check_tcoarse_config,
    variables=[
        tcoarse_dir_variable,
        tcoarse_python_variable,
        tcoarse_conda_env_variable,
        tcoarse_modules_variable,
        tcoarse_scripts_dir_variable,
        tcoarse_src_dir_variable,
        tcoarse_pydock_dir_variable,
        tcoarse_model_variable,
        tcoarse_bimodal_model_variable,
        tcoarse_esmc_model_variable,
        tcoarse_quality_model_variable,
        tcoarse_potential_dir_variable,
        tcoarse_af3_training_variable,
        tcoarse_af3_training_pdbs_variable,
        tcoarse_pydock_sif_variable,
    ],
)
