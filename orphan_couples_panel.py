r"""
Panneau pour rechercher les couplages orphelins : délimiteurs en paire
dont un seul des deux apparaît (ex. * sans son *, \> sans \<).
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QListWidget, QListWidgetItem,
                              QGroupBox, QFormLayout, QComboBox, QFrame)


# Paires prédéfinies : (libellé, ouvrant, fermant)
PRESET_PAIRS = [
    ("* (italique/gras)", "*", "*"),
    ("** (gras)", "**", "**"),
    ("_ (souligné)", "_", "_"),
    (r"\> … \< (guillemets)", "\\>", "\\<"),
    ("[ … ] (crochets)", "[", "]"),
    ("( … ) (parenthèses)", "(", ")"),
]


def _find_all_positions(text: str, needle: str):
    """Retourne la liste des (début, fin, numéro_ligne) pour chaque occurrence de needle dans text."""
    if not needle:
        return []
    result = []
    line = 1
    col = 0
    start = 0
    while True:
        pos = text.find(needle, start)
        if pos < 0:
            break
        # Compter la ligne jusqu'à pos
        line_start = text.rfind('\n', 0, pos)
        if line_start < 0:
            line_start = 0
        line = text.count('\n', 0, pos) + 1
        col = pos - line_start
        result.append((pos, pos + len(needle), line, col))
        start = pos + 1
    return result


def _line_snippet(text: str, position: int, max_len: int = 60) -> str:
    """Retourne un extrait de la ligne contenant position."""
    line_start = text.rfind('\n', 0, position)
    if line_start < 0:
        line_start = 0
    else:
        line_start += 1
    line_end = text.find('\n', position)
    if line_end < 0:
        line_end = len(text)
    line = text[line_start:line_end].strip()
    if len(line) > max_len:
        line = line[:max_len] + "…"
    return line


def find_orphans(text: str, open_str: str, close_str: str):
    """
    Trouve les délimiteurs orphelins (ouvrant sans fermant, ou fermant sans ouvrant).
    Retourne une liste de dict: {'type': 'ouvrant'|'fermant', 'line': int, 'col': int, 'snippet': str}
    """
    if not open_str and not close_str:
        return []
    opens = _find_all_positions(text, open_str) if open_str else []
    closes = _find_all_positions(text, close_str) if close_str else []

    orphans = []
    same = (open_str == close_str)

    if same:
        # Même délimiteur : apparier 1-2, 3-4, ... ; le reste est orphelin
        all_pos = sorted(opens, key=lambda x: x[0])
        i = 0
        while i < len(all_pos):
            if i + 1 < len(all_pos):
                i += 2  # paire ok
            else:
                start, end, line, col = all_pos[i]
                snippet = _line_snippet(text, start)
                orphans.append({
                    'type': 'orphelin',
                    'line': line,
                    'col': col,
                    'snippet': snippet,
                    'delim': open_str
                })
                i += 1
    else:
        # Ouvrant et fermant différents : parcours par position, pile d'ouvrants
        events = []
        for (pos, end, line, col) in opens:
            events.append((pos, 'open', line, col))
        for (pos, end, line, col) in closes:
            events.append((pos, 'close', line, col))
        events.sort(key=lambda x: x[0])

        stack = []
        for pos, kind, line, col in events:
            if kind == 'open':
                stack.append((line, col, pos))
            else:
                if stack:
                    stack.pop()
                else:
                    snippet = _line_snippet(text, pos)
                    orphans.append({
                        'type': 'fermant',
                        'line': line,
                        'col': col,
                        'snippet': snippet,
                        'delim': close_str
                    })
        for line, col, pos in stack:
            snippet = _line_snippet(text, pos)
            orphans.append({
                'type': 'ouvrant',
                'line': line,
                'col': col,
                'snippet': snippet,
                'delim': open_str
            })
    return orphans


class OrphanCouplesPanel(QFrame):
    """Panneau affiché en bas pour rechercher les couplages orphelins."""

    goToLineRequested = pyqtSignal(int, int)  # line, col (page courante)
    goToPageLineRequested = pyqtSignal(int, int, int)  # page_num, line, col (toutes les pages)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        self._orphans_data = []  # liste des dict pour l'élément sélectionné

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        # Choix de la paire
        pair_group = QGroupBox("Paire à rechercher")
        pair_layout = QFormLayout()
        self.preset_combo = QComboBox()
        for label, _o, _c in PRESET_PAIRS:
            self.preset_combo.addItem(label)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        pair_layout.addRow("Prédéfini:", self.preset_combo)

        custom_layout = QHBoxLayout()
        self.open_edit = QLineEdit()
        self.open_edit.setPlaceholderText("Ouvrant (ex. * ou \\>)")
        self.open_edit.setMaximumWidth(120)
        self.close_edit = QLineEdit()
        self.close_edit.setPlaceholderText("Fermant (ex. * ou \\<)")
        self.close_edit.setMaximumWidth(120)
        custom_layout.addWidget(QLabel("Ouvert:"))
        custom_layout.addWidget(self.open_edit)
        custom_layout.addWidget(QLabel("Fermé:"))
        custom_layout.addWidget(self.close_edit)
        pair_layout.addRow("Personnalisé:", custom_layout)

        btn_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("Analyser la page courante")
        self.analyze_btn.clicked.connect(self._analyze_current)
        self.analyze_all_btn = QPushButton("Analyser toutes les pages")
        self.analyze_all_btn.clicked.connect(self._analyze_all)
        btn_layout.addWidget(self.analyze_btn)
        btn_layout.addWidget(self.analyze_all_btn)
        btn_layout.addStretch()
        pair_layout.addRow("", btn_layout)

        pair_group.setLayout(pair_layout)
        layout.addWidget(pair_group)

        # Résultats
        result_group = QGroupBox("Occurrences orphelines")
        result_layout = QVBoxLayout()
        self.result_list = QListWidget()
        self.result_list.setMaximumHeight(180)
        self.result_list.itemDoubleClicked.connect(self._on_result_double_clicked)
        result_layout.addWidget(self.result_list)
        self.result_label = QLabel("Choisir une paire et cliquer sur Analyser.")
        result_layout.addWidget(self.result_label)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

        # Initialiser avec la première paire prédéfinie
        self._on_preset_changed(0)

    def _on_preset_changed(self, index: int):
        if 0 <= index < len(PRESET_PAIRS):
            label, o, c = PRESET_PAIRS[index]
            self.open_edit.setText(o)
            self.close_edit.setText(c)

    def _get_open_close(self) -> tuple:
        return self.open_edit.text().strip(), self.close_edit.text().strip()

    def set_content_callback(self, callback):
        """Définit une fonction sans argument qui retourne le texte à analyser (page courante)."""
        self._content_callback = callback

    def _get_content(self) -> str:
        if hasattr(self, '_content_callback') and self._content_callback:
            return self._content_callback() or ""
        return ""

    def set_all_pages_callback(self, callback):
        """Définit une fonction sans argument qui retourne une liste de (page_num, texte)."""
        self._all_pages_callback = callback

    def _get_all_pages(self) -> list:
        """Retourne [(page_num, text), ...] ou [] si non disponible."""
        if hasattr(self, '_all_pages_callback') and self._all_pages_callback:
            return self._all_pages_callback() or []
        return []

    def _analyze_current(self):
        text = self._get_content()
        open_s, close_s = self._get_open_close()
        if not open_s and not close_s:
            self.result_list.clear()
            self.result_label.setText("Indiquez au moins un délimiteur ouvrant ou fermant.")
            self._orphans_data = []
            return
        self._orphans_data = find_orphans(text, open_s, close_s)
        for o in self._orphans_data:
            o['page'] = 0  # 0 = page courante
        self._refresh_result_list()

    def _analyze_all(self):
        pages = self._get_all_pages()
        open_s, close_s = self._get_open_close()
        if not open_s and not close_s:
            self.result_list.clear()
            self.result_label.setText("Indiquez au moins un délimiteur ouvrant ou fermant.")
            self._orphans_data = []
            return
        if not pages:
            self.result_list.clear()
            self.result_label.setText("Aucun dossier Markdown chargé ou aucune page disponible.")
            self._orphans_data = []
            return
        self._orphans_data = []
        for page_num, text in pages:
            for o in find_orphans(text, open_s, close_s):
                o['page'] = page_num
                self._orphans_data.append(o)
        self._refresh_result_list()

    def _refresh_result_list(self):
        self.result_list.clear()
        type_label = {"ouvrant": "Ouvrant orphelin", "fermant": "Fermant orphelin", "orphelin": "Orphelin"}
        for o in self._orphans_data:
            page_prefix = f"Page {o['page']}, " if o.get('page', 0) else ""  # 0 = page courante
            label = f"{page_prefix}L{o['line']} col {o['col']}: {type_label.get(o['type'], o['type'])} — {o['snippet']}"
            item = QListWidgetItem(label)
            self.result_list.addItem(item)
        if not self._orphans_data:
            self.result_label.setText("Aucun couplage orphelin trouvé.")
        else:
            self.result_label.setText(f"{len(self._orphans_data)} occurrence(s) orpheline(s). Double-clic pour aller à l'emplacement.")

    def _on_result_double_clicked(self, item: QListWidgetItem):
        row = self.result_list.row(item)
        if 0 <= row < len(self._orphans_data):
            o = self._orphans_data[row]
            page = o.get('page', 0)
            if page:
                self.goToPageLineRequested.emit(page, o['line'], o['col'])
            else:
                self.goToLineRequested.emit(o['line'], o['col'])
