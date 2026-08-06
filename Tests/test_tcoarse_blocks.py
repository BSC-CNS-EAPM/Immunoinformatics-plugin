"""
Smoke tests for the TCoaRse blocks.

The blocks never import the TCoaRse dependencies: they build a command line and
hand it to the shared BSC launcher (Include/slurm_utils.py, vendored from the
EAPM plugin). That makes them testable without torch, DockQ, tcrdist,
bsc_calculations or a cluster: this module fakes the block runtime, replaces the
launcher with a recorder, runs every action, and checks the job that each block
would have submitted.

Run it with the environment that provides HorusAPI (the `horus` conda env):

    python Tests/test_tcoarse_blocks.py
    # or
    python -m pytest Tests/test_tcoarse_blocks.py -vv

Set HORUS_PATH to point at a Horus checkout other than ~/GitHub/horus.
"""

import importlib
import os
import shutil
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCLUDE_DIR = os.path.join(REPO_ROOT, "Immunoinformatics", "Include")
HORUS_DIR = os.environ.get("HORUS_PATH", os.path.expanduser("~/GitHub/horus"))

sys.path.insert(0, HORUS_DIR)
sys.path.insert(0, INCLUDE_DIR)

TCOARSE_ROOT = "/opt/tcoarse"
BASENAME = "tcoarse_test"   # the FakeFlow name: outputs are named after the flow


# ==========================#
# Fake runtime
# ==========================#
class FakeRemote:
    """
    Records the commands instead of running them.
    """

    isLocal = True
    name = "Local"
    host = "localhost"

    def __init__(self):
        self.commands = []

    @property
    def workDir(self):
        return os.getcwd()

    def command(self, command, timeout=None, **kwargs):
        self.commands.append(command)

        if "| wc -l" in command:
            return "3\n"

        return ""

    def sendData(self, source, destination):
        return destination

    def getData(self, source, destination):
        return source


class FakeFlow:
    name = "tcoarse_test"
    path = ""
    savedID = "test"


class FakeBlock:
    """
    Minimal stand-in for a PluginBlock / SlurmBlock inside an action.
    """

    def __init__(self, inputs=None, variables=None, config=None):
        self.inputs = inputs or {}
        self.variables = dict(BSC_DEFAULTS)
        self.variables.update(variables or {})
        self.config = config or {}
        self.extraData = {}
        self.outputs = {}
        self.remote = FakeRemote()
        self.flow = FakeFlow()
        self.pluginDir = REPO_ROOT

        # Filled in by the fake launcher
        self.launched = None

    def setOutput(self, output_id, value):
        self.outputs[output_id] = value

    @property
    def command(self):
        assert self.launched, "The block did not launch any job"
        return self.launched["jobs"][0]

    @property
    def uploads(self):
        assert self.launched, "The block did not launch any job"
        return self.launched["uploadFolders"]


# The shared Slurm variables the launcher reads
BSC_DEFAULTS = {
    "script_name": "calculation_script.sh",
    "partition": "gp_bscls",
    "cpus": 1,
    "cpus_per_task": 1,
    "environment_list": [],
    "remove_folder_on_finish": True,
}


def base_config():
    """
    The plugin configuration used by every test.
    """
    return {
        "tcoarse_dir": TCOARSE_ROOT,
        "tcoarse_python": "/opt/envs/tcoarse/bin/python",
        "tcoarse_pydock_sif": "/opt/pydock/pydock.sif",
        "tcoarse_conda_env": "/gpfs/projects/bsc72/conda_envs/tcoarse",
        "tcoarse_modules": "bsc/1.0, anaconda, singularity",
    }


def touch(path, directory=False):
    """
    Create the output a block expects its job to have produced.
    """
    if directory:
        os.makedirs(path, exist_ok=True)
    else:
        with open(path, "w", encoding="utf-8") as file:
            file.write("")

    return path


# ==========================#
# Imports and launcher stub
# ==========================#
# The block modules are imported once, before any test changes the working
# directory: importing HorusAPI pulls in pywebview, which resolves paths
# relative to the directory the interpreter was started from.
MODULES = {
    name: importlib.import_module(f"Blocks.TCoaRse.{name}")
    for name in [
        "AF3Outputs",
        "QualityMetrics",
        "QualityTier",
        "CopyModels",
        "StructureMetadata",
        "Similarities",
        "Embeddings",
        "PredictorESMC",
        "PyDockEnergies",
        "ContactMaps",
        "PairwiseDockQ",
        "EnergeticScorer",
        "MergeEnergies",
        "PredictorTCoaRse",
        "PredictorBimodal",
    ]
}

import slurm_utils  # noqa: E402  (imported after the sys.path setup above)


def _fake_launch(
    block,
    jobs,
    program=None,
    uploadFolders=None,
    modulePurge=False,
    condaEnv=None,
    modules=None,
    exports=None,
):
    """
    Stand-in for slurm_utils.launchCalculationAction.
    """
    block.launched = {
        "jobs": jobs,
        "program": program,
        "uploadFolders": list(uploadFolders or []),
        "condaEnv": condaEnv,
        "modules": modules,
        "exports": exports,
    }


def _fake_download(block):
    """
    Stand-in for slurm_utils.downloadResultsAction.
    """
    return os.getcwd()


slurm_utils.launchCalculationAction = _fake_launch
slurm_utils.downloadResultsAction = _fake_download

_ORIGINAL_CWD = os.getcwd()
_WORKDIRS = []


def block_module(name):
    return MODULES[name]


def setup_function(function=None):  # noqa: ARG001 - pytest hook
    """
    Run every test in its own empty directory (the blocks write there).
    """
    workdir = tempfile.mkdtemp(prefix="tcoarse_test_")
    _WORKDIRS.append(workdir)
    os.chdir(workdir)


def teardown_function(function=None):  # noqa: ARG001 - pytest hook
    """
    Restore the working directory and clean up.
    """
    os.chdir(_ORIGINAL_CWD)

    if _WORKDIRS:
        shutil.rmtree(_WORKDIRS.pop(), ignore_errors=True)


# ==========================#
# Tests
# ==========================#
def test_af3_outputs():
    module = block_module("AF3Outputs")
    block = FakeBlock(variables={"af3_outputs": "/data/examples/"}, config=base_config())

    module.run_af3_outputs(block)

    assert block.outputs["af3_dir"] == "/data/examples"
    assert "wc -l" in block.remote.commands[-1]


def test_quality_metrics_command():
    module = block_module("QualityMetrics")
    block = FakeBlock(
        inputs={"af3_dir": "/data/examples"},
        variables={"cpus_per_task": 8, "threshold": 70, "fast": False},
        config=base_config(),
    )

    module.initial_quality_metrics(block)
    command = block.command

    assert "process_folder.py" in command
    assert "/data/examples" in command
    assert "--workers 8" in command
    assert "--threshold 70" in command
    # The Nextflow pipeline passed a file to an argument expecting a folder
    assert f"--ipsae-scripts-dir {TCOARSE_ROOT}/src" in command
    assert "--fast" not in command

    # The AF3 outputs folder is used in place, never uploaded
    assert block.uploads == []

    touch(f"{BASENAME}_metrics.csv")
    module.final_quality_metrics(block)

    assert block.outputs["metrics_csv"].endswith(f"{BASENAME}_metrics.csv")


def test_environment_is_passed_to_the_launcher():
    module = block_module("QualityMetrics")
    block = FakeBlock(inputs={"af3_dir": "/data/examples"}, config=base_config())

    module.initial_quality_metrics(block)

    assert block.launched["condaEnv"] == "/gpfs/projects/bsc72/conda_envs/tcoarse"
    assert block.launched["modules"] == ["bsc/1.0", "anaconda", "singularity"]
    # bsc_calculations pins its own environment when it is given a program name
    assert block.launched["program"] is None


def test_missing_output_is_reported():
    module = block_module("QualityMetrics")
    block = FakeBlock(inputs={"af3_dir": "/data/examples"}, config=base_config())

    module.initial_quality_metrics(block)

    try:
        module.final_quality_metrics(block)
    except Exception as error:
        assert "was not produced" in str(error)
    else:
        raise AssertionError("A missing output should raise")


def test_quality_tier_does_not_overwrite_the_metrics():
    module = block_module("QualityTier")
    metrics = touch(f"{BASENAME}_metrics.csv")
    block = FakeBlock(
        inputs={"metrics_csv": metrics},
        variables={"open_results": False},
        config=base_config(),
    )

    module.initial_quality_tier(block)
    command = block.command

    assert "quality_tier.py" in command
    assert f"{TCOARSE_ROOT}/pretrained_models/rf_quality.pkl" in command
    assert block.uploads == [f"{BASENAME}_metrics.csv"]

    touch(f"{BASENAME}_quality.csv")
    module.final_quality_tier(block)

    assert block.outputs["quality_csv"].endswith(f"{BASENAME}_quality.csv")
    assert not block.outputs["quality_csv"].endswith("_metrics.csv")


def test_copy_models():
    module = block_module("CopyModels")
    block = FakeBlock(
        inputs={"af3_dir": "/data/examples"},
        variables={"cpus_per_task": 4},
        config=base_config(),
    )

    module.initial_copy_models(block)

    assert "cp_models.py" in block.command
    assert "--workers 4" in block.command

    touch(f"{BASENAME}_pdb", directory=True)
    module.final_copy_models(block)

    assert block.outputs["pdb_dir"].endswith(f"{BASENAME}_pdb")


def test_outputs_are_named_after_the_flow():
    module = block_module("CopyModels")
    block = FakeBlock(inputs={"af3_dir": "/data/examples"}, config=base_config())
    block.flow.name = "My TCoaRse run"

    module.initial_copy_models(block)

    # Not after the AF3 folder, and sanitized into something usable as a path
    assert block.command.endswith("My_TCoaRse_run_pdb --workers 4")

    touch("My_TCoaRse_run_pdb", directory=True)
    module.final_copy_models(block)

    assert block.outputs["pdb_dir"].endswith("My_TCoaRse_run_pdb")


def test_structure_metadata():
    module = block_module("StructureMetadata")
    pdb_dir = touch(f"{BASENAME}_pdb", directory=True)
    block = FakeBlock(inputs={"pdb_dir": pdb_dir}, config=base_config())

    module.initial_structure_metadata(block)

    assert "metadata_from_str.py" in block.command
    assert block.uploads == [f"{BASENAME}_pdb"]

    touch(f"{BASENAME}_metadata.csv")
    module.final_structure_metadata(block)

    assert block.outputs["metadata_csv"].endswith(f"{BASENAME}_metadata.csv")


def test_inputs_from_outside_the_run_folder_are_copied_in():
    module = block_module("StructureMetadata")

    outside = tempfile.mkdtemp(prefix="tcoarse_outside_")
    pdb_dir = os.path.join(outside, f"{BASENAME}_pdb")
    os.makedirs(pdb_dir)

    try:
        block = FakeBlock(inputs={"pdb_dir": pdb_dir}, config=base_config())
        module.initial_structure_metadata(block)
    finally:
        shutil.rmtree(outside, ignore_errors=True)

    # The job only sees the run folder, so the input has to be there
    assert os.path.isdir(f"{BASENAME}_pdb")
    assert block.uploads == [f"{BASENAME}_pdb"]


def test_similarities():
    module = block_module("Similarities")
    block = FakeBlock(
        inputs={
            "metadata_csv": touch(f"{BASENAME}_metadata.csv"),
            "pdb_dir": touch(f"{BASENAME}_pdb", directory=True),
        },
        config=base_config(),
    )

    module.initial_similarities(block)
    command = block.command

    assert f"-pre {TCOARSE_ROOT}/data/af3_training.csv" in command
    assert f"-pre_pdb {TCOARSE_ROOT}/data/pdbs" in command
    assert block.uploads == [f"{BASENAME}_metadata.csv", f"{BASENAME}_pdb"]

    touch("sim_seq.csv")
    touch("sim_str.csv")
    module.final_similarities(block)

    assert block.outputs["sim_seq_csv"].endswith("sim_seq.csv")
    assert block.outputs["sim_str_csv"].endswith("sim_str.csv")


def test_embeddings_on_gpu():
    module = block_module("Embeddings")
    block = FakeBlock(
        inputs={"metadata_csv": touch(f"{BASENAME}_metadata.csv")},
        variables={"device": "cuda", "gpus": 1, "partition": "acc_bscls"},
        config=base_config(),
    )

    module.initial_embeddings(block)
    command = block.command

    assert "emb_generator.py" in command
    assert "-d cuda" in command
    assert "-norm" in command
    assert "--no-compile" in command

    touch(f"{BASENAME}_embeddings.h5")
    module.final_embeddings(block)

    assert block.outputs["embeddings_h5"].endswith(f"{BASENAME}_embeddings.h5")


def test_embeddings_on_cpu():
    module = block_module("Embeddings")
    block = FakeBlock(
        inputs={"metadata_csv": touch(f"{BASENAME}_metadata.csv")},
        variables={"device": "cpu"},
        config=base_config(),
    )

    module.initial_embeddings(block)

    assert "-d cpu" in block.command


def test_predictor_esmc():
    module = block_module("PredictorESMC")
    block = FakeBlock(
        inputs={
            "metadata_csv": touch(f"{BASENAME}_metadata.csv"),
            "embeddings_h5": touch(f"{BASENAME}_embeddings.h5"),
        },
        variables={"open_results": False},
        config=base_config(),
    )

    module.initial_predictor_esmc(block)
    command = block.command

    assert "predictor_esmc.py" in command
    assert f"-m {TCOARSE_ROOT}/pretrained_models/esmc.json" in command

    touch(f"{BASENAME}_esmc_predictions.csv")
    module.final_predictor_esmc(block)

    assert block.outputs["esmc_predictions_csv"].endswith("_esmc_predictions.csv")


def test_pydock_processes_every_chunk():
    module = block_module("PyDockEnergies")
    block = FakeBlock(
        inputs={"pdb_dir": touch(f"{BASENAME}_pdb", directory=True)},
        variables={"cpus_per_task": 16, "complexes_per_chunk": 100},
        config=base_config(),
    )

    module.initial_pydock(block)
    command = block.command

    assert "01_make_manifest.py" in command
    assert "02_make_chunks.py" in command
    assert "03_validate_chain_mapping.py" in command
    assert "worker_chunk.py" in command
    # Every chunk, not only chunk_000000 as in the Nextflow pipeline
    assert "chunks/chunk_*.tsv" in command
    assert "--local-sif /opt/pydock/pydock.sif" in command
    assert "--cpus 16" in command

    with open("pydock_config.yaml", encoding="utf-8") as file:
        config = file.read()

    assert "complexes_per_chunk: 100" in config
    assert f'- "{BASENAME}_pdb"' in config
    assert '- "bindEy"' in config

    # The config travels with the job
    assert block.uploads == [f"{BASENAME}_pdb", "pydock_config.yaml"]

    touch(f"{BASENAME}_pydock_ene.tar")
    module.final_pydock(block)

    assert block.outputs["pydock_tar"].endswith(f"{BASENAME}_pydock_ene.tar")


def test_contact_maps():
    module = block_module("ContactMaps")
    block = FakeBlock(
        inputs={"pdb_dir": touch(f"{BASENAME}_pdb", directory=True)},
        variables={"cpus_per_task": 16, "not_experimental": True},
        config=base_config(),
    )

    module.initial_contact_maps(block)
    command = block.command

    assert "contact_maps.py" in command
    assert "-cm D:E:C:B:A" in command
    assert "-workers 16" in command
    assert command.endswith("-notexp")

    touch(f"{BASENAME}_cm", directory=True)
    module.final_contact_maps(block)

    assert block.outputs["cm_dir"].endswith(f"{BASENAME}_cm")


def test_pairwise_dockq():
    module = block_module("PairwiseDockQ")
    block = FakeBlock(
        inputs={"pdb_dir": touch(f"{BASENAME}_pdb", directory=True)},
        config=base_config(),
    )

    module.initial_pairwise_dockq(block)

    assert "pw_sim.py" in block.command

    touch(f"{BASENAME}_pairwise_dockq.csv")
    module.final_pairwise_dockq(block)

    assert block.outputs["pairwise_dockq_csv"].endswith("_pairwise_dockq.csv")


def test_energetic_scorer():
    module = block_module("EnergeticScorer")
    block = FakeBlock(
        inputs={
            "cm_dir": touch(f"{BASENAME}_cm", directory=True),
            "pdb_dir": touch(f"{BASENAME}_pdb", directory=True),
        },
        variables={"cpus_per_task": 16},
        config=base_config(),
    )

    module.initial_energetic_scorer(block)
    command = block.command

    assert "energetic_scorer.py" in command
    assert f"-pot {TCOARSE_ROOT}/pretrained_models/potential" in command
    assert "-chains D:E:C:A:B" in command
    assert "-w 16" in command
    assert block.uploads == [f"{BASENAME}_cm", f"{BASENAME}_pdb"]

    touch(f"{BASENAME}_tcoarse_energies.csv")
    module.final_energetic_scorer(block)

    assert block.outputs["energies_csv"].endswith("_tcoarse_energies.csv")


def test_merge_energies_with_optional_metrics():
    module = block_module("MergeEnergies")
    block = FakeBlock(
        inputs={
            "energies_csv": touch(f"{BASENAME}_tcoarse_energies.csv"),
            "metadata_csv": touch(f"{BASENAME}_metadata.csv"),
            "pydock_tar": touch(f"{BASENAME}_pydock_ene.tar"),
            "metrics_csv": touch(f"{BASENAME}_metrics.csv"),
        },
        config=base_config(),
    )

    module.initial_merge_energies(block)
    command = block.command

    assert "merge_energies.py" in command
    assert "-metrics" in command
    assert len(block.uploads) == 4

    touch(f"{BASENAME}_tcoarse_pydock_energies.csv")
    module.final_merge_energies(block)

    assert block.outputs["merged_csv"].endswith("_tcoarse_pydock_energies.csv")


def test_predictor_tcoarse():
    module = block_module("PredictorTCoaRse")
    block = FakeBlock(
        inputs={"merged_csv": touch(f"{BASENAME}_tcoarse_pydock_energies.csv")},
        variables={"open_results": False},
        config=base_config(),
    )

    module.initial_predictor_tcoarse(block)
    command = block.command

    assert "predictor_tcoarse.py" in command
    assert f"-m {TCOARSE_ROOT}/pretrained_models/tcoarse.json" in command

    touch(f"{BASENAME}_tcoarse_predictions.csv")
    module.final_predictor_tcoarse(block)

    assert block.outputs["tcoarse_predictions_csv"].endswith("_tcoarse_predictions.csv")


def test_predictor_bimodal():
    module = block_module("PredictorBimodal")
    block = FakeBlock(
        inputs={
            "merged_csv": touch(f"{BASENAME}_tcoarse_pydock_energies.csv"),
            "embeddings_h5": touch(f"{BASENAME}_embeddings.h5"),
        },
        variables={"open_results": False},
        config=base_config(),
    )

    module.initial_predictor_bimodal(block)
    command = block.command

    assert "predictor_bimodal.py" in command
    assert f"-m {TCOARSE_ROOT}/pretrained_models/bimodal.json" in command

    touch(f"{BASENAME}_bimodal_predictions.csv")
    module.final_predictor_bimodal(block)

    assert block.outputs["bimodal_predictions_csv"].endswith("_bimodal_predictions.csv")


def test_missing_configuration_is_reported():
    module = block_module("CopyModels")
    block = FakeBlock(inputs={"af3_dir": "/data/examples"}, config={})

    try:
        module.initial_copy_models(block)
    except Exception as error:
        assert "not configured" in str(error)
    else:
        raise AssertionError("A missing TCoaRse folder should raise")


def test_missing_input_is_reported():
    module = block_module("StructureMetadata")
    block = FakeBlock(config=base_config())

    try:
        module.initial_structure_metadata(block)
    except Exception as error:
        assert "required" in str(error)
    else:
        raise AssertionError("A missing input should raise")


# ==========================#
# Runner
# ==========================#
def main():
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]

    failures = []

    for test in tests:
        setup_function(test)
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as error:  # pylint: disable=broad-except
            import traceback

            failures.append((test.__name__, error))
            print(f"FAIL {test.__name__}: {error}")
            traceback.print_exc()
        finally:
            teardown_function(test)

    print(f"\n{len(tests) - len(failures)}/{len(tests)} tests passed")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
