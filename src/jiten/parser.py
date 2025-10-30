import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

try:
    import wanakana
except ImportError:
    raise RuntimeError("'wanakana-paison' not found. Install it with 'pip install git+https://github.com/lmg-anon/WanaKanaPaison.git'.")

from .morphological_analyser import MorphologicalAnalyser
from .word_info import WordInfo
from .deconjugator import Deconjugator
from .deconjugation_form import DeconjugationForm
from .jmdict.jmdict import JmDict
from .jmdict.jmdict_word import JmDictWord
from .jmdict.word_origin import WordOrigin
from .part_of_speech import PartOfSpeech, PartOfSpeechSection, strings_to_parts_of_speech
from .string_helpers import is_ascii_or_full_width_letter, to_half_width_digits

@dataclass
class DeckWord:
    word_id: int
    original_text: str
    reading_index: int
    occurrences: int = 0
    conjugations: List[str] = field(default_factory=list)
    parts_of_speech: List[PartOfSpeech] = field(default_factory=list)
    origin: WordOrigin = WordOrigin.UNKNOWN

DeckWordCacheKey = Tuple[str, PartOfSpeech, str]
_deck_word_cache_store: Dict[DeckWordCacheKey, DeckWord] = {}

class _DeckWordCache:
    def get(self, key: DeckWordCacheKey) -> Optional[DeckWord]:
        return _deck_word_cache_store.get(key)

    def set(self, key: DeckWordCacheKey, word: DeckWord) -> None:
        _deck_word_cache_store[key] = word

class Parser:
    """
    A static class for parsing Japanese text to identify words and their
    dictionary forms.
    """
    _initialized: bool = False

    USE_CACHE: bool = True
    _deck_word_cache = _DeckWordCache()

    _jmdict = JmDict()
    _deconjugator = Deconjugator()
    _morphological_analyser = MorphologicalAnalyser()

    @staticmethod
    def _ensure_initialized():
        """Ensures that the dictionaries are loaded before parsing."""
        if not Parser._initialized:
            Parser._jmdict.load()
            Parser._initialized = True

    @staticmethod
    def _deconjugate_word(word_info: WordInfo) -> Tuple[bool, Optional[DeckWord]]:
        """
        Finds a dictionary entry for a word, assuming it's not a conjugated verb/adjective.
        """
        text = word_info.text

        if to_half_width_digits(text).isdigit() or (len(text) == 1 and is_ascii_or_full_width_letter(text)):
            return False, None

        candidates = Parser._jmdict.lookup(text)
        text_in_hiragana = wanakana.to_hiragana(text)
        if not wanakana.is_japanese(text) or text != text_in_hiragana:
            candidates.extend(Parser._jmdict.lookup(text_in_hiragana))

        seen_ids = set()
        unique_candidates = [cand for cand in candidates if cand.word_id not in seen_ids and not seen_ids.add(cand.word_id)]

        if not unique_candidates:
            return False, None

        matches = [w for w in unique_candidates if word_info.part_of_speech in strings_to_parts_of_speech(w.parts_of_speech)]

        best_match: Optional[JmDictWord] = None
        if not matches:
            best_match = unique_candidates[0]
        elif len(matches) > 1:
            best_match = max(matches, key=lambda m: m.get_priority_score(wanakana.is_kana(word_info.text)))
        else:
            best_match = matches[0]

        if not best_match:
            return True, None

        reading_index = -1
        if text in best_match.readings:
            reading_index = best_match.readings.index(text)
        if reading_index == -1:
            hiragana_readings = [wanakana.to_hiragana(r) for r in best_match.readings]
            if text_in_hiragana in hiragana_readings:
                reading_index = hiragana_readings.index(text_in_hiragana)

        if reading_index == -1:
            return False, None

        return True, DeckWord(
            word_id=best_match.word_id,
            original_text=word_info.text,
            reading_index=reading_index,
            parts_of_speech=strings_to_parts_of_speech(best_match.parts_of_speech),
            origin=best_match.origin
        )

    @staticmethod
    def _deconjugate_verb_or_adjective(word_info: WordInfo) -> Tuple[bool, Optional[DeckWord]]:
        """Deconjugates a word and finds the best dictionary entry for its base form."""
        deconjugated_forms = sorted(
            Parser._deconjugator.deconjugate(wanakana.to_hiragana(word_info.text)),
            key=lambda d: len(d.text), reverse=True
        )

        candidate_forms: List[Tuple[DeconjugationForm, List[JmDictWord]]] = []
        for form in deconjugated_forms:
            if results := Parser._jmdict.lookup(form.text):
                candidate_forms.append((form, results))

        if not candidate_forms:
            return True, None

        base_dict_word = wanakana.to_hiragana(word_info.dictionary_form.replace("ゎ", "わ").replace("ヮ", "わ"))
        base_word = wanakana.to_hiragana(word_info.text)
        candidate_forms.sort(key=lambda c: (0 if c[0].text == base_dict_word else 1 if c[0].text == base_word else 2))

        matches: List[Tuple[JmDictWord, DeconjugationForm]] = [
            (word, form) for form, words in candidate_forms for word in words
            if word_info.part_of_speech in strings_to_parts_of_speech(word.parts_of_speech)
        ]

        if not matches:
            return False, None

        best_match_tuple: Optional[Tuple[JmDictWord, DeconjugationForm]] = None
        if len(matches) > 1:
            sorted_matches = sorted(matches, key=lambda m: m[0].get_priority_score(wanakana.is_kana(word_info.text)), reverse=True)
            best_match_tuple = sorted_matches[0]
            if not wanakana.is_kana(word_info.normalized_form):
                for word, form in sorted_matches:
                    if word_info.normalized_form in word.readings:
                        best_match_tuple = (word, form)
                        break
        else:
            best_match_tuple = matches[0]

        if not best_match_tuple:
            return False, None

        best_word, best_form = best_match_tuple
        hiragana_readings = [wanakana.to_hiragana(r) for r in best_word.readings]
        reading_index = hiragana_readings.index(best_form.text) if best_form.text in hiragana_readings else -1

        if reading_index == -1:
            return False, None

        return True, DeckWord(
            word_id=best_word.word_id,
            original_text=word_info.text,
            reading_index=reading_index,
            conjugations=best_form.process,
            parts_of_speech=strings_to_parts_of_speech(best_word.parts_of_speech),
            origin=best_word.origin
        )

    @staticmethod
    def _process_word(word_info: WordInfo) -> Optional[DeckWord]:
        """Processes a single WordInfo object to find its dictionary form and details."""
        cache_key = (word_info.text, word_info.part_of_speech, word_info.dictionary_form)
        if Parser.USE_CACHE:
            if cached_word := Parser._deck_word_cache.get(cache_key):
                return DeckWord(**cached_word.__dict__)

        processed_word: Optional[DeckWord] = None
        current_word_info = WordInfo(source=word_info)
        
        for attempt in range(3):
            pos = current_word_info.part_of_speech
            pos_sec1 = current_word_info.part_of_speech_section1

            if pos in {PartOfSpeech.VERB, PartOfSpeech.I_ADJECTIVE, PartOfSpeech.AUXILIARY, PartOfSpeech.NA_ADJECTIVE} or \
                pos_sec1 == PartOfSpeechSection.ADJECTIVAL:
                success, word = Parser._deconjugate_verb_or_adjective(current_word_info)
                if not success or not word:
                    _, word = Parser._deconjugate_word(current_word_info)
                processed_word = word
            else:
                success, word = Parser._deconjugate_word(current_word_info)
                if not success or not word:
                    original_pos = current_word_info.part_of_speech
                    for new_pos in [PartOfSpeech.VERB, PartOfSpeech.I_ADJECTIVE, PartOfSpeech.NA_ADJECTIVE]:
                        current_word_info.part_of_speech = new_pos
                        _, word = Parser._deconjugate_verb_or_adjective(current_word_info)
                        if word:
                            break
                    current_word_info.part_of_speech = original_pos
                processed_word = word

            if processed_word:
                break

            text = current_word_info.text
            if len(text) > 2 and (text.endswith(('っ', 'ー')) or text[-1] == text[-2]):
                current_word_info.text = text[:-1]
            elif text.startswith("お"):
                current_word_info.text = text[1:]
            elif "ー" in text:
                current_word_info.text = text.replace("ー", "")
            else:
                break

        if processed_word and Parser.USE_CACHE:
            Parser._deck_word_cache.set(cache_key, processed_word)

        return processed_word

    @staticmethod
    def _parse_internal(text: str, morphemes_only: bool) -> List[Optional[DeckWord]]:
        """Internal parsing logic shared by public methods."""
        Parser._ensure_initialized()

        sentences = Parser._morphological_analyser.parse(text, morphemes_only=morphemes_only)
        word_infos = [w_tuple[0] for s in sentences for w_tuple in s.words]

        cleaned_infos: List[WordInfo] = []
        for wi in word_infos:
            wi.text = re.sub(r'[^a-zA-Z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\uFF21-\uFF3A\uFF41-\uFF5A\uFF10-\uFF19\u3005．]', '', wi.text)
            wi.text = wi.text.replace("ッー", "")
            if wi.text and not wi.text.isspace():
                cleaned_infos.append(wi)

        return [Parser._process_word(word) for word in cleaned_infos]

    @staticmethod
    def parse_text(text: str) -> List[DeckWord]:
        """
        Parses Japanese text, identifies words, finds their dictionary forms,
        and returns detailed information for each unique word.

        Args:
            text: The Japanese text to parse.

        Returns:
            A list of unique DeckWord objects found in the text.
        """
        results = Parser._parse_internal(text, morphemes_only=False)
        return [word for word in results if word is not None]

    @staticmethod
    def parse_morphemes(text: str) -> List[Optional[DeckWord]]:
        """
        Performs basic morphological analysis (tokenization) and processes
        each morpheme.

        Args:
            text: The Japanese text to parse.

        Returns:
            A list of DeckWord objects (or None if not found) corresponding
            to each morpheme in the input text.
        """
        return Parser._parse_internal(text, morphemes_only=True)