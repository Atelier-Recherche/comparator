"""
Dialog de recherche/remplacement dans tous les fichiers Markdown
"""

import re
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QCheckBox, QGroupBox,
                            QFormLayout, QMessageBox, QProgressDialog, QPlainTextEdit)


class SearchReplaceDialog(QDialog):
    """Dialog pour rechercher et remplacer dans tous les fichiers Markdown"""
    
    def __init__(self, file_pattern, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rechercher/Remplacer dans tous les fichiers Markdown")
        self.setModal(True)
        self.setMinimumSize(500, 300)
        
        self.file_pattern = file_pattern
        self.current_search_index = 0
        self.search_results = []  # Liste de (page_num, file_path, matches)
        
        layout = QVBoxLayout(self)
        
        # Groupe de recherche
        search_group = QGroupBox("Rechercher")
        search_layout = QFormLayout()
        
        # Utiliser QPlainTextEdit pour permettre les sauts de ligne et espaces
        self.search_edit = QPlainTextEdit()
        self.search_edit.setMaximumHeight(80)
        self.search_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.search_edit.setToolTip("Texte ou expression régulière à rechercher\nLes espaces et sauts de ligne sont pris en compte")
        search_layout.addRow("Rechercher:", self.search_edit)
        
        self.regex_checkbox = QCheckBox("Expression régulière")
        search_layout.addRow("", self.regex_checkbox)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Groupe de remplacement
        replace_group = QGroupBox("Remplacer par")
        replace_layout = QFormLayout()
        
        # Utiliser QPlainTextEdit pour permettre les sauts de ligne et espaces
        self.replace_edit = QPlainTextEdit()
        self.replace_edit.setMaximumHeight(80)
        self.replace_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.replace_edit.setToolTip("Texte de remplacement\nLes espaces et sauts de ligne sont pris en compte")
        replace_layout.addRow("Remplacer par:", self.replace_edit)
        
        replace_group.setLayout(replace_layout)
        layout.addWidget(replace_group)
        
        # Informations
        self.info_label = QLabel("Prêt à rechercher")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # Boutons d'action
        action_layout = QHBoxLayout()
        
        self.search_button = QPushButton("Rechercher")
        self.search_button.clicked.connect(self._search_all)
        action_layout.addWidget(self.search_button)
        
        self.next_button = QPushButton("Suivant")
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self._next_match)
        action_layout.addWidget(self.next_button)
        
        self.replace_all_button = QPushButton("Tout remplacer")
        self.replace_all_button.setEnabled(False)
        self.replace_all_button.clicked.connect(self._replace_all)
        action_layout.addWidget(self.replace_all_button)
        
        action_layout.addStretch()
        
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        action_layout.addWidget(close_button)
        
        layout.addLayout(action_layout)
    
    def _search_all(self):
        """Recherche dans tous les fichiers Markdown"""
        # Préserver les espaces et sauts de ligne significatifs
        search_text = self.search_edit.toPlainText().strip('\n\r')
        if not search_text.strip():
            QMessageBox.warning(self, "Attention", "Veuillez entrer un texte à rechercher.")
            return
        
        self.search_results = []
        self.current_search_index = 0
        is_regex = self.regex_checkbox.isChecked()
        
        total_pages = self.file_pattern.get_total_pages()
        if total_pages == 0:
            QMessageBox.warning(self, "Attention", "Aucun fichier Markdown trouvé.")
            return
        
        # Compiler le pattern regex
        try:
            if is_regex:
                pattern = re.compile(search_text)
            else:
                pattern = re.compile(re.escape(search_text))
        except re.error as e:
            QMessageBox.critical(self, "Erreur regex", f"Expression régulière invalide: {e}")
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
                
                # Trouver toutes les occurrences
                matches = list(pattern.finditer(content))
                if matches:
                    self.search_results.append({
                        'page': page_num,
                        'file_path': file_path,
                        'matches': matches,
                        'content': content
                    })
                    matches_count += len(matches)
                    files_with_matches += 1
            except Exception as e:
                print(f"Erreur lors de la lecture de {file_path}: {e}")
        
        # Afficher les résultats
        if matches_count > 0:
            self.info_label.setText(
                f"Trouvé {matches_count} occurrence(s) dans {files_with_matches} fichier(s)."
            )
            self.next_button.setEnabled(True)
            self.replace_all_button.setEnabled(True)
        else:
            self.info_label.setText("Aucune occurrence trouvée.")
            self.next_button.setEnabled(False)
            self.replace_all_button.setEnabled(False)
    
    def _next_match(self):
        """Va à l'occurrence suivante"""
        if not self.search_results:
            return
        
        # Calculer quelle est la prochaine occurrence
        total_matches = sum(len(r['matches']) for r in self.search_results)
        if total_matches == 0:
            return
        
        # Trouver l'occurrence actuelle dans la liste des résultats
        current_match_idx = 0
        for result in self.search_results:
            if current_match_idx + len(result['matches']) > self.current_search_index:
                # Cette occurrence est dans ce fichier
                match_in_file = self.current_search_index - current_match_idx
                match = result['matches'][match_in_file]
                
                # Émettre un signal pour charger ce fichier et sélectionner le texte
                self._highlight_match(result['page'], match.start(), match.end())
                
                # Passer à l'occurrence suivante
                self.current_search_index = (self.current_search_index + 1) % total_matches
                return
            current_match_idx += len(result['matches'])
        
        # Si on arrive ici, on recommence depuis le début
        if self.search_results:
            match = self.search_results[0]['matches'][0]
            self._highlight_match(self.search_results[0]['page'], match.start(), match.end())
            self.current_search_index = 1
    
    def _highlight_match(self, page_num: int, start_pos: int, end_pos: int):
        """Sélectionne le texte correspondant dans l'éditeur"""
        # Cette méthode sera appelée depuis la fenêtre principale
        # On utilise un signal ou une méthode de callback
        if hasattr(self, 'on_match_found'):
            self.on_match_found(page_num, start_pos, end_pos)
    
    def _replace_all(self):
        """Remplace toutes les occurrences"""
        replace_text = self.replace_edit.toPlainText()
        is_regex = self.regex_checkbox.isChecked()
        # Préserver les espaces et sauts de ligne significatifs
        search_text = self.search_edit.toPlainText().strip('\n\r')
        
        if not self.search_results:
            QMessageBox.warning(self, "Attention", "Aucune occurrence à remplacer.")
            return
        
        # Confirmer
        total_count = sum(len(r['matches']) for r in self.search_results)
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous remplacer {total_count} occurrence(s) dans {len(self.search_results)} fichier(s) ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Compiler le pattern
        try:
            if is_regex:
                pattern = re.compile(search_text)
            else:
                pattern = re.compile(re.escape(search_text))
        except re.error as e:
            QMessageBox.critical(self, "Erreur regex", f"Expression régulière invalide: {e}")
            return
        
        # Remplacer dans tous les fichiers
        replaced_count = 0
        files_modified = 0
        
        for result in self.search_results:
            file_path = result['file_path']
            content = result['content']
            
            try:
                # Remplacer toutes les occurrences
                if is_regex:
                    new_content = pattern.sub(replace_text, content)
                else:
                    new_content = content.replace(search_text, replace_text)
                
                # Sauvegarder seulement si le contenu a changé
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    matches_in_file = len(result['matches'])
                    replaced_count += matches_in_file
                    files_modified += 1
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Erreur lors du remplacement dans {file_path.name}: {e}")
        
        # Afficher le résultat
        self.info_label.setText(
            f"Terminé : {replaced_count} occurrence(s) remplacée(s) dans {files_modified} fichier(s)."
        )
        
        QMessageBox.information(
            self, "Remplacement terminé",
            f"{replaced_count} occurrence(s) remplacée(s) dans {files_modified} fichier(s)."
        )
        
        # Réinitialiser la recherche
        self.search_results = []
        self.next_button.setEnabled(False)
        self.replace_all_button.setEnabled(False)
