#!/usr/bin/env python

from utils import TASK_TYPES, METADATA_FILE, SPEECH_TYPES_FILE, PHONE_DICT, FREQ_DICT, SaveConfig
from corpus_extrator import CorpusExtractor
from pathlib import Path
import argparse
import sys
import json


def check_path(path):
    if not path:
        return

    if not path.exists():
        print(f"Error: The path {path} does not exist.")
        sys.exit(1)

    return path


def main():
    parser = argparse.ArgumentParser(
        description="Process IGC-PARLA corpus files and output a TSV file with stylistic fronting or hardspeech data."
    )

    parser.add_argument(
        "xml_path",
        type=Path,
        help="Path to an archive directory containing XML files, or a single XML file.",
    )

    parser.add_argument(
        "--task-type",
        type=str,
        help=f"What type of data you want to extract from the corpus. Defaults to {TASK_TYPES[0]}.",
        default=TASK_TYPES[0],
        choices=TASK_TYPES,
    )

    parser.add_argument(
        "--metadata",
        type=Path,
        help=f"Optional path to an XML metadata file. Defaults to {METADATA_FILE} located in the archive directory.",
        default=None,
    )

    parser.add_argument(
        "--speech-types",
        type=Path,
        help=f"An optional path to a speech type tsv, needed to parse the XML files. Defaults to '{SPEECH_TYPES_FILE}'.",
        default=Path(".", SPEECH_TYPES_FILE),
    )

    parser.add_argument(
        "--freq-dict",
        type=Path,
        help=f"An optional path to a word frequency dict, needed to parse the XML files. Defaults to '{FREQ_DICT}'.",
        default=Path(".", FREQ_DICT),
    )

    parser.add_argument(
        "--phonetic-dict",
        type=Path,
        help=f"An optional path to a phonetic dictionary, needed to parse XML files for hardspeech. Defaults to '{PHONE_DICT}'.",
        default=Path(".", PHONE_DICT),
    )

    parser.add_argument(
        "--out-path",
        type=Path,
        help="Optional path to save the output TSV file. Defaults to the current working directory.",
        default=Path("."),
    )

    parser.add_argument(
        "--config-file",
        type=Path,
        help=f"An optional path to a config.json file, used to only extract data specified in the config file.",
        default=None,
    )

    args = parser.parse_args()

    if not args.xml_path.exists():
        print(f"Error: The path {args.xml_path} does not exist.")
        sys.exit(1)

    path_is_dir = args.xml_path.is_dir()

    if path_is_dir:
        xml_files = list(args.xml_path.rglob("*.xml"))
        metadata = args.metadata or (args.xml_path / METADATA_FILE)
    else:
        xml_files = [args.xml_path]
        metadata = args.metadata

        if not metadata:
            print(
                "Error: Providing a metadata file is required when processing a single file"
            )
            sys.exit(1)

    if not metadata.exists():
        print(f"Error: Metadata file '{metadata}' not found.")
        sys.exit(1)

    speech_path = args.speech_types
    speech_path = check_path(speech_path)

    freq_dict_path = args.freq_dict
    freq_dict_path = check_path(freq_dict_path)

    phonetic_dict_path = args.phonetic_dict
    phonetic_dict_path = check_path(phonetic_dict_path)

    config_path = args.config_file
    config_path = check_path(config_path)

    configs = []
    if config_path:
        with open(config_path, "r") as config_file:
            json_dict = json.load(config_file)
            configs = [SaveConfig(**config) for config in json_dict["configs"]]


    output_dir = args.out_path.resolve()
    if not output_dir.exists():
        print(f"Error: The chosen output directory '{output_dir}' does not exist.")
        sys.exit(1)

    if configs:
        for config in configs:
            print("Extracting from", config)
            corpus = CorpusExtractor(
                metadata, speech_path, phonetic_dict_path, freq_dict_path, args.task_type, config
            )
            corpus.process_files(xml_files)
            if not config.person:
                corpus.save_results(output_dir)
            else:
                corpus.save_results(output_dir, config.person)
    
    else:
        corpus = CorpusExtractor(
            metadata, speech_path, phonetic_dict_path, freq_dict_path, args.task_type, config
        )
        corpus.process_files(xml_files)
        corpus.save_results(output_dir)
        


if __name__ == "__main__":
    main()
