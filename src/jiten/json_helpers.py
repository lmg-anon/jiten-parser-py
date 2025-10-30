from typing import Any, List, Union

def ensure_string_list(value: Union[str, List[str]]) -> List[str]:
    """
    If the input is a string, it wraps it in a list.
    If it's a list of strings, it returns it as is.
    """
    if isinstance(value, str):
        # Single string, wrap it into a string array
        return [value]
    if isinstance(value, list):
        # Array of strings, deserialize normally
        return value
    raise TypeError(f"Expected str or list[str], but got {type(value).__name__}")