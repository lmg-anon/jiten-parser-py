from enum import IntEnum
from typing import List

class PartOfSpeech(IntEnum):
    UNKNOWN = 0
    NOUN = 1
    VERB = 2
    I_ADJECTIVE = 3
    ADVERB = 4
    PARTICLE = 5
    CONJUNCTION = 6
    AUXILIARY = 7
    ADNOMINAL = 8
    INTERJECTION = 9
    SYMBOL = 10
    PREFIX = 11
    FILLER = 12
    NAME = 13
    PRONOUN = 14
    NA_ADJECTIVE = 15
    SUFFIX = 16
    COMMON_NOUN = 17
    SUPPLEMENTARY_SYMBOL = 18
    BLANK_SPACE = 19
    EXPRESSION = 20
    NOMINAL_ADJECTIVE = 21
    NUMERAL = 22
    PRENOUN_ADJECTIVAL = 23
    COUNTER = 24
    ADVERB_TO = 25
    NOUN_SUFFIX = 26

class PartOfSpeechSection(IntEnum):
    NONE = 0
    AMOUNT = 1
    ALPHABET = 2
    FULL_STOP = 3
    BLANK_SPACE = 4
    SUFFIX = 5
    PRONOUN = 6
    INDEPENDANT = 7
    DEPENDANT = 8
    FILLER = 9
    COMMON = 10
    SENTENCE_ENDING_PARTICLE = 11
    COUNTER = 12
    PARALLEL_MARKER = 13
    BINDING_PARTICLE = 14
    POTENTIAL_ADVERB = 15
    CASE_MARKING_PARTICLE = 16
    IRREGULAR_CONJUNCTION = 17
    CONJUNCTION_PARTICLE = 18
    AUXILIARY_VERB_STEM = 19
    ADJECTIVAL_STEM = 20
    COMPOUND_WORD = 21
    QUOTATION = 22
    NOUN_CONJUNCTION = 23
    ADVERBIAL_PARTICLE = 24
    CONJUNCTIVE_PARTICLE_CLASS = 25
    ADVERBIALIZATION = 26
    ADVERBIAL_PARTICLE_OR_PARALLEL_MARKER_OR_SENTENCE_ENDING_PARTICLE = 27
    ADNOMINAL_ADJECTIVE = 28
    PROPER_NOUN = 29
    SPECIAL = 30
    VERB_CONJUNCTION = 31
    PERSON_NAME = 32
    FAMILY_NAME = 33
    ORGANIZATION = 34
    NOT_ADJECTIVE_STEM = 35
    COMMA = 36
    OPENING_BRACKET = 37
    CLOSING_BRACKET = 38
    REGION = 39
    COUNTRY = 40
    NUMERAL = 41
    POSSIBLE_DEPENDANT = 42
    COMMON_NOUN = 43
    SUBSTANTIVE_ADJECTIVE = 44
    POSSIBLE_COUNTER_WORD = 45
    POSSIBLE_SURU = 46
    JUNTAIJOUSHI = 47
    POSSIBLE_NA_ADJECTIVE = 48
    VERB_LIKE = 49
    POSSIBLE_VERB_SURU_NOUN = 50
    ADJECTIVAL = 51
    NA_ADJECTIVE_LIKE = 52
    NAME = 53
    LETTER = 54
    PLACE_NAME = 55
    TARU_ADJECTIVE = 56

def to_part_of_speech(pos_str: str) -> PartOfSpeech:
    match pos_str:
        case "名詞" | "n":
            return PartOfSpeech.NOUN
        case "動詞":
            return PartOfSpeech.VERB
        case _ if pos_str.startswith('v'):
            return PartOfSpeech.VERB
        case "形容詞" | "adj-i" | "adj-ix":
            return PartOfSpeech.I_ADJECTIVE
        case "形状詞" | "adj-na":
            return PartOfSpeech.NA_ADJECTIVE
        case "副詞" | "adv":
            return PartOfSpeech.ADVERB
        case "助詞" | "prt":
            return PartOfSpeech.PARTICLE
        case "接続詞" | "conj":
            return PartOfSpeech.CONJUNCTION
        case "助動詞" | "aux" | "aux-v":
            return PartOfSpeech.AUXILIARY
        case "感動詞" | "int":
            return PartOfSpeech.INTERJECTION
        case "記号":
            return PartOfSpeech.SYMBOL
        case "接頭詞" | "接頭辞" | "pref":
            return PartOfSpeech.PREFIX
        case "フィラー":
            return PartOfSpeech.FILLER
        case ("名" | "company" | "given" | "place" | "person" | "product" | "ship" | 
              "surname" | "unclass" | "name-fem" | "name-masc" | "station" | "group" | 
              "char" | "creat" | "dei" | "doc" | "ev" | "fem" | "fict" | "leg" | 
              "masc" | "myth" | "obj" | "organization" | "oth" | "relig" | "serv" | 
              "work" | "unc"):
            return PartOfSpeech.NAME
        case "代名詞" | "pn":
            return PartOfSpeech.PRONOUN
        case "接尾辞" | "suf":
            return PartOfSpeech.SUFFIX
        case "普通名詞":
            return PartOfSpeech.COMMON_NOUN
        case "補助記号":
            return PartOfSpeech.SUPPLEMENTARY_SYMBOL
        case "空白":
            return PartOfSpeech.BLANK_SPACE
        case "表現" | "exp":
            return PartOfSpeech.EXPRESSION
        case "形動" | "adj-no" | "adj-t" | "adj-f":
            return PartOfSpeech.NOMINAL_ADJECTIVE
        case "連体詞" | "adj-pn":
            return PartOfSpeech.PRENOUN_ADJECTIVAL
        case "数詞" | "num":
            return PartOfSpeech.NUMERAL
        case "助数詞" | "ctr":
            return PartOfSpeech.COUNTER
        case "副詞的と" | "adv-to":
            return PartOfSpeech.ADVERB_TO
        case "名詞接尾辞" | "n-suf":
            return PartOfSpeech.NOUN_SUFFIX
        case _:
            return PartOfSpeech.UNKNOWN

def to_part_of_speech_section(pos_str: str) -> PartOfSpeechSection:
    match pos_str:
        case "*":
            return PartOfSpeechSection.NONE
        case "数":
            return PartOfSpeechSection.AMOUNT
        case "アルファベット":
            return PartOfSpeechSection.ALPHABET
        case "句点":
            return PartOfSpeechSection.FULL_STOP
        case "空白":
            return PartOfSpeechSection.BLANK_SPACE
        case "接尾" | "suf":
            return PartOfSpeechSection.SUFFIX
        case "代名詞" | "pn":
            return PartOfSpeechSection.PRONOUN
        case "自立":
            return PartOfSpeechSection.INDEPENDANT
        case "フィラー":
            return PartOfSpeechSection.FILLER
        case "一般":
            return PartOfSpeechSection.COMMON
        case "非自立":
            return PartOfSpeechSection.DEPENDANT
        case "終助詞":
            return PartOfSpeechSection.SENTENCE_ENDING_PARTICLE
        case "助数詞" | "ctr":
            return PartOfSpeechSection.COUNTER
        case "並立助詞":
            return PartOfSpeechSection.PARALLEL_MARKER
        case "係助詞":
            return PartOfSpeechSection.BINDING_PARTICLE
        case "副詞可能":
            return PartOfSpeechSection.POTENTIAL_ADVERB
        case "格助詞":
            return PartOfSpeechSection.CASE_MARKING_PARTICLE
        case "サ変接続":
            return PartOfSpeechSection.IRREGULAR_CONJUNCTION
        case "接続助詞":
            return PartOfSpeechSection.CONJUNCTION_PARTICLE
        case "助動詞語幹":
            return PartOfSpeechSection.AUXILIARY_VERB_STEM
        case "形容動詞語幹":
            return PartOfSpeechSection.ADJECTIVAL_STEM
        case "連語":
            return PartOfSpeechSection.COMPOUND_WORD
        case "引用":
            return PartOfSpeechSection.QUOTATION
        case "名詞接続":
            return PartOfSpeechSection.NOUN_CONJUNCTION
        case "副助詞":
            return PartOfSpeechSection.ADVERBIAL_PARTICLE
        case "助詞類接続":
            return PartOfSpeechSection.CONJUNCTIVE_PARTICLE_CLASS
        case "副詞化":
            return PartOfSpeechSection.ADVERBIALIZATION
        case "副助詞／並立助詞／終助詞":
            return PartOfSpeechSection.ADVERBIAL_PARTICLE_OR_PARALLEL_MARKER_OR_SENTENCE_ENDING_PARTICLE
        case "連体化":
            return PartOfSpeechSection.ADNOMINAL_ADJECTIVE
        case "固有名詞":
            return PartOfSpeechSection.PROPER_NOUN
        case "特殊":
            return PartOfSpeechSection.SPECIAL
        case "動詞接続":
            return PartOfSpeechSection.VERB_CONJUNCTION
        case "人名":
            return PartOfSpeechSection.PERSON_NAME
        case "姓":
            return PartOfSpeechSection.FAMILY_NAME
        case "組織":
            return PartOfSpeechSection.ORGANIZATION
        case "ナイ形容詞語幹":
            return PartOfSpeechSection.NOT_ADJECTIVE_STEM
        case "読点":
            return PartOfSpeechSection.COMMA
        case "括弧開":
            return PartOfSpeechSection.OPENING_BRACKET
        case "括弧閉":
            return PartOfSpeechSection.CLOSING_BRACKET
        case "地域":
            return PartOfSpeechSection.REGION
        case "国":
            return PartOfSpeechSection.COUNTRY
        case "数詞" | "num":
            return PartOfSpeechSection.NUMERAL
        case "非自立可能":
            return PartOfSpeechSection.POSSIBLE_DEPENDANT
        case "普通名詞":
            return PartOfSpeechSection.COMMON_NOUN
        case "名詞的":
            return PartOfSpeechSection.SUBSTANTIVE_ADJECTIVE
        case "助数詞可能":
            return PartOfSpeechSection.POSSIBLE_COUNTER_WORD
        case "サ変可能":
            return PartOfSpeechSection.POSSIBLE_SURU
        case "準体助詞":
            return PartOfSpeechSection.JUNTAIJOUSHI
        case "形状詞可能":
            return PartOfSpeechSection.POSSIBLE_NA_ADJECTIVE
        case "動詞的":
            return PartOfSpeechSection.VERB_LIKE
        case "サ変形状詞可能":
            return PartOfSpeechSection.POSSIBLE_VERB_SURU_NOUN
        case "形容詞的":
            return PartOfSpeechSection.ADJECTIVAL
        case ("名" | "company" | "given" | "place" | "person" | "product" | "ship" | 
              "surname" | "unclass" | "name-fem" | "name-masc" | "station" | "group" | 
              "char" | "creat" | "dei" | "doc" | "ev" | "fem" | "fict" | "leg" | 
              "masc" | "myth" | "obj" | "organization" | "oth" | "relig" | "serv" | 
              "work" | "unc"):
            return PartOfSpeechSection.NAME
        case "文字":
            return PartOfSpeechSection.LETTER
        case "形状詞的":
            return PartOfSpeechSection.NA_ADJECTIVE_LIKE
        case "地名":
            return PartOfSpeechSection.PLACE_NAME
        case "タリ":
            return PartOfSpeechSection.TARU_ADJECTIVE
        case _:
            return PartOfSpeechSection.NONE

def strings_to_parts_of_speech(pos_list: List[str]) -> List[PartOfSpeech]:
    return [to_part_of_speech(p) for p in pos_list]

def strings_to_part_of_speech_sections(pos_list: List[str]) -> List[PartOfSpeechSection]:
    return [to_part_of_speech_section(p) for p in pos_list]