import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QLabel, QTextBrowser, QFrame
)
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtCore import Qt, Signal

from jiten.parser import Parser, DeckWord
from jiten.jmdict.jmdict import JmDict, to_human_readable_parts_of_speech
from jiten.jmdict.jmdict_word import JmDictWord

class WordLabel(QLabel):
    wordClicked = Signal(object)

    def __init__(self, text, deck_word, parent=None):
        super().__init__(text, parent)
        self.deck_word = deck_word
        self.is_selectable = deck_word is not None
        self.is_selected = False
        
        if self.is_selectable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setStyleSheet("QLabel { color: #a9b7c6; }")
        else:
            self.setStyleSheet("QLabel { color: #808080; }")

    def mousePressEvent(self, event):
        if self.is_selectable:
            self.wordClicked.emit(self.deck_word)
        super().mousePressEvent(event)

    def select(self):
        if not self.is_selectable:
            return
        self.is_selected = True
        self.setStyleSheet("QLabel { color: #d8a6ff; text-decoration: underline; }")

    def deselect(self):
        if not self.is_selectable:
            return
        self.is_selected = False
        self.setStyleSheet("QLabel { color: #a9b7c6; text-decoration: none; }")

class DetailsPane(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        self.conjugation_label = QLabel("")
        self.conjugation_label.setStyleSheet("color: #808080; font-style: italic;")
        
        self.reading_label = QLabel("")
        self.reading_label.setFont(QFont("Meiryo", 12))
        self.reading_label.setStyleSheet("color: #a9b7c6;")

        self.kanji_label = QLabel("")
        self.kanji_label.setFont(QFont("Meiryo", 36, QFont.Weight.Bold))
        self.kanji_label.setStyleSheet("color: #6699cc;")

        self.meanings_browser = QTextBrowser()
        self.meanings_browser.setStyleSheet("""
            QTextBrowser { background-color: transparent; border: none; color: #a9b7c6; font-size: 11pt; }
        """)

        layout.addWidget(self.conjugation_label)
        layout.addWidget(self.reading_label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.kanji_label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.meanings_browser)
        
        self.clear()

    def clear(self):
        self.conjugation_label.hide()
        self.reading_label.setText("")
        self.kanji_label.setText("Select a word to see details")
        self.meanings_browser.setHtml("")

    def update_details(self, parsed_word: DeckWord, jmdict_word: JmDictWord):
        if not parsed_word or not jmdict_word:
            self.clear()
            return

        if parsed_word.conjugations:
            conj_path = " ; ".join(parsed_word.conjugations)
            self.conjugation_label.setText(f"(Conjugation: {conj_path})")
            self.conjugation_label.show()
        else:
            self.conjugation_label.hide()

        kanji_form = jmdict_word.readings[parsed_word.reading_index]
        reading_form = ""

        # Deconjugate the kanji form ONCE to get its base form safely
        kanji_decon_set = Parser._deconjugator.deconjugate(kanji_form)
        base_kanji_form = next(iter(kanji_decon_set)).text if kanji_decon_set else None

        # Now iterate through readings to find a matching base form
        if base_kanji_form:
            for r, rt in zip(jmdict_word.readings, jmdict_word.reading_types):
                if rt.name == 'KANA_READING':
                    kana_decon_set = Parser._deconjugator.deconjugate(r)
                    if kana_decon_set:
                        base_kana_form = next(iter(kana_decon_set)).text
                        if base_kana_form == base_kanji_form:
                            reading_form = r  # Found the matching kana reading
                            break

        # Fallback logic if we didn't find a match or couldn't deconjugate
        if not reading_form and len(jmdict_word.readings_furigana) > parsed_word.reading_index:
             reading_form = jmdict_word.readings_furigana[parsed_word.reading_index].replace('[', ' ').replace(']', '')

        self.reading_label.setText(reading_form)
        self.kanji_label.setText(kanji_form)

        html = "<b>Meanings</b><br><br>"
        for i, definition in enumerate(jmdict_word.definitions):
            if not definition.english_meanings:
                break
            pos_list = to_human_readable_parts_of_speech(definition.parts_of_speech)
            pos_str = f"<font color='#6a8759'><i>({', '.join(pos_list)})</i></font>" if pos_list else ""
            html += f"<b>Sense {i+1}</b> {pos_str}"
            for j, meaning in enumerate(definition.english_meanings):
                html += f"<div>{j+1}. {meaning}</div>"
            html += "<br><br>"
        self.meanings_browser.setHtml(html)

class MainWindow(QMainWindow):
    def __init__(self, jmdict_instance: JmDict):
        super().__init__()
        self.jmdict = jmdict_instance
        self.word_labels = []
        self.setWindowTitle("Jiten Parser GUI")
        self.setGeometry(100, 100, 800, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter a Japanese sentence and press Enter...")
        self.input_field.setFont(QFont("Meiryo", 12))
        self.input_field.returnPressed.connect(self.process_sentence)
        main_layout.addWidget(self.input_field)
        self.sentence_container = QWidget()
        self.sentence_layout = QHBoxLayout(self.sentence_container)
        self.sentence_layout.setContentsMargins(5, 5, 5, 5)
        self.sentence_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(self.sentence_container)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)
        self.details_pane = DetailsPane()
        main_layout.addWidget(self.details_pane, stretch=1)

    def process_sentence(self):
        text = self.input_field.text().strip().replace(" ", "")
        if not text:
            return

        for label in self.word_labels:
            label.deleteLater()
        self.word_labels.clear()
        self.details_pane.clear()

        sentences_info = Parser._morphological_analyser.parse(text, morphemes_only=False)

        flat = [w for sent in sentences_info for w in sent.words]
        flat.sort(key=lambda t: (t[1], -t[2]))

        words_with_pos = []
        consumed_end = 0
        for wi, start, length in flat:
            if start >= consumed_end:
                words_with_pos.append((wi, start, length))
                consumed_end = start + length

        processed_words = [
            Parser._process_word(wi) if wi.part_of_speech else None
            for (wi, _, _) in words_with_pos
        ]

        current_index = 0
        for i, (word_info, start_index, length) in enumerate(words_with_pos):
            if start_index < current_index:
                continue

            deck_word = processed_words[i]

            if start_index > current_index:
                gap_text = text[current_index:start_index]
                gap_label = WordLabel(gap_text, None)
                gap_label.setFont(QFont("Meiryo", 14))
                self.sentence_layout.addWidget(gap_label)
                self.word_labels.append(gap_label)

            word_text = text[start_index:start_index + length]
            word_label = WordLabel(word_text, deck_word)
            word_label.setFont(QFont("Meiryo", 14))
            if deck_word:
                word_label.wordClicked.connect(self.on_word_selected)
            self.sentence_layout.addWidget(word_label)
            self.word_labels.append(word_label)

            current_index = start_index + length

        if current_index < len(text):
            trailing_text = text[current_index:]
            trailing_label = WordLabel(trailing_text, None)
            trailing_label.setFont(QFont("Meiryo", 14))
            self.sentence_layout.addWidget(trailing_label)
            self.word_labels.append(trailing_label)

        first_word = next((w for w in processed_words if w), None)
        if first_word:
            self.on_word_selected(first_word)

    def on_word_selected(self, parsed_word: DeckWord):
        for label in self.word_labels:
            if label.deck_word != parsed_word:
                label.deselect()
            else:
                label.select()
        jmdict_word = self.jmdict.get_word_by_id(parsed_word.word_id)
        self.details_pane.update_details(parsed_word, jmdict_word)


def set_dark_theme(app: QApplication):
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(55, 55, 55))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
    dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(66, 150, 255))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(66, 150, 255))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(dark_palette)


def main():
    app = QApplication(sys.argv)
    set_dark_theme(app)
    jmdict = JmDict()
    try:
        Parser._ensure_initialized()
        jmdict.load()
        window = MainWindow(jmdict_instance=jmdict)
        window.show()
        app.exec()
    except Exception as e:
        print(f"FATAL ERROR: Could not initialize application. {e}")
    finally:
        jmdict.close()
        sys.exit()


if __name__ == "__main__":
    main()