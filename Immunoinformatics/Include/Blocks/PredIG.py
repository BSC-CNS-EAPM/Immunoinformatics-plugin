"""
Module containing the PredIG block for the Immunoinformatics plugin
"""

from os import name

import json
import random
import yaml

from typing import Any, Dict, List, Tuple, Union, cast

from HorusAPI import (
    Extensions,
    PluginBlock,
    PluginVariable,
    SlurmBlock,
    CustomVariable,
    VariableTypes,
    InputBlock,
)
from utils import (
    run_Predig_tapmap,
    runPredigMHCflurry,
    runPredigNetCleave,
    runPredigNOAH,
    runPredigPCH,
)


from Pages.setup_predig import setup_predig_page

setup_predig_variable = CustomVariable(
    id="setup_predig",
    name="Setup PredIG",
    description="Setup the PredIG simulation",
    customPage=setup_predig_page,
    showInCanvas=True,
    type=VariableTypes.ANY,  # type: ignore
)


input_yaml_variable = PluginVariable(
    id="input_yaml",
    name="Input YAML",
    description="Input configuration as a single yaml file. Overrides 'Setup' button.",
    type=VariableTypes.FILE,
    allowedValues=["yaml"],
)

# ==========================#
# Variable inputs
# ==========================#
# inputCSV = PluginVariable(
#     name="Input CSV",
#     id="input_csv",
#     description="The input csv with the epitope and presenting HLA-I allele.",
#     type=VariableTypes.FILE,
#     allowedValues=["csv"],
# )
# inputTxtbox = PluginVariable(
#     name="Input txtbox",
#     id="input_txtbox",
#     description="The input txt with the epitope and presenting HLA-I allele.",
#     type=VariableTypes.TEXT_AREA,
# )
# modelXGVar = PluginVariable(
#     name="PredIG model",
#     id="modelXGvar",
#     description="The PredIG model.",
#     type=VariableTypes.STRING_LIST,
#     defaultValue="/home/perry/data/Programs/Immuno/Predig/spw_xtreme_predig_model.model",
# )
# input_csv_group = VariableGroup(
#     id="file_variable_group",
#     name="File variable group",
#     description="Input with the csv file format.",
#     variables=[inputCSV, modelXGVar],
# )
# input_txt_group = VariableGroup(
#     id="txt_variable_group",
#     name="TxtBox variable group",
#     description="Input with the txt format.",
#     variables=[inputTxtbox, modelXGVar],
# )


# ==========================#
# Variable outputs
# ==========================#
outputPredIG = PluginVariable(
    name="Output CSV",
    id="output_predig",
    description="The output csv",
    type=VariableTypes.FILE,  # type: ignore
    allowedValues=["csv"],
)


##############################
#        Slurm variables     #
##############################
PREDIG_SPLIT_DIR = ".predig_split"
PREDIG_JOB_RUNNER = "predig_job.py"
RECORD_OUTPUT_FILE = "output_predig_record.csv"
JOB_JSON_NAME = "job.json"

DEFAULT_SLURM_TEMPLATE = """#!/bin/bash
#SBATCH --job-name=predig_%record_id%
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=02:00:00

%command%
"""

useSlurmVariable = PluginVariable(
    id="use_slurm",
    name="Use Slurm",
    description=(
        "Submit the FASTA records of the input as Slurm job(s) using the "
        "'Slurm script template'. Only applies to the FASTA simulation mode. "
        "Use the 'Slurm batch size' variable to group several records per job."
    ),
    type=VariableTypes.BOOLEAN,
    defaultValue=False,
    category="Slurm",
)

slurmScriptVariable = PluginVariable(
    id="slurm_script",
    name="Slurm script template",
    description=(
        "SBATCH script template used to submit the FASTA records. The '%command%' "
        "placeholder is replaced with the command that runs the PredIG pipeline for "
        "the records of the job, and '%record_id%' is replaced with the identifier "
        "of the first record of the batch."
    ),
    type=VariableTypes.CODE,
    allowedValues=["shell"],
    defaultValue=DEFAULT_SLURM_TEMPLATE,
    category="Slurm",
)

slurmBatchSizeVariable = PluginVariable(
    id="slurm_batch_size",
    name="Slurm batch size",
    description=(
        "Number of FASTA records to run per Slurm job. Use 1 to submit one job per "
        "record, a number bigger than 1 to group that amount of records per job, or "
        "0 to run all the records in a single job."
    ),
    type=VariableTypes.INTEGER,
    defaultValue=1,
    category="Slurm",
)


##############################
#       Other variables      #
##############################
# seedVar = PluginVariable(
#     name="Seed",
#     id="seed",
#     description="The seed for the random number generator.",
#     type=VariableTypes.INTEGER,
#     defaultValue=1234,
# )
# modelVar = PluginVariable(
#     name="Model",
#     id="model",
#     description="The model to use.",
#     type=VariableTypes.FILE,
#     defaultValue="/home/perry/data/Programs/Immuno/Neoantigens-NOAH/models/model.pkl",
# )
# hlaVar = PluginVariable(
#     name="HLA allele",
#     id="HLA_allele",
#     description="The HLA allele to use.",
#     type=VariableTypes.STRING,
#     defaultValue="HLA-A02:01",
# )
# peptideLenVar = PluginVariable(
#     name="Peptide length",
#     id="peptide_len",
#     description="The length of the peptide. Give a list of sizes",
#     type=VariableTypes.NUMBER_LIST,
#     defaultValue=None,
# )
# matVar = PluginVariable(
#     name="Matrix",
#     id="mat",
#     description="The matrix to use.",
#     type=VariableTypes.FILE,
#     defaultValue="/home/perry/data/Programs/Immuno/netCTLpan-1.1/data/tap.logodds.mat",
# )
# alphaVar = PluginVariable(
#     name="Alpha",
#     id="alpha",
#     description="The alpha value to use.",
#     type=VariableTypes.FLOAT,
#     defaultValue=None,
# )
# precursorLenVar = PluginVariable(
#     name="Precursor length",
#     id="precursor_len",
#     description="The precursor length to use.",
#     type=VariableTypes.INTEGER,
#     defaultValue=None,
# )


def _split_fasta(text: str) -> List[Tuple[str, str]]:
    """
    Split the contents of a (multi)fasta into (header, sequence) records.
    """
    records: List[Tuple[str, str]] = []
    header: Union[str, None] = None
    sequence_lines: List[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(">"):
            if header is not None:
                records.append((header, "\n".join(sequence_lines)))
            header = stripped[1:].strip()
            sequence_lines = []
        elif header is not None and stripped != "":
            sequence_lines.append(stripped)

    if header is not None:
        records.append((header, "\n".join(sequence_lines)))

    return [(h, s) for h, s in records if s != ""]


def _record_id(header: str) -> str:
    """
    Extract a short identifier from a fasta header.
    """
    parts = header.split()
    return parts[0] if len(parts) > 0 else header


def _run_fasta_job(job: Dict[str, Any]):
    """
    Run the whole PredIG pipeline for a single FASTA record inside its own
    working directory. Each job is self-contained so it can be dispatched to
    other executors (e.g. Slurm) later on.

    Delegates to predig_job.run_fasta_job, which is also the entry point used
    by the Slurm jobs.
    """
    from predig_job import run_fasta_job

    return run_fasta_job(job)


def _run_fasta_jobs(common: Dict[str, Any], input_text: str):
    """
    Split the input multiFASTA and run one PredIG pipeline per record.
    Records are processed sequentially; a failing record is reported and
    skipped. Returns the merged DataFrame of all successful records.
    """
    import os
    import shutil

    import pandas as pd

    records = _split_fasta(input_text)

    if len(records) == 0:
        raise ValueError(
            "No valid FASTA records were found in the input. Make sure it contains at least one entry starting with '>' followed by its sequence."
        )

    print(f"Input contains {len(records)} FASTA record(s)")

    base_dir = os.path.abspath(PREDIG_SPLIT_DIR)
    os.makedirs(base_dir, exist_ok=True)

    jobs = []
    for index, (header, sequence) in enumerate(records):
        jobs.append(
            {
                **common,
                "record_id": _record_id(header),
                "fasta_text": f">{header}\n{sequence}\n",
                "workdir": os.path.join(base_dir, f"record_{index}"),
                "ok": False,
            }
        )

    results = []
    failed = []
    total = len(jobs)

    for position, job in enumerate(jobs):
        record_id = job["record_id"]
        print(f"[{position + 1}/{total}] Running PredIG for record '{record_id}'")
        try:
            os.makedirs(job["workdir"], exist_ok=True)
            results.append(_run_fasta_job(job))
            job["ok"] = True
            print(
                f"[{position + 1}/{total}] Record '{record_id}' finished successfully"
            )
        except Exception as e:
            failed.append((record_id, job["workdir"], str(e)))
            print(
                f"[{position + 1}/{total}] Record '{record_id}' failed and was skipped: {e}"
            )

    for job in jobs:
        if job["ok"]:
            shutil.rmtree(job["workdir"], ignore_errors=True)

    if len(results) == 0:
        shutil.rmtree(base_dir, ignore_errors=True)
    else:
        try:
            os.rmdir(base_dir)
        except OSError:
            pass

    if len(failed) > 0:
        print(f"{len(failed)} of {total} FASTA record(s) failed:")
        for record_id, workdir, error in failed:
            print(f"- '{record_id}': {error}")
            print(f"  Partial results kept at '{os.path.abspath(workdir)}'")

    if len(results) == 0:
        raise ValueError("All FASTA records failed. Check the logs above for details.")

    print("Merging results from all records")

    df_final = pd.concat(results, ignore_index=True)

    return df_final.reset_index(drop=True)


def _finalize_output(block: PluginBlock, df_joined) -> None:
    """
    Apply the final column cleanup, save the merged CSV and report the results.
    """
    import glob
    import os

    columns_to_delete: list[str] = block.config.get("columns_to_delete")

    if columns_to_delete:
        columns_to_delete = [c.lower() for c in columns_to_delete]
        for col in df_joined.columns:
            if col.lower() in columns_to_delete:
                df_joined = df_joined.drop(columns=col)

    # Remove any *_output.csv file to prevent other programs messing the folder
    for file in glob.glob("*output*.csv"):
        os.remove(file)

    # Save the results as a CSV
    filename = block.flow.name + "_output.csv"
    df_joined.to_csv(filename, index=False)

    print("PredIG simulations finished")

    safe_path = os.path.abspath(filename)

    from App import AppDelegate  # type: ignore

    if AppDelegate().mode == "webapp":
        # Get only the last 3 components of the path /flo_dir/flow_results/results.csv
        safe_path = "/".join(safe_path.split("/")[-3:])

    print(f"Results are at: '{safe_path}'")

    Extensions().open(
        "immuno",
        "results",
        data={"csv": safe_path},
        title="PredIG results",
    )

    Extensions().storeExtensionResults(
        "immuno",
        "results",
        data={"csv": safe_path},
        title="PredIG results",
    )

    # Save the blocklogs to a file
    with open("predig.log", "w") as f:
        f.write(block.blockLogs)

    block.setOutput(outputPredIG.id, filename)


##############################
#       Slurm execution      #
##############################
def _render_slurm_script(template: str, command: str, record_id: str) -> str:
    """
    Render the Slurm script template for a single FASTA record. The
    '%command%' placeholder is replaced with the command that runs the PredIG
    pipeline and '%record_id%' with the identifier of the record.
    """

    if template is None or template.strip() == "":
        raise ValueError(
            "The Slurm script template is empty. Provide a valid SBATCH script "
            "containing a '%command%' placeholder."
        )

    if "%command%" not in template:
        raise ValueError(
            "The Slurm script template must contain a '%command%' placeholder "
            "where the PredIG command will be inserted."
        )

    return template.replace("%command%", command).replace("%record_id%", record_id)


def _slurm_log_tail(workdir: str, max_lines: int = 30) -> Union[str, None]:
    """
    Return the tail of the Slurm output log of a record working directory,
    if present.
    """
    import glob
    import os

    logs = sorted(glob.glob(os.path.join(workdir, "slurm*.out")))

    if len(logs) == 0:
        return None

    with open(logs[0], "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    tail = "".join(lines[-max_lines:])

    return f"Last lines of '{os.path.basename(logs[0])}':\n{tail}"


def _submit_slurm_jobs(block: PluginBlock, common: Dict[str, Any], input_text: str):
    """
    Prepare one working directory per FASTA record and submit them as Slurm
    job(s) using the 'slurm_script' template variable. The records are grouped
    in batches according to the 'slurm_batch_size' variable: one job per
    record (1), groups of N records, or all the records in a single job (0).
    """
    import os
    import shutil

    records = _split_fasta(input_text)

    if len(records) == 0:
        raise ValueError(
            "No valid FASTA records were found in the input. Make sure it contains at least one entry starting with '>' followed by its sequence."
        )

    print(f"Input contains {len(records)} FASTA record(s)")

    template = block.variables.get(slurmScriptVariable.id)

    # Parse the batch size
    raw_batch_size = block.variables.get(slurmBatchSizeVariable.id, 1)
    try:
        batch_size = int(raw_batch_size)
    except (TypeError, ValueError):
        raise ValueError("The 'Slurm batch size' variable must be an integer.")

    if batch_size < 0:
        raise ValueError("The 'Slurm batch size' variable can not be negative.")

    # A batch size of 0 (or bigger than the amount of records) runs all the
    # records in a single job
    if batch_size == 0 or batch_size > len(records):
        batch_size = len(records)

    base_dir = os.path.abspath(PREDIG_SPLIT_DIR)
    os.makedirs(base_dir, exist_ok=True)

    # Copy the job runner next to the record folders so it is shipped to the
    # remote together with the inputs
    runner_src = os.path.join(block.pluginDir, "Include", PREDIG_JOB_RUNNER)
    if not os.path.isfile(runner_src):
        raise FileNotFoundError(
            f"Could not find the PredIG job runner at '{runner_src}'."
        )
    shutil.copy2(runner_src, os.path.join(base_dir, PREDIG_JOB_RUNNER))

    record_infos = []

    for index, (header, sequence) in enumerate(records):
        record_id = _record_id(header)
        dirname = f"record_{index}"
        workdir = os.path.join(base_dir, dirname)
        os.makedirs(workdir, exist_ok=True)

        job = {
            **common,
            "record_id": record_id,
            "fasta_text": f">{header}\n{sequence}\n",
            "workdir": ".",
        }

        with open(os.path.join(workdir, JOB_JSON_NAME), "w", encoding="utf-8") as f:
            json.dump(job, f, indent=2)

        # Remove results from previous runs of the same record
        output_csv = os.path.join(workdir, RECORD_OUTPUT_FILE)
        if os.path.isfile(output_csv):
            os.remove(output_csv)

        record_infos.append({"record_id": record_id, "dirname": dirname})

    # Group the records in batches and generate one script per batch. The
    # scripts live next to the runner and the record folders (both local and
    # remote), so relative paths are used to reach them.
    batches = [
        record_infos[i : i + batch_size]
        for i in range(0, len(record_infos), batch_size)
    ]

    local_scripts = []

    for index, batch in enumerate(batches):
        record_dirs = " ".join(info["dirname"] for info in batch)

        # Use the configured Python executable so the job inherits the same
        # environment (with pandas, xgboost, NetCleave/NOAH dependencies)
        # as the local run
        python_exec = common.get("python_exec") or "python"
        command = f"{python_exec} {PREDIG_JOB_RUNNER} {record_dirs}"

        # '%record_id%' refers to the first record of the batch
        script_path = os.path.join(base_dir, f"batch_{index}.sbatch")

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(_render_slurm_script(template, command, batch[0]["record_id"]))

        local_scripts.append(script_path)

    print(
        f"Submitting {len(batches)} Slurm job(s) with a batch size of {batch_size} record(s)"
    )

    # Send the folder with the inputs and the runner to the remote if needed
    remote_base_dir = None
    if not block.remote.isLocal:
        from Server.FlowManager import Flow  # type: ignore

        local_flow_workdir = os.path.basename(Flow.flowWorkDir(block.flow.path))
        destination = os.path.join(
            block.remote.workDir, local_flow_workdir, os.path.basename(base_dir)
        )

        print(f"Sending the PredIG inputs to '{destination}'")

        remote_base_dir = block.remote.sendData(base_dir, destination)

    scripts_to_submit = list(local_scripts)
    if remote_base_dir:
        scripts_to_submit = [
            os.path.join(remote_base_dir, os.path.basename(script))
            for script in local_scripts
        ]

    print("scripts_to_submit", scripts_to_submit)

    # Submit all the jobs at once, Horus takes care of polling their status
    job_ids = block.remote.submitJob(scripts_to_submit)
    if isinstance(job_ids, str):
        job_ids = [job_ids]

    for index, (batch, job_id) in enumerate(zip(batches, job_ids)):
        record_ids = ", ".join(info["record_id"] for info in batch)
        print(
            f"Submitted Slurm job {job_id} for batch {index + 1}/{len(batches)}: [{record_ids}]"
        )

    block.extraData["predig_used_slurm"] = True
    block.extraData["predig_base_dir"] = base_dir
    block.extraData["predig_remote_base_dir"] = remote_base_dir
    block.extraData["predig_records"] = record_infos

    print(
        f"{len(batches)} Slurm job(s) submitted. The results will be collected when all the jobs are finished."
    )


def collectSlurmResults(block: PluginBlock):
    """
    Final action of the PredIG block. Collects the outputs of the per-record
    Slurm jobs, merges them and saves the final CSV. Does nothing when the
    Slurm execution was not enabled.
    """
    import os
    import shutil

    if not block.extraData.get("predig_used_slurm", False):
        return None

    # Reset the flag first so a following run never reuses stale state
    block.extraData["predig_used_slurm"] = False

    import pandas as pd

    base_dir = block.extraData.get("predig_base_dir", PREDIG_SPLIT_DIR)
    records = block.extraData.get("predig_records", [])
    remote_base_dir = block.extraData.pop("predig_remote_base_dir", None)

    if remote_base_dir:
        print(f"Downloading the PredIG results from '{remote_base_dir}'")
        block.remote.getData(remote_base_dir, os.path.dirname(base_dir))

    results = []
    failed = []
    total = len(records)

    for position, record in enumerate(records):
        record_id = record["record_id"]
        workdir = os.path.join(base_dir, record["dirname"])
        output_csv = os.path.join(workdir, RECORD_OUTPUT_FILE)

        if os.path.isfile(output_csv):
            results.append(pd.read_csv(output_csv))
            # shutil.rmtree(workdir, ignore_errors=True)
            print(
                f"[{position + 1}/{total}] Record '{record_id}' finished successfully"
            )
        else:
            failed.append((record_id, workdir))
            print(
                f"[{position + 1}/{total}] Record '{record_id}' failed and was skipped"
            )
            log_tail = _slurm_log_tail(workdir)
            if log_tail:
                print(log_tail)

    for key in ("predig_base_dir", "predig_records"):
        block.extraData.pop(key, None)

    if len(results) == 0:
        # shutil.rmtree(base_dir, ignore_errors=True)
        raise ValueError("All FASTA records failed. Check the logs above for details.")

    if len(failed) > 0:
        print(f"{len(failed)} of {total} FASTA record(s) failed:")
        for record_id, workdir in failed:
            print(f"- '{record_id}': Partial results kept at '{workdir}'")

    print("Merging results from all records")

    df_final = pd.concat(results, ignore_index=True)

    _finalize_output(block, df_final.reset_index(drop=True))


# Align action block
def runPredIG(block: PluginBlock):
    """
    Run the PredIG block
    """

    import os

    import xgboost as xgb

    # Get the input file from group
    # if block.selectedInputGroup == input_txt_group.id:
    #     inputFile = str(block.inputs.get(inputTxtbox.id))
    #     with open("input.csv", "w", encoding="utf-8") as file:
    #         file.write(inputFile)
    #     inputFile = "input.csv"
    # else:
    #     inputFile = block.inputs.get(inputCSV.id, None)

    # Get the input from the setup
    input_setup: Union[dict, None] = block.variables.get(setup_predig_variable.id, None)
    input_yaml = block.inputs.get(input_yaml_variable.id)

    if input_yaml:
        # Override the input setup, obtain all values from input_yaml.
        with open(input_yaml, "r", encoding="utf-8") as f:
            input_setup = yaml.safe_load(f)

    if not input_setup:
        raise ValueError(
            "No input setup was provided. Please click on the 'Configure' button and save the setup."
        )

    input_text: Union[str, None] = input_setup.get("input_text")
    if input_text is None or input_text == "":
        raise ValueError("No input CSV was provided.")
    input_text = cast(str, input_text)

    simulation = input_setup.get("simulation")

    if simulation is None:
        raise ValueError("No simulation mode was provided.")

    simulation = int(simulation)

    alleles = ""
    if simulation != 1:
        # If the file contains tab spaces, save a .tsv file
        if "\t" in input_text:
            input_text = input_text.replace("\t", ",")
        elif "," in input_text:
            pass
        else:
            raise ValueError(
                "The input file must contain tab or comma separated values."
            )
    else:
        alleles = input_setup.get("HLA_alleles", "")
        if not alleles or alleles == "":
            raise ValueError(
                "No HLA alleles were provided. Those are required when running PredIG with fasta files."
            )

        import re

        wrong_alleles = []
        for allele in [a.strip() for a in alleles.split("\n") if a.strip() != ""]:
            match = re.match(r"^HLA-[ABC]\*[0-9]{1,3}:[0-9]{1,3}$", allele)
            if not match:
                wrong_alleles.append(allele)

        if len(wrong_alleles) > 0:
            raise ValueError(
                "Please modify or remove the alleles in your list that are not part of the HLA 4-digits resolution format established by IMGT. e.g HLA-A*02:01 or HLA-A*100:101. Binding predictions within PredIG can not interpret other allelic nomenclatures correctly: \n{}".format(
                    "\n".join(wrong_alleles)
                )
            )
        alleles = "\n".join(
            [allele.strip() for allele in alleles.split("\n") if allele.strip() != ""]
        )

    simulation_map = {
        1: "FASTA",
        2: "UNIPROT",
        3: "RECOMBINANT",
    }

    print(f"Simulation type: {simulation_map[simulation]} ({simulation})")

    # Get the seed
    seed = int(input_setup.get("seed", random.randint(0, 10000)))

    # TODO have changed the paths for the lavane, need to be chenged back for perry
    model = input_setup.get(
        "model",
        block.config.get(
            "noah_model_path",
            "/home/perry/data/Programs/Immuno/Neoantigens-NOAH/models/model.pkl",
        ),
    )

    # HLA_allele = block.variables.get(hlaVar.id, "HLA-A02:01")
    # peptide_len = input_setup.get("peptide_len", None)
    # if peptide_len is not None and isinstance(peptide_len, str):
    #     raise ValueError("The peptide length must be a list of integers")
    # elif peptide_len is not None and isinstance(peptide_len, list):
    #     peptide_len = [int(p) for p in peptide_len]
    # else:
    #     peptide_len = None
    peptide_len = None

    modelXG_name = input_setup.get("modelXG", "PredIG-NeoA")
    if modelXG_name == "PredIG-NonCan":
        modelXG = block.config.get(
            "predig_noncan_model_path",
            "/home/perry/data/Programs/Immuno/Predig/spw_indep2_rescale_predig_model.model",
        )
    elif modelXG_name == "PredIG-Path":
        modelXG = block.config.get(
            "predig_path_model_path",
            "/home/perry/data/Programs/Immuno/Predig/spw_indep1_rescale_predig_model.model",
        )
    else:  # "PredIG-NeoA"
        modelXG = block.config.get(
            "predig_neoa_model_path",
            "/home/perry/data/Programs/Immuno/Predig/spw_xtreme_predig_model.model",
        )

    mat = input_setup.get("mat") or block.config.get(
        "tapmap_mat_path",
        "/home/perry/data/Programs/Immuno/netCTLpan-1.1/data/tap.logodds.mat",
    )

    alpha = input_setup.get("alpha")

    precursor_len = input_setup.get("precursor_len")

    # Get the PCH path
    pchPath = block.config.get(
        "PCH_path", "/home/albertcs/Projects/ROC/pch_inout/predig_pch_calc.R"
    )

    # Get the MHCflurry path
    mhcflurryPath = block.config.get("MHC_path", "mhcflurry-predict")

    # Get the NetCleave path
    netCleavePath = block.config.get(
        "cleave_path", "/home/perry/data/Github/NetCleave/NetCleave.py"
    )

    # Get the NOah path
    noahPath = block.config.get(
        "noah_path", "/home/perry/data/Github/Neoantigens-NOAH/noah/main_NOAH.py"
    )
    # Get the netCTLpan path
    tapmat_pred_fsa_path = block.config.get(
        "tapmap_path",
        "/home/perry/data/Programs/Immuno/netCTLpan-1.1/Linux_x86_64/bin/tapmat_pred_fsa",
    )

    rscript_path = block.config.get("rscript_path", "Rscript")
    python_exec = block.config.get("python_exec", "python")

    common = {
        "alleles": [a.strip() for a in alleles.split("\n")],
        "seed": seed,
        "model": model,
        "modelXG": modelXG,
        "mat": mat,
        "alpha": alpha,
        "precursor_len": precursor_len,
        "pchPath": pchPath,
        "rscript_path": rscript_path,
        "mhcflurryPath": mhcflurryPath,
        "netCleavePath": netCleavePath,
        "noahPath": noahPath,
        "tapmap_path": tapmat_pred_fsa_path,
        "python_exec": python_exec,
    }

    use_slurm = bool(block.variables.get(useSlurmVariable.id, False))

    if simulation == 1:
        if use_slurm:
            _submit_slurm_jobs(block, common, input_text)
            return

        block.extraData["predig_used_slurm"] = False
        df_joined = _run_fasta_jobs(common, input_text)
        _finalize_output(block, df_joined)
        return

    if use_slurm:
        print(
            "Slurm submission is only supported for the FASTA simulation mode. "
            "The simulation will run locally."
        )

    block.extraData["predig_used_slurm"] = False

    with open("input.csv", "w", encoding="utf-8") as file:
        # Clean the input CSV by removing unnedded quotes "" before writting
        file.write(input_text)

    # Check if the input file is valid
    if not os.path.isfile("input.csv"):
        raise ValueError("The input file is not valid")

    import pandas as pd

    df = pd.read_csv("input.csv")

    # Replace cells that have "" or ''
    df = df.replace('"', "")
    df = df.replace("'", "")

    # Verify that each row has the correct number of columns (all are filled)
    column_lenght = df.shape[1]

    for i, row in df.iterrows():
        if len(row) != column_lenght:
            raise ValueError(
                "The input CSV file must contain the same number of columns in each row."
            )

    # if df.shape[0] > 5000:
    #     raise ValueError("The input CSV file must contain less than 5000 rows.")
    print("Running NetCleave")
    output_netcleave = runPredigNetCleave(
        df_csv=df,
        predigNetcleave_path=netCleavePath,
        mode=simulation,
        python_exec=python_exec,
    )

    df = cast(pd.DataFrame, df)

    # Run the PCH ["epitope"]
    print("Running PCH")
    output_pch = runPredigPCH(
        df_csv=df,
        seed=int(seed),
        predigPCH_path=pchPath,
        rscript_path=rscript_path,
    )

    print("Running MHCflurry")
    # Run the MHCflurry ["epitope", "hla_allele"]
    output_flurry = runPredigMHCflurry(
        df_csv=df,
        predigMHCflurry_path=mhcflurryPath,
    )

    print("Running NOAH")

    # Run the NOAH, ["HLA", "epitope", "NOAH_score"] id="HLA", "epitope"
    output_noah = runPredigNOAH(
        df_csv=df, predigNOAH_path=noahPath, model=model, python_exec=python_exec
    )

    print("Running tapmat_pred_fsa")
    output_tapmap = run_Predig_tapmap(
        df_csv=df,
        tapmap_path=tapmat_pred_fsa_path,
        mat=mat,
        peptide_len=peptide_len,
        alpha=alpha,
        precursor_len=precursor_len,
    )

    print("Joining the outputs")

    # Sequentially merge the DataFrames on a common non-overlapping column, for example 'epitope'
    # df_joined = output_pch.merge(output_flurry, on="epitope", how="inner")
    # df_joined = df_joined.merge(output_netcleave, on="epitope", how="inner")
    # df_joined = df_joined.merge(output_tapmap, on="epitope", how="inner")
    # df_joined = df_joined.merge(output_noah, on="epitope", how="inner")

    df_joined = output_pch.merge(
        output_flurry, left_index=True, right_index=True, how="left"
    )

    df_joined = df_joined.merge(
        output_netcleave, left_index=True, right_index=True, how="left"
    )

    df_joined = df_joined.merge(
        output_tapmap,
        left_index=True,
        right_index=True,
        how="left",
        suffixes=("", "_tapmap"),
    )

    df_joined["id"] = df_joined["hla_allele"] + "_" + df_joined["epitope"]
    output_noah["id"] = output_noah["hla_allele"] + "_" + output_noah["epitope"]
    df_joined = df_joined.merge(
        output_noah, on="id", how="left", suffixes=("", "_noah")
    )

    print("Launching the XGBoost model")
    if "hla_allele_y" in df_joined.columns:
        df_joined = df_joined.drop(columns=["hla_allele_y"])
    if "hla_allele_x" in df_joined.columns:
        df_joined = df_joined.rename(columns={"hla_allele_x": "hla_allele"})

    df_xgboost = df_joined[
        [
            "netcleave",
            "NOAH",
            "mw_peptide",
            "mw_tcr_contact",
            "hydroph_peptide",
            "hydroph_tcr_contact",
            "charge_peptide",
            "charge_tcr_contact",
            "stab_peptide",
            "mhcflurry_affinity",
            "mhcflurry_affinity_percentile",
            "mhcflurry_processing_score",
            "mhcflurry_presentation_score",
        ]
    ]

    # df_xgboost.to_csv("df_xgboost.csv", index=False)
    predig_model = xgb.Booster()
    predig_model.load_model(modelXG)
    predig_input_matrix = xgb.DMatrix(df_xgboost)
    predig_score = predig_model.predict(predig_input_matrix)
    df_joined = pd.concat([df_joined, pd.Series(predig_score, name="predig")], axis=1)

    df_joined["id"] = df_joined["hla_allele"] + "_" + df_joined["epitope"]

    # Rename and sort the columns
    name_mapping = {
        "Id": "ID",
        "Epitope": "epitope",
        "Hla_allele": "HLA_allele",
        "Predig": "PredIG",
        "NOAH": "NOAH",
        "TAP": "TAP",
        "Netcleave": "NetCleave",
        "Mhcflurry_affinity": "mhcflurry_affinity",
        "Mhcflurry_affinity_percentile": "mhcflurry_affinity_percentile",
        "Mhcflurry_presentation_score": "mhcflurry_presentation_score",
        "Mhcflurry_processing_score": "mhcflurry_processing_score",
        "Hydroph_peptide": "Hydrophobicity_peptide",
        "Mw_peptide": "MW_peptide",
        "Charge_peptide": "Charge_peptide",
        "Stab_peptide": "Stab_peptide",
        "Tcr_contact": "TCR_contact",
        "Hydroph_tcr_contact": "Hydrophobicity_tcr_contact",
        "Mw_tcr_contact": "MW_tcr_contact",
        "Charge_tcr_contact": "Charge_tcr_contact",
    }

    name_mapping = {key.lower(): value for key, value in name_mapping.items()}

    df_joined = df_joined.rename(str.lower, axis="columns")

    # Sort based on the mapping
    df_joined = df_joined[name_mapping.keys()]

    # Rename
    df_joined = df_joined.rename(columns=name_mapping)

    _finalize_output(block, df_joined)


description = "An interpretable predictor of CD8+ T-cell epitope immunogenicity."
description += (
    "\nPredIG predicts the immunogenicity of given pairs of epitope and HLA-I alleles."
)
description += (
    "\nPredIG predicts the immunogenicity of full proteins vs. a list of HLA-I alleles."
)
description += "\nPredIG score is a probability from 0 to 1, being 1 the max likelihood for pHLA-I immunogenicity."
description += "\nNote: Max 500 queries per submission."


predigBlock = SlurmBlock(
    name="PredIG",
    description="An interpretable predictor of CD8+ T-cell epitope immunogenicity.\nPredIG predicts the immunogenicity of given pairs of epitope and HLA-I alleles.\nPredIG predicts the immunogenicity of full proteins vs. a list of HLA-I alleles.\nPredIG score is a probability from 0 to 1, being 1 the max likelihood for pHLA-I immunogenicity.\n\nNote: Max 500 queries per submission.",
    initialAction=runPredIG,
    finalAction=collectSlurmResults,
    failOnSlurmError=False,
    variables=[
        setup_predig_variable,
        useSlurmVariable,
        slurmScriptVariable,
        slurmBatchSizeVariable,
    ],
    # variables=[
    #     seedVar,
    #     modelVar,
    #     hlaVar,
    #     peptideLenVar,
    #     matVar,
    #     alphaVar,
    #     precursorLenVar,
    # ],
    inputs=[input_yaml_variable],
    outputs=[outputPredIG],
)
