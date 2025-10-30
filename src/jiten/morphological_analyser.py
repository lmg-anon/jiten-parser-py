import os
import re
from typing import List, Set, Tuple, Optional

try:
    import wanakana
except ImportError:
    raise RuntimeError("'wanakana-paison' not found. Install it with 'pip install git+https://github.com/lmg-anon/WanaKanaPaison.git'.")

from .word_info import WordInfo
from .sentence_info import SentenceInfo
from .part_of_speech import PartOfSpeech, PartOfSpeechSection
from . import sudachi_interop
from . import amount_combinations

class MorphologicalAnalyser:
    """
    Performs morphological analysis on Japanese text. It uses Sudachi for initial
    tokenization and then applies a series of custom rules to combine and refine
    the morphemes into more meaningful words and expressions.
    """
    SPECIAL_CASES_3: Set[Tuple[str, str, str, Optional[PartOfSpeech]]] = {
        ("な", "の", "で", PartOfSpeech.EXPRESSION),
        ("で", "は", "ない", PartOfSpeech.EXPRESSION),
        ("それ", "で", "も", PartOfSpeech.CONJUNCTION),
        ("なく", "なっ", "た", PartOfSpeech.VERB),
    }

    SPECIAL_CASES_2: Set[Tuple[str, str, Optional[PartOfSpeech]]] = {
        ("じゃ", "ない", PartOfSpeech.EXPRESSION),
        ("に", "しろ", PartOfSpeech.EXPRESSION),
        ("だ", "けど", PartOfSpeech.CONJUNCTION),
        ("だ", "が", PartOfSpeech.CONJUNCTION),
        ("で", "さえ", PartOfSpeech.EXPRESSION),
        ("で", "すら", PartOfSpeech.EXPRESSION),
        ("と", "いう", PartOfSpeech.EXPRESSION),
        ("と", "か", PartOfSpeech.CONJUNCTION),
        ("だ", "から", PartOfSpeech.CONJUNCTION),
        ("これ", "まで", PartOfSpeech.EXPRESSION),
        ("それ", "も", PartOfSpeech.CONJUNCTION),
        ("それ", "だけ", PartOfSpeech.NOUN),
        ("くせ", "に", PartOfSpeech.CONJUNCTION),
        ("の", "で", PartOfSpeech.PARTICLE),
        ("誰", "も", PartOfSpeech.EXPRESSION),
        ("誰", "か", PartOfSpeech.EXPRESSION),
        ("すぐ", "に", PartOfSpeech.ADVERB),
        ("なん", "か", PartOfSpeech.PARTICLE),
        ("だっ", "た", PartOfSpeech.EXPRESSION),
        ("だっ", "たら", PartOfSpeech.CONJUNCTION),
        ("よう", "に", PartOfSpeech.EXPRESSION),
        ("ん", "です", PartOfSpeech.EXPRESSION),
        ("ん", "だ", PartOfSpeech.EXPRESSION),
        ("です", "か", PartOfSpeech.EXPRESSION),
    }

    HONORIFICS_SUFFIXES: List[str] = ["さん", "ちゃん", "くん"]
    _SENTENCE_ENDERS: Set[str] = {'。', '！', '？', '」'}

    def __init__(self, dictionary_path: Optional[str] = None, config_path: Optional[str] = None, config_path_nouserdic: Optional[str] = None):
        """
        Initializes the analyser with paths to necessary resources.
        
        :param dictionary_path: Path to the Sudachi system dictionary (.dic file).
        :param config_path: Path to the main sudachi.json config file.
        :param config_path_nouserdic: Path to the sudachi.json config file without the user dictionary.
        """
        res_dir = os.path.abspath(os.path.dirname(__file__))
        self.dictionary_path = dictionary_path if dictionary_path else os.path.join(res_dir, "resources", "system_full.dic")
        self.config_path = config_path if dictionary_path else os.path.join(res_dir, "resources", "sudachi.json")
        self.config_path_nouserdic = config_path_nouserdic if dictionary_path else os.path.join(res_dir, "resources", "sudachi_nouserdic.json")

    def parse(self, text: str, morphemes_only: bool = False) -> List[SentenceInfo]:
        """
        Parses the input text into a list of sentences, each containing word information.

        :param text: The Japanese text to parse.
        :param morphemes_only: If True, performs only basic tokenization without applying combination rules.
        :return: A list of SentenceInfo objects.
        """
        # Preprocess the text to remove invalid characters
        text = self._preprocess_text(text)

        # Custom stuff in the user dictionary interferes with the mode A morpheme parsing
        config_path = self.config_path_nouserdic if morphemes_only else self.config_path
        
        output = sudachi_interop.process_text(
            config_path, text, self.dictionary_path, mode='A' if morphemes_only else 'C'
        ).split("\n")

        word_infos: List[WordInfo] = []
        for line in output:
            if line == "EOS":
                continue
            
            wi = WordInfo(line)
            if not wi.is_invalid:
                word_infos.append(wi)

        if morphemes_only:
            return [SentenceInfo(text="", words=[(w, 0, 0) for w in word_infos])]

        word_infos = self._process_special_cases(word_infos)
        word_infos = self._combine_prefixes(word_infos)

        word_infos = self._combine_amounts(word_infos)
        word_infos = self._combine_tte(word_infos)
        word_infos = self._combine_auxiliary_verb_stem(word_infos)
        word_infos = self._combine_adverbial_particle(word_infos)
        word_infos = self._combine_suffix(word_infos)
        word_infos = self._combine_auxiliary(word_infos)
        word_infos = self._combine_verb_dependant(word_infos)
        word_infos = self._combine_conjunctive_particle(word_infos)
        word_infos = self._combine_particles(word_infos)

        word_infos = self._combine_final(word_infos)

        word_infos = self._separate_suffix_honorifics(word_infos)
        word_infos = self._filter_misparse(word_infos)

        return self._split_into_sentences(text, word_infos)

    def _filter_misparse(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        """Remove common misparses."""
        for i in range(len(word_infos) - 1, -1, -1):
            word = word_infos[i]
            if word.text in ("なん", "フン", "ふん"):
                word.part_of_speech = PartOfSpeech.PREFIX

            if word.text == "そう":
                word.part_of_speech = PartOfSpeech.ADVERB

            if word.text == "おい":
                word.part_of_speech = PartOfSpeech.INTERJECTION

            if word.text == "つ" and word.part_of_speech == PartOfSpeech.SUFFIX:
                word.part_of_speech = PartOfSpeech.COUNTER

            is_single_kana_char_noun = (
                word.part_of_speech == PartOfSpeech.NOUN and
                (
                    (len(word.text) == 1 and wanakana.is_kana(word.text)) or
                    (len(word.text) == 2 and wanakana.is_kana(word.text[0]) and word.text[1] == 'ー') or
                    word.text in ("エナ", "えな")
                )
            )
            
            if word.text in ("そ", "ー", "る", "ま", "ふ", "ち", "ほ", "す", "じ", "なさ") or is_single_kana_char_noun:
                word_infos.pop(i)
                continue
        
        return word_infos

    def _preprocess_text(self, text: str) -> str:
        """Cleans and prepares text for Sudachi."""
        text = text.replace("<", " ").replace(">", " ")
        text = re.sub(
            r"[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\uFF21-\uFF3A\uFF41-\uFF5A\uFF10-\uFF19\u3005\u3001-\u3003\u3008-\u3011\u3014-\u301F\uFF01-\uFF0F\uFF1A-\uFF1F\uFF3B-\uFF3F\uFF5B-\uFF60\uFF62-\uFF65．\n…\u3000―\u2500()。！？「」）]",
            "",
            text
        )

        # Force spaces and line breaks with some characters so sudachi doesn't try to include them as part of a word
        text = re.sub(r"「", "\n「 ", text)
        text = re.sub(r"」", " 」\n", text)
        text = re.sub(r"〈", " \n〈 ", text)
        text = re.sub(r"〉", " 〉\n", text)
        text = re.sub(r"《", " \n《 ", text)
        text = re.sub(r"》", " 》\n", text)
        text = re.sub(r"“", " \n“ ", text)
        text = re.sub(r"”", " ”\n", text)
        text = re.sub(r"―", " ― ", text)
        text = re.sub(r"。", " 。\n", text)
        text = re.sub(r"！", " ！\n", text)
        text = re.sub(r"？", " ？\n", text)
        
        # Replace line ending ellipsis with a sentence ender to be able to flatten later
        text = text.replace("…\r", "。\r").replace("…\n", "。\n")
        return text

    def _process_special_cases(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        """Handle special cases that could not be covered by the other rules."""
        if not word_infos:
            return word_infos

        new_list = []
        i = 0
        while i < len(word_infos):
            w1 = word_infos[i]

            if w1.part_of_speech == PartOfSpeech.CONJUNCTION and w1.text == "で":
                w1.part_of_speech = PartOfSpeech.PARTICLE
                new_list.append(w1)
                i += 1
                continue

            # Check for 3-word cases
            if i < len(word_infos) - 2:
                w2 = word_infos[i + 1]
                w3 = word_infos[i + 2]

                # surukudasai
                if w1.dictionary_form == "する" and w2.text == "て" and w3.dictionary_form == "くださる":
                    new_word = WordInfo(w1)
                    new_word.text = w1.text + w2.text + w3.text
                    new_list.append(new_word)
                    i += 3
                    continue

                found = False
                for sc in self.SPECIAL_CASES_3:
                    if w1.text == sc[0] and w2.text == sc[1] and w3.text == sc[2]:
                        new_word = WordInfo(w1)
                        new_word.text = w1.text + w2.text + w3.text
                        if sc[3] is not None:
                            new_word.part_of_speech = sc[3]
                        new_list.append(new_word)
                        i += 3
                        found = True
                        break

                if found:
                    continue

            # Check for 2-word cases
            if i < len(word_infos) - 1:
                w2 = word_infos[i + 1]

                found = False
                for sc in self.SPECIAL_CASES_2:
                    if w1.text == sc[0] and w2.text == sc[1]:
                        new_word = WordInfo(w1)
                        new_word.text = w1.text + w2.text
                        if sc[2] is not None:
                            new_word.part_of_speech = sc[2]
                        new_list.append(new_word)
                        i += 2
                        found = True
                        break

                if found:
                    continue

            # This word is (sometimes?) parsed as auxiliary for some reason
            if w1.text == "でしょう":
                new_word = WordInfo(w1)
                new_word.part_of_speech = PartOfSpeech.EXPRESSION
                new_word.part_of_speech_section1 = PartOfSpeechSection.NONE
                new_list.append(new_word)
                i += 1
                continue

            if w1.text == "だし":
                da = WordInfo()
                da.text, da.dictionary_form, da.reading = "だ", "だ", "だ"
                da.part_of_speech = PartOfSpeech.AUXILIARY
                shi = WordInfo()
                shi.text, shi.dictionary_form, shi.reading = "し", "し", "し"
                shi.part_of_speech = PartOfSpeech.CONJUNCTION
                new_list.extend([da, shi])
                i += 1
                continue

            # Always process な as the particle and not the vegetable
            # Always process に as the particle and not the baggage
            if w1.text in ("な", "に"):
                w1.part_of_speech = PartOfSpeech.PARTICLE

            # Always process よう as the noun
            if w1.text == "よう":
                w1.part_of_speech = PartOfSpeech.NOUN

            if w1.text == "十五":
                w1.part_of_speech = PartOfSpeech.NUMERAL

            new_list.append(w1)
            i += 1
        
        return new_list

    def _combine_prefixes(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        if len(word_infos) < 2:
            return word_infos

        new_list = []
        current_word = WordInfo(word_infos[0])

        for i in range(1, len(word_infos)):
            next_word = word_infos[i]
            if current_word.part_of_speech == PartOfSpeech.PREFIX and current_word.normalized_form != "御":
                new_text = current_word.text + next_word.text
                current_word = WordInfo(next_word)
                current_word.text = new_text
            else:
                new_list.append(current_word)
                current_word = WordInfo(next_word)

        new_list.append(current_word)

        return new_list

    def _combine_amounts(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        if len(word_infos) < 2:
            return word_infos

        new_list = []
        current_word = WordInfo(word_infos[0])
        for i in range(1, len(word_infos)):
            next_word = word_infos[i]

            is_amount = (current_word.has_part_of_speech_section(PartOfSpeechSection.AMOUNT) or
                         current_word.has_part_of_speech_section(PartOfSpeechSection.NUMERAL))
            is_combination = (current_word.text, next_word.text) in amount_combinations.COMBINATIONS

            if is_amount and is_combination:
                text = current_word.text + next_word.text
                current_word = WordInfo(next_word)
                current_word.text = text
                current_word.part_of_speech = PartOfSpeech.NOUN
            else:
                new_list.append(current_word)
                current_word = WordInfo(next_word)

        new_list.append(current_word)

        return new_list

    def _combine_tte(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        if len(word_infos) < 2:
            return word_infos

        new_list = []
        current_word = WordInfo(word_infos[0])
        for i in range(1, len(word_infos)):
            next_word = word_infos[i]
            if current_word.text.endswith("っ") and next_word.text.startswith("て"):
                current_word.text += next_word.text
            else:
                new_list.append(current_word)
                current_word = WordInfo(next_word)

        new_list.append(current_word)

        return new_list

    def _combine_verb_dependant(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        if len(word_infos) < 2:
            return word_infos

        word_infos = self._combine_verb_dependants(word_infos)
        word_infos = self._combine_verb_possible_dependants(word_infos)
        word_infos = self._combine_verb_dependants_suru(word_infos)
        word_infos = self._combine_verb_dependants_teiru(word_infos)

        return word_infos

    def _combine_verb_dependants(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        if len(word_infos) < 2:
            return word_infos

        new_list = []
        current_word = WordInfo(word_infos[0])

        for i in range(1, len(word_infos)):
            next_word = word_infos[i]
            if (next_word.has_part_of_speech_section(PartOfSpeechSection.DEPENDANT) and
                current_word.part_of_speech == PartOfSpeech.VERB):
                current_word.text += next_word.text
            else:
                new_list.append(current_word)
                current_word = WordInfo(next_word)

        new_list.append(current_word)

        return new_list

    def _combine_verb_possible_dependants(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        if len(word_infos) < 2:
            return word_infos

        new_list = []
        current_word = WordInfo(word_infos[0])

        for i in range(1, len(word_infos)):
            next_word = word_infos[i]

            # Condition uses accumulator (verb) and next word (possible dependant + specific forms)
            is_possible = (next_word.has_part_of_speech_section(PartOfSpeechSection.POSSIBLE_DEPENDANT) and
                           current_word.part_of_speech == PartOfSpeech.VERB and
                           next_word.dictionary_form in ("得る", "する", "しまう", "おる", "きる", "こなす", "いく", "貰う", "いる", "ない"))

            if is_possible:
                current_word.text += next_word.text
            else:
                new_list.append(current_word)
                current_word = WordInfo(next_word)

        new_list.append(current_word)

        return new_list

    def _combine_verb_dependants_suru(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        if len(word_infos) < 2:
            return word_infos

        new_list = []
        i = 0
        while i < len(word_infos):
            current_word = word_infos[i]
            if i + 1 < len(word_infos):
                next_word = word_infos[i + 1]
                if (current_word.has_part_of_speech_section(PartOfSpeechSection.POSSIBLE_SURU) and
                    next_word.dictionary_form == "する" and next_word.text not in ("する", "しない")):
                    combined_word = WordInfo(current_word)
                    combined_word.text += next_word.text
                    combined_word.part_of_speech = PartOfSpeech.VERB
                    new_list.append(combined_word)
                    i += 2
                    continue
            new_list.append(WordInfo(current_word))
            i += 1

        return new_list

    def _combine_verb_dependants_teiru(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        if len(word_infos) < 3:
            return word_infos

        new_list = []
        i = 0
        while i < len(word_infos):
            if i + 2 < len(word_infos):
                current_word, next1, next2 = word_infos[i], word_infos[i+1], word_infos[i+2]
                if (current_word.part_of_speech == PartOfSpeech.VERB and
                    next1.dictionary_form == "て" and next2.dictionary_form == "いる"):
                    combined_word = WordInfo(current_word)
                    combined_word.text += next1.text + next2.text
                    new_list.append(combined_word)
                    i += 3
                    continue
            new_list.append(WordInfo(word_infos[i]))
            i += 1

        return new_list

    def _combine_adverbial_particle(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        if len(word_infos) < 2:
            return word_infos

        new_list = []
        current_word = WordInfo(word_infos[0])
        for i in range(1, len(word_infos)):
            next_word = word_infos[i]

            # i.e　だり, たり
            should_combine = (next_word.has_part_of_speech_section(PartOfSpeechSection.ADVERBIAL_PARTICLE) and
                              next_word.dictionary_form in ("だり", "たり") and
                              current_word.part_of_speech == PartOfSpeech.VERB)

            if should_combine:
                current_word.text += next_word.text
            else:
                new_list.append(current_word)
                current_word = WordInfo(next_word)

        new_list.append(current_word)

        return new_list

    def _combine_conjunctive_particle(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        if len(word_infos) < 2:
            return word_infos

        new_list = [word_infos[0]]
        for i in range(1, len(word_infos)):
            current_word = word_infos[i]
            previous_word = new_list[-1]

            should_combine = (current_word.has_part_of_speech_section(PartOfSpeechSection.CONJUNCTION_PARTICLE) and
                              current_word.text in ("て", "で", "ちゃ", "ば") and
                              previous_word.part_of_speech in (PartOfSpeech.VERB, PartOfSpeech.I_ADJECTIVE, PartOfSpeech.AUXILIARY))

            if should_combine:
                previous_word.text += current_word.text
            else:
                new_list.append(current_word)

        return new_list

    def _combine_auxiliary(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        if len(word_infos) < 2:
            return word_infos

        new_list = [word_infos[0]]
        for i in range(1, len(word_infos)):
            current_word = word_infos[i]
            previous_word = new_list[-1]
            if current_word.part_of_speech != PartOfSpeech.AUXILIARY:
                new_list.append(current_word)
                continue

            prev_is_combinable = (previous_word.part_of_speech in (PartOfSpeech.VERB, PartOfSpeech.I_ADJECTIVE, PartOfSpeech.NA_ADJECTIVE, PartOfSpeech.AUXILIARY) or
                                  previous_word.has_part_of_speech_section(PartOfSpeechSection.ADJECTIVAL))
            is_desu_exception = (current_word.dictionary_form == "です" and not
                                 (previous_word.part_of_speech == PartOfSpeech.VERB and current_word.text in ("でし", "でした")))
            should_combine = (prev_is_combinable and
                              not is_desu_exception and
                              current_word.text not in ("な", "に", "なら", "だろう") and
                              current_word.dictionary_form not in ("らしい", "べし", "ようだ", "やがる"))

            if should_combine:
                previous_word.text += current_word.text
            else:
                new_list.append(current_word)

        return new_list

    def _combine_auxiliary_verb_stem(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        if len(word_infos) < 2:
            return word_infos

        new_list = []
        current_word = WordInfo(word_infos[0])
        for i in range(1, len(word_infos)):
            next_word, prev_word = word_infos[i], word_infos[i-1]

            should_combine = (next_word.has_part_of_speech_section(PartOfSpeechSection.AUXILIARY_VERB_STEM) and
                              next_word.text not in ("ように", "よう", "みたい") and
                              prev_word.part_of_speech in (PartOfSpeech.VERB, PartOfSpeech.I_ADJECTIVE))

            if should_combine:
                current_word.text += next_word.text
            else:
                new_list.append(current_word)
                current_word = WordInfo(next_word)

        new_list.append(current_word)

        return new_list

    def _combine_suffix(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        if len(word_infos) < 2:
            return word_infos

        new_list = []
        current_word = WordInfo(word_infos[0])

        for i in range(1, len(word_infos)):
            next_word, prev_word = word_infos[i], word_infos[i-1]

            is_suffix = (next_word.part_of_speech == PartOfSpeech.SUFFIX or
                         next_word.has_part_of_speech_section(PartOfSpeechSection.SUFFIX))
            is_combinable = (next_word.dictionary_form in ("っこ", "さ", "がる") or
                             (next_word.dictionary_form == "ら" and prev_word.part_of_speech == PartOfSpeech.PRONOUN))

            if is_suffix and is_combinable:
                current_word.text += next_word.text
            else:
                new_list.append(current_word)
                current_word = WordInfo(next_word)

        new_list.append(current_word)

        return new_list

    def _combine_particles(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        if len(word_infos) < 2:
            return word_infos

        new_list = []
        i = 0
        while i < len(word_infos):
            current_word = word_infos[i]

            if i + 1 < len(word_infos):
                next_word = word_infos[i + 1]
                combined_text = ""

                if (current_word.text, next_word.text) == ("に", "は"): combined_text = "には"
                elif (current_word.text, next_word.text) == ("と", "は"): combined_text = "とは"
                elif (current_word.text, next_word.text) == ("で", "は"): combined_text = "では"
                elif (current_word.text, next_word.text) == ("の", "に"): combined_text = "のに"

                if combined_text:
                    combined_word = WordInfo(current_word)
                    combined_word.text = combined_text
                    new_list.append(combined_word)
                    i += 2
                    continue

            new_list.append(WordInfo(current_word))
            i += 1

        return new_list

    def _separate_suffix_honorifics(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        """
        Tries to separate honorifics from proper names.
        This still doesn't work for all cases
        """
        if len(word_infos) < 2:
            return word_infos

        new_list = []
        for word in word_infos:
            current_word = WordInfo(word)
            separated = False

            for honorific in self.HONORIFICS_SUFFIXES:
                is_proper_noun = (current_word.has_part_of_speech_section(PartOfSpeechSection.PERSON_NAME) or
                                  current_word.has_part_of_speech_section(PartOfSpeechSection.PROPER_NOUN))

                if (current_word.text.endswith(honorific) and len(current_word.text) > len(honorific) and is_proper_noun):
                    current_word.text = current_word.text[:-len(honorific)]
                    if current_word.dictionary_form.endswith(honorific):
                        current_word.dictionary_form = current_word.dictionary_form[:-len(honorific)]
                    suffix = WordInfo()
                    suffix.text, suffix.reading, suffix.dictionary_form = honorific, honorific, honorific
                    suffix.part_of_speech = PartOfSpeech.SUFFIX
                    new_list.extend([current_word, suffix])
                    separated = True
                    break

            if not separated:
                new_list.append(current_word)

        return word_infos

    def _combine_final(self, word_infos: List[WordInfo]) -> List[WordInfo]:
        """Cleanup method / 2nd pass for some cases."""
        if len(word_infos) < 2:
            return word_infos

        new_list = []
        current_word = WordInfo(word_infos[0])
        for i in range(1, len(word_infos)):
            next_word, prev_word = word_infos[i], word_infos[i-1]
            if next_word.text == "ば" and prev_word.part_of_speech == PartOfSpeech.VERB:
                current_word.text += next_word.text
            else:
                new_list.append(current_word)
                current_word = WordInfo(next_word)

        new_list.append(current_word)

        return new_list

    def _split_into_sentences(self, text: str, word_infos: List[WordInfo]) -> List[SentenceInfo]:
        sentences: List[SentenceInfo] = []

        # Need a flat text for the sentence to corresponds if they're cut between 2 lines
        text = text.replace("\r", "").replace("\n", "")

        # Split raw text into sentences
        current_sentence_chars = []
        seen_ender = False
        for char in text:
            current_sentence_chars.append(char)

            # Detect if sentence ender was seen
            if char in self._SENTENCE_ENDERS:
                seen_ender = True
                continue

            # Handle possible multiple enders in a row
            if seen_ender:
                if char in self._SENTENCE_ENDERS:
                    continue

                # Flush the sentence and append the character to the next one instead
                last_char = current_sentence_chars.pop()
                sentences.append(SentenceInfo("".join(current_sentence_chars)))
                current_sentence_chars = [last_char]
                seen_ender = False

        # Handle leftover buffer
        if current_sentence_chars:
            sentences.append(SentenceInfo("".join(current_sentence_chars)))

        # Assign words to sentences
        current_sentence_idx, current_char_idx = 0, 0
        for word in word_infos:
            if not word.text:
                continue

            word_assigned = False
            while current_sentence_idx < len(sentences) and not word_assigned:
                sentence = sentences[current_sentence_idx]
                word_idx = sentence.text.find(word.text, current_char_idx)

                if word_idx >= 0:
                    current_char_idx = word_idx + len(word.text)
                    sentence.words.append((word, word_idx, len(word.text)))
                    word_assigned = True
                else:
                    # Word not found, check if it spans across to the next sentence
                    if current_sentence_idx + 1 < len(sentences):
                        remaining = sentence.text[current_char_idx:]
                        next_sentence = sentences[current_sentence_idx + 1]

                        for i in range(1, len(word.text)):
                            part1, part2 = word.text[:i], word.text[i:]
                            if remaining.endswith(part1) and next_sentence.text.startswith(part2):
                                # Word spans sentences, merge them
                                sentence.text += next_sentence.text
                                sentences.pop(current_sentence_idx + 1)

                                # Retry finding the word in the merged sentence
                                word_idx = sentence.text.find(word.text, current_char_idx)
                                if word_idx >= 0:
                                    current_char_idx = word_idx + len(word.text)
                                    sentence.words.append((word, word_idx, len(word.text)))
                                    word_assigned = True
                                break

                    if word_assigned:
                        continue

                    current_sentence_idx += 1
                    current_char_idx = 0

        return sentences