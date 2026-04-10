"""
Panneau optionnel pour coller et nettoyer du texte avec recherche/remplacement
supportant les sauts de ligne
"""

import re
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QPlainTextEdit, QLineEdit, QCheckBox,
                            QGroupBox, QFormLayout, QMessageBox, QSplitter)


class TextCleanerPanel(QWidget):
    """Panneau pour coller et nettoyer du texte avec recherche/remplacement"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nettoyage de texte")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Zone de texte source (coller ici)
        source_group = QGroupBox("Texte source (coller ici)")
        source_layout = QVBoxLayout()
        self.source_text_edit = QPlainTextEdit()
        self.source_text_edit.setPlaceholderText("Collez votre texte ici...")
        source_layout.addWidget(self.source_text_edit)
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # Zone de recherche/remplacement
        search_replace_group = QGroupBox("Rechercher/Remplacer")
        search_replace_layout = QFormLayout()
        
        # Recherche
        self.search_edit = QPlainTextEdit()
        self.search_edit.setPlaceholderText("Texte à rechercher (support des sauts de ligne)")
        self.search_edit.setMaximumHeight(80)
        search_replace_layout.addRow("Rechercher:", self.search_edit)
        
        # Remplacement
        self.replace_edit = QPlainTextEdit()
        self.replace_edit.setPlaceholderText("Texte de remplacement (support des sauts de ligne)")
        self.replace_edit.setMaximumHeight(80)
        search_replace_layout.addRow("Remplacer par:", self.replace_edit)
        
        # Options
        options_layout = QHBoxLayout()
        self.regex_checkbox = QCheckBox("Expression régulière")
        self.case_sensitive_checkbox = QCheckBox("Sensible à la casse")
        options_layout.addWidget(self.regex_checkbox)
        options_layout.addWidget(self.case_sensitive_checkbox)
        options_layout.addStretch()
        search_replace_layout.addRow("Options:", options_layout)
        
        # Boutons d'action
        action_layout = QHBoxLayout()
        self.replace_button = QPushButton("Remplacer")
        self.replace_button.clicked.connect(self._replace_first)
        action_layout.addWidget(self.replace_button)
        
        self.replace_all_button = QPushButton("Tout remplacer")
        self.replace_all_button.clicked.connect(self._replace_all)
        action_layout.addWidget(self.replace_all_button)
        
        self.clear_button = QPushButton("Effacer")
        self.clear_button.clicked.connect(self._clear_source)
        action_layout.addWidget(self.clear_button)
        
        action_layout.addStretch()
        search_replace_layout.addRow("", action_layout)
        
        search_replace_group.setLayout(search_replace_layout)
        layout.addWidget(search_replace_group)
        
        # Zone de texte nettoyé
        cleaned_group = QGroupBox("Texte nettoyé")
        cleaned_layout = QVBoxLayout()
        self.cleaned_text_edit = QPlainTextEdit()
        self.cleaned_text_edit.setPlaceholderText("Le texte nettoyé apparaîtra ici...")
        self.cleaned_text_edit.setReadOnly(True)
        cleaned_layout.addWidget(self.cleaned_text_edit)
        
        # Boutons pour le texte nettoyé
        cleaned_buttons_layout = QHBoxLayout()
        self.copy_button = QPushButton("Copier le texte nettoyé")
        self.copy_button.clicked.connect(self._copy_cleaned)
        cleaned_buttons_layout.addWidget(self.copy_button)
        
        self.paste_to_editor_button = QPushButton("Coller dans l'éditeur Markdown")
        self.paste_to_editor_button.clicked.connect(self._paste_to_editor)
        cleaned_buttons_layout.addWidget(self.paste_to_editor_button)
        
        cleaned_buttons_layout.addStretch()
        cleaned_layout.addLayout(cleaned_buttons_layout)
        
        cleaned_group.setLayout(cleaned_layout)
        layout.addWidget(cleaned_group)
        
        # Initialiser avec le texte source
        self.source_text_edit.textChanged.connect(self._on_source_changed)
    
    def _on_source_changed(self):
        """Appelé quand le texte source change"""
        # Mettre à jour automatiquement le texte nettoyé
        self._update_cleaned_text()
    
    def _update_cleaned_text(self):
        """Met à jour le texte nettoyé avec le texte source actuel"""
        source_text = self.source_text_edit.toPlainText()
        self.cleaned_text_edit.setPlainText(source_text)
    
    def _replace_first(self):
        """Remplace la première occurrence"""
        search_text = self.search_edit.toPlainText()
        replace_text = self.replace_edit.toPlainText()
        
        if not search_text:
            QMessageBox.warning(self, "Attention", "Veuillez entrer un texte à rechercher.")
            return
        
        source_text = self.source_text_edit.toPlainText()
        cleaned_text = self._perform_replace(source_text, search_text, replace_text, replace_all=False)
        self.cleaned_text_edit.setPlainText(cleaned_text)
    
    def _replace_all(self):
        """Remplace toutes les occurrences"""
        search_text = self.search_edit.toPlainText()
        replace_text = self.replace_edit.toPlainText()
        
        if not search_text:
            QMessageBox.warning(self, "Attention", "Veuillez entrer un texte à rechercher.")
            return
        
        source_text = self.source_text_edit.toPlainText()
        cleaned_text = self._perform_replace(source_text, search_text, replace_text, replace_all=True)
        self.cleaned_text_edit.setPlainText(cleaned_text)
    
    def _perform_replace(self, text: str, search: str, replace: str, replace_all: bool) -> str:
        """Effectue le remplacement avec support des sauts de ligne"""
        is_regex = self.regex_checkbox.isChecked()
        case_sensitive = self.case_sensitive_checkbox.isChecked()
        
        try:
            if is_regex:
                # Mode expression régulière
                flags = 0 if case_sensitive else re.IGNORECASE
                pattern = re.compile(search, flags)
                
                if replace_all:
                    return pattern.sub(replace, text)
                else:
                    return pattern.sub(replace, text, count=1)
            else:
                # Mode texte simple - support des sauts de ligne
                if case_sensitive:
                    # Recherche sensible à la casse - méthode simple
                    if replace_all:
                        return text.replace(search, replace)
                    else:
                        return text.replace(search, replace, 1)
                else:
                    # Recherche insensible à la casse - utiliser regex pour gérer correctement
                    # On échappe le texte de recherche pour le traiter comme littéral
                    escaped_search = re.escape(search)
                    flags = re.IGNORECASE
                    pattern = re.compile(escaped_search, flags)
                    
                    if replace_all:
                        return pattern.sub(replace, text)
                    else:
                        return pattern.sub(replace, text, count=1)
        except re.error as e:
            QMessageBox.critical(self, "Erreur regex", f"Expression régulière invalide: {e}")
            return text
    
    def _clear_source(self):
        """Efface le texte source"""
        self.source_text_edit.clear()
        self.cleaned_text_edit.clear()
    
    def _copy_cleaned(self):
        """Copie le texte nettoyé dans le presse-papiers"""
        cleaned_text = self.cleaned_text_edit.toPlainText()
        if cleaned_text:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(cleaned_text)
            QMessageBox.information(self, "Copié", "Texte copié dans le presse-papiers.")
        else:
            QMessageBox.warning(self, "Attention", "Aucun texte à copier.")
    
    def _paste_to_editor(self):
        """Colle le texte nettoyé dans l'éditeur Markdown"""
        cleaned_text = self.cleaned_text_edit.toPlainText()
        if cleaned_text:
            # Émettre un signal pour que la fenêtre principale puisse coller dans l'éditeur
            self.pasteToEditorRequested.emit(cleaned_text)
        else:
            QMessageBox.warning(self, "Attention", "Aucun texte à coller.")
    
    # Signal pour demander de coller dans l'éditeur
    pasteToEditorRequested = pyqtSignal(str)
