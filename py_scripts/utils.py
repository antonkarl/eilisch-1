from collections import namedtuple
from xml.etree.ElementTree import Element
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

Token = namedtuple("Token", ["word", "lemma", "tag"])
Affiliation = namedtuple("Affiliation", ["party", "role", "coalition", "gov"])

VERBS = {"vera": "be", "hafa": "have", "munu": "mod", "skulu": "mod"}
TAGS = ("sþ", "ss", "sn")
TASK_TYPES = ["sf_main_clause", "sf_sub_clause", "hardspeech"]
HS_PATTERN_1 = r"\b\w*[aeiouyáéíóúý]{1,2}[ptk](?![ptk])\w*\b"
HS_PATTERN_2 = r"\b[^aeiouyáéíóúý\s]*[aeiouyáéíóúý]{1,2}[ptk](?![ptk])\w*\b"
HS_PATTERN_3 = r".*: [ptkc]_h.*"

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
    "lex_score",
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
    "word",
    "lemma",
    "pos",
    "word_freq",
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
    person: str = ''

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

# def clean_hardspeech(rows: list):
#     new_rows = []
#     word_list = [row[11] for row in rows]
#     split_words = get_word_splits(word_list)
#     for i, word in enumerate(split_words):
#         if re.match(HS_PATTERN_2, word, flags=re.IGNORECASE | re.UNICODE):
#             new_rows.append(rows[i])

#     return new_rows