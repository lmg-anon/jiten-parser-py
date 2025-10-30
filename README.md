# Jiten-Parser-Py

A Python port of the [Jiten's Parser library](https://github.com/Sirush/Jiten) (commit: [2e3588f8](https://github.com/Sirush/Jiten/commit/2e3588f838fb1865c96c70ec9e83f46cc40db090)) for Japanese text segmentation.

## Installation

Requires Python 3.8+.

```bash
pip install git+https://github.com/lmg-anon/jiten-parser-py.git
python -m jiten.setup_deps
```

## Usage

```python
from jiten.parser import Parser
from jiten.jmdict.jmdict import JmDict

jmdict = JmDict()

text = "美少女がアニメを見ている。"
parsed_words = Parser.parse_text(text)

for word in parsed_words:
    entry = jmdict.get_word_by_id(word.word_id)
    if entry:
        dictionary_form = entry.readings[word.reading_index]
        meanings = entry.definitions[0].english_meanings if entry.definitions else []
        print(f"'{word.original_text}' -> {dictionary_form} | {meanings[:2]}")
```
**Output:**
```
'美少女' -> 美少女 | ['beautiful girl']
'が' -> が | ['indicates the subject of a sentence']
'アニメ' -> アニメ | ['animation', 'animated film']
'を' -> を | ['indicates direct object of action']
'見ている' -> 見る | ['to see', 'to look']
```

## Interactive GUI Example

The repository includes a simple GUI that mimics Jiten's website.

<img width="795" height="629" alt="image" src="https://github.com/user-attachments/assets/56f95fe7-00e8-4e02-ba27-da802e6fe77b" />

To run it, first install the additional dependencies:
```bash
pip install "jiten-parser[gui] @ git+https://github.com/lmg-anon/jiten-parser-py.git"
```

Then run using this command:
```bash
python -m jiten.app.gui
```

## License & Acknowledgements

This project is licensed under the Apacha-2.0 License.

This project is a port and utilizes resources from the following projects:
*   **[Jiten's Parser](https://github.com/Sirush/Jiten)** by **Sirush**: The original C# library, deconjugation rules, and data resources.
*   **[Sudachi](https://github.com/WorksApplications/sudachi.rs)**: The Japanese morphological analyzer.
*   **[EDRDG](http://www.edrdg.org/)**: The [JMDict](http://www.edrdg.org/jmdict/j_jmdict.html) and JMnedict dictionary files, used in conformance with the Group's [licence](http://www.edrdg.org/edrdg/licence.html).
