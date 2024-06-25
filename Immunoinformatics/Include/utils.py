import os
import subprocess

import pandas as pd


def runPredigPCH(df_csv: pd.DataFrame, seed: int, predigPCH_path: str) -> pd.DataFrame:

    # Check if 'peptide' and 'allele' columns exist
    if "peptide" not in df_csv.columns:
        raise ValueError("The input CSV file must contain 'peptide' column.")

    df_csv = df_csv[["peptide"]]
    df_csv.to_csv("input.csv", index=False)

    # Run the PCH
    try:
        proc = subprocess.Popen(
            ["Rscript", predigPCH_path, "--input", "input.csv", "--seed", str(seed)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate()
        print("Output:", stdout.decode())
        print("Error:", stderr.decode())
    except Exception as e:
        raise Exception(f"An error occurred while running the predigPCH: {e}")

    output = "input_pch.csv"

    df = pd.read_csv(output)
    df = df.rename(columns={"peptide": "epitope"})
    # df.set_index("epitope", inplace=True)
    df.to_csv("output_pch.csv", index=True)

    return df


def runPredigMHCflurry(df_csv: pd.DataFrame, predigMHCflurry_path: str) -> pd.DataFrame:

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
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate()
        print("Output:", stdout.decode())
        print("Error:", stderr.decode())
    except Exception as e:
        raise Exception(f"An error occurred while running the PredigMHCflurry: {e}")

    df = pd.read_csv(output)
    df.drop("mhcflurry_presentation_percentile", axis=1, inplace=True)
    df = df.rename(columns={"allele": "hla_allele", "peptide": "epitope"})
    df["id"] = df["hla_allele"] + "_" + df["epitope"]
    # df.set_index("epitope", inplace=True)
    df.to_csv(output, index=True)

    return df


def runPredigNetCleave(df_csv: pd.DataFrame, predigNetcleave_path: str):

    # Check if 'peptide' and 'allele' columns exist
    if "peptide" not in df_csv.columns or "allele" not in df_csv.columns:
        raise ValueError("The input CSV file must contain 'peptide' and 'allele' column.")

    df_csv = df_csv[["peptide", "uniprot_id"]]
    df_csv = df_csv.rename(columns={"peptide": "epitope"})
    df_csv.to_csv("input_NetCleave.csv", index=False)

    # Run the NetCleave
    try:
        proc = subprocess.Popen(
            [
                "python",
                predigNetcleave_path,
                "--predict",
                "input_NetCleave.csv",
                "--pred_input",
                str(2),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate()
        print("Output:", stdout.decode())
        print("Error:", stderr.decode())
    except Exception as e:
        raise Exception(f"An error occurred while running the NetCleave: {e}")

    output = "output_NetCleave.csv"
    df = pd.read_csv("output/input_NetCleave_NetCleave.csv")
    df = df[["epitope", "prediction"]]
    df = df.rename(columns={"prediction": "netcleave"})
    # df.set_index("epitope", inplace=True)
    df.to_csv(output, index=True)

    return df


def runPredigNOAH(df_csv: pd.DataFrame, predigNOAH_path: str, model: str) -> pd.DataFrame:

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

    output = "output_noah_parsed.csv"

    df = pd.read_csv(
        "output_noah.csv",
        delimiter="\t",
        header=None,
    )
    df.columns = ["hla_allele", "epitope", "NOAH_score"]
    df["id"] = df["hla_allele"] + "_" + df["epitope"]
    # df.set_index("epitope", inplace=True)
    df.to_csv(output, index=True)

    return df


def run_Predig_tapmap(
    df_csv: pd.DataFrame,
    tapmap_path: str,
    mat: str,
    peptide_len: int,
    alpha: float,
    precursor_len: int,
) -> pd.DataFrame:

    # Check if 'peptide' and 'allele' columns exist
    if "peptide" not in df_csv.columns:
        raise ValueError("The input CSV file must contain 'peptide'.")

    df_csv = df_csv[["peptide"]]
    with open("input_tapmap.csv", "w") as f:
        for i, peptide in enumerate(df_csv["peptide"]):
            f.write(f">{i}\n")
            f.write(peptide + "\n")
    input_csv = os.path.join(os.getcwd(), "input_tapmap.csv")

    command = tapmap_path
    if mat:
        command += f" -mat {mat} "
    if alpha:
        command += f"-a {alpha} "
    if peptide_len:
        command += f"-l {peptide_len} "
    if precursor_len:
        command += f"-pl {precursor_len} "
    command += f"{input_csv} > output_tapmap.txt"
    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        stdout, stderr = proc.communicate()
        print("Output:", stdout.decode())
        print("Error:", stderr.decode())
    except Exception as e:
        raise Exception(f"An error occurred while running the tapmap: {e}")
    print("Parsing tapmap output")

    output = "output_tapmap.csv"

    with open("output_tapmap.txt", "r") as infile:
        epitope = []
        tap = []
        for line in infile:
            if not line.startswith("#"):
                parts = line.split()
                if len(parts) >= 3:  # Ensure there are at least three parts in the line
                    epitope.append(parts[1])
                    tap.append(parts[2])

    df = pd.DataFrame({"epitope": epitope, "TAP": tap})
    # df.set_index("epitope", inplace=True)
    df.to_csv(output, index=True)

    return df
