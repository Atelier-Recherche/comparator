"""
Highlighter pour colorer les caractères invisibles (espaces, tabs)
"""

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QTextCharFormat, QColor, QSyntaxHighlighter


class InvisibleCharsHighlighter(QSyntaxHighlighter):
    """Highlighter pour colorer les caractères invisibles"""
    
    def __init__(self, parent=None, color: QColor = None):
        super().__init__(parent)
        self.invisible_color = color or QColor(128, 128, 128)  # Gris par défaut
        self.enabled = False
        self.show_line_breaks = False
        
        # Format pour les espaces, tabs et fins de ligne
        self.space_format = QTextCharFormat()
        self.tab_format = QTextCharFormat()
        self.line_end_format = QTextCharFormat()
        self._update_formats()
    
    def set_color(self, color: QColor):
        """Définit la couleur des caractères invisibles"""
        self.invisible_color = color
        self._update_formats()
        if self.enabled:
            self.rehighlight()
    
    def set_show_line_breaks(self, show: bool):
        """Active/désactive l'affichage des sauts de ligne"""
        self.show_line_breaks = show
        if self.enabled:
            self.rehighlight()
    
    def set_enabled(self, enabled: bool):
        """Active/désactive le highlighter"""
        self.enabled = enabled
        if enabled:
            self.rehighlight()
        else:
            self.setFormat(0, self.document().characterCount(), QTextCharFormat())
    
    def _update_formats(self):
        """Met à jour les formats de caractères"""
        self.space_format.setForeground(self.invisible_color)
        self.tab_format.setForeground(self.invisible_color)
        self.line_end_format.setForeground(self.invisible_color)
    
    def highlightBlock(self, text: str):
        """Applique la mise en évidence sur un bloc de texte"""
        if not self.enabled:
            return
        
        # Colorer uniquement les espaces et tabs
        # Ce highlighter est appliqué en premier, donc les autres highlighters peuvent écraser
        # mais on ne colore que les espaces/tabs, donc ça ne devrait pas poser problème
        
        # Colorer les espaces
        space_regex = QRegularExpression(r' ')
        iterator = space_regex.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.space_format)
        
        # Colorer les tabs
        tab_regex = QRegularExpression(r'\t')
        iterator = tab_regex.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.tab_format)
        
        # Ne PAS colorer le dernier caractère pour les sauts de ligne
        # Les sauts de ligne sont gérés par le widget personnalisé qui dessine les caractères ¶
