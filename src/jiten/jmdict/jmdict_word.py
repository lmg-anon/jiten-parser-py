from dataclasses import dataclass, field
from typing import List, Optional

from .jmdict_reading_type import JmDictReadingType
from .jmdict_definition import JmDictDefinition
from .jmdict_lookup import JmDictLookup
from .word_origin import WordOrigin

@dataclass
class JmDictWord:
    word_id: int = 0
    readings: List[str] = field(default_factory=list)
    readings_furigana: List[str] = field(default_factory=list)
    reading_types: List[JmDictReadingType] = field(default_factory=list)
    obsolete_readings: Optional[List[str]] = field(default_factory=list)
    parts_of_speech: List[str] = field(default_factory=list)
    definitions: List[JmDictDefinition] = field(default_factory=list)
    lookups: List[JmDictLookup] = field(default_factory=list)
    pitch_accents: Optional[List[int]] = field(default_factory=list)
    priorities: Optional[List[str]] = field(default_factory=list)
    origin: WordOrigin = WordOrigin.UNKNOWN

    def get_priority_score(self, is_kana: bool) -> int:
        """
        Calculates a priority score for the word based on its frequency tags.
        """
        if not self.priorities:
            return 0

        score = 0

        # Special priority for common words that get the wrong reading by default
        # i.e. 秋, 陽, etc
        if "jiten" in self.priorities:
            score += 100

        if "ichi1" in self.priorities:
            score += 20

        if "ichi2" in self.priorities:
            score += 10

        if "news1" in self.priorities:
            score += 15

        if "news2" in self.priorities:
            score += 10

        if "gai1" in self.priorities or "gai2" in self.priorities:
            score += 5

        nf = next((p for p in self.priorities if p.startswith("nf")), None)
        if nf:
            nf_rank = int(nf[2:])
            score += max(0, 5 - int(round(nf_rank / 10.0)))

        if score == 0:
            if "spec1" in self.priorities:
                score += 15

            if "spec2" in self.priorities:
                score += 5

        if "uk" in self.parts_of_speech:
            if is_kana:
                score += 10
            else:
                score -= 10

        return score