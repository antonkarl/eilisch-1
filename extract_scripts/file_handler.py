from utils import (
    TEI_NS,
    is_in_timespan,
    DATE_FORMAT,
    GOVERNMENTS,
    Affiliation,
    SaveConfig,
)
from datetime import datetime
from speech import Speech
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from pathlib import Path
from typing import Optional


class FileHandler:
    """
    Initialize the FileHandler with a TEI file, metadata, task type, and optional save configuration.

    Args:
        teifile: Path to the TEI file to process.
        metadata: Metadata dictionary containing information about MPs, parties, etc.
        task_type: Type of task to perform (default is "sf_sub_clause").
        save_data: Optional configuration for saving data.
    """

    def __init__(
        self,
        teifile,
        metadata,
        task_type="sf_sub_clause",
        save_data: Optional[SaveConfig] = None,
    ):
        self.root = ET.parse(teifile).getroot()
        self.task_type = task_type
        self.metadata = metadata
        self.save_data = save_data
        self.file_date = self.root.findall(".//tei:bibl/tei:date", TEI_NS)[0].text
        self.file_year = self.file_date.split("-")[0]
        self.speeches = self.root.findall(".//tei:u", TEI_NS)
        self.results = []
        self.mp_affiliations = {}

        if not (self.save_data and self.save_data.years) or (
            int(self.file_year) in self.save_data.years
        ):
            self.process_file()

    def get_results(self):
        """
        Retrieve the results of processing the TEI file.

        Returns:
            A list of results extracted from the TEI file.
        """
        return self.results

    def process_file(self):
        """
        Process the TEI file to extract speeches and affiliations.

        This method identifies MPs and their affiliations, then processes each speech in the file.
        """
        if self.speeches:
            mps = set(
                [
                    speech.attrib["who"][1:]
                    for speech in self.speeches
                    if "who" in speech.attrib
                ]
            )
            self.mp_affiliations = {
                mp: self.find_current_affiliation(
                    self.metadata["mp_dict"][mp]["affiliations"],
                    self.file_date,
                    self.metadata["relations"],
                )
                for mp in mps
            }

            for speech in self.speeches:
                self.process_speech(speech)

    def process_speech(self, teispeech):
        """
        Process an individual speech element from the TEI file.

        Args:
            teispeech: An XML element representing a speech.
        """
        if "who" in teispeech.attrib:

            author = teispeech.attrib["who"][1:]

            if self.save_data and self.save_data.person != author:
                return

            speech = Speech(
                teispeech,
                self.file_date,
                self.file_year,
                self.metadata,
                self.mp_affiliations,
                self.task_type,
            )

            speech.check_speech()
            results = speech.get_results()

            if self.save_data and self.save_data.save_path:
                speech.save_speech_text(self.save_data.save_path)

            self.results.extend(results)

    def find_current_affiliation(
        self, affiliations: list[Element], date: str, relations
    ):
        """
        Finds the current affiliation (party and role) of a person based on the provided date.

        Args:
            affiliations: List of affiliation elements with time spans.
            date: Date to check in "YYYY-MM-DD" format.
            relations: List of relations to determine party status.

        Returns:
            Affiliation: An object containing the party, role, and party status.
        """
        date = datetime.strptime(date, DATE_FORMAT)

        party = role = gov = None

        for affiliation in affiliations:
            if is_in_timespan(affiliation, date):

                ref = affiliation.attrib["ref"][1:]

                # Checks if speaker is the president of Iceland
                if "President" in ref:
                    role = "president"

                elif ref.startswith("party"):
                    party = ref

                if "ana" in affiliation.attrib:
                    ana = affiliation.attrib["ana"].split(" ")
                    for info in ana:
                        if info[1:].startswith(("LV", "HS", "FV")):
                            gov = info[1:]

                if role != "minister" and ref in GOVERNMENTS:
                    role = affiliation.attrib["role"]

        party_status = self.check_party_status(party, date, role, relations)

        return Affiliation(party, role, party_status, gov)

    def check_party_status(self, party_id, date, role, relations):
        """
        Determines the party's status (majority or minority) based on the role and date.

        Args:
            party_id: The ID of the party.
            date: The date to check for party status.
            role: The role of the individual (e.g., "minister").
            relations: List of relations to determine majority or minority status.

        Returns:
            str: "majority" if the party is in the majority or the role is minister,
                "minority" if not, or None if no party ID is provided.
        """
        if role == "minister":
            return "majority"
        elif not party_id:
            return

        for relation in relations:
            if is_in_timespan(relation, date):
                majority_parties = relation.attrib["mutual"].split()

                if f"#{party_id}" in majority_parties:
                    return "majority"
                return "minority"
