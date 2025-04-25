from utils import Token, TEI_NS, HS_PATTERN_3, TAGS, TASK_TYPES, VERBS
from lexicalrichness import LexicalRichness
import re

MATTR_WINDOW = 500

class Speech:
    def __init__(
        self, teispeech, speech_date, speech_year, metadata, mp_affiliations, task_type
    ):
        self.speech = teispeech
        self.metadata = metadata
        self.task_type = task_type
        self.speech_date = speech_date
        self.speech_year = speech_year
        self.word_count = 0
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
        self.lex_score = self.get_mattr_score()

        self.results = []

        # self.check_speech()

    def save_speech_text(self, path):

        filename = path / f"{self.author_id}_{self.speech_id}.txt"
        with open(filename, "w+") as f:
            f.write(self.full_speech_text)


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
        
    def get_mattr_score(self):
        """Calculates the MATTR score for the speech."""
        lex = LexicalRichness(self.full_speech_text)
        try:
            lex_score =  lex.mattr(window_size=MATTR_WINDOW)
        except ValueError:
            try:
                lex_score = lex.ttr
        
            except ZeroDivisionError:
                lex_score = 0.0
        
        return lex_score

    def join_speech(self):

        text = []
        for asentence in self.speech.findall(".//tei:s", TEI_NS):
            for aword in asentence.iter():
                element_tag = aword.tag.split("}")[-1]
                if element_tag in ["w", "pc"]:
                    if element_tag == "w":
                        self.word_count += 1
                    is_joined = not bool(aword.get("join"))
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
                    self.lex_score,
                    self.word_count,
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