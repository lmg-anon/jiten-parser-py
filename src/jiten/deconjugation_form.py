from typing import List, Set

class DeconjugationForm:
    def __init__(self, text: str, original_text: str, tags: List[str], seen_text: Set[str], process: List[str]):
        self.text: str = text
        self.original_text: str = original_text
        self.tags: List[str] = tags
        self.seen_text: Set[str] = seen_text
        self.process: List[str] = process
        self._hash_code = self._calculate_hash()

    def _calculate_hash(self) -> int:
        return hash((
            self.text,
            self.original_text,
            tuple(self.tags),
            frozenset(self.seen_text),
            tuple(self.process)
        ))

    def __eq__(self, other) -> bool:
        if not isinstance(other, DeconjugationForm):
            return False
        
        return (self.text == other.text and
                self.original_text == other.original_text and
                self.tags == other.tags and
                self.seen_text == other.seen_text and
                self.process == other.process)

    def __hash__(self) -> int:
        return self._hash_code

    def __repr__(self) -> str:
        return (f"DeconjugationForm(text='{self.text}', original_text='{self.original_text}', "
                f"tags={self.tags}, seen_text={self.seen_text}, process={self.process})")