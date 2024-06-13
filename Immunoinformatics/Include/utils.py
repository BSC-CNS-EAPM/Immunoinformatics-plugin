import os
import subprocess

import pandas as pd


def runPredigPCH(df_csv: pd.DataFrame, seed: int, predigPCH_path: str) -> str:

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


def runPredigMHCflurry(df_csv: pd.DataFrame, predigMHCflurry_path: str) -> str:

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


def runPredigNetCleave(df_csv: pd.DataFrame, predigNetcleave_path: str):

    # Check if 'peptide' and 'allele' columns exist
    if "peptide" not in df_csv.columns or "allele" not in df_csv.columns:
        raise ValueError("The input CSV file must contain 'peptide' and 'allele' column.")

    df_csv = df_csv[["peptide", "uniprot_id"]]
    df_csv = df_csv.rename(columns={"peptide": "epitope"})
    df_csv.to_csv("input_NetCleave.csv", index=False)

    output = "output_NetCleave.csv"

    # Run the NetCleave
    try:
        with subprocess.Popen(
            [
                "python",
                predigNetcleave_path,
                "--predict",
                "input_NetCleave.csv",
                "--pred_input",
                str(2),
            ]
        ) as proc:
            proc.wait()
    except Exception as e:
        raise Exception(f"An error occurred while running the NetCleave: {e}")

    # output = inputFile.replace(".fasta", "_netcleave.csv")

    # Set output
    # Columns epitope,uniprot_id, cleavage_site, netcleave, netc_warning
    return output


def runPredigNOAH(df_csv: pd.DataFrame, predigNOAH_path: str, model: str):

    # Check if 'peptide' and 'allele' columns exist
    if "peptide" not in df_csv.columns or "allele" not in df_csv.columns:
        if not "peptide" in df_csv.columns and "HLA" not in df_csv.columns:
            raise ValueError(
                "The input CSV file must contain 'peptide' and 'allele' or HLA columns."
            )

    df_csv = df_csv[["peptide", "allele"]]
    df_csv = df_csv.rename(columns={"allele": "HLA"})
    df_csv.to_csv("input_noah.csv", index=False)

    # Run the NOAH
    print("Running NOAH")
    try:
        with subprocess.Popen(
            [
                "python",
                predigNOAH_path,
                "-i",
                "input_noah.csv",
                "-m",
                model,
                "-o",
                "output_noah.csv",
            ]
        ) as proc:
            proc.wait()
    except Exception as e:
        raise Exception(f"An error occurred while running the NOAH: {e}")
    print("Parsing NOAH output")

    df = pd.read_csv("output_noah.csv", delimiter="\t")

    df.columns = ["HLA", "peptide", "NOAH_score"]
    df["id"] = df["HLA"] + "_" + df["peptide"]
    df.to_csv("noah_output_parsed.csv", index=False)

    output = "noah_output_parsed.csv"

    print("NOAH finished")

    # Set output
    return output
