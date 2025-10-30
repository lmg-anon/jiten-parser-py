import cProfile
import pstats
import io

from jiten.parser import Parser, DeckWord
from jiten.jmdict.jmdict import JmDict, to_human_readable_parts_of_speech
from jiten.jmdict.jmdict_word import JmDictWord

PROFILE = False

def _format_jmdict_details(word: JmDictWord) -> str:
    lines = []
    readings_str = " / ".join(word.readings_furigana)
    header = f"Readings: {readings_str}"
    
    extra_info = []
    if word.pitch_accents:
        extra_info.append(f"Pitch: {', '.join(map(str, word.pitch_accents))}")
    if word.origin and word.origin.name != 'UNKNOWN':
        extra_info.append(f"Origin: {word.origin.name.capitalize()}")
    if extra_info:
        header += f"  [{' | '.join(extra_info)}]"
    
    lines.append(header)

    for i, definition in enumerate(word.definitions):
        if not definition.english_meanings:
            break
        pos_list = to_human_readable_parts_of_speech(definition.parts_of_speech)
        pos_str = f"({', '.join(pos_list)})" if pos_list else ""
        lines.append(f"\n  Sense {i+1} {pos_str}")
        for j, meaning in enumerate(definition.english_meanings):
            lines.append(f"    {j+1}. {meaning}")
            
    return "\n".join(lines)

def format_parsed_word(parsed_word: DeckWord, jmdict: JmDict):
    print(f"- Parsed from text: '{parsed_word.original_text}'")
    if parsed_word.conjugations:
        conjugation_path = " -> ".join(parsed_word.conjugations)
        print(f"   └─ Conjugation: [{conjugation_path}]")

    full_word_entry = jmdict.get_word_by_id(parsed_word.word_id)
    if full_word_entry:
        print(_format_jmdict_details(full_word_entry))
    else:
        print(f"  Could not find JMDict entry for ID: {parsed_word.word_id}")

def print_profile_stats(profiler):
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)
    print(s.getvalue())

def main():
    jmdict = JmDict()
    try:
        Parser._ensure_initialized()
        jmdict.load()
    except Exception as e:
        print(f"\nAn unexpected error occurred during loading: {e}")
        return

    try:
        while True:
            query = input("Enter Japanese text (or 'q' to quit): ").strip()
            if not query:
                continue
            if query.lower() == 'q':
                break

            print(f"\nAnalyzing '{query}'...")

            profiler = None
            if PROFILE:
                profiler = cProfile.Profile()
                profiler.enable()

            parsed_words = Parser.parse_text(query)

            if PROFILE:
                profiler.disable()

            if not parsed_words:
                print(f"No words identified.")
            else:
                print(f"Found {len(parsed_words)} word(s):")
                print("=" * 20)
                for word_entry in parsed_words:
                    format_parsed_word(word_entry, jmdict)
                    print("-" * 20)

            if PROFILE:
                print_profile_stats(profiler)

    finally:
        jmdict.close()

if __name__ == "__main__":
    main()