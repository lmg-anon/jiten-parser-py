from dataclasses import dataclass, field
from typing import List, Tuple

from .word_info import WordInfo

@dataclass
class SentenceInfo:
    text: str
    words: List[Tuple[WordInfo, int, int]] = field(default_factory=list)