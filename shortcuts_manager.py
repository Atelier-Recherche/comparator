"""
Gestionnaire de raccourcis clavier pour l'application
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTableWidget, QTableWidgetItem,
                            QHeaderView, QMessageBox, QKeySequenceEdit,
                            QGroupBox, QFormLayout, QLineEdit)


class ShortcutsManagerDialog(QDialog):
    """Dialog pour gérer les raccourcis clavier"""
    
    shortcutsChanged = pyqtSignal(dict)  # Émis quand les raccourcis changent
    
    def __init__(self, shortcuts: dict = None, custom_buttons: list = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestionnaire de raccourcis")
        self.setModal(True)
        self.setMinimumSize(700, 500)
        
        self.shortcuts = shortcuts.copy() if shortcuts else {}
        self.custom_buttons = custom_buttons or []
        self.editing_item = None
        
        layout = QVBoxLayout(self)
        
        # Table des raccourcis
        info_label = QLabel("Double-cliquez sur une cellule pour modifier le raccourci")
        layout.addWidget(info_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Action", "Raccourci actuel", "Nouveau raccourci"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        layout.addWidget(self.table)
        
        # Zone d'édition
        edit_group = QGroupBox("Modifier le raccourci")
        edit_layout = QFormLayout()
        
        self.action_label = QLabel("")
        edit_layout.addRow("Action:", self.action_label)
        
        self.shortcut_edit = QKeySequenceEdit()
        self.shortcut_edit.setKeySequence(QKeySequence())
        edit_layout.addRow("Raccourci:", self.shortcut_edit)
        
        button_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Appliquer")
        self.apply_btn.clicked.connect(self._apply_shortcut)
        self.apply_btn.setEnabled(False)
        button_layout.addWidget(self.apply_btn)
        
        self.clear_btn = QPushButton("Effacer")
        self.clear_btn.clicked.connect(self._clear_shortcut)
        self.clear_btn.setEnabled(False)
        button_layout.addWidget(self.clear_btn)
        
        button_layout.addStretch()
        edit_layout.addRow("", button_layout)
        
        edit_group.setLayout(edit_layout)
        layout.addWidget(edit_group)
        
        # Boutons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        reset_btn = QPushButton("Réinitialiser tout")
        reset_btn.clicked.connect(self._reset_all)
        button_layout.addWidget(reset_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._apply_and_close)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Charger les raccourcis
        self._load_shortcuts()
    
    def _load_shortcuts(self):
        """Charge les raccourcis dans la table"""
        # Définir les actions par défaut avec leurs raccourcis par défaut
        default_actions = [
            ("Afficher/masquer sauts de ligne", "show_line_breaks", ""),
            ("Afficher/masquer espaces", "show_spaces", ""),
            ("Inverser couleurs PDF", "invert_pdf_colors", ""),
            ("Zoom PDF +", "zoom_pdf_in", "Ctrl++"),
            ("Zoom PDF -", "zoom_pdf_out", "Ctrl+-"),
            ("Police Markdown +", "font_larger", ""),
            ("Police Markdown -", "font_smaller", ""),
            ("Rechercher/Remplacer", "search_replace", "Ctrl+F"),
            ("Nouveau projet", "new_project", "Ctrl+N"),
            ("Ouvrir projet", "open_project", "Ctrl+O"),
            ("Enregistrer projet", "save_project", "Ctrl+S"),
            ("Panneau de nettoyage", "text_cleaner_panel", ""),
        ]
        
        # Remplacer les raccourcis par défaut par ceux sauvegardés s'ils existent
        for i, (name, action_id, default) in enumerate(default_actions):
            if action_id in self.shortcuts:
                default_actions[i] = (name, action_id, self.shortcuts[action_id])
        
        # Ajouter les boutons personnalisés
        actions = default_actions.copy()
        for i, button in enumerate(self.custom_buttons):
            actions.append((f"Bouton: {button.get('name', 'Sans nom')}", f"custom_button_{i}", ""))
        
        self.table.setRowCount(len(actions))
        
        for row, (action_name, action_id, default_shortcut) in enumerate(actions):
            # Nom de l'action
            name_item = QTableWidgetItem(action_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            # Raccourci actuel
            current_shortcut = self.shortcuts.get(action_id, default_shortcut)
            shortcut_item = QTableWidgetItem(current_shortcut if current_shortcut else "Aucun")
            shortcut_item.setFlags(shortcut_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            shortcut_item.setData(Qt.ItemDataRole.UserRole, action_id)
            self.table.setItem(row, 1, shortcut_item)
            
            # Nouveau raccourci (vide pour l'instant)
            new_item = QTableWidgetItem("")
            new_item.setFlags(new_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            new_item.setData(Qt.ItemDataRole.UserRole, action_id)
            self.table.setItem(row, 2, new_item)
        
        self.table.resizeColumnsToContents()
    
    def _on_cell_double_clicked(self, row: int, column: int):
        """Appelé quand une cellule est double-cliquée"""
        if column == 2:  # Colonne "Nouveau raccourci"
            action_item = self.table.item(row, 0)
            shortcut_item = self.table.item(row, 1)
            new_item = self.table.item(row, 2)
            
            if action_item and shortcut_item and new_item:
                action_name = action_item.text()
                action_id = shortcut_item.data(Qt.ItemDataRole.UserRole)
                current_shortcut = shortcut_item.text()
                
                self.action_label.setText(action_name)
                if current_shortcut and current_shortcut != "Aucun":
                    self.shortcut_edit.setKeySequence(QKeySequence(current_shortcut))
                else:
                    self.shortcut_edit.setKeySequence(QKeySequence())
                
                self.editing_item = new_item
                self.apply_btn.setEnabled(True)
                self.clear_btn.setEnabled(True)
    
    def _apply_shortcut(self):
        """Applique le raccourci sélectionné"""
        if not self.editing_item:
            return
        
        key_sequence = self.shortcut_edit.keySequence()
        action_id = self.editing_item.data(Qt.ItemDataRole.UserRole)
        
        if key_sequence.isEmpty():
            QMessageBox.warning(self, "Attention", "Veuillez entrer un raccourci valide.")
            return
        
        # Vérifier les conflits
        shortcut_str = key_sequence.toString()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            if item and item.data(Qt.ItemDataRole.UserRole) != action_id:
                if item.text() == shortcut_str:
                    QMessageBox.warning(
                        self, "Conflit",
                        f"Ce raccourci est déjà utilisé par: {self.table.item(row, 0).text()}"
                    )
                    return
        
        # Mettre à jour la table
        self.editing_item.setText(shortcut_str)
        self.shortcuts[action_id] = shortcut_str
        self.editing_item = None
        self.apply_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.shortcut_edit.setKeySequence(QKeySequence())
        self.action_label.setText("")
    
    def _clear_shortcut(self):
        """Efface le raccourci sélectionné"""
        if not self.editing_item:
            return
        
        action_id = self.editing_item.data(Qt.ItemDataRole.UserRole)
        self.editing_item.setText("")
        if action_id in self.shortcuts:
            del self.shortcuts[action_id]
        
        self.editing_item = None
        self.apply_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.shortcut_edit.setKeySequence(QKeySequence())
        self.action_label.setText("")
    
    def _reset_all(self):
        """Réinitialise tous les raccourcis"""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous réinitialiser tous les raccourcis aux valeurs par défaut ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.shortcuts = {}
            self._load_shortcuts()
    
    def _apply_and_close(self):
        """Applique les changements et ferme"""
        self.shortcutsChanged.emit(self.shortcuts)
        self.accept()
    
    def get_shortcuts(self) -> dict:
        """Retourne les raccourcis configurés"""
        return self.shortcuts
