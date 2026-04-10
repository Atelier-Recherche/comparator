"""
QPlainTextEdit personnalisé pour colorer les caractères de séparation de paragraphe
"""

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QTextOption, QTextCharFormat, QTextBlock
from PyQt6.QtWidgets import QPlainTextEdit


class CustomPlainTextEdit(QPlainTextEdit):
    """QPlainTextEdit personnalisé qui permet de colorer les caractères de séparation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.invisible_chars_color = QColor(128, 128, 128)
        self.show_line_breaks = False
        self.show_spaces = False
    
    def set_invisible_chars_color(self, color: QColor):
        """Définit la couleur des caractères invisibles"""
        self.invisible_chars_color = color
        if self.show_line_breaks or self.show_spaces:
            self.viewport().update()
    
    def set_show_line_breaks(self, show: bool):
        """Active/désactive l'affichage des sauts de ligne"""
        self.show_line_breaks = show
        self.viewport().update()
    
    def set_show_spaces(self, show: bool):
        """Active/désactive l'affichage des espaces"""
        self.show_spaces = show
        self.viewport().update()
    
    def paintEvent(self, event):
        """Surcharge le rendu pour colorer les caractères de séparation"""
        # Rendu normal (Qt ne dessinera pas les séparateurs car le flag n'est pas activé)
        super().paintEvent(event)
        
        # Si les sauts de ligne ou les espaces sont activés, dessiner les caractères avec la couleur personnalisée
        if self.show_line_breaks or self.show_spaces:
            painter = QPainter(self.viewport())
            painter.setPen(self.invisible_chars_color)
            painter.setFont(self.font())
            
            # Obtenir le premier bloc visible
            block = self.firstVisibleBlock()
            top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
            bottom = top + self.blockBoundingRect(block).height()
            
            # Parcourir tous les blocs visibles
            while block.isValid() and top <= event.rect().bottom():
                if block.isVisible() and bottom >= event.rect().top():
                    layout = block.layout()
                    if layout:
                        block_rect = self.blockBoundingGeometry(block).translated(self.contentOffset())
                        block_text = block.text()
                        
                        # Pour chaque ligne dans le bloc
                        for line_num in range(layout.lineCount()):
                            line = layout.lineAt(line_num)
                            line_rect = line.naturalTextRect()
                            line_start = line.textStart()
                            line_length = line.textLength()
                            
                            # Dessiner les espaces (·) si activé
                            if self.show_spaces:
                                # Parcourir les caractères de la ligne
                                line_text = block_text[line_start:line_start + line_length]
                                char_width = self.fontMetrics().horizontalAdvance(' ')
                                
                                for char_idx, char in enumerate(line_text):
                                    if char == ' ':
                                        # Calculer la position X approximative
                                        # Utiliser la position dans la ligne multipliée par la largeur d'un caractère
                                        x_offset = char_idx * char_width
                                        x = int(block_rect.left() + line_rect.x() + x_offset + char_width / 2)
                                        
                                        # Position Y : baseline de la ligne
                                        y = int(block_rect.top() + line_rect.y() + line_rect.height() - self.fontMetrics().descent())
                                        
                                        # Dessiner le point (·) avec la couleur personnalisée
                                        painter.drawText(x, y, "·")
                            
                            # Dessiner les sauts de ligne (¶) uniquement à la fin des blocs (vrais retours à la ligne),
                            # pas à la fin des lignes de retour automatique (word wrap)
                            if self.show_line_breaks and line_num == layout.lineCount() - 1:
                                # Position de la fin de la ligne
                                x = int(block_rect.left() + line_rect.x() + line_rect.width())
                                # Position verticale : utiliser la baseline de la ligne
                                y = int(block_rect.top() + line_rect.y() + line_rect.height() - self.fontMetrics().descent())
                                
                                # Dessiner le caractère ¶ avec la couleur personnalisée
                                painter.drawText(x + 2, y, "¶")
                
                block = block.next()
                if not block.isValid():
                    break
                top = bottom
                bottom = top + self.blockBoundingRect(block).height()
            
            painter.end()
