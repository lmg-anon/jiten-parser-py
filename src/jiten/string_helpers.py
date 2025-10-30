HALF_WIDTH_TO_FULL_WIDTH = {
    '0': '０', '1': '１', '2': '２', '3': '３', '4': '４',
    '5': '５', '6': '６', '7': '７', '8': '８', '9': '９'
}

FULL_WIDTH_TO_HALF_WIDTH = {
    '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
    '５': '5', '６': '6', '７': '7', '８': '8', '９': '9'
}

def to_full_width_digits(input_str: str) -> str:
    """
    Converts half-width ASCII digits ('0'-'9') in a string to their
    full-width counterparts ('０'-'９').
    """
    return "".join(HALF_WIDTH_TO_FULL_WIDTH.get(char, char) for char in input_str)

def to_half_width_digits(input_str: str) -> str:
    """
    Converts full-width digits ('０'-'９') in a string to their
    half-width ASCII counterparts ('0'-'9').
    """
    return "".join(FULL_WIDTH_TO_HALF_WIDTH.get(char, char) for char in input_str)

def is_ascii_or_full_width_letter(input_str: str) -> bool:
    """
    Checks if the first character of a string is an ASCII or full-width letter.
    Returns False if the string is empty.
    """
    if not input_str:
        return False
    
    c = input_str[0]
    return ('a' <= c <= 'z' or
            'A' <= c <= 'Z' or
            'ａ' <= c <= 'ｚ' or
            'Ａ' <= c <= 'Ｚ')