from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class DeconjugationVirtualRule:
    dec_end: str
    con_end: str
    dec_tag: Optional[str]
    con_tag: Optional[str]
    detail: str