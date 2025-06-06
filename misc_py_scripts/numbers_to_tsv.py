#!/usr/bin/env python3
from numbers_parser import Document
from pathlib import Path
import pandas as pd
import argparse
import warnings

# Define the columns that should be converted to integers
# This is because in the conversion process the int columns are sometimes read as floats
int_columns = [
    "year",
    "id",
    "year_born",
    "is_stylized",
    "is_hardspeech",
    "nfv_freq",
    "speech_word_count",
    "correction"
    ]

def get_numbers_data(filename: str) -> pd.DataFrame:
    doc = Document("../data/yfirfarið-GLF/agustagustsson-corrected.numbers")
    sheet = doc.sheets[0]
    table = sheet.tables[0]
    data = table.rows(values_only=True)

    df = pd.DataFrame(data[1:], columns=data[0])
    for col in int_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

    return df


parser = argparse.ArgumentParser()

parser.add_argument(
    "input",
    nargs="+",
    help="One or more .numbers files, or a single directory containing .numbers files"
)
parser.add_argument(
    "--output",
    type=str,
    default="tsv_files",
    help="Output directory for TSV files (default: 'tsv_files' in cwd)"
)
args = parser.parse_args()

if __name__ == "__main__":

    input_files = args.input
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    for input_file in input_files:
        input_path = Path(input_file)
        if input_path.is_dir():
            numbers_files = list(input_path.glob("*.numbers"))
        elif input_path.suffix == ".numbers":
            numbers_files = [input_path]
        else:
            print(f"Skipping {input_file}: not a .numbers file or directory.")
            continue

        for numbers_file in numbers_files:
            # Suppress RuntimeWarning from numbers_parser
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                df = get_numbers_data(numbers_file)

            tsv_filename = output_dir / (numbers_file.stem + ".tsv")
            df.to_csv(tsv_filename, sep="\t", index=False)
            print(f"Converted {numbers_file} to {tsv_filename}")