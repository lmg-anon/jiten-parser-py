from dataclasses import dataclass, field
from typing import List

@dataclass
class JmDictDefinition:
    definition_id: int
    word_id: int
    parts_of_speech: List[str] = field(default_factory=list)
    english_meanings: List[str] = field(default_factory=list)
    dutch_meanings: List[str] = field(default_factory=list)
    french_meanings: List[str] = field(default_factory=list)
    german_meanings: List[str] = field(default_factory=list)
    spanish_meanings: List[str] = field(default_factory=list)
    hungarian_meanings: List[str] = field(default_factory=list)
    russian_meanings: List[str] = field(default_factory=list)
    slovenian_meanings: List[str] = field(default_factory=list)