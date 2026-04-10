"""
Dialog de configuration du décalage entre pages PDF et Markdown
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QSpinBox, QPushButton, QGroupBox)


class OffsetConfigDialog(QDialog):
    """Dialog pour configurer le décalage entre pages"""
    
    offsetChanged = pyqtSignal(int)  # Émis quand le décalage change
    
    def __init__(self, current_offset: int = 0, pdf_page: int = 0, 
                 markdown_page: int = 0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration du décalage")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Explication
        info_label = QLabel(
            "Le décalage détermine la correspondance entre les pages PDF et Markdown.\n"
            "Formule: Page Markdown = Page PDF + Décalage"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Configuration du décalage
        offset_group = QGroupBox("Décalage")
        offset_layout = QVBoxLayout()
        
        offset_control_layout = QHBoxLayout()
        offset_control_layout.addWidget(QLabel("Décalage:"))
        
        self.offset_spinbox = QSpinBox()
        self.offset_spinbox.setRange(-1000, 1000)
        self.offset_spinbox.setValue(current_offset)
        self.offset_spinbox.valueChanged.connect(self._on_offset_changed)
        offset_control_layout.addWidget(self.offset_spinbox)
        offset_control_layout.addStretch()
        
        offset_layout.addLayout(offset_control_layout)
        offset_group.setLayout(offset_layout)
        layout.addWidget(offset_group)
        
        # Aperçu de la correspondance
        preview_group = QGroupBox("Aperçu de la correspondance")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel()
        self._update_preview(pdf_page, markdown_page, current_offset)
        preview_layout.addWidget(self.preview_label)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Boutons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        apply_button = QPushButton("Appliquer")
        apply_button.clicked.connect(self._apply_offset)
        button_layout.addWidget(apply_button)
        
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.pdf_page = pdf_page
        self.markdown_page = markdown_page
    
    def _on_offset_changed(self, value: int):
        """Met à jour l'aperçu quand le décalage change"""
        self._update_preview(self.pdf_page, self.markdown_page, value)
    
    def _update_preview(self, pdf_page: int, markdown_page: int, offset: int):
        """Met à jour le texte d'aperçu"""
        calculated_md_page = pdf_page + offset
        self.preview_label.setText(
            f"Page PDF {pdf_page} ↔ Page Markdown {calculated_md_page}\n"
            f"Décalage actuel: {offset}"
        )
    
    def _apply_offset(self):
        """Applique le décalage"""
        offset = self.offset_spinbox.value()
        self.offsetChanged.emit(offset)
        self.accept()
    
    def get_offset(self) -> int:
        """Retourne la valeur du décalage"""
        return self.offset_spinbox.value()
