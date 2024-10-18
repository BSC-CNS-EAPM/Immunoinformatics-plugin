import os
import shutil
import subprocess
import typing
import pandas as pd


def runPredigPCH(df_csv: pd.DataFrame, seed: int, predigPCH_path: str):

    # Check if 'peptide' and 'allele' columns exist
    if "peptide" not in df_csv.columns and "epitope" not in df_csv.columns:
        raise ValueError(
            "The input CSV file must contain 'peptide' or 'epitope' column."
        )

    if "epitope" in df_csv.columns:
        df_csv = df_csv.rename(columns={"epitope": "peptide"})

    df_csv = df_csv[["peptide"]]
    df_csv.to_csv(".input_pch.csv", index=False)

    # Run the PCH
    try:
        proc = subprocess.Popen(
            [
                "Rscript",
                predigPCH_path,
                "--input",
                ".input_pch.csv",
                "--seed",
                str(seed),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate()
        print("Output:", stdout.decode())
        print("Error:", stderr.decode())
    except Exception as e:
        raise Exception(f"An error occurred while running the predigPCH: {e}")

    df = pd.read_csv(".input_pch_pch.csv")
    df = df.rename(columns={"peptide": "epitope"})
    df.to_csv("output_pch.csv", index=True)

    os.remove(".input_pch.csv")
    os.remove(".input_pch_pch.csv")

    return df


def runPredigMHCflurry(df_csv: pd.DataFrame, predigMHCflurry_path: str):

    # Check if 'peptide' and 'allele' columns exist
    if "peptide" not in df_csv.columns and "epitope" not in df_csv.columns:
        raise ValueError(
            "The input CSV file must contain 'peptide' or 'epitope' column."
        )
    if "HLA_allele" not in df_csv.columns and "allele" not in df_csv.columns:
        raise ValueError(
            "The input CSV file must contain 'allele' or 'hla_allele' column."
        )

    if "hla_allele" in df_csv.columns:
        df_csv = df_csv.rename(columns={"hla_allele": "allele"})
    if "HLA_allele" in df_csv.columns:
        df_csv = df_csv.rename(columns={"HLA_allele": "allele"})
    if "epitope" in df_csv.columns:
        df_csv = df_csv.rename(columns={"epitope": "peptide"})

    df_csv = df_csv[["peptide", "allele"]]
    df_csv.to_csv(".input_MHCflurry.csv", index=False)

    output = "output_MHCflurry.csv"

    # Run the MHCflurry
    try:
        proc = subprocess.Popen(
            [
                predigMHCflurry_path,
                ".input_MHCflurry.csv",
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
    df = df.rename(columns={"allele": "hla_allele", "peptide": "epitope"})
    df.to_csv(output, index=True)

    os.remove(".input_MHCflurry.csv")

    return df


def runPredigNetCleave(
    predigNetcleave_path: str,
    mode: int,
    df_csv: typing.Optional[pd.DataFrame] = None,
    fasta: typing.Optional[str] = None,
):

    if df_csv is None and fasta is None:
        raise ValueError("Either df_csv or fasta must be provided.")

    net_cleave_input = ""
    if df_csv is not None:

        # Check if 'peptide' and 'allele' columns exist
        if "peptide" not in df_csv.columns and "epitope" not in df_csv.columns:
            raise ValueError(
                "The input CSV file must contain 'peptide' or 'epitope' column."
            )

        if "epitope" in df_csv.columns:
            df_csv = df_csv.rename(columns={"epitope": "peptide"})

        if "uniprot_id" not in df_csv.columns:
            raise ValueError("The input CSV file must contain 'uniprot_id' column.")

        df_csv = df_csv[["peptide", "uniprot_id"]]
        df_csv = df_csv.rename(columns={"peptide": "epitope"})
        net_cleave_input = ".input_NetCleave.csv"
        df_csv.to_csv(net_cleave_input, index=False)
    elif fasta is not None:
        net_cleave_input = fasta

    # Run the NetCleave
    # python_path_env = "/home/lavane/micromamba/envs/horus/bin/python"
    python_path_env = "/home/perry/miniconda3/envs/horus/bin/python"

    # --pred_input
    # 1: fasta
    # 2: uniprot
    # 3: recombinant protein seq
    try:
        proc = subprocess.Popen(
            [
                python_path_env,
                predigNetcleave_path,
                "--predict",
                net_cleave_input,
                "--pred_input",
                str(mode),
            ],
            # env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate()
        print("Output:", stdout.decode())
        print("Error:", stderr.decode())
    except Exception as e:
        raise Exception(f"An error occurred while running the NetCleave: {e}")

    if mode == 1:
        output = "input_NetCleave.csv"
    else:
        output = "output_NetCleave.csv"

    output = os.path.join("output", output)
    df = pd.read_csv(output)
    df = df[["epitope", "prediction"]]
    df = df.rename(columns={"prediction": "netcleave"})
    df.to_csv(output, index=True)

    shutil.rmtree("output")

    return df


def runPredigNOAH(
    df_csv: pd.DataFrame, predigNOAH_path: str, model: str, python_exec: str = "python"
) -> pd.DataFrame:

    # Check if 'peptide' and 'allele' columns exist
    if "peptide" not in df_csv.columns and "epitope" not in df_csv.columns:
        raise ValueError(
            "The input CSV file must contain 'peptide' and 'allele' column."
        )
    if (
        "HLA_allele" not in df_csv.columns
        and "allele" not in df_csv.columns
        and "HLA" not in df_csv.columns
    ):
        raise ValueError(
            "The input CSV file must contain 'allele' or 'hla_allele' or 'HLA' column."
        )

    if "hla_allele" in df_csv.columns:
        df_csv = df_csv.rename(columns={"hla_allele": "allele"})
    if "HLA_allele" in df_csv.columns:
        df_csv = df_csv.rename(columns={"HLA_allele": "allele"})
    if "epitope" in df_csv.columns:
        df_csv = df_csv.rename(columns={"epitope": "peptide"})

    df_csv = df_csv[["peptide", "allele"]]
    df_csv = df_csv.rename(columns={"allele": "HLA"})
    df_csv.to_csv(".input_noah.csv", index=False)

    # Run the NOAH
    try:
        with subprocess.Popen(
            [
                python_exec,
                predigNOAH_path,
                "-i",
                ".input_noah.csv",
                "-m",
                model,
                "-o",
                ".output_noah.csv",
            ]
        ) as proc:
            proc.wait()
    except Exception as e:
        raise Exception(f"An error occurred while running the NOAH: {e}")
    print("Parsing NOAH output")

    output = "output_noah_parsed.csv"

    df = pd.read_csv(
        ".output_noah.csv",
        delimiter="\t",
        header=None,
    )
    df.columns = ["hla_allele", "epitope", "NOAH"]
    df.to_csv(output, index=True)

    os.remove(".input_noah.csv")
    os.remove(".output_noah.csv")

    return df


def run_Predig_tapmap(
    df_csv: pd.DataFrame,
    tapmap_path: str,
    mat: str,
    peptide_len: list[int],
    alpha: typing.Union[float, None],
    precursor_len: typing.Union[int, None],
) -> pd.DataFrame:

    # Check if 'peptide' and 'allele' columns exist
    if "peptide" not in df_csv.columns and "epitope" not in df_csv.columns:
        raise ValueError(
            "The input CSV file must contain 'peptide' and 'allele' column."
        )

    if "epitope" in df_csv.columns:
        df_csv = df_csv.rename(columns={"epitope": "peptide"})

    df_csv = df_csv[["peptide"]]
    dict_sizes = {}
    if peptide_len is None:
        for peptide in df_csv["peptide"]:
            if len(peptide) in dict_sizes:
                dict_sizes[len(peptide)].append(peptide)
            else:
                dict_sizes[len(peptide)] = [peptide]
    else:
        for peptide in df_csv["peptide"]:
            if len(peptide) in peptide_len:
                if len(peptide) in dict_sizes:
                    dict_sizes[len(peptide)].append(peptide)
                else:
                    dict_sizes[len(peptide)] = [peptide]

    for size in dict_sizes:
        with open(f".input_tapmap_{size}.fasta", "w") as f:
            for i, peptide in enumerate(dict_sizes[size]):
                f.write(f">{i}\n")
                f.write(peptide + "\n")

    for size in dict_sizes:
        print(f"Running tapmap for peptides of size {size}")
        command = tapmap_path
        if mat:
            command += f" -mat {mat} "
        if alpha:
            command += f"-a {alpha} "
        command += f"-l {size} "
        if precursor_len:
            command += f"-pl {precursor_len} "
        command += f".input_tapmap_{size}.fasta > .output_tapmap_{size}.txt"
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
            raise Exception(
                f"An error occurred while running the tapmap size={size}: {e}"
            )

    print("Parsing tapmap output")

    epitope = []
    tap = []
    for size in dict_sizes:
        with open(f".output_tapmap_{size}.txt", "r") as infile:
            for line in infile:
                if not line.startswith("#"):
                    parts = line.split()
                    if (
                        len(parts) >= 3
                    ):  # Ensure there are at least three parts in the line
                        epitope.append(parts[1])
                        tap.append(parts[2])

    for size in dict_sizes:
        os.remove(f".input_tapmap_{size}.fasta")
        os.remove(f".output_tapmap_{size}.txt")

    df = pd.DataFrame({"epitope": epitope, "TAP": tap})
    df.to_csv("output_tapmap.csv", index=False)

    return df
