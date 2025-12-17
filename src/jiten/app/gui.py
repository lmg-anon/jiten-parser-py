import sys
import html
import re
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

        self.kanji_label = QLabel("")
        self.kanji_label.setTextFormat(Qt.TextFormat.RichText)
        self.kanji_label.setStyleSheet("color: #6699cc;")

        self.meanings_browser = QTextBrowser()
        self.meanings_browser.setStyleSheet("""
            QTextBrowser { background-color: transparent; border: none; color: #a9b7c6; font-size: 11pt; }
        """)

        layout.addWidget(self.conjugation_label)
        layout.addWidget(self.kanji_label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.meanings_browser)
        
        self.clear()

    def clear(self):
        self.conjugation_label.hide()
        self.kanji_label.setText("Select a word to see details")
        self.meanings_browser.setHtml("")

    def update_details(self, parsed_word: DeckWord, jmdict_word: JmDictWord):
        if not parsed_word or not jmdict_word:
            self.clear()
            return

        conjugations = [c for c in parsed_word.conjugations if c and not c.startswith("(")]
        if conjugations:
            self.conjugation_label.setText(f"(Conjugation: {' ; '.join(conjugations)})")
            self.conjugation_label.show()
        else:
            self.conjugation_label.hide()

        kanji_form = jmdict_word.readings[parsed_word.reading_index]
        raw_furi = ""
        if len(jmdict_word.readings_furigana) > parsed_word.reading_index:
            raw_furi = jmdict_word.readings_furigana[parsed_word.reading_index]

        s_furi = "font-size: 12pt; color: #a9b7c6; text-align: center;"
        s_kanji = "font-size: 36pt; font-weight: bold; color: #6699cc;"
        s_empty = "font-size: 12pt;"

        if raw_furi and '[' in raw_furi:
            pattern = re.compile(r'([\u4e00-\u9fafヶ々]+)\[([^\]]+)\]')
            td_top = ""
            td_bot = ""
            last_pos = 0
            
            for match in pattern.finditer(raw_furi):
                pre = raw_furi[last_pos:match.start()]
                if pre:
                    td_top += f"<td style='{s_empty}'></td>"
                    td_bot += f"<td style='{s_kanji}'>{html.escape(pre)}</td>"
                
                td_top += f"<td style='{s_furi}'>{html.escape(match.group(2))}</td>"
                td_bot += f"<td style='{s_kanji}'>{html.escape(match.group(1))}</td>"
                last_pos = match.end()
            
            if last_pos < len(raw_furi):
                post = raw_furi[last_pos:]
                td_top += f"<td style='{s_empty}'></td>"
                td_bot += f"<td style='{s_kanji}'>{html.escape(post)}</td>"

            self.kanji_label.setText(f"<table cellspacing='0'><tr>{td_top}</tr><tr>{td_bot}</tr></table>")
        elif raw_furi and raw_furi != kanji_form:
            self.kanji_label.setText(f"<table cellspacing='0'><tr><td style='{s_furi}'>{html.escape(raw_furi)}</td></tr><tr><td style='{s_kanji}'>{html.escape(kanji_form)}</td></tr></table>")
        else:
            self.kanji_label.setText(f"<span style='{s_kanji}'>{html.escape(kanji_form)}</span>")

        out_html = "<b>Meanings</b><br><br>"
        for i, definition in enumerate(jmdict_word.definitions):
            if not definition.english_meanings:
                break
            pos_list = to_human_readable_parts_of_speech(definition.parts_of_speech)
            pos_str = f"<font color='#6a8759'><i>({', '.join(pos_list)})</i></font>" if pos_list else ""
            out_html += f"<b>Sense {i+1}</b> {pos_str}"
            for j, meaning in enumerate(definition.english_meanings):
                out_html += f"<div>{j+1}. {html.escape(meaning)}</div>"
            out_html += "<br><br>"
        self.meanings_browser.setHtml(out_html)

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
        text = self.input_field.text().replace("\u3000", " ").strip()
        if not text:
            return

        for label in self.word_labels:
            label.deleteLater()
        self.word_labels.clear()
        self.details_pane.clear()

        sentences_info = Parser._morphological_analyser.parse(text, morphemes_only=False)

        tokens = [w[0] for sent in sentences_info for w in sent.words]
        cursor = 0
        text_len = len(text)

        for word_info in tokens:
            token_text = word_info.text
            if not token_text.strip(): continue

            # 1. Exact match at cursor
            if cursor < text_len and text.startswith(token_text, cursor):
                self._add_token(token_text, word_info)
                cursor += len(token_text)
            else:
                # 2. Lookahead (handle skipped spaces/symbols)
                try:
                    found_idx = text.find(token_text, cursor, min(text_len, cursor + 20))
                    if found_idx != -1:
                        self._add_label(text[cursor:found_idx], None) # Add gap
                        self._add_token(token_text, word_info)
                        cursor = found_idx + len(token_text)
                except ValueError: pass

        if cursor < text_len:
            self._add_label(text[cursor:], None)

        # Auto-select first word
        first = next((l for l in self.word_labels if l.is_selectable), None)
        if first: self.on_word_selected(first.deck_word)

    def _add_token(self, text, word_info):
        deck_word = None
        if word_info.part_of_speech:
            deck_word = Parser._process_word(word_info)
        
        # Filter out punctuation/symbols from being clickable
        ignored = {'BLANK_SPACE', 'SUPPLEMENTARY_SYMBOL', 'PUNCTUATION'}
        pos_str = str(word_info.part_of_speech).upper() if word_info.part_of_speech else ""
        
        if pos_str in ignored:
            deck_word = None

        self._add_label(text, deck_word)

    def _add_label(self, text, deck_word):
        label = WordLabel(text, deck_word)
        label.setFont(QFont("Meiryo", 14))
        if deck_word:
            label.wordClicked.connect(self.on_word_selected)
        self.sentence_layout.addWidget(label)
        self.word_labels.append(label)

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