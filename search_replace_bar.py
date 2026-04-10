"""
Barre de recherche/remplacement intégrée dans la fenêtre principale
"""

import re
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QCheckBox, QMessageBox,
                            QPlainTextEdit, QComboBox)


class SearchReplaceBar(QWidget):
    """Barre de recherche/remplacement intégrée"""
    
    matchFound = pyqtSignal(int, int, int)  # page_num, start_pos, end_pos
    replaceRequested = pyqtSignal(int, int, int, str)  # page_num, start_pos, end_pos, replace_text
    replaceAllRequested = pyqtSignal(str, str, bool)  # search_text, replace_text, is_regex
    
    def __init__(self, file_pattern, parent=None):
        super().__init__(parent)
        self.file_pattern = file_pattern
        self.current_search_index = 0
        self.search_results = []  # Liste de dicts avec page, file_path, matches, content
        self.current_match = None  # (result_index, match_index)
        
        self.setVisible(False)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Ligne principale
        main_layout = QHBoxLayout()
        
        # Recherche
        main_layout.addWidget(QLabel("Rechercher:"))
        # Utiliser QPlainTextEdit pour permettre les sauts de ligne et espaces
        self.search_edit = QPlainTextEdit()
        self.search_edit.setMaximumHeight(50)  # Permettre quelques lignes
        self.search_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.search_edit.setToolTip("Texte ou expression régulière\nLes espaces et sauts de ligne sont pris en compte")
        # Créer un conteneur pour le QPlainTextEdit
        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.addWidget(self.search_edit)
        main_layout.addWidget(search_container)
        
        # Options
        self.regex_checkbox = QCheckBox("Regex")
        main_layout.addWidget(self.regex_checkbox)
        
        # Boutons de recherche
        self.search_button = QPushButton("Rechercher")
        self.search_button.clicked.connect(self._search_all)
        main_layout.addWidget(self.search_button)
        
        self.next_button = QPushButton("Suivant")
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self._search_next)
        main_layout.addWidget(self.next_button)
        
        self.previous_button = QPushButton("Précédent")
        self.previous_button.setEnabled(False)
        self.previous_button.clicked.connect(self._search_previous)
        main_layout.addWidget(self.previous_button)
        
        # Séparateur (widget vide avec espace fixe)
        separator = QWidget()
        separator.setFixedWidth(20)
        main_layout.addWidget(separator)
        
        # Remplacement
        main_layout.addWidget(QLabel("Remplacer:"))
        # Utiliser QPlainTextEdit pour permettre les sauts de ligne
        self.replace_edit = QPlainTextEdit()
        self.replace_edit.setMaximumHeight(50)  # Permettre quelques lignes
        self.replace_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.replace_edit.setPlaceholderText("Texte de remplacement (\\n pour saut de ligne, \\g<1> pour groupes regex)")
        # Note: QPlainTextEdit ne supporte pas vraiment placeholderText en PyQt6,
        # mais on peut mettre un tooltip
        self.replace_edit.setToolTip("Texte de remplacement\nUtilisez \\n pour un saut de ligne\nEn mode regex, utilisez \\g<1>, \\g<2> pour référencer les groupes")
        # Créer un conteneur pour le QPlainTextEdit
        replace_container = QWidget()
        replace_layout = QVBoxLayout(replace_container)
        replace_layout.setContentsMargins(0, 0, 0, 0)
        replace_layout.addWidget(self.replace_edit)
        main_layout.addWidget(replace_container)
        
        self.replace_button = QPushButton("Remplacer")
        self.replace_button.setEnabled(False)
        self.replace_button.clicked.connect(self._replace_current)
        main_layout.addWidget(self.replace_button)
        
        self.replace_all_button = QPushButton("Tout remplacer")
        self.replace_all_button.setEnabled(False)
        self.replace_all_button.clicked.connect(self._replace_all)
        main_layout.addWidget(self.replace_all_button)
        
        # Info et fermer
        self.info_label = QLabel("")
        self.info_label.setMinimumWidth(200)
        main_layout.addWidget(self.info_label)
        
        close_button = QPushButton("✕")
        close_button.setMaximumWidth(30)
        close_button.setToolTip("Fermer la barre de recherche")
        close_button.clicked.connect(self.hide)
        main_layout.addWidget(close_button)
        
        layout.addLayout(main_layout)
    
    def showEvent(self, event):
        """Quand la barre est affichée, focus sur le champ de recherche"""
        super().showEvent(event)
        self.search_edit.setFocus()
        # Sélectionner tout le texte pour QPlainTextEdit
        cursor = self.search_edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        self.search_edit.setTextCursor(cursor)
    
    def _search_all(self):
        """Recherche dans tous les fichiers Markdown"""
        # Préserver les espaces et sauts de ligne significatifs
        # Enlever seulement les sauts de ligne en début/fin, pas les espaces
        search_text = self.search_edit.toPlainText()
        # Enlever uniquement les sauts de ligne en début/fin
        search_text = search_text.strip('\n\r')
        if not search_text.strip():
            self.info_label.setText("Entrez un texte à rechercher")
            return
        
        self.search_results = []
        self.current_search_index = 0
        self.current_match = None
        is_regex = self.regex_checkbox.isChecked()
        
        total_pages = self.file_pattern.get_total_pages()
        if total_pages == 0:
            self.info_label.setText("Aucun fichier Markdown trouvé")
            return
        
        # Compiler le pattern regex
        try:
            if is_regex:
                pattern = re.compile(search_text)
            else:
                pattern = re.compile(re.escape(search_text))
        except re.error as e:
            self.info_label.setText(f"Erreur regex: {e}")
            return
        
        # Rechercher dans tous les fichiers
        matches_count = 0
        files_with_matches = 0
        
        for page_num in range(1, total_pages + 1):
            file_path = self.file_pattern.get_filepath(page_num)
            if not file_path or not file_path.exists():
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                matches = list(pattern.finditer(content))
                if matches:
                    self.search_results.append({
                        'page': page_num,
                        'file_path': file_path,
                        'matches': matches,
                        'content': content,
                        'search_text': search_text,
                        'is_regex': is_regex
                    })
                    matches_count += len(matches)
                    files_with_matches += 1
            except Exception as e:
                print(f"Erreur lors de la lecture de {file_path}: {e}")
        
        # Afficher les résultats
        if matches_count > 0:
            self.info_label.setText(f"{matches_count} occurrence(s) dans {files_with_matches} fichier(s)")
            self.next_button.setEnabled(True)
            self.previous_button.setEnabled(True)
            self.replace_button.setEnabled(True)
            self.replace_all_button.setEnabled(True)
            self._go_to_match(0, 0)  # Aller à la première occurrence
        else:
            self.info_label.setText("Aucune occurrence trouvée")
            self.next_button.setEnabled(False)
            self.previous_button.setEnabled(False)
            self.replace_button.setEnabled(False)
            self.replace_all_button.setEnabled(False)
    
    def _get_total_matches(self):
        """Retourne le nombre total d'occurrences"""
        return sum(len(r['matches']) for r in self.search_results)
    
    def _go_to_match(self, result_index: int, match_index: int):
        """Va à un match spécifique"""
        if not self.search_results or result_index >= len(self.search_results):
            return
        
        result = self.search_results[result_index]
        if match_index >= len(result['matches']):
            return
        
        match = result['matches'][match_index]
        self.current_match = (result_index, match_index)
        
        total = self._get_total_matches()
        current = sum(len(self.search_results[i]['matches']) for i in range(result_index)) + match_index + 1
        self.info_label.setText(f"{current}/{total} occurrences")
        
        # Émettre le signal
        self.matchFound.emit(result['page'], match.start(), match.end())
    
    def _search_next(self):
        """Va à l'occurrence suivante"""
        if not self.search_results:
            self._search_all()
            return
        
        total_matches = self._get_total_matches()
        if total_matches == 0:
            return
        
        # Trouver la position actuelle
        if self.current_match is None:
            result_idx, match_idx = 0, 0
        else:
            result_idx, match_idx = self.current_match
            
            # Avancer
            match_idx += 1
            while result_idx < len(self.search_results):
                if match_idx < len(self.search_results[result_idx]['matches']):
                    break
                result_idx += 1
                match_idx = 0
            
            # Si on a dépassé, recommencer depuis le début
            if result_idx >= len(self.search_results):
                result_idx, match_idx = 0, 0
        
        self._go_to_match(result_idx, match_idx)
    
    def _search_previous(self):
        """Va à l'occurrence précédente"""
        if not self.search_results:
            return
        
        total_matches = self._get_total_matches()
        if total_matches == 0:
            return
        
        # Trouver la position actuelle
        if self.current_match is None:
            result_idx = len(self.search_results) - 1
            match_idx = len(self.search_results[result_idx]['matches']) - 1
        else:
            result_idx, match_idx = self.current_match
            
            # Reculer
            match_idx -= 1
            while result_idx >= 0:
                if match_idx >= 0:
                    break
                result_idx -= 1
                if result_idx >= 0:
                    match_idx = len(self.search_results[result_idx]['matches']) - 1
            
            # Si on a dépassé, aller à la fin
            if result_idx < 0:
                result_idx = len(self.search_results) - 1
                match_idx = len(self.search_results[result_idx]['matches']) - 1
        
        self._go_to_match(result_idx, match_idx)
    
    def _replace_current(self):
        """Remplace l'occurrence actuellement sélectionnée"""
        if not self.current_match or not self.search_results:
            return
        
        result_idx, match_idx = self.current_match
        if result_idx >= len(self.search_results):
            return
        
        result = self.search_results[result_idx]
        if match_idx >= len(result['matches']):
            return
        
        match = result['matches'][match_idx]
        replace_text = self.replace_edit.toPlainText()
        
        # Traiter les séquences d'échappement pour les sauts de ligne
        replace_text = replace_text.replace('\\n', '\n')
        
        # Si regex, traiter les références de groupes (\1, \2, etc.)
        if result['is_regex']:
            # Convertir les références de groupes de \1 à \g<1> (format Python)
            import re
            # Remplacer \1, \2, etc. par \g<1>, \g<2>, etc.
            replace_text = re.sub(r'\\([1-9]\d*)', r'\\g<\1>', replace_text)
        
        # Émettre le signal pour le remplacement
        self.replaceRequested.emit(result['page'], match.start(), match.end(), replace_text)
        
        # Refaire la recherche pour mettre à jour les positions
        # (après un petit délai pour laisser le fichier se sauvegarder)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(200, self._refresh_after_replace)
    
    def _refresh_after_replace(self):
        """Rafraîchit la recherche après un remplacement"""
        # Conserver la recherche actuelle
        search_text = self.search_edit.toPlainText()
        if search_text:
            self._search_all()
            # Revenir approximativement à la position précédente
            if self.current_match:
                result_idx, match_idx = self.current_match
                # Essayer de se replacer au même endroit (peut changer si le texte a changé)
                self._go_to_match(min(result_idx, len(self.search_results) - 1), 
                                min(match_idx, len(self.search_results[result_idx]['matches']) - 1) if result_idx < len(self.search_results) else 0)
    
    def _replace_all(self):
        """Remplace toutes les occurrences"""
        if not self.search_results:
            return
        
        # Préserver les espaces et sauts de ligne significatifs
        search_text = self.search_edit.toPlainText().strip('\n\r')
        replace_text = self.replace_edit.toPlainText()
        is_regex = self.regex_checkbox.isChecked()
        
        # Traiter les séquences d'échappement pour les sauts de ligne
        replace_text = replace_text.replace('\\n', '\n')
        
        # Si regex, traiter les références de groupes
        if is_regex:
            import re
            # Remplacer \1, \2, etc. par \g<1>, \g<2>, etc. pour Python regex
            replace_text = re.sub(r'\\([1-9]\d*)', r'\\g<\1>', replace_text)
        
        total_count = self._get_total_matches()
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous remplacer {total_count} occurrence(s) dans {len(self.search_results)} fichier(s) ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Émettre le signal pour le remplacement global
        self.replaceAllRequested.emit(search_text, replace_text, is_regex)
        
        # Rafraîchir après un délai
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(300, lambda: self._search_all() if self.search_edit.toPlainText() else None)
