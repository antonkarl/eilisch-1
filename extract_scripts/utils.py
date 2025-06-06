from collections import namedtuple
from xml.etree.ElementTree import Element
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

Token = namedtuple("Token", ["word", "lemma", "tag"])
Affiliation = namedtuple("Affiliation", ["party", "role", "coalition", "gov"])

EXTRACTION_DATA_PATH = Path("./extraction_data")

METADATA_FILE = "IGC-Parla-22.10.ana.xml"
SPEECH_TYPES_FILE = EXTRACTION_DATA_PATH / "speech_types.tsv"
PHONE_DICT = EXTRACTION_DATA_PATH / "ice_pron_dict_north_clear.tsv"
FREQ_DICT = EXTRACTION_DATA_PATH / "giga_simple_freq_2.json"

VERBS = {"vera": "be", "hafa": "have", "munu": "mod", "skulu": "mod"}
TAGS = ("sþ", "ss", "sn")
TASK_TYPES = ["sf_main_clause", "sf_sub_clause", "hardspeech"]
HS_PATTERN = r".*[^cfhkpstvglmnr0CDNGT] ([ptkc])_h.*"
HS_VOICED_PATTERN = r".*[lmnr]_0 ([ptkc])[^_].*"
WINDOW = 200
MATTR_WINDOWS = [100, 300, 500]

# XML namespace
TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XML_NS = "{http://www.w3.org/XML/1998/namespace}"
DATE_FORMAT = "%Y-%m-%d"


GOVERNMENTS = ("HS", "FV", "LV", "GOV_HS", "GOV_FV", "GOV_LV")
SF_HEADERS = [
    "year",
    "date",
    "speech_type",
    "person",
    "sex",
    "year_born",
    "role",
    "speaker_type",
    "party_id",
    "party_name",
    "party_status",
    "gov",
    "is_stylized",
    "relevant_text",
    "finite_verb",
    "non-finite_verb",
    "nfv_freq",
    *[f"mattr_{score}" for score in MATTR_WINDOWS],
    "word_rank_mean",
    "word_rank_median",
    "speech_word_count",
    "full_text",
    "speech_source",
    "speech_id",
]

HS_HEADERS = [
    "year",
    "date",
    "speech_type",
    "person",
    "sex",
    "year_born",
    "role",
    "speaker_type",
    "party_id",
    "party_name",
    "party_status",
    "gov",
    "before",
    "word",
    "after",
    "is_hardspeech",
    "plosive",
    "lemma",
    "pos",
    "word_freq",
    *[f"mattr_{score}" for score in MATTR_WINDOWS],
    "word_rank_mean",
    "word_rank_median",
    "speech_word_count",
    "full_text",
    "speech_source",
    "speech_id",
]

headers = {
    "hardspeech": HS_HEADERS,
    "sf_main_clause": SF_HEADERS,
    "sf_sub_clause": SF_HEADERS,
}


@dataclass
class SaveConfig:
    save_path: Optional[Path] = None
    years: list[Optional[int]] = field(default_factory=list)
    timespans: list[Optional[int]] = field(default_factory=list)
    person: str = ''
    max_year: int = 2024

    def __post_init__(self):
        if self.timespans:
            for start, end in self.timespans:
                self.years.extend(list(range(start, end + 1)))
        
        if self.save_path:
            if isinstance(self.save_path, str):
                self.save_path = Path(self.save_path)
            
            if self.person:
                self.save_path = self.save_path / self.person
    
    def __str__(self):
        text = ""
        if self.person:
            text = self.person
        else:
            text = f"{min(self.years)}-{max(self.years)}"
        return f"Config<{text}>"


def is_in_timespan(element: Element, date: datetime):
    """
    Checks if a given date is within the "from" and "to" attributes of an XML element.

    Args:
        element (Element): XML element with optional "from" and "to" attributes.
        date (datetime): Date to check.

    Returns:
        bool: True if the date is within the time span, False otherwise.
    """

    date_from = datetime.min
    date_to = datetime.max

    if "from" in element.attrib:
        date_from = datetime.strptime(element.attrib["from"], DATE_FORMAT)
    if "to" in element.attrib:
        date_to = datetime.strptime(element.attrib["to"], DATE_FORMAT)

    if date_from <= date <= date_to:
        return True
    return False
