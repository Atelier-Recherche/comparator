"""
Dialog de configuration des patterns de mise en évidence
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QListWidget, QListWidgetItem,
                            QLineEdit, QCheckBox, QColorDialog, QGroupBox,
                            QFormLayout, QMessageBox)
from color_utils import get_contrast_text_color, color_to_list, list_to_color


class HighlightConfigDialog(QDialog):
    """Dialog pour configurer les patterns de mise en évidence"""
    
    patternsChanged = pyqtSignal(list)  # Émis quand les patterns changent
    
    def __init__(self, patterns: list = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration de la mise en évidence")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        self.patterns = patterns.copy() if patterns else []
        
        layout = QVBoxLayout(self)
        
        # Liste des patterns
        list_group = QGroupBox("Patterns de mise en évidence")
        list_layout = QVBoxLayout()
        
        self.pattern_list = QListWidget()
        self.pattern_list.currentRowChanged.connect(self._on_pattern_selected)
        list_layout.addWidget(self.pattern_list)
        
        list_buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Ajouter")
        self.add_button.clicked.connect(self._add_pattern)
        list_buttons_layout.addWidget(self.add_button)
        
        self.remove_button = QPushButton("Supprimer")
        self.remove_button.clicked.connect(self._remove_pattern)
        list_buttons_layout.addWidget(self.remove_button)
        
        list_layout.addLayout(list_buttons_layout)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        # Formulaire d'édition
        form_group = QGroupBox("Éditer le pattern sélectionné")
        form_layout = QFormLayout()
        
        self.pattern_edit = QLineEdit()
        self.pattern_edit.setPlaceholderText("Entrez le pattern (texte ou regex)")
        form_layout.addRow("Pattern:", self.pattern_edit)
        
        self.regex_checkbox = QCheckBox("Expression régulière")
        form_layout.addRow("", self.regex_checkbox)
        
        color_layout = QHBoxLayout()
        self.color_button = QPushButton("Choisir couleur")
        self.color_button.clicked.connect(self._choose_color)
        self.color_preview = QLabel()
        self.color_preview.setMinimumSize(50, 30)
        self.color_preview.setStyleSheet("background-color: yellow; border: 1px solid black;")
        self.current_color = QColor(255, 255, 0)  # Jaune par défaut
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(self.color_preview)
        color_layout.addStretch()
        form_layout.addRow("Couleur de fond:", color_layout)
        
        # Couleur du texte
        text_color_layout = QHBoxLayout()
        self.text_color_button = QPushButton("Choisir couleur")
        self.text_color_button.clicked.connect(self._choose_text_color)
        self.text_color_preview = QLabel()
        self.text_color_preview.setMinimumSize(50, 30)
        self.text_color_preview.setStyleSheet("background-color: black; border: 1px solid black;")
        self.current_text_color = None  # Auto par défaut
        text_color_layout.addWidget(self.text_color_button)
        text_color_layout.addWidget(self.text_color_preview)
        text_color_layout.addStretch()
        form_layout.addRow("Couleur du texte:", text_color_layout)
        
        self.auto_text_color_checkbox = QCheckBox("Couleur automatique (meilleur contraste)")
        self.auto_text_color_checkbox.setChecked(True)
        self.auto_text_color_checkbox.toggled.connect(self._on_auto_text_color_toggled)
        form_layout.addRow("", self.auto_text_color_checkbox)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Boutons de dialogue
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        apply_button = QPushButton("Appliquer")
        apply_button.clicked.connect(self._apply_patterns)
        button_layout.addWidget(apply_button)
        
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # Charger les patterns existants
        self._refresh_pattern_list()
    
    def _refresh_pattern_list(self):
        """Met à jour la liste des patterns"""
        self.pattern_list.clear()
        for i, pattern in enumerate(self.patterns):
            pattern_text = pattern.get('pattern', '')
            is_regex = pattern.get('is_regex', False)
            color = pattern.get('color', [255, 255, 0])
            
            # Convertir la couleur en QColor si nécessaire
            if isinstance(color, list):
                qcolor = QColor(*color[:3])
            else:
                qcolor = QColor(color)
            
            label = f"{pattern_text} ({'regex' if is_regex else 'texte'})"
            item = QListWidgetItem(label)
            item.setBackground(qcolor)
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.pattern_list.addItem(item)
        
        if self.pattern_list.count() > 0:
            self.pattern_list.setCurrentRow(0)
            self._on_pattern_selected(0)
        else:
            self._clear_form()
    
    def _on_pattern_selected(self, row: int):
        """Appelé quand un pattern est sélectionné"""
        if row < 0 or row >= len(self.patterns):
            self._clear_form()
            return
        
        pattern = self.patterns[row]
        self.pattern_edit.setText(pattern.get('pattern', ''))
        self.regex_checkbox.setChecked(pattern.get('is_regex', False))
        
        color = pattern.get('color', [255, 255, 0])
        if isinstance(color, list):
            self.current_color = QColor(*color[:3])
        else:
            self.current_color = QColor(color)
        
        text_color = pattern.get('text_color')
        if text_color:
            if isinstance(text_color, list):
                self.current_text_color = QColor(*text_color[:3])
            else:
                self.current_text_color = QColor(text_color)
            self.auto_text_color_checkbox.setChecked(False)
        else:
            self.current_text_color = None
            self.auto_text_color_checkbox.setChecked(pattern.get('auto_text_color', True))
        
        self._update_color_preview()
        self._update_text_color_preview()
    
    def _clear_form(self):
        """Efface le formulaire"""
        self.pattern_edit.clear()
        self.regex_checkbox.setChecked(False)
        self.current_color = QColor(255, 255, 0)
        self.current_text_color = None
        self.auto_text_color_checkbox.setChecked(True)
        self._update_color_preview()
        self._update_text_color_preview()
    
    def _update_color_preview(self):
        """Met à jour l'aperçu de la couleur"""
        color_str = self.current_color.name()
        self.color_preview.setStyleSheet(
            f"background-color: {color_str}; border: 1px solid black;"
        )
        # Mettre à jour aussi la couleur du texte si auto
        if self.auto_text_color_checkbox.isChecked():
            self._update_text_color_preview()
    
    def _update_text_color_preview(self):
        """Met à jour l'aperçu de la couleur du texte"""
        if self.auto_text_color_checkbox.isChecked() or self.current_text_color is None:
            text_color = get_contrast_text_color(self.current_color)
            self.text_color_preview.setStyleSheet(
                f"background-color: {text_color.name()}; border: 1px solid black;"
            )
            self.text_color_preview.setToolTip("Automatique (meilleur contraste)")
        else:
            color_str = self.current_text_color.name()
            self.text_color_preview.setStyleSheet(
                f"background-color: {color_str}; border: 1px solid black;"
            )
            self.text_color_preview.setToolTip("Couleur personnalisée")
    
    def _choose_text_color(self):
        """Ouvre le sélecteur de couleur pour le texte"""
        if self.current_text_color is None:
            current_color = get_contrast_text_color(self.current_color)
        else:
            current_color = self.current_text_color
        
        color = QColorDialog.getColor(current_color, self, "Choisir la couleur du texte")
        if color.isValid():
            self.current_text_color = color
            self.auto_text_color_checkbox.setChecked(False)
            self._update_text_color_preview()
    
    def _on_auto_text_color_toggled(self, checked: bool):
        """Appelé quand la case auto est cochée/décochée"""
        self._update_text_color_preview()
    
    def _choose_color(self):
        """Ouvre le sélecteur de couleur"""
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self._update_color_preview()
    
    def _add_pattern(self):
        """Ajoute un nouveau pattern"""
        pattern_text = self.pattern_edit.text().strip()
        if not pattern_text:
            QMessageBox.warning(self, "Attention", "Veuillez entrer un pattern.")
            return
        
        text_color_list = None
        if not self.auto_text_color_checkbox.isChecked() and self.current_text_color:
            text_color_list = [self.current_text_color.red(), 
                             self.current_text_color.green(), 
                             self.current_text_color.blue()]
        
        new_pattern = {
            'pattern': pattern_text,
            'is_regex': self.regex_checkbox.isChecked(),
            'color': [self.current_color.red(), self.current_color.green(), 
                     self.current_color.blue()],
            'text_color': text_color_list,
            'auto_text_color': self.auto_text_color_checkbox.isChecked()
        }
        
        self.patterns.append(new_pattern)
        self._refresh_pattern_list()
        self.pattern_list.setCurrentRow(len(self.patterns) - 1)
    
    def _remove_pattern(self):
        """Supprime le pattern sélectionné"""
        current_row = self.pattern_list.currentRow()
        if current_row < 0 or current_row >= len(self.patterns):
            return
        
        reply = QMessageBox.question(
            self, "Confirmation", 
            "Êtes-vous sûr de vouloir supprimer ce pattern ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.patterns[current_row]
            self._refresh_pattern_list()
    
    def _apply_patterns(self):
        """Applique les patterns"""
        # Si un pattern est en cours d'édition, le sauvegarder
        current_row = self.pattern_list.currentRow()
        if current_row >= 0 and current_row < len(self.patterns):
            pattern_text = self.pattern_edit.text().strip()
            if pattern_text:
                text_color_list = None
                if not self.auto_text_color_checkbox.isChecked() and self.current_text_color:
                    text_color_list = [self.current_text_color.red(), 
                                     self.current_text_color.green(), 
                                     self.current_text_color.blue()]
                
                self.patterns[current_row] = {
                    'pattern': pattern_text,
                    'is_regex': self.regex_checkbox.isChecked(),
                    'color': [self.current_color.red(), self.current_color.green(),
                             self.current_color.blue()],
                    'text_color': text_color_list,
                    'auto_text_color': self.auto_text_color_checkbox.isChecked()
                }
        
        self.patternsChanged.emit(self.patterns)
        self.accept()
    
    def get_patterns(self) -> list:
        """Retourne la liste des patterns"""
        return self.patterns
