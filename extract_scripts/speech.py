from utils import Token, TEI_NS, HS_PATTERN, TAGS, TASK_TYPES, VERBS, WINDOW, MATTR_WINDOWS
from lexicalrichness import LexicalRichness
import re
from statistics import median


class Speech:
    """
    Initialize the Speech object with TEI speech data, metadata, and task type.

    Args:
        teispeech: XML element representing the speech.
        speech_date: Date of the speech in "YYYY-MM-DD" format.
        speech_year: Year of the speech as a string.
        metadata: Metadata dictionary containing information about MPs, parties, etc.
        mp_affiliations: Dictionary mapping MP IDs to their affiliations.
        task_type: Type of task to perform (e.g., "sf_sub_clause").
    """
    def __init__(
        self, teispeech, speech_date, speech_year, metadata, mp_affiliations, task_type
    ):
        # Input parameters
        self.speech = teispeech
        self.speech_date = speech_date
        self.speech_year = speech_year
        self.metadata = metadata
        self.task_type = task_type

        # Metadata and speaker information
        self.author_id = teispeech.attrib["who"][1:]
        self.mp = metadata["mp_dict"][self.author_id]
        self.party_id, self.role, self.party_status, self.gov = mp_affiliations[
            self.author_id
        ]
        self.party = metadata["parties"].get(self.party_id)
        self.speaker_type = self.determine_speaker_type()

        # Speech content and analysis
        self.speech_id = teispeech.attrib["{http://www.w3.org/XML/1998/namespace}id"]
        self.speech_source = teispeech.attrib["source"]
        self.word_count = 0
        self.word_ranks = []
        self.speech_type = self.determine_speech_type()
        self.full_speech_text = self.join_speech()
        self.lex_score = [self.get_mattr_score(window) for window in MATTR_WINDOWS]
        self.rank_sum = sum(self.word_ranks)
        self.rank_mean = sum(self.word_ranks) / len(self.word_ranks) if self.word_ranks else 0
        self.rank_median = median(self.word_ranks) if self.word_ranks else 0

        # Results
        self.results = []

    def save_speech_text(self, path):
        """
        Save the full speech text to a file.

        Args:
            path: Directory path where the speech text will be saved.
        """
        filename = path / f"{self.author_id}_{self.speech_id}.txt"
        with open(filename, "w+") as f:
            f.write(self.full_speech_text)

    def determine_speaker_type(self):
        """
        Determines the type of speaker based on speech annotations.

        Returns:
            str: Speaker type (e.g., "chair", "guest", or "regular").
        """
        notes = self.speech.attrib.get("ana", "").split()
        if "#chair" in notes:
            return "chair"
        elif "#guest" in notes:
            return "guest"
        else:
            return "regular"

    def determine_speech_type(self):
        """
        Determines the type of speech based on the speech source.

        Returns:
            str: Speech type description.
        """
        speech_types = self.metadata["speech_types"]
        base_source = self.speech_source.split("?")[0]
        try:
            return speech_types[base_source]
        except KeyError:
            return self.resolve_speech_type_from_pattern(
                self.speech_source, speech_types
            )
        
    def get_mattr_score(self, window_size=WINDOW):
        """
        Calculates the MATTR score for the speech.

        Args:
            window_size: Size of the moving window for MATTR calculation.

        Returns:
            float: MATTR score.
        """
        lex = LexicalRichness(self.full_speech_text)
        try:
            lex_score =  lex.mattr(window_size=window_size)
        except ValueError:
            try:
                lex_score = lex.ttr
        
            except ZeroDivisionError:
                lex_score = 0.0
        
        return lex_score
    
    def get_token(self, aword):
        """
        Extracts a token from an XML word element.

        Args:
            aword: XML element representing a word.

        Returns:
            Token: A Token object containing word, lemma, and tag information.
        """
        element_tag = aword.tag.split("}")[-1]
        if element_tag in ["w", "pc"]:
            word = aword.text
            if element_tag == "w":
                lemma = aword.get("lemma")
            else:
                lemma = "NONE"
            tag = aword.get("pos")
            return Token(word, lemma, tag)

    def join_speech(self):
        """
        Joins all words in the speech into a single text string.

        Returns:
            str: Full speech text.
        """
        text = []
        for asentence in self.speech.findall(".//tei:s", TEI_NS):
            for aword in asentence.iter():
                token = self.get_token(aword)
                if token:
                    is_joined = not bool(aword.get("join"))
                    word = token.word + " " * is_joined
                    text.append(word)
                    if token.lemma != "NONE":
                        self.word_ranks.append(self.get_word_freq(token, rank=True))
                        self.word_count += 1

        return "".join(text)

    def check_speech(self):
        """
        Processes the speech to extract results based on the task type.
        """
        for asentence in self.speech.findall(".//tei:s", TEI_NS):
            sentence = []

            for aword in asentence.iter():
                token = self.get_token(aword)
                if not token:
                    continue
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
                    *self.lex_score,
                    self.rank_mean,
                    self.rank_median,
                    self.word_count,
                    full_text,
                    self.speech_source,
                    self.speech_id,
                ]

                self.results.append(data)

    def get_results(self):
        """
        Retrieve the results of processing the speech.

        Returns:
            list: List of extracted results.
        """
        return self.results

    def slices(self, chunks, slicelen=3):
        """
        Yields all sequences of a specified length from a list of elements.

        Args:
            chunks: List of elements to slice.
            slicelen: Length of each slice (default is 3).

        Yields:
            list: Slices of the specified length.
        """
        for idx in range(len(chunks) - slicelen + 1):
            slice = chunks[idx : idx + slicelen]
            yield slice

    def check_sentence(self, sentence) -> list[list]:
        """
        Checks if the given sentence based on the given task type.

        Args:
            sentence: List of Token objects representing the sentence.

        Returns:
            list[list]: Sentence results depending on task type.
        """
        rows = []

        if self.task_type == TASK_TYPES[0]:
            self.check_main_clause(sentence, rows)
        elif self.task_type == TASK_TYPES[1]:
            self.check_sub_clause(sentence, rows)
        else:
            self.check_hardspeech(sentence, rows)

        return rows

    def get_word_freq(self, token: Token, rank=False):
        """
        Retrieves the frequency or rank of a word based on its lemma and tag.

        Args:
            token: Token object containing word, lemma, and tag information.
            rank: Whether to return the rank instead of frequency (default is False).

        Returns:
            int: Frequency or rank of the word.
        """
        if token.tag.startswith("n"):
            tag = token.tag[:2]
        else:
            tag = token.tag[0]

        try:
            results = self.metadata["freq_dict"][token.lemma][tag]
        except KeyError:
            results = 0, 0
        
        if rank:
            return results[1]
        return results[0]
    
    def get_hardspeech_env(self, i: int, sentence: list[Token], max_len=10):
        """
        Retrieves the context (before and after) of a word in a sentence.

        Args:
            i: Index of the word in the sentence.
            sentence: List of Token objects representing the sentence.
            max_len: Maximum number of words to include in the context (default is 10).

        Returns:
            tuple: Context before and after the word as strings.
        """
        start = 0
        if i > max_len:
            start = i - max_len

        before = [token.word for token in sentence[start:i]]
        after = [token.word for token in sentence[(i+1):(i+max_len+1)]]

        return " ".join(before), " ".join(after)

    def check_hardspeech(self, sentence: list[Token], rows: list):
        """
        Checks for hard speech patterns in a sentence.

        Args:
            sentence: List of Token objects representing the sentence.
            rows: List to store the results of the check.
        """
        for i, token in enumerate(sentence):

            transcription = self.metadata["phone_dict"].get(token.word.lower(), "")
            match = re.match(HS_PATTERN, transcription)
            if match:
                frq = self.get_word_freq(token)
                before, after = self.get_hardspeech_env(i, sentence)
                rows.append([before, token.word, after, "", match.group(1), token.lemma, token.tag, frq])
            # if re.match(HS_PATTERN_2, token.word, flags=re.UNICODE | re.IGNORECASE):

    def check_sub_clause(self, sentence, rows):
        """
        Checks for SF patterns in a sentence's sub-clause.

        Args:
            sentence: List of Token objects representing the sentence.
            rows: List to store the results of the check.
        """
        for slice in self.slices(sentence):
            if slice[0].lemma == "sem" and slice[0].tag == "ct":

                # If no stylization is present
                if (
                    re.match("s.*[123].*", slice[1].tag)
                    and slice[1].lemma in VERBS.keys()
                    and slice[2].tag.startswith(TAGS)
                ):
                    slice_text = " ".join([token.word for token in slice])
                    frq = self.get_word_freq(slice[2])
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
                    frq = self.get_word_freq(slice[1])
                    rows.append(
                        [1, slice_text, VERBS[slice[2].lemma], slice[1].lemma, frq]
                    )

    def check_main_clause(self, sent, rows: list):
        """
        Checks for SF patterns in a sentence's main clause.

        Args:
            sent: List of Token objects representing the sentence.
            rows: List to store the results of the check.
        """
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
            frq = self.get_word_freq(sent[2])
            rows.append([0, text, VERBS[sent[1].lemma], sent[2].lemma, frq])

        elif sent[1].lemma in VERBS.keys() and sent[0].tag.startswith(TAGS):
            text = " ".join([token.word for token in sent[:2]])
            frq = self.get_word_freq(sent[1])
            rows.append([1, text, VERBS[sent[1].lemma], sent[0].lemma])

    def resolve_speech_type_from_pattern(self, speech_source, speech_types):
        """
        Attempts to resolve speech type using regex if not directly found.

        Args:
            speech_source: Source string of the speech.
            speech_types: Dictionary mapping sources to speech types.

        Returns:
            str: Resolved speech type or "none" if not found.
        """
        pattern = r"=(\d+)"
        results = re.findall(pattern, speech_source)
        if results:
            base_source = (
                f"http://www.althingi.is/altext/raeda/{results[0]}/{results[1]}.html"
            )
            return speech_types.get(base_source, "none")
        return "none"