from tqdm import tqdm
import pandas as pd
import json
from file_handler import FileHandler
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET
from utils import TEI_NS, XML_NS, headers, SaveConfig
from typing import Optional


class CorpusExtractor:
    """
    Initialize the CorpusExtractor with metadata, speech type, phonetic dictionary, frequency list, and task type.

    Args:
        metadata_file: Path to the metadata XML file.
        speech_type_file: Path to the speech type file.
        phonetic_dict_file: Path to the phonetic dictionary file.
        freq_list: Path to the frequency list file.
        task_type: Type of task to perform (e.g., extraction type).
        save_data: Optional configuration for saving data.
    """
    def __init__(
        self, metadata_file, speech_type_file, phonetic_dict_file, freq_list, task_type, save_data: Optional[SaveConfig] = None
    ):
        self.metadata_root = ET.parse(metadata_file)
        self.metadata = self.get_metadata(
            speech_type_file, phonetic_dict_file, freq_list
        )
        self.results = []
        self.task_type = task_type
        self.data = None
        self.save_data = save_data

        if save_data and save_data.save_path:
            save_data.save_path.mkdir(parents=True, exist_ok=True)

    def process_files(self, teifiles: list[Path]):
        """
        Process a list of TEI files to extract data based on the task type.

        Args:
            teifiles: List of paths to TEI files to process.
        """
        for teifile in tqdm(teifiles, desc=f"Extracting {self.task_type} data"):
            if self.save_data and self.save_data.years:
                try:
                    if int(teifile.parent.stem) not in self.save_data.years:
                        continue
                except ValueError:
                    continue
            handler = FileHandler(teifile, self.metadata, self.task_type, save_data=self.save_data)
            results = handler.get_results()
            self.results.extend(results)

        self.data = pd.DataFrame(self.results)

    def save_results(self, save_path, file_name=None):
        """
        Save the extracted results to a specified path in TSV format.

        Args:
            save_path: Directory where the results will be saved.
            file_name: Optional name for the output file. Defaults to task type.
        """
        save_path.mkdir(parents=True, exist_ok=True)

        if file_name:
            save_path = save_path / f"{file_name}.tsv" 
        else:
            save_path = save_path / f"{self.task_type}.tsv"

        self.data.to_csv(
            save_path, sep="\t", index=False, header=headers[self.task_type]
        )

        print("Data saved to", save_path)

    def get_metadata(self, speech_type_file, phonetic_dict_file, freq_list):
        """
        Retrieve metadata including speech types, phonetic dictionary, and frequency list.

        Args:
            speech_type_file: Path to the speech type file.
            phonetic_dict_file: Path to the phonetic dictionary file.
            freq_list: Path to the frequency list file.

        Returns:
            A dictionary containing metadata information.
        """
        return {
            "mp_dict": self.get_mp_data(),
            "parties": self.get_parties(),
            "relations": self.get_relations(),
            "speech_types": self.get_speech_types(speech_type_file),
            "phone_dict": self.get_phone_dict(phonetic_dict_file),
            "freq_dict": self.get_frq_dict(freq_list),
        }

    def get_phone_dict(self, dict_file):
        """
        Load a phonetic dictionary from a file.

        Args:
            dict_file: Path to the phonetic dictionary file.

        Returns:
            A dictionary mapping words to their phonetic representations.
        """
        data = pd.read_csv(dict_file, sep="\t", header=None)
        csv_dict = pd.Series(data.iloc[:, -1].values, index=data[0]).to_dict()

        return csv_dict

    def get_frq_dict(self, dict_file: Path):
        """
        Load or generate a frequency dictionary from a file.

        Args:
            dict_file: Path to the frequency list file.

        Returns:
            A dictionary mapping words and parts of speech to their frequencies.
        """
        if dict_file.suffix == ".json":
            with open(dict_file, "r") as json_file:
                word_dict = json.load(json_file)
        else:
            word_dict = defaultdict(lambda: defaultdict(int))
            data = pd.read_csv(dict_file, sep="\t", header=None)
            total = len(data)
            for _, (word, pos, freq) in tqdm(
                data.iterrows(), desc="Populating freq dict.", total=total
            ):
                word_dict[word][pos] = freq

            file_name = dict_file.stem
            dir = dict_file.parent
            new_file = dir / f"{file_name}.json"
            print("Saving data to json...")
            with open(new_file, "w") as json_file:
                json.dump(word_dict, json_file, indent=4)

        return word_dict

    def get_mp_data(self):
        """
        Extract metadata about members of parliament (MPs) from the XML metadata file.

        Returns:
            A dictionary containing MP data including sex, birth year, affiliations, and active years.
        """
        mp_dict = dict()

        # get mp person data
        mps = self.metadata_root.findall(".//tei:person", TEI_NS)
        for mp in mps:

            mp_id = mp.attrib[f"{XML_NS}id"]
            sex = mp.find(".//tei:sex", TEI_NS).attrib["value"]
            birth = mp.find(".//tei:birth", TEI_NS).attrib["when"]

            mp_fields = dict()
            mp_fields["sex"] = sex
            mp_fields["birth"] = birth
            affiliations = mp.findall(".//tei:affiliation", TEI_NS)
            year_from = 3000
            year_to = 0

            for element in affiliations:

                if "from" in element.attrib:
                    year_from = min(
                        year_from, int(element.attrib["from"].split("-")[0])
                    )
                if "to" in element.attrib:
                    year_to = max(year_to, int(element.attrib["to"].split("-")[0]))

                mp_fields["year_from"] = year_from
                mp_fields["year_to"] = year_to

            mp_fields["affiliations"] = affiliations
            mp_dict[mp_id] = mp_fields

        return mp_dict

    def get_parties(self):
        """
        Retrieve all political parties from the XML metadata file.

        Returns:
            A dictionary mapping party IDs to their names.
        """
        orgs = self.metadata_root.findall(".//tei:org", TEI_NS)
        parties = {}
        for org in orgs:

            if org.attrib["role"] == "politicalParty":
                name = org.find(".//tei:orgName", TEI_NS).text
                party_id = org.attrib[f"{XML_NS}id"]
                parties[party_id] = name

        return parties

    def get_relations(self):
        """
        Retrieve all relations from the XML metadata file.

        Returns:
            A list of relations extracted from the metadata.
        """
        relations = self.metadata_root.findall(".//tei:relation", TEI_NS)
        return relations

    def get_speech_types(self, speech_type_file):
        """
        Collect speech types from a file.

        Args:
            speech_type_file: Path to the speech type file.

        Returns:
            A dictionary mapping speech type URLs to their descriptions.
        """
        speech_types = pd.read_csv(
            speech_type_file, sep="\t", index_col=0, header=None, names=["type"]
        )
        speech_types.index = speech_types.index.str.replace("https", "http")
        speech_types = speech_types.to_dict()["type"]

        return speech_types
