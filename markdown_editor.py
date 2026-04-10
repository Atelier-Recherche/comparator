"""
Éditeur Markdown en texte brut avec sauvegarde automatique
"""

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QTextOption, QTextCharFormat, QTextFormat, QPalette
from PyQt6.QtWidgets import QPlainTextEdit, QVBoxLayout, QLabel, QWidget
from highlighter import PatternHighlighter
from invisible_chars_highlighter import InvisibleCharsHighlighter
from custom_text_edit import CustomPlainTextEdit


class MarkdownEditor(QWidget):
    """Éditeur Markdown en texte brut avec mise en évidence"""
    
    fileSaved = pyqtSignal(str)  # Émis quand un fichier est sauvegardé
    contentChanged = pyqtSignal()  # Émis quand le contenu change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file_path = None
        self.highlighter = None
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._save_file)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label d'information
        self.info_label = QLabel("Aucun fichier ouvert")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)
        
        # Éditeur de texte personnalisé pour colorer les caractères de séparation
        self.text_edit = CustomPlainTextEdit()
        from PyQt6.QtGui import QFontDatabase
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(12)  # Taille par défaut
        self.text_edit.setFont(font)
        self.text_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_edit)
        
        # Highlighter pour les caractères invisibles (créé en premier pour ne pas écraser les autres)
        self.invisible_highlighter = InvisibleCharsHighlighter(self.text_edit.document())
        
        # Highlighter principal (créé après pour que ses formats prennent priorité)
        self.highlighter = PatternHighlighter(self.text_edit.document())
        
        # Sélection de recherche (pour utiliser les couleurs personnalisées)
        self.search_selection = None
        
        # Options pour les caractères invisibles
        self.show_line_breaks = False
        self.show_spaces = False
        self.invisible_chars_color = QColor(128, 128, 128)  # Gris par défaut
        self._update_text_options()
    
    def load_file(self, file_path: str):
        """Charge un fichier dans l'éditeur"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.current_file_path = file_path
            self.text_edit.setPlainText(content)
            self.info_label.setText(f"Fichier: {file_path}")
            return True
        except Exception as e:
            print(f"Erreur lors du chargement du fichier {file_path}: {e}")
            return False
    
    def get_content(self) -> str:
        """Retourne le contenu actuel de l'éditeur"""
        return self.text_edit.toPlainText()
    
    def set_content(self, content: str):
        """Définit le contenu de l'éditeur"""
        self.text_edit.setPlainText(content)
    
    def _on_text_changed(self):
        """Appelé quand le contenu change"""
        self.contentChanged.emit()
        # Démarrer le timer de sauvegarde automatique (délai de 1 seconde)
        if self.current_file_path:
            self.save_timer.stop()
            self.save_timer.start(1000)  # 1 seconde de délai
    
    def _save_file(self):
        """Sauvegarde le fichier actuel"""
        if not self.current_file_path:
            return
        
        try:
            content = self.text_edit.toPlainText()
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.fileSaved.emit(self.current_file_path)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du fichier: {e}")
    
    def save_file(self, file_path: str = None):
        """Sauvegarde le fichier (manuellement ou automatiquement)"""
        if file_path:
            self.current_file_path = file_path
        
        if self.current_file_path:
            self.save_timer.stop()  # Arrêter le timer si en cours
            self._save_file()
    
    def clear(self):
        """Efface le contenu de l'éditeur"""
        self.text_edit.clear()
        self.current_file_path = None
        self.info_label.setText("Aucun fichier ouvert")
    
    def set_highlight_patterns(self, patterns: list, search_highlight_color=None, 
                              search_text_color=None, auto_search_text_color=True):
        """
        Définit les patterns de mise en évidence
        
        Args:
            patterns: Liste de dictionnaires avec 'pattern', 'color', 'is_regex', 'text_color', 'auto_text_color'
            search_highlight_color: Couleur pour la recherche/remplacement
            search_text_color: Couleur du texte pour la recherche (None pour auto)
            auto_search_text_color: Calcul automatique de la couleur du texte pour la recherche
        """
        self.highlighter.clear_patterns()
        
        for p in patterns:
            pattern = p.get('pattern', '')
            color = p.get('color')
            is_regex = p.get('is_regex', False)
            text_color = p.get('text_color')
            auto_text_color = p.get('auto_text_color', True)
            
            if pattern and color:
                # Convertir la couleur si c'est une chaîne ou un tuple
                if isinstance(color, str):
                    qcolor = QColor(color)
                elif isinstance(color, (list, tuple)):
                    from color_utils import list_to_color
                    qcolor = list_to_color(color)
                else:
                    qcolor = color
                
                # Convertir la couleur du texte si fournie
                qtext_color = None
                if text_color is not None:
                    if isinstance(text_color, str):
                        qtext_color = QColor(text_color)
                    elif isinstance(text_color, (list, tuple)):
                        from color_utils import list_to_color
                        qtext_color = list_to_color(text_color)
                    else:
                        qtext_color = text_color
                
                self.highlighter.add_pattern(pattern, qcolor, is_regex, 
                                           qtext_color, auto_text_color)
        
        # Ajouter le pattern de recherche si fourni
        if search_highlight_color:
            from color_utils import list_to_color, get_contrast_text_color
            if isinstance(search_highlight_color, (list, tuple)):
                search_bg = list_to_color(search_highlight_color)
            else:
                search_bg = search_highlight_color
            
            search_txt = search_text_color
            if search_txt and isinstance(search_txt, (list, tuple)):
                search_txt = list_to_color(search_txt)
            elif auto_search_text_color:
                search_txt = get_contrast_text_color(search_bg)
            
            # Le pattern de recherche sera géré séparément
            self.search_highlight_color = search_bg
            self.search_text_color = search_txt
    
    def set_font_size(self, size: int):
        """Définit la taille de la police"""
        font = self.text_edit.font()
        font.setPointSize(size)
        self.text_edit.setFont(font)
    
    def get_font_size(self) -> int:
        """Retourne la taille actuelle de la police"""
        return self.text_edit.font().pointSize()
    
    def highlight_search_match(self, start_pos: int, end_pos: int, 
                               bg_color, text_color):
        """Surligne un match de recherche avec les couleurs données"""
        from PyQt6.QtGui import QTextCharFormat, QTextCursor
        from PyQt6.QtWidgets import QTextEdit
        
        # Créer un format avec les couleurs
        char_format = QTextCharFormat()
        char_format.setBackground(bg_color)
        char_format.setForeground(text_color)
        
        # Créer une sélection extra pour le surlignage
        # QPlainTextEdit utilise le même type que QTextEdit pour ExtraSelection
        extra_selection = QTextEdit.ExtraSelection()
        cursor = self.text_edit.textCursor()
        cursor.setPosition(start_pos)
        cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
        extra_selection.cursor = cursor
        extra_selection.format = char_format
        
        # Appliquer la sélection
        self.text_edit.setExtraSelections([extra_selection])
        
        # Déplacer le curseur pour voir la sélection
        cursor.setPosition(start_pos)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()
    
    def clear_search_highlight(self):
        """Efface le surlignage de recherche"""
        self.text_edit.setExtraSelections([])
    
    def _update_text_options(self):
        """Met à jour les options d'affichage du texte"""
        option = QTextOption()
        flags = QTextOption.Flag(0)
        
        # Si on utilise l'éditeur personnalisé, on ne laisse jamais Qt dessiner les séparateurs
        # car on les dessine nous-mêmes avec la bonne couleur
        # Sinon, utiliser le rendu par défaut de Qt
        if not hasattr(self.text_edit, 'set_show_line_breaks'):
            # Éditeur standard : utiliser le flag Qt
            if self.show_line_breaks:
                flags |= QTextOption.Flag.ShowLineAndParagraphSeparators
            if self.show_spaces:
                flags |= QTextOption.Flag.ShowTabsAndSpaces
        # Si on utilise CustomPlainTextEdit, on active quand même le flag pour les espaces
        # pour que Qt dessine les points, puis on les redessine par-dessus avec notre couleur
        elif self.show_spaces:
            flags |= QTextOption.Flag.ShowTabsAndSpaces
        
        option.setFlags(flags)
        self.text_edit.document().setDefaultTextOption(option)
        
        # Appliquer la couleur des caractères invisibles via le highlighter
        # Le highlighter ne gère que les espaces et tabs, pas les sauts de ligne
        self.invisible_highlighter.set_color(self.invisible_chars_color)
        self.invisible_highlighter.set_show_line_breaks(False)  # Ne pas utiliser le highlighter pour les sauts de ligne
        self.invisible_highlighter.set_enabled(self.show_spaces)  # Activer seulement pour les espaces
        
        # Mettre à jour l'éditeur personnalisé pour les sauts de ligne et les espaces
        if hasattr(self.text_edit, 'set_invisible_chars_color'):
            self.text_edit.set_invisible_chars_color(self.invisible_chars_color)
            self.text_edit.set_show_line_breaks(self.show_line_breaks)
            if hasattr(self.text_edit, 'set_show_spaces'):
                self.text_edit.set_show_spaces(self.show_spaces)
    
    def set_show_line_breaks(self, show: bool):
        """Affiche/masque les sauts de ligne"""
        self.show_line_breaks = show
        self._update_text_options()
        # Réappliquer les patterns de mise en évidence après la mise à jour
        if self.highlighter:
            self.highlighter.rehighlight()
    
    def set_show_spaces(self, show: bool):
        """Affiche/masque les espaces"""
        self.show_spaces = show
        self._update_text_options()
        # Réappliquer les patterns de mise en évidence après la mise à jour
        # pour éviter que le highlighter des caractères invisibles n'écrase les formats
        if self.highlighter:
            self.highlighter.rehighlight()
    
    def get_show_line_breaks(self) -> bool:
        """Retourne si les sauts de ligne sont affichés"""
        return self.show_line_breaks
    
    def get_show_spaces(self) -> bool:
        """Retourne si les espaces sont affichés"""
        return self.show_spaces
    
    def set_invisible_chars_color(self, color):
        """Définit la couleur des caractères invisibles"""
        if isinstance(color, (list, tuple)):
            from color_utils import list_to_color
            self.invisible_chars_color = list_to_color(color)
        else:
            self.invisible_chars_color = color
        self._update_text_options()
