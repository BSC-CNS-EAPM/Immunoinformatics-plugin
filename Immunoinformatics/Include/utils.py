import datetime
import os
import shutil
import subprocess
import time
import typing

import pandas as pd

from HorusAPI import PluginBlock, PluginVariable, SlurmBlock, VariableTypes


def runPredigPCH(df_csv: pd.DataFrame, input_name: str, seed: int, predigPCH_path: str) -> str:

    # Check if 'peptide' and 'allele' columns exist
    if "peptide" not in df_csv.columns:
        raise ValueError("The input CSV file must contain 'peptide' column.")

    df_csv = df_csv[["peptide"]]
    df_csv.to_csv("input.csv", index=False)

    # Run the PCH
    try:
        proc = subprocess.Popen(
            ["Rscript", predigPCH_path, "--input", "input.csv", "--seed", str(seed)]
        )
        proc.wait()
    except Exception as e:
        raise Exception(f"An error occurred while running the predigPCH: {e}")

    output = "input_pch.csv"

    df = pd.read_csv(output)

    df = df.rename(columns={"peptide": "epitope"})

    df.to_csv("output_pch.csv", index=False)

    return os.path.abspath("output_pch.csv")


def runPredigMHCflurry(df_csv: pd.DataFrame, input_name: str, predigMHCflurry_path: str) -> str:

    # Check if 'peptide' and 'allele' columns exist
    if "peptide" not in df_csv.columns or "allele" not in df_csv.columns:
        raise ValueError("The input CSV file must contain 'peptide' and 'allele' column.")

    df_csv = df_csv[["peptide", "allele"]]
    df_csv.to_csv("input_MHCflurry.csv", index=False)

    output = "output_MHCflurry.csv"

    # Run the MHCflurry
    try:
        proc = subprocess.Popen(
            [
                predigMHCflurry_path,
                "input_MHCflurry.csv",
                "--out",
                output,
                "--no-throw",
                "--always-include-best-allele",
                "--no-flanking",
            ]
        )
        proc.wait()
    except Exception as e:
        raise Exception(f"An error occurred while running the PredigMHCflurry: {e}")

    df = pd.read_csv(output)

    df.drop("mhcflurry_presentation_percentile", axis=1, inplace=True)
    df = df.rename(columns={"allele": "hla_allele", "peptide": "epitope"})
    df["id"] = df["hla_allele"] + "_" + df["epitope"]

    df.to_csv(output, index=False)

    return output
