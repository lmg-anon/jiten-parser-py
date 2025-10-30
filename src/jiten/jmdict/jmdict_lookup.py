from dataclasses import dataclass

@dataclass(frozen=True)
class JmDictLookup:
    word_id: int
    lookup_key: str = ""