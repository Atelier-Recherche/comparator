"""
Système de mise en évidence pour l'éditeur Markdown
"""

import re
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QTextCharFormat, QColor, QSyntaxHighlighter


class PatternHighlighter(QSyntaxHighlighter):
    """Syntax highlighter personnalisé pour mettre en évidence des patterns"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.patterns = []  # Liste de tuples (pattern, format, is_regex)
    
    def add_pattern(self, pattern: str, color: QColor, is_regex: bool = False, 
                   text_color: QColor = None, auto_text_color: bool = True):
        """
        Ajoute un pattern de mise en évidence
        
        Args:
            pattern: Le pattern à rechercher (texte simple ou regex)
            color: La couleur pour la mise en évidence (fond)
            is_regex: Si True, le pattern est traité comme une regex
            text_color: Couleur du texte (None pour auto)
            auto_text_color: Si True, calcule automatiquement la couleur du texte pour le contraste
        """
        from color_utils import get_contrast_text_color
        
        char_format = QTextCharFormat()
        char_format.setBackground(color)
        
        # Définir la couleur du texte
        if auto_text_color and text_color is None:
            text_color = get_contrast_text_color(color)
        
        if text_color is not None:
            char_format.setForeground(text_color)
        
        if is_regex:
            try:
                regex = QRegularExpression(pattern)
                if regex.isValid():
                    self.patterns.append((regex, char_format, True))
            except Exception:
                pass
        else:
            # Échapper les caractères spéciaux pour regex
            escaped_pattern = re.escape(pattern)
            regex = QRegularExpression(escaped_pattern)
            if regex.isValid():
                self.patterns.append((regex, char_format, False))
    
    def clear_patterns(self):
        """Supprime tous les patterns de mise en évidence"""
        self.patterns.clear()
        self.rehighlight()
    
    def remove_pattern(self, pattern: str, is_regex: bool = False):
        """Supprime un pattern spécifique"""
        if is_regex:
            self.patterns = [p for p in self.patterns 
                           if not (p[2] and p[0].pattern() == pattern)]
        else:
            escaped_pattern = re.escape(pattern)
            self.patterns = [p for p in self.patterns 
                           if not (not p[2] and p[0].pattern() == escaped_pattern)]
        self.rehighlight()
    
    def highlightBlock(self, text: str):
        """Applique la mise en évidence sur un bloc de texte"""
        for regex, char_format, _ in self.patterns:
            iterator = regex.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                # Appliquer directement le format - il écrasera les formats précédents
                # (comme ceux des caractères invisibles) car ce highlighter est créé après
                self.setFormat(match.capturedStart(), match.capturedLength(), char_format)
