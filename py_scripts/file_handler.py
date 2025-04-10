from utils import TEI_NS, is_in_timespan, DATE_FORMAT, GOVERNMENTS, Affiliation
from datetime import datetime
from speech import Speech
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

class FileHandler:
    def __init__(self, teifile, metadata, task_type="sf_sub_clause"):
        self.root = ET.parse(teifile).getroot()
        self.task_type = task_type
        self.metadata = metadata
        self.file_date = self.root.findall(".//tei:bibl/tei:date", TEI_NS)[0].text
        self.file_year = self.file_date.split("-")[0]
        self.speeches = self.root.findall(".//tei:u", TEI_NS)
        self.results = []
        self.mp_affiliations = {}

        self.process_file()

    def get_results(self):
        return self.results

    def process_file(self):
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
        if "who" in teispeech.attrib:

            speech = Speech(
                teispeech,
                self.file_date,
                self.file_year,
                self.metadata,
                self.mp_affiliations,
                self.task_type,
            )

            results = speech.get_results()
            self.results.extend(results)

    def find_current_affiliation(
        self, affiliations: list[Element], date: str, relations
    ):
        """
        Finds the current affiliation (party and role) of a person based on the provided date.

        Args:
            affiliations (list[Element]): List of affiliation elements with time spans.
            date (str): Date to check in "YYYY-MM-DD" format.

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
            party_id (str): The ID of the party.
            date (datetime): The date to check for party status.
            role (str): The role of the individual (e.g., "minister").

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
