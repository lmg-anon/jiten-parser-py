import csv
import json
import os
import pickle
import re
import sqlite3
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from enum import IntEnum
from typing import Dict, List, Optional, Iterator

try:
    import wanakana
except ImportError:
    raise RuntimeError("'wanakana-paison' not found. Install it with 'pip install git+https://github.com/lmg-anon/WanaKanaPaison.git'.")

from .word_origin import WordOrigin
from .jmdict_reading_type import JmDictReadingType
from .jmdict_lookup import JmDictLookup
from .jmdict_definition import JmDictDefinition
from .jmdict_word import JmDictWord
from .jmdict_furigana import JmDictFurigana, Furigana

_POS_DICTIONARY = {
    "bra": "Brazilian", "hob": "Hokkaido-ben",
    "ksb": "Kansai-ben", "ktb": "Kantou-ben",
    "kyb": "Kyoto-ben", "kyu": "Kyuushuu-ben",
    "nab": "Nagano-ben", "osb": "Osaka-ben",
    "rkb": "Ryuukyuu-ben", "thb": "Touhoku-ben",
    "tsb": "Tosa-ben", "tsug": "Tsugaru-ben",
    "agric": "agriculture", "anat": "anatomy",
    "archeol": "archeology", "archit": "architecture",
    "art": "art, aesthetics", "astron": "astronomy",
    "audvid": "audiovisual", "aviat": "aviation",
    "baseb": "baseball", "biochem": "biochemistry",
    "biol": "biology", "bot": "botany",
    "Buddh": "Buddhism", "bus": "business",
    "cards": "card games", "chem": "chemistry",
    "Christn": "Christianity", "cloth": "clothing",
    "comp": "computing", "cryst": "crystallography",
    # Name types from JMNedict
    "name": "name", "name-fem": "female name",
    "name-male": "male name", "name-given": "given name",
    "name-surname": "surname", "name-place": "place name",
    "name-person": "person name",
    "name-unclass": "unclassified name",
    "name-station": "station name",
    "name-organization": "organization name",
    "name-company": "company name",
    "name-product": "product name",
    "name-work": "work name", "dent": "dentistry",
    "ecol": "ecology", "econ": "economics",
    "elec": "electricity, elec. eng.",
    "electr": "electronics", "embryo": "embryology",
    "engr": "engineering", "ent": "entomology",
    "film": "film", "finc": "finance",
    "fish": "fishing", "food": "food, cooking",
    "gardn": "gardening, horticulture", "genet": "genetics",
    "geogr": "geography", "geol": "geology",
    "geom": "geometry", "go": "go (game)",
    "golf": "golf", "gramm": "grammar",
    "grmyth": "Greek mythology", "hanaf": "hanafuda",
    "horse": "horse racing", "kabuki": "kabuki",
    "law": "law", "ling": "linguistics",
    "logic": "logic", "MA": "martial arts",
    "mahj": "mahjong", "manga": "manga",
    "math": "mathematics", "mech": "mechanical engineering",
    "med": "medicine", "met": "meteorology",
    "mil": "military", "mining": "mining",
    "music": "music", "noh": "noh",
    "ornith": "ornithology", "paleo": "paleontology",
    "pathol": "pathology", "pharm": "pharmacology",
    "phil": "philosophy", "photo": "photography",
    "physics": "physics", "physiol": "physiology",
    "politics": "politics", "print": "printing",
    "psy": "psychiatry", "psyanal": "psychoanalysis",
    "psych": "psychology", "rail": "railway",
    "rommyth": "Roman mythology", "Shinto": "Shinto",
    "shogi": "shogi", "ski": "skiing",
    "sports": "sports", "stat": "statistics",
    "stockm": "stock market", "sumo": "sumo",
    "telec": "telecommunications", "tradem": "trademark",
    "tv": "television", "vidg": "video games",
    "zool": "zoology", "abbr": "abbreviation",
    "arch": "archaic", "char": "character",
    "chn": "children's language", "col": "colloquial",
    "company": "company name", "creat": "creature",
    "dated": "dated term", "dei": "deity",
    "derog": "derogatory", "doc": "document",
    "euph": "euphemistic", "ev": "event",
    "fam": "familiar language",
    "fem": "female term or language", "fict": "fiction",
    "form": "formal or literary term",
    "given": "given name or forename, gender not specified",
    "group": "group", "hist": "historical term",
    "hon": "honorific or respectful (sonkeigo)",
    "hum": "humble (kenjougo)",
    "id": "idiomatic expression",
    "joc": "jocular, humorous term", "leg": "legend",
    "m-sl": "manga slang", "male": "male term or language",
    "myth": "mythology", "net-sl": "Internet slang",
    "obj": "object", "obs": "obsolete term",
    "on-mim": "onomatopoeic or mimetic",
    "organization": "organization name", "oth": "other",
    "person": "full name of a particular person",
    "place": "place name", "poet": "poetical term",
    "pol": "polite (teineigo)", "product": "product name",
    "proverb": "proverb", "quote": "quotation",
    "rare": "rare term", "relig": "religion",
    "sens": "sensitive", "serv": "service",
    "ship": "ship name", "sl": "slang",
    "station": "railway station",
    "surname": "family or surname",
    "uk": "usually written using kana",
    "unclass": "unclassified name", "vulg": "vulgar",
    "work": "work of art, literature, music, etc. name",
    "X": "rude or X-rated term (not displayed in educational software)",
    "yoji": "yojijukugo",
    "adj-f": "noun or verb acting prenominally",
    "adj-i": "adjective (keiyoushi)",
    "adj-ix": "adjective (keiyoushi) - yoi/ii class",
    "adj-kari": "'kari' adjective (archaic)",
    "adj-ku": "'ku' adjective (archaic)",
    "adj-na": "adjectival nouns or quasi-adjectives (keiyodoshi)",
    "adj-nari": "archaic/formal form of na-adjective",
    "adj-no": "nouns which may take the genitive case particle 'no'",
    "adj-pn": "pre-noun adjectival (rentaishi)",
    "adj-shiku": "'shiku' adjective (archaic)",
    "adj-t": "'taru' adjective", "adv": "adverb (fukushi)",
    "adv-to": "adverb taking the 'to' particle",
    "aux": "auxiliary", "aux-adj": "auxiliary adjective",
    "aux-v": "auxiliary verb", "conj": "conjunction",
    "cop": "copula", "ctr": "counter",
    "exp": "expressions (phrases, clauses, etc.)",
    "int": "interjection (kandoushi)",
    "n": "noun (common) (futsuumeishi)",
    "n-adv": "adverbial noun (fukushitekimeishi)",
    "n-pr": "proper noun",
    "n-pref": "noun, used as a prefix",
    "n-suf": "noun, used as a suffix",
    "n-t": "noun (temporal) (jisoumeishi)",
    "num": "numeric", "pn": "pronoun", "pref": "prefix",
    "prt": "particle", "suf": "suffix",
    "unc": "unclassified", "v-unspec": "verb unspecified",
    "v1": "Ichidan verb",
    "v1-s": "Ichidan verb - kureru special class",
    "v2a-s": "Nidan verb with 'u' ending (archaic)",
    "v2b-k": "Nidan verb (upper class) with 'bu' ending (archaic)",
    "v2b-s": "Nidan verb (lower class) with 'bu' ending (archaic)",
    "v2d-k": "Nidan verb (upper class) with 'dzu' ending (archaic)",
    "v2d-s": "Nidan verb (lower class) with 'dzu' ending (archaic)",
    "v2g-k": "Nidan verb (upper class) with 'gu' ending (archaic)",
    "v2g-s": "Nidan verb (lower class) with 'gu' ending (archaic)",
    "v2h-k": "Nidan verb (upper class) with 'hu/fu' ending (archaic)",
    "v2h-s": "Nidan verb (lower class) with 'hu/fu' ending (archaic)",
    "v2k-k": "Nidan verb (upper class) with 'ku' ending (archaic)",
    "v2k-s": "Nidan verb (lower class) with 'ku' ending (archaic)",
    "v2m-k": "Nidan verb (upper class) with 'mu' ending (archaic)",
    "v2m-s": "Nidan verb (lower class) with 'mu' ending (archaic)",
    "v2n-s": "Nidan verb (lower class) with 'nu' ending (archaic)",
    "v2r-k": "Nidan verb (upper class) with 'ru' ending (archaic)",
    "v2r-s": "Nidan verb (lower class) with 'ru' ending (archaic)",
    "v2s-s": "Nidan verb (lower class) with 'su' ending (archaic)",
    "v2t-k": "Nidan verb (upper class) with 'tsu' ending (archaic)",
    "v2t-s": "Nidan verb (lower class) with 'tsu' ending (archaic)",
    "v2w-s": "Nidan verb (lower class) with 'u' ending and 'we' conjugation (archaic)",
    "v2y-k": "Nidan verb (upper class) with 'yu' ending (archaic)",
    "v2y-s": "Nidan verb (lower class) with 'yu' ending (archaic)",
    "v2z-s": "Nidan verb (lower class) with 'zu' ending (archaic)",
    "v4b": "Yodan verb with 'bu' ending (archaic)",
    "v4g": "Yodan verb with 'gu' ending (archaic)",
    "v4h": "Yodan verb with 'hu/fu' ending (archaic)",
    "v4k": "Yodan verb with 'ku' ending (archaic)",
    "v4m": "Yodan verb with 'mu' ending (archaic)",
    "v4n": "Yodan verb with 'nu' ending (archaic)",
    "v4r": "Yodan verb with 'ru' ending (archaic)",
    "v4s": "Yodan verb with 'su' ending (archaic)",
    "v4t": "Yodan verb with 'tsu' ending (archaic)",
    "v5aru": "Godan verb - -aru special class",
    "v5b": "Godan verb with 'bu' ending",
    "v5g": "Godan verb with 'gu' ending",
    "v5k": "Godan verb with 'ku' ending",
    "v5k-s": "Godan verb - Iku/Yuku special class",
    "v5m": "Godan verb with 'mu' ending",
    "v5n": "Godan verb with 'nu' ending",
    "v5r": "Godan verb with 'ru' ending",
    "v5r-i": "Godan verb with 'ru' ending (irregular verb)",
    "v5s": "Godan verb with 'su' ending",
    "v5t": "Godan verb with 'tsu' ending",
    "v5u": "Godan verb with 'u' ending",
    "v5u-s": "Godan verb with 'u' ending (special class)",
    "v5uru": "Godan verb - Uru old class verb (old form of Eru)",
    "vi": "intransitive verb",
    "vk": "Kuru verb - special class",
    "vn": "irregular nu verb",
    "vr": "irregular ru verb, plain form ends with -ri",
    "vs": "noun or participle which takes the aux. verb suru",
    "vs-c": "su verb - precursor to the modern suru",
    "vs-i": "suru verb - included",
    "vs-s": "suru verb - special class",
    "vt": "transitive verb",
    "vz": "Ichidan verb - zuru verb (alternative form of -jiru verbs)",
    "gikun": "gikun (meaning as reading) or jukujikun (special kanji reading)",
    "ik": "irregular kana usage",
    "ok": "out-dated or obsolete kana usage",
    "sk": "search-only kana form", "boxing": "boxing",
    "chmyth": "Chinese mythology",
    "civeng": "civil engineering",
    "figskt": "figure skating", "internet": "Internet",
    "jpmyth": "Japanese mythology", "min": "mineralogy",
    "motor": "motorsport",
    "prowres": "professional wrestling", "surg": "surgery",
    "vet": "veterinary terms",
    "ateji": "ateji (phonetic) reading",
    "iK": "word containing irregular kanji usage",
    "io": "irregular okurigana usage",
    "oK": "word containing out-dated kanji or kanji usage",
    "rK": "rarely used kanji form",
    "sK": "search-only kanji form",
    "rk": "rarely used kana form",
}

_entities: Dict[str, str] = {}
_entities_rev: Dict[str, str] = {}

# Delimiter for storing lists as strings in the database
MEANING_DELIMITER = ";;;"

JMDICT_LOG = False

class JmDict:
    """
    An interface to the JMDict dictionary.

    Usage:
        jmdict = JmDict()
        try:
            results = jmdict.lookup("食べる")
            for word in results:
                print(word.readings_furigana)
        finally:
            jmdict.close()
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initializes JmDict.

        Args:
            db_path: Path to the SQLite database file. If None, a default
                     path ('data/jmdict.db') will be used.
        """
        jmdict_dir = os.path.abspath(os.path.dirname(__file__))
        if db_path is None:
            db_path = os.path.join(jmdict_dir, "data", "jmdict.db")
        
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._word_cache: Dict[int, JmDictWord] = {}

    def _print(self, *args, **kwargs):
        if JMDICT_LOG:
            print(*args, **kwargs)

    def load(self, source_paths: Optional[Dict[str, str]] = None, force_rebuild: bool = False):
        """
        Ensures the dictionary database is available and up-to-date.

        If the database doesn't exist, is outdated, or if force_rebuild is True,
        it will be built from the source files. Otherwise, it connects to the
        existing database.

        Args:
            source_paths: A dictionary containing paths to all source files.
                          Expected keys: 'dtd', 'jmdict', 'furigana', 'jmnedict',
                                         'pitch_accent_dir', 'origin'.
            force_rebuild: If True, deletes the existing database and rebuilds it.
        """
        jmdict_dir = os.path.abspath(os.path.dirname(__file__))
        data_dir = os.path.join(jmdict_dir, "data")
        if source_paths is None:
            source_paths = {
                'dtd': os.path.join(data_dir, "jmdict_dtd.xml"),
                'jmdict': os.path.join(data_dir, "JMdict"),
                'furigana': os.path.join(data_dir, "JmdictFurigana.json"),
                'jmnedict': os.path.join(data_dir, "JMnedict.xml"),
                'pitch_accent_dir': os.path.join(data_dir, "pitch_accents"),
                'origin': os.path.join(data_dir, "vocab_origin.csv")
            }

        start_time = time.time()
        
        if force_rebuild or not self._is_db_valid(source_paths.values()):
            self._print("Database not found or is outdated. Building from source files...")
            if not os.path.exists(source_paths['dtd']):
                raise Exception("Source files not found for database rebuilding.")
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            self._create_and_populate_db(source_paths)
        else:
            self._print(f"Connecting to existing JMDict database: {self.db_path}")

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        end_time = time.time()
        word_count = self.conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        self._print(f"JMDict ready in {end_time - start_time:.2f} seconds.")
        self._print(f"Total words in database: {word_count}")

    def _is_db_valid(self, source_file_paths: List[str]) -> bool:
        if not os.path.exists(self.db_path):
            return False
        
        db_mtime = os.path.getmtime(self.db_path)
        
        for path in source_file_paths:
            if not path or not os.path.exists(path):
                continue
            
            if os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        filepath = os.path.join(root, file)
                        if os.path.getmtime(filepath) > db_mtime:
                            self._print(f"DB is stale. Reason: {filepath} is newer.")
                            return False
            elif os.path.exists(path):
                if os.path.getmtime(path) > db_mtime:
                    self._print(f"DB is stale. Reason: {path} is newer.")
                    return False
        return True

    def _create_and_populate_db(self, paths: Dict[str, str]):
        """
        Orchestrates the full parsing of source files and populates a new
        SQLite database with the processed data.
        """
        self._print("Parsing source files...")
        self._load_entities(paths['dtd'])
        word_infos = self._get_word_infos(paths['jmdict'])
        word_infos.extend(self._get_custom_words())
        furigana_dict = self._load_furigana(paths['furigana'])
        self._process_words(word_infos, furigana_dict)
        self._apply_custom_priorities(word_infos)

        existing_readings = {r for w in word_infos for r in w.readings}
        name_words = self._import_jmnedict(paths['jmnedict'], existing_readings)
        self._process_words(name_words, {})
        word_infos.extend(name_words)

        # Consolidate words by ID, preferring the first entry found
        final_words: Dict[int, JmDictWord] = {}
        for word in word_infos:
            if word.word_id not in final_words:
                final_words[word.word_id] = word
        
        self._print("Applying pitch accents and vocabulary origins...")
        self._import_pitch_accents(final_words, paths.get('pitch_accent_dir', ''))
        self._import_vocabulary_origin(final_words, paths.get('origin', ''))

        self._print(f"Populating SQLite database at {self.db_path}...")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        db_conn = sqlite3.connect(self.db_path)
        cursor = db_conn.cursor()

        self._create_tables(cursor)
        self._populate_tables(cursor, final_words.values())

        self._print("Creating database indexes for faster lookups...")
        self._create_indexes(cursor)

        db_conn.commit()
        db_conn.close()
        self._print("Database build complete.")

    def _create_tables(self, cursor: sqlite3.Cursor):
        cursor.execute("""
        CREATE TABLE words (
            word_id INTEGER PRIMARY KEY,
            origin INTEGER
        )""")
        
        cursor.execute("""
        CREATE TABLE readings (
            word_id INTEGER,
            reading_order INTEGER,
            reading_text TEXT,
            reading_type INTEGER,
            PRIMARY KEY (word_id, reading_order),
            FOREIGN KEY (word_id) REFERENCES words(word_id)
        )""")

        cursor.execute("""
        CREATE TABLE readings_furigana (
            word_id INTEGER,
            furigana_order INTEGER,
            furigana_text TEXT,
            PRIMARY KEY (word_id, furigana_order),
            FOREIGN KEY (word_id) REFERENCES words(word_id)
        )""")

        cursor.execute("""
        CREATE TABLE definitions (
            definition_id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER,
            english_meanings TEXT,
            dutch_meanings TEXT,
            french_meanings TEXT,
            german_meanings TEXT,
            spanish_meanings TEXT,
            hungarian_meanings TEXT,
            russian_meanings TEXT,
            slovenian_meanings TEXT,
            FOREIGN KEY (word_id) REFERENCES words(word_id)
        )""")

        cursor.execute("""
        CREATE TABLE definition_pos (
            definition_id INTEGER,
            pos_text TEXT,
            PRIMARY KEY (definition_id, pos_text),
            FOREIGN KEY (definition_id) REFERENCES definitions(definition_id)
        )""")

        cursor.execute("CREATE TABLE parts_of_speech (word_id INTEGER, pos_text TEXT, FOREIGN KEY (word_id) REFERENCES words(word_id))")
        cursor.execute("CREATE TABLE priorities (word_id INTEGER, priority_text TEXT, FOREIGN KEY (word_id) REFERENCES words(word_id))")
        cursor.execute("CREATE TABLE pitch_accents (word_id INTEGER, pitch_order INTEGER, pitch_value INTEGER, FOREIGN KEY (word_id) REFERENCES words(word_id))")
        cursor.execute("CREATE TABLE lookups (lookup_key TEXT, word_id INTEGER, FOREIGN KEY (word_id) REFERENCES words(word_id))")

    def _populate_tables(self, cursor: sqlite3.Cursor, words: Iterator[JmDictWord]):
        words_data, readings_data, furigana_data = [], [], []
        definitions_data, def_pos_data, pos_data = [], [], []
        priorities_data, pitch_data, lookups_data = [], [], []

        for word in words:
            words_data.append((word.word_id, word.origin.value))
            
            for i, r in enumerate(word.readings):
                readings_data.append((word.word_id, i, r, word.reading_types[i].value))
            for i, f in enumerate(word.readings_furigana):
                furigana_data.append((word.word_id, i, f))
            for p in word.parts_of_speech:
                pos_data.append((word.word_id, p))
            for p in word.priorities:
                priorities_data.append((word.word_id, p))
            for i, p in enumerate(word.pitch_accents):
                pitch_data.append((word.word_id, i, p))
            for l in word.lookups:
                lookups_data.append((l.lookup_key, l.word_id))

            for definition in word.definitions:
                cursor.execute("""
                    INSERT INTO definitions (word_id, english_meanings, dutch_meanings, french_meanings, german_meanings, spanish_meanings, hungarian_meanings, russian_meanings, slovenian_meanings)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    word.word_id,
                    MEANING_DELIMITER.join(definition.english_meanings),
                    MEANING_DELIMITER.join(definition.dutch_meanings),
                    MEANING_DELIMITER.join(definition.french_meanings),
                    MEANING_DELIMITER.join(definition.german_meanings),
                    MEANING_DELIMITER.join(definition.spanish_meanings),
                    MEANING_DELIMITER.join(definition.hungarian_meanings),
                    MEANING_DELIMITER.join(definition.russian_meanings),
                    MEANING_DELIMITER.join(definition.slovenian_meanings)
                ))
                def_id = cursor.lastrowid
                for pos in definition.parts_of_speech:
                    def_pos_data.append((def_id, pos))

        cursor.executemany("INSERT INTO words VALUES (?, ?)", words_data)
        cursor.executemany("INSERT INTO readings VALUES (?, ?, ?, ?)", readings_data)
        cursor.executemany("INSERT INTO readings_furigana VALUES (?, ?, ?)", furigana_data)
        cursor.executemany("INSERT INTO definition_pos VALUES (?, ?)", def_pos_data)
        cursor.executemany("INSERT INTO parts_of_speech VALUES (?, ?)", pos_data)
        cursor.executemany("INSERT INTO priorities VALUES (?, ?)", priorities_data)
        cursor.executemany("INSERT INTO pitch_accents VALUES (?, ?, ?)", pitch_data)
        cursor.executemany("INSERT INTO lookups VALUES (?, ?)", lookups_data)

    def _create_indexes(self, cursor: sqlite3.Cursor):
        cursor.execute("CREATE INDEX idx_lookup_key ON lookups (lookup_key)")
        cursor.execute("CREATE INDEX idx_definition_word_id ON definitions (word_id)")
        cursor.execute("CREATE INDEX idx_reading_word_id ON readings (word_id)")

    def get_word_by_id(self, word_id: int) -> Optional[JmDictWord]:
        """
        Retrieves a single word and all its details from the database by its ID.
        """
        if not self.conn:
            self.load()

        if word_id in self._word_cache:
            return self._word_cache[word_id]

        cursor = self.conn.cursor()
        word_row = cursor.execute("SELECT * FROM words WHERE word_id = ?", (word_id,)).fetchone()
        if not word_row:
            return None

        word = JmDictWord(word_id=word_row['word_id'], origin=WordOrigin(word_row['origin']))
        
        # Rehydrate lists
        word.readings = [r['reading_text'] for r in cursor.execute("SELECT reading_text FROM readings WHERE word_id = ? ORDER BY reading_order", (word_id,))]
        word.reading_types = [JmDictReadingType(r['reading_type']) for r in cursor.execute("SELECT reading_type FROM readings WHERE word_id = ? ORDER BY reading_order", (word_id,))]
        word.readings_furigana = [r['furigana_text'] for r in cursor.execute("SELECT furigana_text FROM readings_furigana WHERE word_id = ? ORDER BY furigana_order", (word_id,))]
        word.parts_of_speech = [r['pos_text'] for r in cursor.execute("SELECT pos_text FROM parts_of_speech WHERE word_id = ?", (word_id,))]
        word.priorities = [r['priority_text'] for r in cursor.execute("SELECT priority_text FROM priorities WHERE word_id = ?", (word_id,))]
        word.pitch_accents = [r['pitch_value'] for r in cursor.execute("SELECT pitch_value FROM pitch_accents WHERE word_id = ? ORDER BY pitch_order", (word_id,))]

        # Rehydrate definitions
        def_rows = cursor.execute("SELECT * FROM definitions WHERE word_id = ?", (word_id,)).fetchall()
        for def_row in def_rows:
            definition = JmDictDefinition(definition_id=def_row['definition_id'], word_id=word_id)
            definition.english_meanings = def_row['english_meanings'].split(MEANING_DELIMITER) if def_row['english_meanings'] else []
            definition.dutch_meanings = def_row['dutch_meanings'].split(MEANING_DELIMITER) if def_row['dutch_meanings'] else []
            definition.french_meanings = def_row['french_meanings'].split(MEANING_DELIMITER) if def_row['french_meanings'] else []
            definition.german_meanings = def_row['german_meanings'].split(MEANING_DELIMITER) if def_row['german_meanings'] else []
            definition.spanish_meanings = def_row['spanish_meanings'].split(MEANING_DELIMITER) if def_row['spanish_meanings'] else []
            definition.hungarian_meanings = def_row['hungarian_meanings'].split(MEANING_DELIMITER) if def_row['hungarian_meanings'] else []
            definition.russian_meanings = def_row['russian_meanings'].split(MEANING_DELIMITER) if def_row['russian_meanings'] else []
            definition.slovenian_meanings = def_row['slovenian_meanings'].split(MEANING_DELIMITER) if def_row['slovenian_meanings'] else []
            definition.parts_of_speech = [r['pos_text'] for r in cursor.execute("SELECT pos_text FROM definition_pos WHERE definition_id = ?", (def_row['definition_id'],))]
            word.definitions.append(definition)

        self._word_cache[word_id] = word
        return word

    def lookup(self, key: str) -> List[JmDictWord]:
        """
        Looks up a term and returns a list of matching JmDictWord objects.
        """
        if not self.conn:
            self.load()
        
        cursor = self.conn.cursor()
        # Use DISTINCT to avoid fetching the same word multiple times if a key matches multiple readings
        word_id_rows = cursor.execute("SELECT DISTINCT word_id FROM lookups WHERE lookup_key = ?", (key,)).fetchall()
        
        results = []
        for row in word_id_rows:
            word = self.get_word_by_id(row['word_id'])
            if word:
                results.append(word)
        return results

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _load_entities(self, dtd_path: str):
        global _entities, _entities_rev
        if _entities:
            return

        entity_re = re.compile(r'<!ENTITY\s+([a-zA-Z0-9_-]+)\s+"([^"]+)">')
        extra_dtd_lines = [
            '<!ENTITY name-char "character">', '<!ENTITY name-company "company name">',
            '<!ENTITY name-creat "creature">', '<!ENTITY name-dei "deity">',
            '<!ENTITY name-doc "document">', '<!ENTITY name-ev "event">',
            '<!ENTITY name-fem "female given name or forename">', '<!ENTITY name-fict "fiction">',
            '<!ENTITY name-given "given name or forename, gender not specified">',
            '<!ENTITY name-group "group">', '<!ENTITY name-leg "legend">',
            '<!ENTITY name-masc "male given name or forename">', '<!ENTITY name-myth "mythology">',
            '<!ENTITY name-obj "object">', '<!ENTITY name-organization "organization name">',
            '<!ENTITY name-oth "other">', '<!ENTITY name-person "full name of a particular person">',
            '<!ENTITY name-place "place name">', '<!ENTITY name-product "product name">',
            '<!ENTITY name-relig "religion">', '<!ENTITY name-serv "service">',
            '<!ENTITY name-ship "ship name">', '<!ENTITY name-station "railway station">',
            '<!ENTITY name-surname "family or surname">', '<!ENTITY name-unclass "unclassified name">',
            '<!ENTITY name-work "work of art, literature, music, etc. name">'
        ]
        with open(dtd_path, 'r', encoding='utf-8') as f:
            all_lines = f.read().splitlines() + extra_dtd_lines

        for line in all_lines:
            match = entity_re.match(line)
            if match:
                key, value = match.groups()
                if key not in _entities:
                    _entities[key] = value
        _entities_rev = {v: k for k, v in _entities.items()}

    def _el_to_pos(self, el: str) -> str:
        return _entities_rev.get(el, el)

    def _get_word_infos(self, dictionary_path: str) -> List[JmDictWord]:
        word_infos = []
        context = ET.iterparse(dictionary_path, events=('end',))
        for _, elem in context:
            if elem.tag == 'entry':
                word_info = JmDictWord()
                seq = elem.find('ent_seq')
                if seq is not None and seq.text:
                    word_info.word_id = int(seq.text)

                for k_ele in elem.findall('k_ele'):
                    self._parse_k_ele(k_ele, word_info)
                for r_ele in elem.findall('r_ele'):
                    self._parse_r_ele(r_ele, word_info)
                for sense in elem.findall('sense'):
                    self._parse_sense(sense, word_info)

                word_info.readings = [r.replace("ゎ", "わ").replace(
                    "ヮ", "わ") for r in word_info.readings]
                word_infos.append(word_info)
                elem.clear()
        return word_infos

    def _parse_k_ele(self, k_ele_node: ET.Element, word_info: JmDictWord):
        keb = k_ele_node.find('keb')
        if keb is not None and keb.text:
            word_info.readings.append(keb.text)
            word_info.reading_types.append(JmDictReadingType.READING)
        for pri in k_ele_node.findall('ke_pri'):
            if pri.text and pri.text not in word_info.priorities:
                word_info.priorities.append(pri.text)

    def _parse_r_ele(self, r_ele_node: ET.Element, word_info: JmDictWord):
        reb_node = r_ele_node.find('reb')
        if reb_node is None or not reb_node.text:
            return
        reb = reb_node.text
        restrictions = [
            r.text for r in r_ele_node.findall('re_restr') if r.text]
        is_obsolete = any(
            inf.text == '&ok;' for inf in r_ele_node.findall('re_inf'))
        for pri in r_ele_node.findall('re_pri'):
            if pri.text and pri.text not in word_info.priorities:
                word_info.priorities.append(pri.text)
        if not restrictions or any(reading in restrictions for reading in word_info.readings):
            if is_obsolete:
                word_info.obsolete_readings.append(reb)
            else:
                word_info.readings.append(reb)
                word_info.reading_types.append(JmDictReadingType.KANA_READING)

    def _parse_sense(self, sense_node: ET.Element, word_info: JmDictWord):
        sense = JmDictDefinition(definition_id=0, word_id=word_info.word_id)
        restrictions = [r.text for r in sense_node.findall('stagr') if r.text]
        for gloss in sense_node.findall('gloss'):
            if not gloss.text:
                continue
            lang = gloss.get(
                '{http://www.w3.org/XML/1998/namespace}lang', 'eng')
            if lang == 'eng':
                sense.english_meanings.append(gloss.text)
            elif lang == 'dut':
                sense.dutch_meanings.append(gloss.text)
            elif lang == 'fre':
                sense.french_meanings.append(gloss.text)
            elif lang == 'ger':
                sense.german_meanings.append(gloss.text)
            elif lang == 'spa':
                sense.spanish_meanings.append(gloss.text)
            elif lang == 'hun':
                sense.hungarian_meanings.append(gloss.text)
            elif lang == 'rus':
                sense.russian_meanings.append(gloss.text)
            elif lang == 'slv':
                sense.slovenian_meanings.append(gloss.text)
        for pos in sense_node.findall('pos'):
            if pos.text:
                sense.parts_of_speech.append(self._el_to_pos(pos.text))
        for misc in sense_node.findall('misc'):
            if misc.text:
                sense.parts_of_speech.append(self._el_to_pos(misc.text))
        if not restrictions or any(reading in restrictions for reading in word_info.readings):
            word_info.definitions.append(sense)

    def _get_custom_words(self) -> List[JmDictWord]:
        return [
            JmDictWord(word_id=8000000, readings=["でした"], readings_furigana=["でした"], reading_types=[JmDictReadingType.KANA_READING], definitions=[
                       JmDictDefinition(definition_id=0, word_id=8000000, english_meanings=["was, were"], parts_of_speech=["exp"])]),
            JmDictWord(word_id=8000001, readings=["イクシオトキシン"], readings_furigana=["イクシオトキシン"], reading_types=[JmDictReadingType.KANA_READING], definitions=[
                       JmDictDefinition(definition_id=0, word_id=8000001, english_meanings=["ichthyotoxin"], parts_of_speech=["n"])]),
            JmDictWord(word_id=8000002, readings=["逢魔", "おうま"], readings_furigana=["逢[おう]魔[ま]", "おうま"], reading_types=[JmDictReadingType.READING, JmDictReadingType.KANA_READING], pitch_accents=[0], definitions=[JmDictDefinition(
                definition_id=0, word_id=8000002, english_meanings=["meeting with evil spirits; encounter with demons or monsters", "(esp. in compounds) reference to the supernatural or ominous happenings at twilight (逢魔が時 \"the time to meet demons\")"], parts_of_speech=["exp"])])
        ]

    def _load_furigana(self, furigana_path: str) -> Dict[str, List[JmDictFurigana]]:
        furigana_dict = defaultdict(list)
        with open(furigana_path, 'r', encoding='utf-8-sig') as f:
            for item in json.load(f):
                furi = JmDictFurigana.from_dict(item)
                furigana_dict[furi.text].append(furi)
        return furigana_dict

    def _process_words(self, word_infos: List[JmDictWord], furigana_dict: Dict[str, List[JmDictFurigana]]):
        for word in word_infos:
            lookups, seen_lookups = [], set()
            for i, r in enumerate(word.readings):
                lookup_key = wanakana.to_hiragana(
                    r, convert_long_vowel_mark=False)
                lookup_key_lv = wanakana.to_hiragana(r)
                if lookup_key not in seen_lookups:
                    lookups.append(JmDictLookup(word.word_id, lookup_key))
                    seen_lookups.add(lookup_key)
                if lookup_key_lv != lookup_key and lookup_key_lv not in seen_lookups:
                    lookups.append(JmDictLookup(word.word_id, lookup_key_lv))
                    seen_lookups.add(lookup_key_lv)
                if wanakana.is_katakana(r) and r not in seen_lookups:
                    lookups.append(JmDictLookup(word.word_id, r))
                    seen_lookups.add(r)

                furi_reading = None
                if len(r) == 1 and wanakana.is_kanji(r):
                    kana = next((rd for j, rd in enumerate(
                        word.readings) if word.reading_types[j] == JmDictReadingType.KANA_READING), None)
                    if kana:
                        furi_reading = f"{r}[{kana}]"
                elif r in furigana_dict:
                    furi_reading = next(
                        (f.parse() for f in furigana_dict[r] if f.reading in word.readings), None)
                word.readings_furigana.append(furi_reading or r)

            word.parts_of_speech = sorted(
                list({pos for d in word.definitions for pos in d.parts_of_speech}))
            word.lookups = lookups

    def _apply_custom_priorities(self, word_infos: List[JmDictWord]):
        word_map = {w.word_id: w for w in word_infos}
        custom_ids = [1332650, 2848543, 1160790, 1203260, 1397260, 1499720, 1315130, 1191730, 2844190, 2207630, 1442490, 1423310, 1502390, 1343100, 1610040, 2059630, 1495580,
                      1288850, 1392580, 1511350, 1648450, 1534790, 2105530, 1223615, 1421850, 1020650, 1310640, 1495770, 1375610, 1605840, 1334590, 1609980, 1579260, 1351580, 2820490, 1983760]
        for word_id in custom_ids:
            if word_id in word_map:
                word_map[word_id].priorities.append("jiten")
        if 2029110 in word_map:
            word_map[2029110].definitions.append(JmDictDefinition(definition_id=0, word_id=2029110, parts_of_speech=[
                                                 "prt"], english_meanings=["indicates na-adjective"]))

    def _import_jmnedict(self, jmnedict_path: str, existing_readings: set) -> List[JmDictWord]:
        names_by_key = {}
        context = ET.iterparse(jmnedict_path, events=('end',))
        for _, elem in context:
            if elem.tag == 'entry':
                entry = JmDictWord()
                primary_key = None
                seq = elem.find('ent_seq')
                entry.word_id = int(
                    seq.text) if seq is not None and seq.text else 0
                for k_ele in elem.findall('k_ele'):
                    self._parse_k_ele(k_ele, entry)
                    if primary_key is None and entry.readings:
                        primary_key = entry.readings[0]
                for r_ele in elem.findall('r_ele'):
                    self._parse_r_ele(r_ele, entry)
                for trans in elem.findall('trans'):
                    self._parse_name_trans(trans, entry)
                entry.readings = [r.replace("ゎ", "わ").replace(
                    "ヮ", "わ") for r in entry.readings]
                if any(r in existing_readings for r in entry.readings):
                    elem.clear()
                    continue
                if primary_key is None and entry.readings:
                    primary_key = entry.readings[0]
                if primary_key:
                    if primary_key in names_by_key:
                        self._merge_name_entries(
                            names_by_key[primary_key], entry)
                    else:
                        names_by_key[primary_key] = entry
                elem.clear()
        name_words = list(names_by_key.values())
        for word in name_words:
            word.priorities.append("name")
        return name_words

    def _parse_name_trans(self, trans_node: ET.Element, word_info: JmDictWord):
        definition = JmDictDefinition(
            definition_id=0, word_id=word_info.word_id)
        for name_type in trans_node.findall('name_type'):
            if name_type.text:
                definition.parts_of_speech.append(
                    self._el_to_pos(name_type.text))
        for trans_det in trans_node.findall('trans_det'):
            if trans_det.text:
                definition.english_meanings.append(trans_det.text)
        if not definition.parts_of_speech:
            definition.parts_of_speech.append("name")
        if definition.english_meanings:
            word_info.definitions.append(definition)

    def _merge_name_entries(self, target: JmDictWord, source: JmDictWord):
        for i, reading in enumerate(source.readings):
            if reading not in target.readings:
                target.readings.append(reading)
                target.reading_types.append(source.reading_types[i])
        target.definitions.extend(source.definitions)
        if source.priorities:
            for p in source.priorities:
                if p not in target.priorities:
                    target.priorities.append(p)

    def _import_pitch_accents(self, words: Dict[int, JmDictWord], pitch_accent_dir: str):
        if not os.path.isdir(pitch_accent_dir):
            return
        pitch_dict = {}
        for fname in os.listdir(pitch_accent_dir):
            if fname.startswith("term_meta_bank_") and fname.endswith(".json"):
                with open(os.path.join(pitch_accent_dir, fname), 'r', encoding='utf-8') as f:
                    for item in json.load(f):
                        if item[0] and item[0] not in pitch_dict:
                            pitch_dict[item[0]] = [p['position'] for p in item[2].get('pitches', [])]
        for word in words.values():
            for reading in word.readings:
                if reading in pitch_dict:
                    word.pitch_accents = pitch_dict[reading]
                    break

    def _import_vocabulary_origin(self, words: Dict[int, JmDictWord], origin_path: str):
        if not os.path.isfile(origin_path):
            return
        origin_map = {}
        with open(origin_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                word, origin_char = row[0], row[1].strip()
                if origin_char == '和':
                    origin = WordOrigin.WAGO
                elif origin_char == '漢':
                    origin = WordOrigin.KANGO
                elif origin_char == '外':
                    origin = WordOrigin.GAIRAIGO
                else:
                    origin = WordOrigin.UNKNOWN
                origin_map[word] = origin
        for word in words.values():
            match = next((r for i, r in enumerate(word.readings) if r in origin_map and word.reading_types[i] == JmDictReadingType.READING), None)
            if match is None:
                match = next((r for r in word.readings if r in origin_map), None)
            if match:
                word.origin = origin_map[match]

def to_human_readable_parts_of_speech(pos_list: List[str]) -> List[str]:
    """Converts part-of-speech codes to human-readable strings."""
    return [_POS_DICTIONARY.get(p, p) for p in pos_list]