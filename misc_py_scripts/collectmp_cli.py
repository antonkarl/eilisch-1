#!/usr/bin/env python

from py_scripts.collectmp import examineFile, headers, metadata_name, speech_types_name, get_metadata, TASK_TYPES
import pandas as pd
import argparse
from pathlib import Path
from tqdm import tqdm
import sys


def process_files(xml_files, metadata_file, speech_path, task_type):
    metadata = get_metadata(metadata_file, speech_path)

    rows = []
    for file in tqdm(
        xml_files, desc="Processing files", unit="file(s)", colour="#1ecbe1"
    ):
        results = examineFile(file, metadata, task_type)
        rows.extend(results)

    return rows


def save_tsv_file(data, out_path, task_type):
    df = pd.DataFrame(data)
    file = out_path / "collectmp_out.tsv"

    df.to_csv(file, sep="\t", header=headers[task_type], index=False)
    print(f"TSV file saved to: {file}")


def main():
    parser = argparse.ArgumentParser(
        description="Process IGC-PARLA corpus files and output a TSV file with stylistic fronting data."
    )

    parser.add_argument(
        "xml_path",
        type=Path,
        help="Path to an archive directory containing XML files, or a single XML file."
    )

    parser.add_argument(
        "--task-type",
        type=str,
        help=f"What type of data you want to extract from the corpus. Defaults to {TASK_TYPES[0]}.",
        default=TASK_TYPES[0],
        choices=TASK_TYPES
    )

    parser.add_argument(
        "--metadata",
        type=Path,
        help=f"Optional path to an XML metadata file. Defaults to {metadata_name} located in the archive directory.",
        default=None
    )

    parser.add_argument(
        "--speech-types",
        type=Path,
        help=f"An optional path to a speech type tsv, need to parse the XML files. Defaults to '{speech_types_name}' within the cwd.",
        default=None
    )

    parser.add_argument(
        "--out-path",
        type=Path,
        help="Optional path to save the output TSV file. Defaults to the current working directory.",
        default=Path(".")
    )


    args = parser.parse_args()

    if not args.xml_path.exists():
        print(f"Error: The path {args.xml_path} does not exist.")
        sys.exit(1)

    path_is_dir = args.xml_path.is_dir()

    if path_is_dir:
        xml_files = list(args.xml_path.rglob("*.xml"))
        metadata = args.metadata or (args.xml_path / metadata_name)
    else:
        xml_files = [args.xml_path]
        metadata = args.metadata

        if not metadata:
            print("Error: Passing a metadata file is required when processing a single file")
            sys.exit(1)

    if not metadata.exists():
        print(f"Error: Metadata file '{metadata}' not found.")
        sys.exit(1)

    speech_path = args.speech_types

    if not speech_path:
        speech_path = Path(".", speech_types_name)

    if not speech_path.exists():
        print(f"Error: The speech types path {speech_path} does not exist.")

    output_dir = args.out_path.resolve()
    if not output_dir.exists():
        print(f"Error: The chosen output directory '{output_dir}' does not exist.")
        sys.exit(1)

    data = process_files(xml_files, metadata, speech_path, args.task_type)
    save_tsv_file(data, output_dir, args.task_type)

if __name__ == "__main__":
    main()    