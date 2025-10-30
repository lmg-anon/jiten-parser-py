from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from .json_helpers import ensure_string_list

@dataclass
class DeconjugationRule:
    type: str
    detail: str
    dec_end: List[str]
    con_end: List[str]
    context_rule: Optional[str] = None
    dec_tag: Optional[List[str]] = None
    con_tag: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeconjugationRule':
        dec_tag_val = data.get("dec_tag")
        con_tag_val = data.get("con_tag")

        return cls(
            type=data.get("type", ""),
            detail=data.get("detail", ""),
            context_rule=data.get("contextrule"),
            dec_end=ensure_string_list(data.get("dec_end", [])),
            con_end=ensure_string_list(data.get("con_end", [])),
            dec_tag=ensure_string_list(dec_tag_val) if dec_tag_val is not None else None,
            con_tag=ensure_string_list(con_tag_val) if con_tag_val is not None else None
        )