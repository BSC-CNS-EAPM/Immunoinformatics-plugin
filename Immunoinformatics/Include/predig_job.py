"""
Standalone runner for one or more PredIG FASTA records.

This module intentionally has no HorusAPI dependencies so it can be executed
on any environment with python, pandas and xgboost available (for example, a
Slurm compute node). It can be imported by the PredIG block or executed as a
script:

    python predig_job.py <workdir> [<workdir> ...]

where each <workdir> is the working directory of a record containing a job.json
file with all the job parameters. Passing more than one workdir runs several
records sequentially inside the same job (batching). For each record, the
resulting DataFrame is saved as <workdir>/output_predig_record.csv. The script
exits with a non-zero code if any of the records fails.
"""

import json
import os
import sys

from typing import Any, Dict, List


def run_fasta_job(job: Dict[str, Any]):
    """
    Run the whole PredIG pipeline for a single FASTA record inside its own
    working directory. Each job is self-contained so it can be dispatched to
    other executors (e.g. Slurm).
    """
    import pandas as pd
    import xgboost as xgb

    from utils import (
        run_Predig_tapmap,
        runPredigMHCflurry,
        runPredigNetCleave,
        runPredigNOAH,
        runPredigPCH,
    )

    workdir = job["workdir"]

    with open(os.path.join(workdir, "input.fasta"), "w", encoding="utf-8") as file:
        file.write(job["fasta_text"])

    print("Running NetCleave")
    df = runPredigNetCleave(
        predigNetcleave_path=job["netCleavePath"],
        mode=1,
        fasta=os.path.join(workdir, "input.fasta"),
        python_exec=job["python_exec"],
        workdir=workdir,
    )

    # Add a new column to the dataframe, the HLA alleles
    df_list = []
    for value in job["alleles"]:
        df_copy = df.copy()
        df_copy["HLA_allele"] = value
        df_list.append(df_copy)

    df = pd.concat(df_list, ignore_index=True)

    # Remove the index colum (does not have names)
    df = df.reset_index(drop=True)

    # Save as csv
    df.to_csv(os.path.join(workdir, "input_fasta.csv"), index=False)

    # Run the PCH ["epitope"]
    print("Running PCH")
    output_pch = runPredigPCH(
        df_csv=df,
        seed=int(job["seed"]),
        predigPCH_path=job["pchPath"],
        rscript_path=job["rscript_path"],
        workdir=workdir,
    )

    print("Running MHCflurry")
    # Run the MHCflurry ["epitope", "hla_allele"]
    output_flurry = runPredigMHCflurry(
        df_csv=df,
        predigMHCflurry_path=job["mhcflurryPath"],
        workdir=workdir,
    )

    print("Running NOAH")

    # Run the NOAH, ["HLA", "epitope", "NOAH_score"] id="HLA", "epitope"
    output_noah = runPredigNOAH(
        df_csv=df,
        predigNOAH_path=job["noahPath"],
        model=job["model"],
        python_exec=job["python_exec"],
        workdir=workdir,
    )

    print("Running tapmat_pred_fsa")
    output_tapmap = run_Predig_tapmap(
        df_csv=df,
        tapmap_path=job["tapmap_path"],
        mat=job["mat"],
        peptide_len=None,
        alpha=job["alpha"],
        precursor_len=job["precursor_len"],
        workdir=workdir,
    )

    print("Joining the outputs")

    df_joined = output_pch.merge(
        output_flurry, left_index=True, right_index=True, how="left"
    )

    df_joined = df_joined.merge(df, left_index=True, right_index=True, how="left")

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
    predig_model.load_model(job["modelXG"])
    predig_input_matrix = xgb.DMatrix(df_xgboost)
    predig_score = predig_model.predict(predig_input_matrix)
    df_joined = pd.concat([df_joined, pd.Series(predig_score, name="predig")], axis=1)

    df_joined["id"] = df_joined["hla_allele"] + "_" + df_joined["epitope"]

    df_joined["source_protein"] = job["record_id"]

    # Rename and sort the columns
    name_mapping = {
        "Id": "ID",
        "Source_protein": "source_protein",
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

    return df_joined.reset_index(drop=True)


def _run_single(workdir: str) -> None:
    """
    Run the PredIG pipeline for a single record: load the job parameters from
    <workdir>/job.json, run the pipeline and save the results as
    <workdir>/output_predig_record.csv.
    """

    job_path = os.path.join(workdir, "job.json")

    if not os.path.isfile(job_path):
        raise FileNotFoundError(f"The job configuration file '{job_path}' does not exist.")

    with open(job_path, "r", encoding="utf-8") as f:
        job = json.load(f)

    # The job runs inside the given workdir (relative paths are resolved from there)
    job["workdir"] = os.path.abspath(workdir)

    df = run_fasta_job(job)

    output_path = os.path.join(job["workdir"], "output_predig_record.csv")
    df.to_csv(output_path, index=False)

    print(f"Saved the results of record '{job['record_id']}' to '{output_path}'")


def main(workdirs: List[str]) -> int:
    """
    Entry point of the script: run the PredIG pipeline for each of the given
    workdirs sequentially. All the records are attempted even if some of them
    fail. Returns 0 if all succeeded, 1 otherwise.
    """

    # Make sure the plugin utils module can be imported when running standalone
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    failed = []

    for position, workdir in enumerate(workdirs):
        try:
            _run_single(workdir)
        except Exception:
            import traceback

            print(f"Record in workdir '{workdir}' failed:", flush=True)
            traceback.print_exc()
            failed.append(workdir)
            print(f"[{position + 1}/{len(workdirs)}] Continuing with the next record", flush=True)

    if len(failed) > 0:
        print(f"{len(failed)} of {len(workdirs)} record(s) failed", flush=True)
        return 1

    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python predig_job.py <workdir> [<workdir> ...]", file=sys.stderr)
        sys.exit(2)

    sys.exit(main(sys.argv[1:]))
