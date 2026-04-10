"""
Dialog de préférences pour les couleurs et autres réglages
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QGroupBox, QFormLayout, QCheckBox,
                            QListWidget, QListWidgetItem, QLineEdit, QTextEdit,
                            QMessageBox, QSplitter)
from color_utils import get_contrast_text_color, list_to_color, color_to_list


class PreferencesDialog(QDialog):
    """Dialog de préférences de l'application"""
    
    preferencesChanged = pyqtSignal(dict)  # Émis quand les préférences changent
    
    def __init__(self, preferences: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Préférences")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        
        # Préférences par défaut
        self.default_prefs = {
            'search_highlight_color': [255, 255, 0],  # Jaune
            'search_text_color': None,  # Auto
            'auto_search_text_color': True,
            'custom_buttons': [],  # Liste de {'name': str, 'text': str}
            'invisible_chars_color': [128, 128, 128]  # Gris par défaut
        }
        
        self.preferences = preferences.copy() if preferences else self.default_prefs.copy()
        
        layout = QVBoxLayout(self)
        
        # Couleurs de recherche/remplacement
        search_group = QGroupBox("Recherche/Remplplacement")
        search_layout = QFormLayout()
        
        # Couleur de surlignage
        highlight_layout = QHBoxLayout()
        self.search_highlight_color_label = QLabel()
        self.search_highlight_color_label.setMinimumSize(50, 30)
        self.search_highlight_color_label.setStyleSheet("border: 1px solid black;")
        highlight_layout.addWidget(self.search_highlight_color_label)
        
        highlight_btn = QPushButton("Choisir couleur")
        highlight_btn.clicked.connect(self._choose_search_highlight_color)
        highlight_layout.addWidget(highlight_btn)
        highlight_layout.addStretch()
        
        search_layout.addRow("Couleur de surlignage:", highlight_layout)
        
        # Couleur du texte
        text_color_layout = QHBoxLayout()
        self.search_text_color_label = QLabel()
        self.search_text_color_label.setMinimumSize(50, 30)
        self.search_text_color_label.setStyleSheet("border: 1px solid black;")
        text_color_layout.addWidget(self.search_text_color_label)
        
        text_color_btn = QPushButton("Choisir couleur")
        text_color_btn.clicked.connect(self._choose_search_text_color)
        text_color_layout.addWidget(text_color_btn)
        text_color_layout.addStretch()
        
        search_layout.addRow("Couleur du texte:", text_color_layout)
        
        self.auto_text_color_checkbox = QCheckBox("Couleur automatique (meilleur contraste)")
        self.auto_text_color_checkbox.setChecked(self.preferences.get('auto_search_text_color', True))
        self.auto_text_color_checkbox.toggled.connect(self._on_auto_text_color_toggled)
        search_layout.addRow("", self.auto_text_color_checkbox)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Couleur des caractères invisibles
        invisible_chars_group = QGroupBox("Caractères invisibles")
        invisible_chars_layout = QFormLayout()
        
        invisible_color_layout = QHBoxLayout()
        self.invisible_chars_color_label = QLabel()
        self.invisible_chars_color_label.setMinimumSize(50, 30)
        self.invisible_chars_color_label.setStyleSheet("border: 1px solid black;")
        invisible_color_layout.addWidget(self.invisible_chars_color_label)
        
        invisible_color_btn = QPushButton("Choisir couleur")
        invisible_color_btn.clicked.connect(self._choose_invisible_chars_color)
        invisible_color_layout.addWidget(invisible_color_btn)
        invisible_color_layout.addStretch()
        
        invisible_chars_layout.addRow("Couleur des caractères invisibles (¶, ·):", invisible_color_layout)
        
        invisible_chars_group.setLayout(invisible_chars_layout)
        layout.addWidget(invisible_chars_group)
        
        # Boutons personnalisés
        buttons_group = QGroupBox("Boutons personnalisés")
        buttons_layout = QVBoxLayout()
        
        # Liste des boutons
        list_label = QLabel("Boutons configurés:")
        buttons_layout.addWidget(list_label)
        
        self.buttons_list = QListWidget()
        self.buttons_list.setMaximumHeight(150)
        self.buttons_list.itemSelectionChanged.connect(self._on_button_selected)
        buttons_layout.addWidget(self.buttons_list)
        
        # Formulaire pour éditer un bouton
        edit_layout = QFormLayout()
        
        self.button_name_edit = QLineEdit()
        self.button_name_edit.setPlaceholderText("Nom du bouton")
        edit_layout.addRow("Nom:", self.button_name_edit)
        
        self.button_text_edit = QTextEdit()
        self.button_text_edit.setPlaceholderText("Texte à insérer (peut contenir des sauts de ligne)")
        self.button_text_edit.setMaximumHeight(80)
        edit_layout.addRow("Texte:", self.button_text_edit)
        
        buttons_layout.addLayout(edit_layout)
        
        # Boutons d'action
        button_actions_layout = QHBoxLayout()
        
        self.add_button_btn = QPushButton("Ajouter")
        self.add_button_btn.clicked.connect(self._add_custom_button)
        button_actions_layout.addWidget(self.add_button_btn)
        
        self.update_button_btn = QPushButton("Modifier")
        self.update_button_btn.setEnabled(False)
        self.update_button_btn.clicked.connect(self._update_custom_button)
        button_actions_layout.addWidget(self.update_button_btn)
        
        self.remove_button_btn = QPushButton("Supprimer")
        self.remove_button_btn.setEnabled(False)
        self.remove_button_btn.clicked.connect(self._remove_custom_button)
        button_actions_layout.addWidget(self.remove_button_btn)
        
        button_actions_layout.addStretch()
        buttons_layout.addLayout(button_actions_layout)
        
        buttons_group.setLayout(buttons_layout)
        layout.addWidget(buttons_group)
        
        # Charger les boutons existants
        self._load_custom_buttons()
        
        # Boutons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        apply_button = QPushButton("Appliquer")
        apply_button.clicked.connect(self._apply_preferences)
        button_layout.addWidget(apply_button)
        
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # Initialiser l'affichage
        self._update_color_previews()
    
    def _choose_invisible_chars_color(self):
        """Ouvre le sélecteur de couleur pour les caractères invisibles"""
        current_color_list = self.preferences.get('invisible_chars_color', [128, 128, 128])
        current_color = list_to_color(current_color_list)
        
        from PyQt6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(current_color, self, "Choisir la couleur des caractères invisibles")
        if color.isValid():
            self.preferences['invisible_chars_color'] = color_to_list(color)
            self._update_color_previews()
    
    def _update_color_previews(self):
        """Met à jour les aperçus de couleurs"""
        # Couleur de surlignage
        highlight_color = list_to_color(self.preferences.get('search_highlight_color', [255, 255, 0]))
        self.search_highlight_color_label.setStyleSheet(
            f"background-color: {highlight_color.name()}; border: 1px solid black;"
        )
        
        # Couleur du texte
        auto_text = self.preferences.get('auto_search_text_color', True)
        if auto_text:
            text_color = get_contrast_text_color(highlight_color)
            self.search_text_color_label.setStyleSheet(
                f"background-color: {text_color.name()}; border: 1px solid black;"
            )
            self.search_text_color_label.setToolTip("Automatique (meilleur contraste)")
        else:
            text_color_list = self.preferences.get('search_text_color')
            if text_color_list:
                text_color = list_to_color(text_color_list)
            else:
                text_color = QColor(0, 0, 0)  # Noir par défaut
            self.search_text_color_label.setStyleSheet(
                f"background-color: {text_color.name()}; border: 1px solid black;"
            )
            self.search_text_color_label.setToolTip("Couleur personnalisée")
        
        # Couleur des caractères invisibles
        invisible_color_list = self.preferences.get('invisible_chars_color', [128, 128, 128])
        invisible_color = list_to_color(invisible_color_list)
        self.invisible_chars_color_label.setStyleSheet(
            f"background-color: {invisible_color.name()}; border: 1px solid black;"
        )
    
    def _choose_search_highlight_color(self):
        """Ouvre le sélecteur de couleur pour le surlignage"""
        current_color = list_to_color(self.preferences.get('search_highlight_color', [255, 255, 0]))
        from PyQt6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(current_color, self, "Choisir la couleur de surlignage")
        if color.isValid():
            self.preferences['search_highlight_color'] = color_to_list(color)
            self._update_color_previews()
    
    def _choose_search_text_color(self):
        """Ouvre le sélecteur de couleur pour le texte"""
        text_color_list = self.preferences.get('search_text_color')
        if text_color_list:
            current_color = list_to_color(text_color_list)
        else:
            current_color = QColor(0, 0, 0)
        
        from PyQt6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(current_color, self, "Choisir la couleur du texte")
        if color.isValid():
            self.preferences['search_text_color'] = color_to_list(color)
            self.preferences['auto_search_text_color'] = False
            self.auto_text_color_checkbox.setChecked(False)
            self._update_color_previews()
    
    def _on_auto_text_color_toggled(self, checked: bool):
        """Appelé quand la case auto est cochée/décochée"""
        self.preferences['auto_search_text_color'] = checked
        if checked:
            self.preferences['search_text_color'] = None
        self._update_color_previews()
    
    def _apply_preferences(self):
        """Applique les préférences"""
        self.preferencesChanged.emit(self.preferences)
        self.accept()
    
    def get_preferences(self) -> dict:
        """Retourne les préférences actuelles"""
        return self.preferences
    
    def _load_custom_buttons(self):
        """Charge les boutons personnalisés dans la liste"""
        self.buttons_list.clear()
        custom_buttons = self.preferences.get('custom_buttons', [])
        for button in custom_buttons:
            name = button.get('name', 'Sans nom')
            self.buttons_list.addItem(name)
    
    def _on_button_selected(self):
        """Appelé quand un bouton est sélectionné dans la liste"""
        selected_items = self.buttons_list.selectedItems()
        if selected_items:
            index = self.buttons_list.row(selected_items[0])
            custom_buttons = self.preferences.get('custom_buttons', [])
            if 0 <= index < len(custom_buttons):
                button = custom_buttons[index]
                self.button_name_edit.setText(button.get('name', ''))
                self.button_text_edit.setPlainText(button.get('text', ''))
                self.update_button_btn.setEnabled(True)
                self.remove_button_btn.setEnabled(True)
        else:
            self.button_name_edit.clear()
            self.button_text_edit.clear()
            self.update_button_btn.setEnabled(False)
            self.remove_button_btn.setEnabled(False)
    
    def _add_custom_button(self):
        """Ajoute un nouveau bouton personnalisé"""
        name = self.button_name_edit.text().strip()
        text = self.button_text_edit.toPlainText()
        
        if not name:
            QMessageBox.warning(self, "Attention", "Veuillez entrer un nom pour le bouton.")
            return
        
        if 'custom_buttons' not in self.preferences:
            self.preferences['custom_buttons'] = []
        
        # Vérifier si le nom existe déjà
        for btn in self.preferences['custom_buttons']:
            if btn.get('name') == name:
                QMessageBox.warning(self, "Attention", f"Un bouton avec le nom '{name}' existe déjà.")
                return
        
        # Ajouter le bouton
        self.preferences['custom_buttons'].append({
            'name': name,
            'text': text
        })
        
        self._load_custom_buttons()
        self.button_name_edit.clear()
        self.button_text_edit.clear()
    
    def _update_custom_button(self):
        """Met à jour le bouton sélectionné"""
        selected_items = self.buttons_list.selectedItems()
        if not selected_items:
            return
        
        index = self.buttons_list.row(selected_items[0])
        name = self.button_name_edit.text().strip()
        text = self.button_text_edit.toPlainText()
        
        if not name:
            QMessageBox.warning(self, "Attention", "Veuillez entrer un nom pour le bouton.")
            return
        
        custom_buttons = self.preferences.get('custom_buttons', [])
        if 0 <= index < len(custom_buttons):
            # Vérifier si le nom existe déjà (sauf pour le bouton actuel)
            for i, btn in enumerate(custom_buttons):
                if i != index and btn.get('name') == name:
                    QMessageBox.warning(self, "Attention", f"Un bouton avec le nom '{name}' existe déjà.")
                    return
            
            # Mettre à jour
            custom_buttons[index] = {
                'name': name,
                'text': text
            }
            self._load_custom_buttons()
            # Resélectionner l'item mis à jour
            self.buttons_list.setCurrentRow(index)
    
    def _remove_custom_button(self):
        """Supprime le bouton sélectionné"""
        selected_items = self.buttons_list.selectedItems()
        if not selected_items:
            return
        
        index = self.buttons_list.row(selected_items[0])
        
        reply = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment supprimer ce bouton ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            custom_buttons = self.preferences.get('custom_buttons', [])
            if 0 <= index < len(custom_buttons):
                custom_buttons.pop(index)
                self._load_custom_buttons()
                self.button_name_edit.clear()
                self.button_text_edit.clear()
                self.update_button_btn.setEnabled(False)
                self.remove_button_btn.setEnabled(False)
