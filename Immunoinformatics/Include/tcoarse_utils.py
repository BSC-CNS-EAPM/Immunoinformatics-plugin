"""
Shared helpers for the TCoaRse blocks.

The TCoaRse pipeline is a set of standalone python scripts (the same ones the
`tcoarse_prediction.nf` Nextflow pipeline calls). Instead of vendoring their
very heavy dependencies (torch, transformers, DockQ, tcrdist, anarci...) into
the plugin, every block builds a command line and submits it as a BSC job
through the shared launcher of slurm_utils.py (the EAPM one), so the same block
works locally and on MareNostrum/Nord3.

Consequences of using that launcher, and the reason the blocks below work with
plain relative filenames:

    - the job runs inside a run folder (the flow folder locally, a copy of it on
      the remote), so every intermediate file is referenced by its name,
    - `launch()` uploads only what the job needs (`uploadFolders`),
    - `finish()` downloads the results back into the flow folder, which is why
      every block outputs a local absolute path.

The only path that is *not* uploaded is the AlphaFold3 outputs folder: it is
huge and it already lives on the machine that runs the jobs, so it is used as an
absolute path there.
"""

import os
import re
import shutil
import typing

from HorusAPI import PluginBlock, PluginVariable, SlurmBlock, VariableTypes

from Configs.tcoarseConfig import (  # type: ignore
    tcoarse_af3_training_pdbs_variable,
    tcoarse_af3_training_variable,
    tcoarse_bimodal_model_variable,
    tcoarse_conda_env_variable,
    tcoarse_dir_variable,
    tcoarse_esmc_model_variable,
    tcoarse_model_variable,
    tcoarse_modules_variable,
    tcoarse_potential_dir_variable,
    tcoarse_pydock_dir_variable,
    tcoarse_pydock_sif_variable,
    tcoarse_python_variable,
    tcoarse_quality_model_variable,
    tcoarse_scripts_dir_variable,
    tcoarse_src_dir_variable,
)

from slurm_utils import cpusPerTaskVariable as _CPUS_PER_TASK  # type: ignore
from slurm_utils import cpusVariable as _CPUS  # type: ignore

TCOARSE_CATEGORY = "TCoaRse"
"""Palette category shared by every TCoaRse block."""

TCOARSE_COLOR = None
"""Palette color shared by every TCoaRse block. None uses the Horus default."""


# ==========================#
# Configuration
# ==========================#
def _config(block: PluginBlock, variable: PluginVariable) -> typing.Optional[str]:
    """
    Return a configured value, treating empty strings as unset.
    """
    value = block.config.get(variable.id)

    if isinstance(value, str):
        value = value.strip()

    return value or None


def tcoarse_root(block: PluginBlock) -> str:
    """
    The TCoaRse installation folder. Raises when it has not been configured.
    """
    root = _config(block, tcoarse_dir_variable)

    if not root:
        raise Exception(
            "The TCoaRse installation folder is not configured. "
            "Set it in Settings > Plugins > Immunoinformatics > TCoaRse."
        )

    return os.path.normpath(root)


def _resolve(block: PluginBlock, override: PluginVariable, *relative: str) -> str:
    """
    Return the configured override, or the path relative to the TCoaRse root.
    """
    configured = _config(block, override)

    if configured:
        return configured

    return os.path.join(tcoarse_root(block), *relative)


def python_exec(block: PluginBlock) -> str:
    """
    The python interpreter of the TCoaRse environment.
    """
    return _config(block, tcoarse_python_variable) or "python"


def conda_env(block: PluginBlock) -> typing.Optional[str]:
    """
    Conda environment activated by the job on the cluster, if any.
    """
    return _config(block, tcoarse_conda_env_variable)


def cluster_modules(block: PluginBlock) -> typing.Optional[typing.List[str]]:
    """
    Modules loaded by the job before activating the environment.
    """
    configured = _config(block, tcoarse_modules_variable)

    if not configured:
        return None

    modules = [module.strip() for module in configured.split(",") if module.strip()]

    return modules or None


def script_path(block: PluginBlock, name: str) -> str:
    """
    Absolute path to a script of the TCoaRse `scripts` folder.
    """
    return os.path.join(_resolve(block, tcoarse_scripts_dir_variable, "scripts"), name)


def src_dir(block: PluginBlock) -> str:
    """
    Folder holding pdockq.py, pdockq2_pae.py and ipsae.py.
    """
    return _resolve(block, tcoarse_src_dir_variable, "src")


def pydock_dir(block: PluginBlock) -> str:
    """
    Folder holding the pyDock driver scripts.
    """
    return _resolve(block, tcoarse_pydock_dir_variable, "pydock")


def tcoarse_model(block: PluginBlock) -> str:
    """Path to the TCoaRse XGBoost model."""
    return _resolve(block, tcoarse_model_variable, "pretrained_models", "tcoarse.json")


def bimodal_model(block: PluginBlock) -> str:
    """Path to the bimodal model."""
    return _resolve(
        block, tcoarse_bimodal_model_variable, "pretrained_models", "bimodal.json"
    )


def esmc_model(block: PluginBlock) -> str:
    """Path to the ESMC model."""
    return _resolve(block, tcoarse_esmc_model_variable, "pretrained_models", "esmc.json")


def quality_model(block: PluginBlock) -> str:
    """Path to the random forest that assigns the quality tier."""
    return _resolve(
        block, tcoarse_quality_model_variable, "pretrained_models", "rf_quality.pkl"
    )


def potential_dir(block: PluginBlock) -> str:
    """Folder with the statistical potentials."""
    return _resolve(
        block, tcoarse_potential_dir_variable, "pretrained_models", "potential"
    )


def af3_training_csv(block: PluginBlock) -> str:
    """Reference AF3 training set."""
    return _resolve(block, tcoarse_af3_training_variable, "data", "af3_training.csv")


def af3_training_pdbs(block: PluginBlock) -> str:
    """Reference AF3 training structures."""
    return _resolve(block, tcoarse_af3_training_pdbs_variable, "data", "pdbs")


def pydock_sif(block: PluginBlock) -> str:
    """Path to the pyDock singularity image."""
    sif = _config(block, tcoarse_pydock_sif_variable)

    if not sif:
        raise Exception(
            "The pyDock Singularity image is not configured. "
            "Set it in Settings > Plugins > Immunoinformatics > TCoaRse."
        )

    return sif


# ==========================#
# Naming
# ==========================#
def safe_name(name: str) -> str:
    """
    Turn an arbitrary name into something usable as a path/job name.
    """
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_") or "tcoarse"


def output_prefix(block: PluginBlock) -> str:
    """
    Prefix shared by every file the pipeline writes: the name of the flow.

    `params.basename` of the Nextflow pipeline was the name of the AF3 outputs
    folder, which every process had to recover from the name of its input. The
    flow name is known to every block without carrying it around, so a flow
    named "examples" writes `examples_metrics.csv`, `examples_pdb`, ...
    """
    return safe_name(block.flow.name or "tcoarse")


# ==========================#
# Inputs
# ==========================#
def required_input(block: PluginBlock, variable: PluginVariable) -> str:
    """
    Read an input, raising a readable error when it is not connected.
    """
    value = block.inputs.get(variable.id)

    if value is None or value == "":
        raise Exception(f"The input '{variable.name}' is required.")

    return str(value)


def variable_or(
    block: PluginBlock, variable: PluginVariable, default: typing.Any
) -> typing.Any:
    """
    Read a block variable falling back to `default` when it is unset.
    """
    value = block.variables.get(variable.id)

    if value is None or value == "":
        return default

    return value


def job_cpus(block: PluginBlock, default: int = 1) -> int:
    """
    Number of workers the scripts should use.

    The TCoaRse scripts parallelize inside a single task, so this follows the
    shared "CPUs per task" Slurm variable and falls back to "CPUs" when it is
    left at its default.
    """
    cpus_per_task = int(variable_or(block, _CPUS_PER_TASK, 0) or 0)

    if cpus_per_task > 1:
        return cpus_per_task

    return max(int(variable_or(block, _CPUS, 0) or 0), default)


def stage(path: str) -> str:
    """
    Make an input available inside the run folder and return its relative name.

    Inputs produced by an upstream TCoaRse block already live in the flow
    folder, so nothing is copied in the usual case. A file picked from anywhere
    else is copied in, because the job only ever sees the run folder.
    """
    source = os.path.normpath(str(path))
    name = os.path.basename(source)

    if not name or name in (os.curdir, os.pardir):
        raise Exception(f"Invalid input path: {path}")

    destination = os.path.abspath(name)

    if os.path.abspath(source) == destination:
        return name

    if not os.path.exists(source):
        raise Exception(f"The input does not exist: {source}")

    if os.path.exists(destination):
        if os.path.isdir(destination):
            shutil.rmtree(destination)
        else:
            os.remove(destination)

    if os.path.isdir(source):
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)

    print(f"Copied '{source}' into the run folder")

    return name


def ensure_produced(path: str, what: str) -> str:
    """
    Raise a readable error when an expected output is missing, and return its
    absolute path.
    """
    if not os.path.exists(path):
        raise Exception(
            f"{what} was not produced: {path}. Check the job logs above for the error."
        )

    return os.path.abspath(path)


# ==========================#
# Execution
# ==========================#
def launch(
    block: SlurmBlock,
    command: str,
    upload: typing.Optional[typing.List[str]] = None,
    program: typing.Optional[str] = None,
    exports: typing.Optional[typing.List[str]] = None,
) -> None:
    """
    Submit a TCoaRse step through the shared BSC launcher.

    :param command: the shell command of the job.
    :param upload: files/folders of the run folder the job needs on the remote.
                   The AF3 outputs folder is never uploaded (see the module
                   docstring).
    """
    from slurm_utils import launchCalculationAction  # type: ignore

    launchCalculationAction(
        block,
        [command],
        program,
        uploadFolders=list(upload or []),
        condaEnv=conda_env(block),
        modules=cluster_modules(block),
        exports=exports,
    )


def finish(block: SlurmBlock) -> str:
    """
    Download the results of the job into the flow folder.
    """
    from slurm_utils import downloadResultsAction  # type: ignore

    return downloadResultsAction(block)


# ==========================#
# Results
# ==========================#
def show_results(block: PluginBlock, csv_path: str, title: str) -> None:
    """
    Open a CSV produced by a block in the plugin results page.
    """
    from HorusAPI import Extensions

    safe_path = os.path.abspath(csv_path)

    try:
        from App import AppDelegate  # type: ignore

        if AppDelegate().mode == "webapp":
            # The webapp resolves the path relative to the user folder:
            # keep the last three components (flow dir / results dir / file)
            head, results_dir = os.path.split(os.path.dirname(safe_path))
            flow_dir = os.path.basename(head)
            safe_path = os.path.join(
                flow_dir, results_dir, os.path.basename(safe_path)
            )
    except Exception:
        pass

    print(f"Results are at: '{safe_path}'")

    Extensions().storeExtensionResults(
        "immuno",
        "results",
        data={"csv": safe_path},
        title=title,
    )
