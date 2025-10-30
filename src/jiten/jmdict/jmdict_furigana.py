from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Furigana:
    ruby: str = ""
    rt: str = ""

@dataclass
class JmDictFurigana:
    text: str = ""
    reading: str = ""
    furiganas: List[Furigana] = field(default_factory=list)

    def parse(self) -> str:
        """Formats the furigana as a string like: kanji[reading]."""
        return "".join(f"{f.ruby}[{f.rt}]" if f.rt else f.ruby for f in self.furiganas)

    @classmethod
    def from_dict(cls, data: Dict) -> 'JMDictFurigana':
        return cls(
            text=data.get("text", ""),
            reading=data.get("reading", ""),
            furiganas=[Furigana(**f) for f in data.get("furigana", [])]
        )