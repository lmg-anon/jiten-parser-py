import re
from .part_of_speech import (
    PartOfSpeech, 
    PartOfSpeechSection, 
    to_part_of_speech, 
    to_part_of_speech_section
)

class WordInfo:
    def __init__(self, source=None):
        self.text: str = ""
        self.part_of_speech: PartOfSpeech = PartOfSpeech.UNKNOWN
        self.part_of_speech_section1: PartOfSpeechSection = PartOfSpeechSection.NONE
        self.part_of_speech_section2: PartOfSpeechSection = PartOfSpeechSection.NONE
        self.part_of_speech_section3: PartOfSpeechSection = PartOfSpeechSection.NONE
        self.normalized_form: str = ""
        self.dictionary_form: str = ""
        self.reading: str = ""
        self.is_invalid: bool = False

        if isinstance(source, str):
            self._init_from_sudachi_line(source)
        elif isinstance(source, WordInfo):
            self._init_from_other(source)

    def _init_from_other(self, other: 'WordInfo'):
        self.text = other.text
        self.part_of_speech = other.part_of_speech
        self.part_of_speech_section1 = other.part_of_speech_section1
        self.part_of_speech_section2 = other.part_of_speech_section2
        self.part_of_speech_section3 = other.part_of_speech_section3
        self.normalized_form = other.normalized_form
        self.dictionary_form = other.dictionary_form
        self.reading = other.reading
        self.is_invalid = other.is_invalid

    def _init_from_sudachi_line(self, sudachi_line: str):
        parts = re.split(r'\t', sudachi_line)
        if len(parts) < 6:
            self.is_invalid = True
            return

        pos_parts = parts[1].split(',')
        if len(pos_parts) < 4:
            self.is_invalid = True
            return

        self.text = parts[0]
        self.part_of_speech = to_part_of_speech(pos_parts[0])
        self.part_of_speech_section1 = to_part_of_speech_section(pos_parts[1])
        self.part_of_speech_section2 = to_part_of_speech_section(pos_parts[2])
        self.part_of_speech_section3 = to_part_of_speech_section(pos_parts[3])
        self.normalized_form = parts[2]
        self.dictionary_form = parts[3]
        self.reading = parts[5]

    def has_part_of_speech_section(self, section: PartOfSpeechSection) -> bool:
        return (self.part_of_speech_section1 == section or
                self.part_of_speech_section2 == section or
                self.part_of_speech_section3 == section)

    def __repr__(self):
        if self.is_invalid:
            return "WordInfo(is_invalid=True)"
        return (f"WordInfo(text='{self.text}', pos='{self.part_of_speech.name}', "
                f"dict_form='{self.dictionary_form}')")