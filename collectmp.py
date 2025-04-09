import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from pathlib import Path
from collections import namedtuple, defaultdict
from datetime import datetime
from tqdm import tqdm
import pandas as pd
import re
import json


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


class Speech:
    def __init__(
        self, teispeech, speech_date, speech_year, metadata, mp_affiliations, task_type
    ):
        self.speech = teispeech
        self.metadata = metadata
        self.task_type = task_type
        self.speech_date = speech_date
        self.speech_year = speech_year
        self.author_id = teispeech.attrib["who"][1:]
        self.mp = metadata["mp_dict"][self.author_id]
        self.party_id, self.role, self.party_status, self.gov = mp_affiliations[
            self.author_id
        ]
        self.party = metadata["parties"].get(self.party_id)
        self.speaker_type = self.determine_speaker_type()
        self.speech_id = teispeech.attrib["{http://www.w3.org/XML/1998/namespace}id"]
        self.speech_source = teispeech.attrib["source"]
        self.speech_type = self.determine_speech_type()
        self.full_speech_text = self.join_speech()
        self.results = []

        self.check_speech()

    def determine_speaker_type(self):
        """Determines the type of speaker based on speech annotations."""
        notes = self.speech.attrib.get("ana", "").split()
        if "#chair" in notes:
            return "chair"
        elif "#guest" in notes:
            return "guest"
        else:
            return "regular"

    def determine_speech_type(self):
        """Determines the type of speech based on the speech source."""
        speech_types = self.metadata["speech_types"]
        base_source = self.speech_source.split("?")[0]
        try:
            return speech_types[base_source]
        except KeyError:
            return self.resolve_speech_type_from_pattern(
                self.speech_source, speech_types
            )

    def join_speech(self):

        text = []
        for asentence in self.speech.findall(".//tei:s", TEI_NS):
            for aword in asentence.iter():
                element_tag = aword.tag.split("}")[-1]
                if element_tag in ["w", "pc"]:
                    is_joined = bool(aword.get("join"))
                    word = aword.text + " " * is_joined
                    text.append(word)

        return "".join(text)

    def check_speech(self):
        for asentence in self.speech.findall(".//tei:s", TEI_NS):
            sentence = []

            for aword in asentence.iter():
                element_tag = aword.tag.split("}")[-1]
                if element_tag in ["w", "pc"]:
                    word = aword.text
                    if element_tag == "w":
                        lemma = aword.get("lemma")
                    else:
                        lemma = "NONE"
                    tag = aword.get("pos")
                    token = Token(word, lemma, tag)
                    sentence.append(token)

            full_text = " ".join([token.word for token in sentence])
            results = self.check_sentence(sentence)

            for result in results:
                data = [
                    self.speech_year,
                    self.speech_date,
                    self.speech_type,
                    self.author_id,
                    self.mp["sex"],
                    self.mp["birth"].split("-")[0],
                    self.role,
                    self.speaker_type,
                    self.party_id,
                    self.party,
                    self.party_status,
                    self.gov,
                    *result,
                    full_text,
                    self.speech_source,
                    self.speech_id,
                ]

                self.results.append(data)

    def get_results(self):
        return self.results

    def slices(self, chunks, slicelen=3):
        """Yields all squences of n length (default is 3) from a list of elements"""
        for idx in range(len(chunks) - slicelen + 1):
            slice = chunks[idx : idx + slicelen]
            yield slice

    def check_sentence(self, sentence) -> list[list]:
        """
        Checks if the given sentence has the environment for stylization.

        Args:
            sentence (list[Token])

        Returns:
            list[list]: Sentence results, including presence of stylization, sequence text and included verbs.
        """

        rows = []

        if self.task_type == TASK_TYPES[0]:
            self.check_main_clause(sentence, rows)
        elif self.task_type == TASK_TYPES[1]:
            self.check_sub_clause(sentence, rows)
        else:
            self.check_hardspeech(sentence, rows)

        return rows

    def get_word_freq(self, token: Token, tag):
        try:
            frq = self.metadata["freq_dict"][token.lemma][tag]
        except KeyError:
            frq = 0

        return frq

    def check_hardspeech(self, sentence: list[Token], rows: list):

        for token in sentence:

            if token.tag[0] == "n":
                tag = token.tag[:2]
            else:
                tag = token.tag[0]

            transcription = self.metadata["phone_dict"].get(token.word.lower(), "")
            match = re.match(HS_PATTERN_3, transcription)
            if match:
                frq = self.get_word_freq(token, tag, self.metadata)
                rows.append([token.word, token.lemma, tag, frq])
            # if re.match(HS_PATTERN_2, token.word, flags=re.UNICODE | re.IGNORECASE):

    def check_sub_clause(self, sentence, rows):

        for slice in self.slices(sentence):
            if slice[0].lemma == "sem" and slice[0].tag == "ct":

                # If no stylization is present
                if (
                    re.match("s.*[123].*", slice[1].tag)
                    and slice[1].lemma in VERBS.keys()
                    and slice[2].tag.startswith(TAGS)
                ):
                    slice_text = " ".join([token.word for token in slice])
                    frq = self.get_word_freq(slice[2], slice[2].tag[0])
                    rows.append(
                        [0, slice_text, VERBS[slice[1].lemma], slice[2].lemma, frq]
                    )

                # If stylization is present
                elif (
                    re.match("s.*[123].*", slice[2].tag)
                    and slice[2].lemma in VERBS.keys()
                    and slice[1].tag.startswith(TAGS)
                ):
                    slice_text = " ".join([token.word for token in slice])
                    frq = self.get_word_freq(slice[1], slice[1].tag[0])
                    rows.append(
                        [1, slice_text, VERBS[slice[2].lemma], slice[1].lemma, frq]
                    )

    def check_main_clause(self, sent, rows: list):

        if len(sent) <= 3:
            return

        # TODO: Athuga hvort það þurfi að skoða orð sem koma á efti stýlfærslu svo hægt sé að sjá hvort setning sé með frumlag eða ekki.
        #       T.d. í setningum eins og "Benda vil ég háttv. ráðhera á ..." o.þ.h.
        elif (
            sent[0].tag == "fphen"
            and sent[1].lemma in VERBS.keys()
            and sent[2].tag.startswith(TAGS)
        ):
            text = " ".join([token.word for token in sent[:3]])
            frq = self.get_word_freq(sent[2], sent[2].tag[0])
            rows.append([0, text, VERBS[sent[1].lemma], sent[2].lemma, frq])

        elif sent[1].lemma in VERBS.keys() and sent[0].tag.startswith(TAGS):
            text = " ".join([token.word for token in sent[:2]])
            frq = self.get_word_freq(sent[1], sent[1].tag[0])
            rows.append([1, text, VERBS[sent[1].lemma], sent[0].lemma])

    def resolve_speech_type_from_pattern(self, speech_source, speech_types):
        """Attempts to resolve speech type using regex if not directly found."""
        pattern = r"=(\d+)"
        results = re.findall(pattern, speech_source)
        if results:
            base_source = (
                f"http://www.althingi.is/altext/raeda/{results[0]}/{results[1]}.html"
            )
            return speech_types.get(base_source, "none")
        return "none"


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


class CorpusExtractor:
    def __init__(
        self, metadata_file, speech_type_file, phonetic_dict_file, freq_list, task_type
    ):
        self.metadata = self.get_metadata(
            metadata_file, speech_type_file, phonetic_dict_file, freq_list
        )
        self.results = []
        self.task_type = task_type
        self.data = None

    def process_files(self, teifiles):
        for teifile in tqdm(teifiles, desc=f"Extracting {self.task_type} data"):
            handler = FileHandler(teifile, self.metadata, self.task_type)
            results = handler.get_results()
            self.results.extend(results)

        self.data = pd.DataFrame(self.results)

    def get_metadata(
        self, metadata_file, speech_type_file, phonetic_dict_file, freq_list
    ):
        return {
            "mp_dict": self.get_mp_data(metadata_file),
            "parties": self.get_parties(metadata_file),
            "relations": self.get_relations(metadata_file),
            "speech_types": self.get_speech_types(speech_type_file),
            "phone_dict": self.get_phone_dict(phonetic_dict_file),
            "freq_dict": self.get_frq_dict(freq_list),
        }

    def get_phone_dict(self, dict_file):
        data = pd.read_csv(dict_file, sep="\t", header=None)
        csv_dict = pd.Series(data.iloc[:, -1].values, index=data[0]).to_dict()

        return csv_dict

    def get_frq_dict(self, dict_file: Path):
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

    def get_mp_data(self, metadata_file):
        mp_dict = dict()

        # get mp person data
        root = ET.parse(metadata_file)
        mps = root.findall(".//tei:person", TEI_NS)
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

    # Retrieve all parties
    def get_parties(self, metadata_file):
        root = ET.parse(metadata_file)
        orgs = root.findall(".//tei:org", TEI_NS)
        parties = {}
        for org in orgs:

            if org.attrib["role"] == "politicalParty":
                name = org.find(".//tei:orgName", TEI_NS).text
                party_id = org.attrib[f"{XML_NS}id"]
                parties[party_id] = name

        return parties

    def get_relations(self, metadata_file):
        root = ET.parse(metadata_file)
        relations = root.findall(".//tei:relation", TEI_NS)
        return relations

    # Collect speech types from file
    def get_speech_types(self, speech_type_file):
        speech_types = pd.read_csv(
            speech_type_file, sep="\t", index_col=0, header=None, names=["type"]
        )
        speech_types.index = speech_types.index.str.replace("https", "http")
        speech_types = speech_types.to_dict()["type"]

        return speech_types


# def clean_hardspeech(rows: list):
#     new_rows = []
#     word_list = [row[11] for row in rows]
#     split_words = get_word_splits(word_list)
#     for i, word in enumerate(split_words):
#         if re.match(HS_PATTERN_2, word, flags=re.IGNORECASE | re.UNICODE):
#             new_rows.append(rows[i])

#     return new_rows


def main():
    basedir = Path(".")
    data_dir = basedir / "data"
    corpus_dir = data_dir / "IGC-Parla-22.10.ana"
    metadata_file = corpus_dir / "IGC-Parla-22.10.ana.xml"
    speech_type_file = data_dir / "speech_types.tsv"
    phonetic_dict_file = data_dir / "ice_pron_dict_north_clear.csv"
    frequency_list = data_dir / "frequency_lists" / "giga_simple_freq.json"

    # althingiFiles = list(Path(corpus_dir).rglob("*.xml"))
    year = "2019"
    althingiFiles = list(Path(corpus_dir / year).rglob("*.xml"))

    task_type = TASK_TYPES[1]

    corpus = CorpusExtractor(
        metadata_file,
        speech_type_file,
        phonetic_dict_file,
        frequency_list,
        task_type,
    )
    corpus.process_files(althingiFiles)
    data = corpus.data
    print(data.head())

    # metadata = get_metadata(
    #     metadata_file, speech_type_file, phonetic_dict_file, frequency_list
    # )

    # rows = []
    # for path in tqdm(althingiFiles, desc=f"Extracting {task_type} data"):
    #     results = examineFile(path, metadata, task_type=task_type)
    #     rows.extend(results)

    # save_path = data_dir / task_type
    # save_path.mkdir(parents=True, exist_ok=True)

    # data = pd.DataFrame(rows)
    # data.to_csv(
    #     save_path / f"{task_type}.tsv", sep="\t", index=False, header=headers[task_type]
    # )


if __name__ == "__main__":
    main()
