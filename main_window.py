"""
Fenêtre principale de l'application Comparateur PDF-Markdown
"""

import os
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                            QFileDialog, QMenuBar, QMenu, QToolBar,
                            QStatusBar, QLabel, QSpinBox, QMessageBox,
                            QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
                            QSlider, QSplitter, QPlainTextEdit, QFrame)
from pdf_viewer import PDFViewer
from markdown_editor import MarkdownEditor
from file_pattern import FilePattern
from project_manager import ProjectManager
from offset_config import OffsetConfigDialog
from highlight_config import HighlightConfigDialog
from search_replace_bar import SearchReplaceBar
from preferences_dialog import PreferencesDialog
from config_storage import ConfigStorage
from text_cleaner_panel import TextCleanerPanel
from orphan_couples_panel import OrphanCouplesPanel
from shortcuts_manager import ShortcutsManagerDialog


class PatternConfigDialog(QDialog):
    """Dialog pour configurer manuellement le pattern de nommage"""
    
    def __init__(self, detected_pattern: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration du pattern de nommage")
        self.setModal(True)
        
        layout = QFormLayout(self)
        
        info_label = QLabel(
            "Configurez le pattern de nommage des fichiers Markdown.\n"
            "Utilisez {:04d} pour un nombre à 4 chiffres avec zéros,\n"
            "{:03d} pour 3 chiffres, etc.\n"
            "Exemples: page{:03d}.md ou arbeitsc - {:04d}.md"
        )
        info_label.setWordWrap(True)
        layout.addRow(info_label)
        
        self.pattern_edit = QLineEdit()
        self.pattern_edit.setText(detected_pattern)
        self.pattern_edit.setPlaceholderText("Ex: page{num:03d}.md ou arbeitsc - {num:04d}.md")
        layout.addRow("Pattern:", self.pattern_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def get_pattern(self) -> str:
        return self.pattern_edit.text()


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Comparateur PDF-Markdown")
        self.setMinimumSize(1200, 800)
        
        # Variables d'état
        self.pdf_path = None
        self.markdown_directory = None
        self.file_pattern = None
        self.page_offset = 0
        self.synchronized = True
        self.highlight_patterns = []
        # Charger les préférences depuis la configuration
        self.config_storage = ConfigStorage()
        self.preferences = self.config_storage.get_preferences()
        # S'assurer que custom_buttons existe
        if 'custom_buttons' not in self.preferences:
            self.preferences['custom_buttons'] = []
        # S'assurer que invisible_chars_color existe
        if 'invisible_chars_color' not in self.preferences:
            self.preferences['invisible_chars_color'] = [128, 128, 128]
        # S'assurer que shortcuts existe
        if 'shortcuts' not in self.preferences:
            self.preferences['shortcuts'] = {}
        self.project_manager = ProjectManager()
        
        # Dictionnaire pour stocker les raccourcis personnalisés
        self.custom_shortcuts = {}
        
        # Créer l'interface
        self._create_widgets()
        self._create_menu_bar()
        self._create_toolbar()
        self._create_status_bar()
        self._connect_signals()
        
        # Raccourcis clavier
        self._setup_shortcuts()
        
        # Appliquer la couleur des caractères invisibles
        self._apply_invisible_chars_color()
        
        # Appliquer les raccourcis personnalisés
        self._apply_custom_shortcuts()
        
        # Restaurer la géométrie de la fenêtre
        saved_geometry = self.config_storage.get_window_geometry()
        if saved_geometry:
            self.setGeometry(
                saved_geometry['x'],
                saved_geometry['y'],
                saved_geometry['width'],
                saved_geometry['height']
            )
        
        # Restaurer l'état du panneau de nettoyage après un petit délai
        # pour laisser l'interface se construire complètement
        saved_visible = self.config_storage.get_text_cleaner_panel_visible()
        if saved_visible and hasattr(self, 'text_cleaner_action'):
            QTimer.singleShot(100, lambda: self._toggle_text_cleaner_panel(True))
        # Restaurer l'état du panneau couplages orphelins
        saved_orphan = self.config_storage.get_orphan_couples_panel_visible()
        if saved_orphan and hasattr(self, 'orphan_couples_action'):
            QTimer.singleShot(150, lambda: self._toggle_orphan_couples_panel(True))
        
        # Appliquer l'état du contexte PDF au viewer
        self.pdf_viewer.set_show_adjacent_context(self.config_storage.get_show_pdf_context())
        
        # Charger le dernier projet ouvert
        self._load_last_project()
    
    def _create_widgets(self):
        """Crée les widgets principaux"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal vertical
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Splitter horizontal principal pour PDF et la zone droite
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panneau PDF (gauche)
        self.pdf_viewer = PDFViewer()
        main_splitter.addWidget(self.pdf_viewer)
        
        # Splitter horizontal pour Markdown et panneau de nettoyage (droite)
        right_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Conteneur Markdown : contexte page précédente + éditeur + contexte page suivante
        self._md_context_lines = 8
        markdown_container = QWidget()
        markdown_layout = QVBoxLayout(markdown_container)
        markdown_layout.setContentsMargins(0, 0, 0, 0)
        markdown_layout.setSpacing(0)
        
        self.md_context_prev_widget = QPlainTextEdit()
        self.md_context_prev_widget.setReadOnly(True)
        self.md_context_prev_widget.setMaximumHeight(120)
        self.md_context_prev_widget.setPlaceholderText("(fin de la page précédente)")
        self.md_context_prev_widget.setVisible(self.config_storage.get_show_markdown_context())
        markdown_layout.addWidget(self.md_context_prev_widget)
        
        self.markdown_editor = MarkdownEditor()
        markdown_layout.addWidget(self.markdown_editor)
        
        self.md_context_next_widget = QPlainTextEdit()
        self.md_context_next_widget.setReadOnly(True)
        self.md_context_next_widget.setMaximumHeight(120)
        self.md_context_next_widget.setPlaceholderText("(début de la page suivante)")
        self.md_context_next_widget.setVisible(self.config_storage.get_show_markdown_context())
        markdown_layout.addWidget(self.md_context_next_widget)
        
        right_splitter.addWidget(markdown_container)
        
        # Panneau de nettoyage de texte (à droite, caché par défaut)
        self.text_cleaner_panel = None  # Sera créé quand nécessaire
        
        main_splitter.addWidget(right_splitter)
        
        # Sauvegarder les références aux splitters pour pouvoir ajuster les tailles
        self.main_splitter = main_splitter
        self.right_splitter = right_splitter
        
        # Restaurer les tailles sauvegardées ou utiliser les valeurs par défaut
        splitter_sizes = self.config_storage.get_splitter_sizes()
        main_sizes = splitter_sizes.get('main', [500, 500])
        right_sizes = splitter_sizes.get('right', [600, 400])
        
        main_splitter.setSizes(main_sizes)
        # Pour le splitter horizontal de droite, on n'a qu'un seul widget pour l'instant (Markdown)
        # Les tailles seront restaurées quand le panneau de nettoyage sera créé
        if len(right_sizes) == 2 and right_sizes[1] == 0:
            # Panneau masqué, utiliser juste la taille totale pour Markdown
            right_splitter.setSizes([sum(right_sizes), 0])
        else:
            # Si le panneau sera créé plus tard, on utilise les tailles sauvegardées
            right_splitter.setSizes([sum(right_sizes) if isinstance(right_sizes, list) else 1000, 0])
        
        # Connecter les signaux pour sauvegarder les tailles quand elles changent
        main_splitter.splitterMoved.connect(self._on_main_splitter_moved)
        right_splitter.splitterMoved.connect(self._on_right_splitter_moved)
        
        main_layout.addWidget(main_splitter, stretch=1)
        
        # Barre de recherche/remplacement (en bas, cachée par défaut)
        self.search_replace_bar = None  # Sera créée quand nécessaire
        
        # Panneau couplages orphelins (en bas, caché par défaut)
        self.orphan_couples_panel = None
    
    def _create_menu_bar(self):
        """Crée la barre de menus"""
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu("Fichier")
        
        new_project_action = file_menu.addAction("Nouveau projet")
        new_project_action.setShortcut(QKeySequence.StandardKey.New)
        new_project_action.triggered.connect(self._new_project)
        
        open_project_action = file_menu.addAction("Ouvrir projet")
        open_project_action.setShortcut(QKeySequence.StandardKey.Open)
        open_project_action.triggered.connect(self._open_project)
        
        file_menu.addSeparator()
        
        save_project_action = file_menu.addAction("Enregistrer projet")
        save_project_action.setShortcut(QKeySequence.StandardKey.Save)
        save_project_action.triggered.connect(self._save_project)
        
        save_as_project_action = file_menu.addAction("Enregistrer projet sous...")
        save_as_project_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_project_action.triggered.connect(self._save_project_as)
        
        file_menu.addSeparator()
        
        load_pdf_action = file_menu.addAction("Charger PDF...")
        load_pdf_action.triggered.connect(self._load_pdf)
        
        load_markdown_action = file_menu.addAction("Charger dossier Markdown...")
        load_markdown_action.triggered.connect(self._load_markdown)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Quitter")
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        
        # Menu Édition
        edit_menu = menubar.addMenu("Édition")
        
        undo_action = edit_menu.addAction("Annuler")
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self._undo)
        
        redo_action = edit_menu.addAction("Refaire")
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self._redo)
        
        edit_menu.addSeparator()
        
        cut_action = edit_menu.addAction("Couper")
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(self._cut)
        
        copy_action = edit_menu.addAction("Copier")
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self._copy)
        
        paste_action = edit_menu.addAction("Coller")
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self._paste)
        
        select_all_action = edit_menu.addAction("Tout sélectionner")
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.triggered.connect(self._select_all)
        
        edit_menu.addSeparator()
        
        search_replace_action = edit_menu.addAction("Rechercher/Remplacer...")
        search_replace_action.setShortcut(QKeySequence.StandardKey.Find)
        search_replace_action.triggered.connect(self._open_search_replace)
        
        # Menu Affichage
        view_menu = menubar.addMenu("Affichage")
        
        highlight_config_action = view_menu.addAction("Configurer mise en évidence...")
        highlight_config_action.triggered.connect(self._configure_highlight)
        
        preferences_action = view_menu.addAction("Préférences...")
        preferences_action.triggered.connect(self._open_preferences)
        
        shortcuts_action = view_menu.addAction("Gestionnaire de raccourcis...")
        shortcuts_action.triggered.connect(self._open_shortcuts_manager)
        
        view_menu.addSeparator()
        
        zoom_in_action = view_menu.addAction("Zoom PDF +")
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self._zoom_pdf_in)
        
        zoom_out_action = view_menu.addAction("Zoom PDF -")
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self._zoom_pdf_out)
        
        view_menu.addSeparator()
        
        font_larger_action = view_menu.addAction("Police Markdown +")
        font_larger_action.triggered.connect(self._markdown_font_larger)
        
        font_smaller_action = view_menu.addAction("Police Markdown -")
        font_smaller_action.triggered.connect(self._markdown_font_smaller)
        
        view_menu.addSeparator()
        
        text_cleaner_action = view_menu.addAction("Panneau de nettoyage de texte")
        text_cleaner_action.setCheckable(True)
        # Restaurer l'état sauvegardé
        saved_visible = self.config_storage.get_text_cleaner_panel_visible()
        text_cleaner_action.setChecked(saved_visible)
        text_cleaner_action.toggled.connect(self._toggle_text_cleaner_panel)
        self.text_cleaner_action = text_cleaner_action  # Sauvegarder la référence
        
        orphan_couples_action = view_menu.addAction("Panneau couplages orphelins")
        orphan_couples_action.setCheckable(True)
        saved_orphan_visible = self.config_storage.get_orphan_couples_panel_visible()
        orphan_couples_action.setChecked(saved_orphan_visible)
        orphan_couples_action.toggled.connect(self._toggle_orphan_couples_panel)
        self.orphan_couples_action = orphan_couples_action
        
        view_menu.addSeparator()
        
        # Contexte des pages adjacentes
        self.show_pdf_context_action = view_menu.addAction("Afficher contexte des pages (PDF)")
        self.show_pdf_context_action.setCheckable(True)
        self.show_pdf_context_action.setChecked(self.config_storage.get_show_pdf_context())
        self.show_pdf_context_action.toggled.connect(self._toggle_show_pdf_context)
        
        self.show_markdown_context_action = view_menu.addAction("Afficher contexte des pages (Markdown)")
        self.show_markdown_context_action.setCheckable(True)
        self.show_markdown_context_action.setChecked(self.config_storage.get_show_markdown_context())
        self.show_markdown_context_action.toggled.connect(self._toggle_show_markdown_context)
        
        view_menu.addSeparator()
        
        self.dynamic_highlight_action = view_menu.addAction("Mode surlignement dynamique")
        self.dynamic_highlight_action.setCheckable(True)
        self.dynamic_highlight_action.setChecked(self.config_storage.get_dynamic_highlight_enabled())
        self.dynamic_highlight_action.toggled.connect(self._toggle_dynamic_highlight)
        
        view_menu.addSeparator()
        
        sync_action = view_menu.addAction("Synchronisation")
        sync_action.setCheckable(True)
        sync_action.setChecked(True)
        sync_action.toggled.connect(self._toggle_synchronization)
        
        # Menu Aide
        help_menu = menubar.addMenu("Aide")
        
        manual_action = help_menu.addAction("Manuel")
        manual_action.setShortcut(QKeySequence("F1"))
        manual_action.triggered.connect(self._show_manual)
        
        about_action = help_menu.addAction("À propos")
        about_action.triggered.connect(self._show_about)
    
    def _create_toolbar(self):
        """Crée la barre d'outils"""
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)
        
        # Indicateur de page PDF
        self.toolbar.addWidget(QLabel("PDF:"))
        self.pdf_page_spinbox = QSpinBox()
        self.pdf_page_spinbox.setMinimum(1)
        self.pdf_page_spinbox.setMaximum(1)
        self.pdf_page_spinbox.valueChanged.connect(self._on_pdf_page_changed)
        self.toolbar.addWidget(self.pdf_page_spinbox)
        self.toolbar.addWidget(QLabel("/"))
        self.pdf_total_label = QLabel("0")
        self.toolbar.addWidget(self.pdf_total_label)
        
        self.toolbar.addSeparator()
        
        # Décalage
        self.toolbar.addWidget(QLabel("Décalage:"))
        self.offset_spinbox = QSpinBox()
        self.offset_spinbox.setRange(-1000, 1000)
        self.offset_spinbox.setValue(0)
        self.offset_spinbox.valueChanged.connect(self._on_offset_changed)
        self.toolbar.addWidget(self.offset_spinbox)
        
        offset_config_button = self.toolbar.addAction("⚙️")
        offset_config_button.setToolTip("Configurer le décalage")
        offset_config_button.triggered.connect(self._configure_offset)
        self.toolbar.addWidget(QLabel(""))
        
        self.toolbar.addSeparator()
        
        # Indicateur de page Markdown
        self.toolbar.addWidget(QLabel("Markdown:"))
        self.markdown_page_label = QLabel("0")
        self.toolbar.addWidget(self.markdown_page_label)
        self.toolbar.addWidget(QLabel("/"))
        self.markdown_total_label = QLabel("0")
        self.toolbar.addWidget(self.markdown_total_label)
        
        self.toolbar.addSeparator()
        
        # Contrôles de zoom PDF
        self.toolbar.addWidget(QLabel("Zoom PDF:"))
        zoom_out_btn = self.toolbar.addAction("−")
        zoom_out_btn.setToolTip("Diminuer le zoom")
        zoom_out_btn.triggered.connect(self._zoom_pdf_out)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toolbar.addWidget(self.zoom_label)
        
        zoom_in_btn = self.toolbar.addAction("+")
        zoom_in_btn.setToolTip("Augmenter le zoom")
        zoom_in_btn.triggered.connect(self._zoom_pdf_in)
        
        self.toolbar.addSeparator()
        
        # Contrôle de taille de police Markdown
        self.toolbar.addWidget(QLabel("Police:"))
        font_smaller_btn = self.toolbar.addAction("−")
        font_smaller_btn.setToolTip("Diminuer la taille de police")
        font_smaller_btn.triggered.connect(self._markdown_font_smaller)
        
        self.font_size_label = QLabel("12pt")
        self.font_size_label.setMinimumWidth(50)
        self.font_size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toolbar.addWidget(self.font_size_label)
        
        font_larger_btn = self.toolbar.addAction("+")
        font_larger_btn.setToolTip("Augmenter la taille de police")
        font_larger_btn.triggered.connect(self._markdown_font_larger)
        
        self.toolbar.addSeparator()
        
        # Boutons pour les caractères invisibles Markdown
        self.show_line_breaks_action = self.toolbar.addAction("¶")
        self.show_line_breaks_action.setCheckable(True)
        self.show_line_breaks_action.setChecked(False)
        self.show_line_breaks_action.setToolTip("Afficher/masquer les sauts de ligne (¶)")
        self.show_line_breaks_action.triggered.connect(self._toggle_show_line_breaks)
        
        self.show_spaces_action = self.toolbar.addAction("·")
        self.show_spaces_action.setCheckable(True)
        self.show_spaces_action.setChecked(False)
        self.show_spaces_action.setToolTip("Afficher/masquer les espaces (·)")
        self.show_spaces_action.triggered.connect(self._toggle_show_spaces)
        
        self.toolbar.addSeparator()
        
        # Bouton pour inverser les couleurs du PDF
        self.invert_pdf_colors_action = self.toolbar.addAction("🌙")
        self.invert_pdf_colors_action.setCheckable(True)
        self.invert_pdf_colors_action.setChecked(False)
        self.invert_pdf_colors_action.setToolTip("Inverser les couleurs du PDF (mode sombre)")
        self.invert_pdf_colors_action.triggered.connect(self._toggle_invert_pdf_colors)
        
        # Appliquer un style avec cadre fin pour tous les boutons de la barre d'outils
        self.toolbar.setStyleSheet("""
            QToolButton {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 2px;
                margin: 1px;
            }
            QToolButton:hover {
                border: 1px solid #a0a0a0;
                background-color: #f0f0f0;
            }
            QToolButton:checked {
                border: 1px solid #808080;
                background-color: #e0e0e0;
            }
            QToolButton:pressed {
                border: 1px solid #606060;
                background-color: #d0d0d0;
            }
        """)
        
        self.toolbar.addSeparator()
        
        # Boutons personnalisés (seront ajoutés dynamiquement)
        self.custom_buttons_widgets = []
        self._update_custom_buttons()
        
        # Initialiser le dictionnaire des raccourcis personnalisés
        self.custom_shortcuts = {}
    
    def _create_status_bar(self):
        """Crée la barre de statut"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Prêt")
    
    def _connect_signals(self):
        """Connecte les signaux"""
        self.pdf_viewer.pageChanged.connect(self._on_pdf_page_changed_signal)
        self.pdf_viewer.textSelected.connect(self._on_pdf_text_selected)
        self.markdown_editor.text_edit.selectionChanged.connect(self._on_markdown_selection_changed)
    
    def _setup_shortcuts(self):
        """Configure les raccourcis clavier"""
        # Page Up / Page Down pour navigation
        page_up_shortcut = QShortcut(QKeySequence(Qt.Key.Key_PageUp), self)
        page_up_shortcut.activated.connect(self.previous_page)
        
        page_down_shortcut = QShortcut(QKeySequence(Qt.Key.Key_PageDown), self)
        page_down_shortcut.activated.connect(self.next_page)
    
    def _new_project(self):
        """Crée un nouveau projet"""
        if self._check_unsaved_changes():
            self._reset_project()
    
    def _open_project(self):
        """Ouvre un projet existant"""
        if self._check_unsaved_changes():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Ouvrir un projet", "",
                "Fichiers de projet (*.comparator *.json);;Tous les fichiers (*)"
            )
            
            if file_path:
                self._load_project(file_path)
    
    def _save_project(self):
        """Sauvegarde le projet actuel"""
        if not self.project_manager.current_project_path:
            self._save_project_as()
        else:
            self._save_project_to_file(str(self.project_manager.current_project_path))
    
    def _save_project_as(self):
        """Sauvegarde le projet sous un nouveau nom"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le projet", "",
            "Fichiers de projet (*.comparator);;Fichiers JSON (*.json);;Tous les fichiers (*)"
        )
        
        if file_path:
            self._save_project_to_file(file_path)
    
    def _save_project_to_file(self, file_path: str):
        """Sauvegarde les données du projet dans un fichier"""
        pattern_str = self.file_pattern.pattern if self.file_pattern else ""
        
        project_data = self.project_manager.export_project_data(
            self.pdf_path or "",
            self.markdown_directory or "",
            pattern_str,
            self.page_offset,
            self.synchronized,
            self.highlight_patterns,
            self.pdf_viewer.get_zoom(),
            self.markdown_editor.get_font_size()
        )
        # Ajouter les préférences
        project_data['preferences'] = self.preferences
        
        if self.project_manager.save_project(file_path, project_data):
            # Sauvegarder le chemin comme dernier projet ouvert
            self.config_storage.set_last_project_path(file_path)
            self.status_bar.showMessage(f"Projet sauvegardé: {file_path}", 3000)
        else:
            QMessageBox.critical(self, "Erreur", "Impossible de sauvegarder le projet.")
    
    def _load_project(self, file_path: str):
        """Charge un projet depuis un fichier"""
        project_data = self.project_manager.load_project(file_path)
        
        if not project_data:
            # Ne pas afficher d'erreur si c'est le chargement automatique du dernier projet
            return
        
        # Sauvegarder le chemin du projet comme dernier projet ouvert
        self.config_storage.set_last_project_path(file_path)
        
        # Charger les données
        pdf_path = project_data.get('pdf_path', '')
        markdown_dir = project_data.get('markdown_directory', '')
        pattern_str = project_data.get('markdown_pattern', '')
        self.page_offset = project_data.get('page_offset', 0)
        self.synchronized = project_data.get('synchronized', True)
        self.highlight_patterns = project_data.get('highlight_patterns', [])
        
        # Charger les préférences si disponibles
        if 'preferences' in project_data:
            self.preferences = project_data['preferences']
            # S'assurer que custom_buttons existe
            if 'custom_buttons' not in self.preferences:
                self.preferences['custom_buttons'] = []
            # Sauvegarder les préférences dans la config globale
            self.config_storage.set_preferences(self.preferences)
        
        # Charger le PDF
        if pdf_path and Path(pdf_path).exists():
            self._load_pdf_file(pdf_path)
        
        # Charger le dossier Markdown
        if markdown_dir and Path(markdown_dir).exists():
            self._load_markdown_directory(markdown_dir, pattern_str)
        
        # Appliquer les patterns de mise en évidence
        self._apply_highlight_patterns()
        
        # Mettre à jour les boutons personnalisés
        self._update_custom_buttons()
        
        # Mettre à jour l'interface
        self.offset_spinbox.setValue(self.page_offset)
        
        # Restaurer le zoom et la taille de police si sauvegardés
        zoom_level = project_data.get('zoom_level', 1.0)
        if zoom_level:
            self.pdf_viewer.set_zoom(zoom_level)
        
        font_size = project_data.get('font_size', 12)
        if font_size:
            self.markdown_editor.set_font_size(font_size)
        
        self._update_zoom_label()
        self._update_font_size_label()
        
        self.status_bar.showMessage(f"Projet chargé: {file_path}", 3000)
    
    def _reset_project(self):
        """Réinitialise le projet"""
        self.pdf_path = None
        self.markdown_directory = None
        self.file_pattern = None
        self.page_offset = 0
        self.synchronized = True
        self.highlight_patterns = []
        self.pdf_viewer.doc = None
        self.markdown_editor.clear()
        self._update_page_indicators()
    
    def _check_unsaved_changes(self) -> bool:
        """Vérifie s'il y a des modifications non sauvegardées"""
        # Pour l'instant, toujours retourner True
        # Dans une version complète, on pourrait vérifier les modifications
        return True
    
    def _load_pdf(self):
        """Ouvre le dialog pour charger un PDF"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Charger un fichier PDF", "",
            "Fichiers PDF (*.pdf);;Tous les fichiers (*)"
        )
        
        if file_path:
            self._load_pdf_file(file_path)
    
    def _load_pdf_file(self, file_path: str, restore_page: bool = True):
        """Charge un fichier PDF
        
        Args:
            restore_page: Si True, restaure la dernière page affichée
        """
        if self.pdf_viewer.load_pdf(file_path):
            self.pdf_path = file_path
            self._update_page_indicators()
            self._update_zoom_label()
            self.status_bar.showMessage(f"PDF chargé: {file_path}", 3000)
            
            # Restaurer la dernière page affichée si disponible
            if restore_page:
                last_page = self.config_storage.get_last_pdf_page(file_path)
                if last_page is not None and last_page >= 1:
                    # last_page est 1-indexed, current_page_num est 0-indexed
                    page_index = last_page - 1
                    if page_index < self.pdf_viewer.get_page_count():
                        self.pdf_viewer.go_to_page(page_index)
                        self._update_page_indicators()
            
            # Afficher la page sauvegardée ou synchroniser si synchronisé
            if self.synchronized:
                self._sync_to_pdf_page()
        else:
            QMessageBox.critical(self, "Erreur", "Impossible de charger le PDF.")
    
    def _load_markdown(self):
        """Ouvre le dialog pour charger un dossier Markdown"""
        directory = QFileDialog.getExistingDirectory(
            self, "Choisir le dossier contenant les fichiers Markdown"
        )
        
        if directory:
            self._load_markdown_directory(directory)
    
    def _load_markdown_directory(self, directory: str, pattern: str = None):
        """Charge un dossier Markdown"""
        try:
            if pattern:
                self.file_pattern = FilePattern(directory, pattern)
            else:
                self.file_pattern = FilePattern(directory)
            
            if not self.file_pattern.pattern:
                # Proposer de configurer manuellement
                dialog = PatternConfigDialog("", self)
                if dialog.exec():
                    pattern = dialog.get_pattern()
                    if pattern:
                        self.file_pattern = FilePattern(directory, pattern)
                    else:
                        QMessageBox.warning(
                            self, "Attention",
                            "Aucun pattern détecté. Veuillez configurer manuellement."
                        )
                        return
                else:
                    return
            
            self.markdown_directory = directory
            self._update_page_indicators()
            
            # Mettre à jour la barre de recherche si elle existe
            if self.search_replace_bar:
                self.search_replace_bar.file_pattern = self.file_pattern
            
            self.status_bar.showMessage(f"Dossier Markdown chargé: {directory}", 3000)
            
            # Charger la première page si synchronisé
            if self.synchronized:
                self._sync_to_pdf_page()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {e}")
    
    def _configure_highlight(self):
        """Ouvre le dialog de configuration de mise en évidence"""
        dialog = HighlightConfigDialog(self.highlight_patterns, self)
        dialog.patternsChanged.connect(self._on_highlight_patterns_changed)
        dialog.exec()
    
    def _on_highlight_patterns_changed(self, patterns: list):
        """Appelé quand les patterns de mise en évidence changent"""
        self.highlight_patterns = patterns
        self._apply_highlight_patterns()
    
    def _apply_highlight_patterns(self):
        """Applique les patterns de mise en évidence avec les préférences"""
        search_bg = self.preferences.get('search_highlight_color')
        search_txt = self.preferences.get('search_text_color')
        auto_search = self.preferences.get('auto_search_text_color', True)
        self.markdown_editor.set_highlight_patterns(
            self.highlight_patterns,
            search_bg, search_txt, auto_search
        )
    
    def _open_preferences(self):
        """Ouvre le dialog de préférences"""
        dialog = PreferencesDialog(self.preferences, self)
        dialog.preferencesChanged.connect(self._on_preferences_changed)
        dialog.exec()
    
    def _on_preferences_changed(self, preferences: dict):
        """Appelé quand les préférences changent"""
        self.preferences = preferences
        self.config_storage.set_preferences(preferences)  # Sauvegarder dans la config
        self._apply_highlight_patterns()
        self._update_custom_buttons()
        self._apply_invisible_chars_color()
        self._apply_custom_shortcuts()
    
    def _on_main_splitter_moved(self, pos: int, index: int):
        """Appelé quand le splitter principal est déplacé"""
        sizes = self.main_splitter.sizes()
        self.config_storage.set_splitter_sizes(main_sizes=sizes)
    
    def _on_right_splitter_moved(self, pos: int, index: int):
        """Appelé quand le splitter de droite est déplacé"""
        sizes = self.right_splitter.sizes()
        self.config_storage.set_splitter_sizes(right_sizes=sizes)
    
    def closeEvent(self, event):
        """Appelé quand la fenêtre se ferme - sauvegarde l'état actuel"""
        # Sauvegarder le numéro de page PDF actuel
        if self.pdf_path and self.pdf_viewer.doc:
            current_page = self.pdf_viewer.current_page_num + 1  # Convertir en 1-indexed
            self.config_storage.set_last_pdf_page(self.pdf_path, current_page)
        
        # Sauvegarder les tailles des splitters
        main_sizes = self.main_splitter.sizes()
        right_sizes = self.right_splitter.sizes()
        self.config_storage.set_splitter_sizes(main_sizes=main_sizes, right_sizes=right_sizes)
        
        # Sauvegarder la géométrie de la fenêtre
        geometry = self.geometry()
        self.config_storage.set_window_geometry(
            geometry.x(),
            geometry.y(),
            geometry.width(),
            geometry.height()
        )
        
        # Sauvegarder l'état du panneau de nettoyage
        if hasattr(self, 'text_cleaner_action'):
            self.config_storage.set_text_cleaner_panel_visible(self.text_cleaner_action.isChecked())
        if hasattr(self, 'orphan_couples_action'):
            self.config_storage.set_orphan_couples_panel_visible(self.orphan_couples_action.isChecked())
        
        # Sauvegarder contexte pages et surlignement dynamique
        if hasattr(self, 'show_pdf_context_action'):
            self.config_storage.set_show_pdf_context(self.show_pdf_context_action.isChecked())
        if hasattr(self, 'show_markdown_context_action'):
            self.config_storage.set_show_markdown_context(self.show_markdown_context_action.isChecked())
        if hasattr(self, 'dynamic_highlight_action'):
            self.config_storage.set_dynamic_highlight_enabled(self.dynamic_highlight_action.isChecked())
        
        # S'assurer que les préférences sont sauvegardées
        self.config_storage.set_preferences(self.preferences)
        
        # Appeler la méthode parent pour fermer normalement
        super().closeEvent(event)
    
    def _load_last_project(self):
        """Charge le dernier projet ouvert si disponible"""
        last_project = self.config_storage.get_last_project_path()
        if last_project and Path(last_project).exists():
            # Charger après un petit délai pour laisser l'interface se construire
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self._load_project(last_project))
    
    def _configure_offset(self):
        """Ouvre le dialog de configuration du décalage"""
        pdf_page = self.pdf_viewer.current_page_num + 1
        markdown_page = self._calculate_markdown_page(pdf_page)
        
        dialog = OffsetConfigDialog(
            self.page_offset, pdf_page, markdown_page, self
        )
        dialog.offsetChanged.connect(self._on_offset_changed)
        dialog.exec()
    
    def _on_offset_changed(self, value: int):
        """Appelé quand le décalage change"""
        self.page_offset = value
        if self.synchronized:
            self._sync_to_pdf_page()
    
    def _toggle_synchronization(self, enabled: bool):
        """Active/désactive la synchronisation"""
        self.synchronized = enabled
    
    def _toggle_show_pdf_context(self, enabled: bool):
        """Active/désactive l'affichage du contexte des pages adjacentes (PDF)."""
        self.pdf_viewer.set_show_adjacent_context(enabled)
        self.config_storage.set_show_pdf_context(enabled)
    
    def _toggle_show_markdown_context(self, enabled: bool):
        """Active/désactive l'affichage du contexte des pages adjacentes (Markdown)."""
        self.config_storage.set_show_markdown_context(enabled)
        self._update_markdown_context_visibility()
    
    def _toggle_dynamic_highlight(self, enabled: bool):
        """Active/désactive le mode surlignement dynamique PDF ↔ Markdown."""
        self.config_storage.set_dynamic_highlight_enabled(enabled)
        self._apply_dynamic_highlight_mode()
    
    def _update_markdown_context_visibility(self):
        """Affiche ou masque les zones de contexte Markdown (page précédente/suivante)."""
        if not hasattr(self, 'md_context_prev_widget'):
            return
        visible = self.show_markdown_context_action.isChecked()
        self.md_context_prev_widget.setVisible(visible)
        self.md_context_next_widget.setVisible(visible)
        if visible:
            self._update_markdown_context_content()
    
    def _update_markdown_context_content(self):
        """Met à jour le contenu des zones contexte page précédente/suivante."""
        if not self.file_pattern or not hasattr(self, 'md_context_prev_widget'):
            return
        pdf_page = self.pdf_viewer.current_page_num + 1
        markdown_page = self._calculate_markdown_page(pdf_page)
        total = self.file_pattern.get_total_pages()
        # Dernières lignes de la page précédente
        if markdown_page > 1:
            path = self.file_pattern.get_filepath(markdown_page - 1)
            if path and path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.read().splitlines()
                    self.md_context_prev_widget.setPlainText("\n".join(lines[-self._md_context_lines:]))
                    # Scroller en bas pour afficher la fin de la page précédente
                    from PyQt6.QtGui import QTextCursor
                    cursor = self.md_context_prev_widget.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    self.md_context_prev_widget.setTextCursor(cursor)
                    self.md_context_prev_widget.verticalScrollBar().setValue(
                        self.md_context_prev_widget.verticalScrollBar().maximum()
                    )
                except Exception:
                    self.md_context_prev_widget.setPlainText("")
            else:
                self.md_context_prev_widget.setPlainText("")
        else:
            self.md_context_prev_widget.setPlainText("")
        # Premières lignes de la page suivante
        if markdown_page < total:
            path = self.file_pattern.get_filepath(markdown_page + 1)
            if path and path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.read().splitlines()
                    self.md_context_next_widget.setPlainText("\n".join(lines[:self._md_context_lines]))
                except Exception:
                    self.md_context_next_widget.setPlainText("")
            else:
                self.md_context_next_widget.setPlainText("")
        else:
            self.md_context_next_widget.setPlainText("")
    
    def _apply_dynamic_highlight_mode(self):
        """Active ou désactive l'affichage du surlignement dynamique (connexions déjà faites, on efface si désactivé)."""
        if not self.dynamic_highlight_action.isChecked():
            self.pdf_viewer.clear_highlight_rects()
            self.markdown_editor.clear_search_highlight()
    
    def _normalize_text_for_match(self, s: str) -> str:
        """Normalise le texte pour la recherche croisée PDF/Markdown."""
        import re
        s = (s or "").replace("\r\n", "\n").replace("\r", " ").replace("\n", " ")
        return re.sub(r'\s+', ' ', s).strip()
    
    def _on_pdf_text_selected(self, text: str):
        """Surligne dans l'éditeur Markdown le texte sélectionné dans le PDF (si mode surlignement dynamique)."""
        if not hasattr(self, 'dynamic_highlight_action') or not self.dynamic_highlight_action.isChecked():
            return
        if not text or not self.file_pattern:
            return
        content = self.markdown_editor.get_content()
        if not content:
            return
        text_norm = self._normalize_text_for_match(text)
        if not text_norm:
            return
        start_orig, end_orig = self._find_normalized_in_content(content, text_norm)
        if start_orig is None:
            return
        from color_utils import list_to_color, get_contrast_text_color
        search_bg_list = self.preferences.get('search_highlight_color', [255, 255, 0])
        search_txt_list = self.preferences.get('search_text_color')
        auto_search = self.preferences.get('auto_search_text_color', True)
        search_bg = list_to_color(search_bg_list) if isinstance(search_bg_list, list) else search_bg_list
        if auto_search or search_txt_list is None:
            search_txt = get_contrast_text_color(search_bg)
        else:
            search_txt = list_to_color(search_txt_list) if isinstance(search_txt_list, list) else search_txt_list
        self.markdown_editor.highlight_search_match(start_orig, end_orig, search_bg, search_txt)
    
    def _find_normalized_in_content(self, content: str, text_norm: str) -> tuple:
        """Trouve la première occurrence de text_norm (normalisé) dans content. Retourne (start, end) en indices originaux ou (None, None)."""
        import re
        if not text_norm or not content:
            return (None, None)
        norm_to_orig_start = []
        norm_chars = []
        i = 0
        n = len(content)
        while i < n:
            start = i
            if content[i:i+2] == '\r\n':
                norm_chars.append(' ')
                norm_to_orig_start.append(start)
                i += 2
            elif content[i] in '\r\n':
                norm_chars.append(' ')
                norm_to_orig_start.append(start)
                i += 1
            elif content[i].isspace():
                norm_chars.append(' ')
                norm_to_orig_start.append(start)
                i += 1
                while i < n and content[i].isspace():
                    i += 1
            else:
                norm_chars.append(content[i])
                norm_to_orig_start.append(start)
                i += 1
        normalized = ''.join(norm_chars)
        idx = normalized.find(text_norm)
        if idx < 0:
            return (None, None)
        start_orig = norm_to_orig_start[idx]
        end_idx = idx + len(text_norm)
        if end_idx >= len(norm_to_orig_start):
            end_orig = len(content)
        else:
            end_orig = norm_to_orig_start[end_idx]
        return (start_orig, end_orig)
    
    def _on_markdown_selection_changed(self):
        """Surligne sur le PDF le texte sélectionné dans l'éditeur Markdown (si mode surlignement dynamique)."""
        if not hasattr(self, 'dynamic_highlight_action') or not self.dynamic_highlight_action.isChecked():
            return
        cursor = self.markdown_editor.text_edit.textCursor()
        text = cursor.selectedText()
        if not text:
            self.pdf_viewer.clear_highlight_rects()
            return
        text_norm = self._normalize_text_for_match(text)
        if not text_norm:
            self.pdf_viewer.clear_highlight_rects()
            return
        rects = self.pdf_viewer.find_text_rects_in_page(text_norm)
        if rects:
            self.pdf_viewer.set_highlight_rects(rects)
        else:
            self.pdf_viewer.clear_highlight_rects()
    
    def _toggle_text_cleaner_panel(self, enabled: bool):
        """Affiche/masque le panneau de nettoyage de texte"""
        # Créer le panneau s'il n'existe pas
        if self.text_cleaner_panel is None:
            self.text_cleaner_panel = TextCleanerPanel(self)
            self.text_cleaner_panel.pasteToEditorRequested.connect(self._paste_cleaned_text_to_editor)
            
            # Ajouter le panneau au splitter horizontal à droite
            self.right_splitter.addWidget(self.text_cleaner_panel)
        
        # Afficher/masquer le panneau
        if enabled:
            self.text_cleaner_panel.show()
            # Restaurer les tailles sauvegardées ou utiliser les proportions par défaut
            splitter_sizes = self.config_storage.get_splitter_sizes()
            right_sizes = splitter_sizes.get('right', [600, 400])
            
            # Si le panneau était masqué, les tailles peuvent être [total, 0]
            # Dans ce cas, utiliser les proportions par défaut
            if len(right_sizes) == 2 and right_sizes[1] == 0:
                current_sizes = self.right_splitter.sizes()
                if len(current_sizes) == 2:
                    total = sum(current_sizes) if sum(current_sizes) > 0 else 1000
                    right_sizes = [int(total * 0.6), int(total * 0.4)]
            
            self.right_splitter.setSizes(right_sizes)
        else:
            self.text_cleaner_panel.hide()
            # Redonner tout l'espace au Markdown
            current_sizes = self.right_splitter.sizes()
            if len(current_sizes) == 2:
                total = sum(current_sizes)
                self.right_splitter.setSizes([total, 0])
                # Sauvegarder les tailles (avec 0 pour le panneau masqué)
                self.config_storage.set_splitter_sizes(right_sizes=[total, 0])
        
        # Sauvegarder l'état de visibilité
        self.config_storage.set_text_cleaner_panel_visible(enabled)
    
    def _toggle_orphan_couples_panel(self, enabled: bool):
        """Affiche/masque le panneau couplages orphelins (en bas)."""
        if self.orphan_couples_panel is None:
            self.orphan_couples_panel = OrphanCouplesPanel(self)
            self.orphan_couples_panel.set_content_callback(self.markdown_editor.get_content)
            self.orphan_couples_panel.set_all_pages_callback(self._get_all_markdown_pages_content)
            self.orphan_couples_panel.goToLineRequested.connect(self._on_orphan_go_to_line)
            self.orphan_couples_panel.goToPageLineRequested.connect(self._on_orphan_go_to_page_line)
            central_widget = self.centralWidget()
            main_layout = central_widget.layout()
            main_layout.addWidget(self.orphan_couples_panel)
        if enabled:
            self.orphan_couples_panel.show()
        else:
            self.orphan_couples_panel.hide()
        self.config_storage.set_orphan_couples_panel_visible(enabled)
    
    def _get_all_markdown_pages_content(self):
        """Retourne une liste de (page_num, texte) pour toutes les pages Markdown du projet."""
        if not self.file_pattern:
            return []
        result = []
        for page_num in range(1, self.file_pattern.get_total_pages() + 1):
            path = self.file_pattern.get_filepath(page_num)
            if path and path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        result.append((page_num, f.read()))
                except Exception:
                    result.append((page_num, ''))
        return result

    def _on_orphan_go_to_line(self, line: int, col: int):
        """Place le curseur dans l'éditeur Markdown à la ligne et colonne indiquées (1-based)."""
        from PyQt6.QtGui import QTextCursor
        te = self.markdown_editor.text_edit
        doc = te.document()
        block = doc.findBlockByLineNumber(line - 1)  # 0-based
        if block.isValid():
            cursor = te.textCursor()
            cursor.setPosition(block.position() + min(col, len(block.text())))
            te.setTextCursor(cursor)
            te.ensureCursorVisible()

    def _on_orphan_go_to_page_line(self, page_num: int, line: int, col: int):
        """Charge la page Markdown donnée puis place le curseur à la ligne/colonne. Garde la sync PDF↔Markdown."""
        if not self.file_pattern:
            return
        # Page PDF correspondante : markdown_page = pdf_page + offset => pdf_page = markdown_page - offset
        pdf_page_1based = page_num - self.page_offset
        pdf_count = self.pdf_viewer.get_page_count() if self.pdf_viewer.doc else 0
        if pdf_count and 1 <= pdf_page_1based <= pdf_count:
            # Aller à la page PDF pour rétablir la sync ; _sync_to_pdf_page chargera le bon Markdown
            self.pdf_viewer.go_to_page(pdf_page_1based - 1)
        else:
            # Pas de PDF ou page hors plage : charger le Markdown directement
            path = self.file_pattern.get_filepath(page_num)
            if path and path.exists():
                self.markdown_editor.load_file(str(path))
                self.markdown_page_label.setText(str(page_num))
        QTimer.singleShot(150, lambda: self._on_orphan_go_to_line(line, col))
    
    def _paste_cleaned_text_to_editor(self, text: str):
        """Colle le texte nettoyé dans l'éditeur Markdown"""
        cursor = self.markdown_editor.text_edit.textCursor()
        cursor.insertText(text)
        self.markdown_editor.text_edit.setTextCursor(cursor)
    
    def _update_page_indicators(self):
        """Met à jour les indicateurs de page"""
        # PDF
        if self.pdf_viewer.doc:
            pdf_count = self.pdf_viewer.get_page_count()
            self.pdf_page_spinbox.setMaximum(pdf_count)
            self.pdf_total_label.setText(str(pdf_count))
            self.pdf_page_spinbox.setValue(self.pdf_viewer.current_page_num + 1)
        else:
            self.pdf_page_spinbox.setMaximum(1)
            self.pdf_total_label.setText("0")
        
        # Markdown
        if self.file_pattern:
            md_count = self.file_pattern.get_total_pages()
            self.markdown_total_label.setText(str(md_count))
        else:
            self.markdown_total_label.setText("0")
            self.markdown_page_label.setText("0")
    
    def _calculate_markdown_page(self, pdf_page: int) -> int:
        """Calcule le numéro de page Markdown à partir de la page PDF"""
        return pdf_page + self.page_offset
    
    def _on_pdf_page_changed_signal(self, page_num: int):
        """Appelé quand la page PDF change via le signal"""
        self._update_page_indicators()
        if self.synchronized:
            self._sync_to_pdf_page()
    
    def _on_pdf_page_changed(self, page_num: int):
        """Appelé quand l'utilisateur change la page via le spinbox"""
        self.pdf_viewer.go_to_page(page_num - 1)
    
    def _sync_to_pdf_page(self):
        """Synchronise la page Markdown avec la page PDF"""
        if not self.file_pattern:
            return
        
        pdf_page = self.pdf_viewer.current_page_num + 1
        markdown_page = self._calculate_markdown_page(pdf_page)
        
        if markdown_page >= 1 and markdown_page <= self.file_pattern.get_total_pages():
            file_path = self.file_pattern.get_filepath(markdown_page)
            if file_path and file_path.exists():
                self.markdown_editor.load_file(str(file_path))
                self.markdown_page_label.setText(str(markdown_page))
            else:
                self.markdown_editor.clear()
                self.markdown_page_label.setText("0")
        if hasattr(self, 'show_markdown_context_action') and self.show_markdown_context_action.isChecked():
            self._update_markdown_context_content()
    
    def next_page(self):
        """Page suivante"""
        self.pdf_viewer.next_page()
    
    def previous_page(self):
        """Page précédente"""
        self.pdf_viewer.previous_page()
    
    def _zoom_pdf_in(self):
        """Augmente le zoom du PDF"""
        self.pdf_viewer.zoom_in()
        self._update_zoom_label()
    
    def _zoom_pdf_out(self):
        """Diminue le zoom du PDF"""
        self.pdf_viewer.zoom_out()
        self._update_zoom_label()
    
    def _update_zoom_label(self):
        """Met à jour le label du zoom"""
        zoom_percent = int(self.pdf_viewer.get_zoom() * 100)
        self.zoom_label.setText(f"{zoom_percent}%")
    
    def _markdown_font_larger(self):
        """Augmente la taille de police du Markdown"""
        current_size = self.markdown_editor.get_font_size()
        new_size = min(72, current_size + 1)
        self.markdown_editor.set_font_size(new_size)
        self._update_font_size_label()
    
    def _markdown_font_smaller(self):
        """Diminue la taille de police du Markdown"""
        current_size = self.markdown_editor.get_font_size()
        new_size = max(6, current_size - 1)
        self.markdown_editor.set_font_size(new_size)
        self._update_font_size_label()
    
    def _update_font_size_label(self):
        """Met à jour le label de la taille de police"""
        size = self.markdown_editor.get_font_size()
        self.font_size_label.setText(f"{size}pt")
    
    def _undo(self):
        """Annuler la dernière action"""
        self.markdown_editor.text_edit.undo()
    
    def _redo(self):
        """Refaire la dernière action annulée"""
        self.markdown_editor.text_edit.redo()
    
    def _cut(self):
        """Couper la sélection"""
        self.markdown_editor.text_edit.cut()
    
    def _copy(self):
        """Copier la sélection"""
        self.markdown_editor.text_edit.copy()
    
    def _paste(self):
        """Coller"""
        self.markdown_editor.text_edit.paste()
    
    def _select_all(self):
        """Sélectionner tout le texte"""
        self.markdown_editor.text_edit.selectAll()
    
    def _show_manual(self):
        """Affiche le manuel d'utilisation"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Manuel d'utilisation")
        dialog.setMinimumSize(700, 600)
        
        layout = QVBoxLayout(dialog)
        
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        
        manual_text = """
        <h1>Manuel d'utilisation - Comparateur PDF-Markdown</h1>
        
        <h2>Fonctionnalités principales</h2>
        
        <h3>1. Chargement des fichiers</h3>
        <ul>
        <li><b>Charger un PDF :</b> Menu Fichier → Charger PDF...</li>
        <li><b>Charger des fichiers Markdown :</b> Menu Fichier → Charger dossier Markdown...
        <br/>Le logiciel détecte automatiquement le pattern de nommage (ex: page001.md, arbeitsc - 0007.md)</li>
        </ul>
        
        <h3>2. Navigation</h3>
        <ul>
        <li><b>Page suivante/précédente :</b> Touches Page Up / Page Down</li>
        <li><b>Décalage entre pages :</b> Utilisez le spinbox "Décalage" dans la barre d'outils pour ajuster la correspondance entre pages PDF et Markdown</li>
        <li><b>Synchronisation :</b> Menu Affichage → Synchronisation (peut être désactivée pour navigation indépendante)</li>
        </ul>
        
        <h3>3. Édition Markdown</h3>
        <ul>
        <li>Édition en texte brut (pas d'interprétation Markdown)</li>
        <li>Sauvegarde automatique après 1 seconde d'inactivité</li>
        <li>Menu Édition : Copier, Coller, Couper, Annuler, Refaire, Tout sélectionner</li>
        </ul>
        
        <h3>4. Mise en évidence</h3>
        <ul>
        <li><b>Configurer des patterns :</b> Menu Affichage → Configurer mise en évidence...
        <br/>Vous pouvez ajouter des patterns avec recherche simple ou regex, choisir les couleurs de fond et de texte</li>
        <li><b>Préférences :</b> Menu Affichage → Préférences... pour configurer les couleurs de recherche/remplacement</li>
        </ul>
        
        <h3>5. Recherche/Remplacement</h3>
        <ul>
        <li><b>Rechercher/Remplacer :</b> Menu Édition → Rechercher/Remplacer... (ou Ctrl+F)</li>
        <li>Recherche dans tous les fichiers Markdown du projet</li>
        <li>Bouton "Suivant" pour naviguer entre les occurrences</li>
        <li>Bouton "Tout remplacer" pour remplacer toutes les occurrences</li>
        <li>Support des expressions régulières</li>
        </ul>
        
        <h3>6. Annotations PDF</h3>
        <ul>
        <li>Clic droit sur le PDF pour ajouter des annotations (texte, surlignage, note)</li>
        <li>Les annotations sont sauvegardées directement dans le fichier PDF</li>
        </ul>
        
        <h3>7. Zoom et police</h3>
        <ul>
        <li><b>Zoom PDF :</b> Boutons +/- dans la barre d'outils ou Menu Affichage → Zoom PDF +/-
        <br/>Raccourcis : Ctrl+Plus / Ctrl+Moins</li>
        <li><b>Taille police Markdown :</b> Boutons +/- dans la barre d'outils ou Menu Affichage → Police Markdown +/-
        </li>
        </ul>
        
        <h3>8. Projets</h3>
        <ul>
        <li><b>Nouveau projet :</b> Menu Fichier → Nouveau projet (Ctrl+N)</li>
        <li><b>Ouvrir projet :</b> Menu Fichier → Ouvrir projet (Ctrl+O)</li>
        <li><b>Enregistrer projet :</b> Menu Fichier → Enregistrer projet (Ctrl+S)
        <br/>Les projets sauvegardent : chemins PDF/Markdown, patterns, décalage, préférences, etc.</li>
        </ul>
        
        <h2>Raccourcis clavier</h2>
        <ul>
        <li><b>Ctrl+N :</b> Nouveau projet</li>
        <li><b>Ctrl+O :</b> Ouvrir projet</li>
        <li><b>Ctrl+S :</b> Enregistrer projet</li>
        <li><b>Ctrl+F :</b> Rechercher/Remplacer</li>
        <li><b>Ctrl+C :</b> Copier</li>
        <li><b>Ctrl+V :</b> Coller</li>
        <li><b>Ctrl+X :</b> Couper</li>
        <li><b>Ctrl+Z :</b> Annuler</li>
        <li><b>Ctrl+Y :</b> Refaire</li>
        <li><b>Page Up / Page Down :</b> Navigation entre pages</li>
        <li><b>F1 :</b> Manuel</li>
        </ul>
        """
        
        text_browser.setHtml(manual_text)
        layout.addWidget(text_browser)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def _show_about(self):
        """Affiche la fenêtre À propos"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        from PyQt6.QtCore import Qt
        
        dialog = QDialog(self)
        dialog.setWindowTitle("À propos")
        dialog.setFixedSize(400, 250)
        
        layout = QVBoxLayout(dialog)
        
        title_label = QLabel("<h2>Comparateur PDF-Markdown</h2>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        version_label = QLabel("Version 1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        description_label = QLabel(
            "<p align='center'>"
            "Application pour comparer des fichiers PDF avec des fichiers Markdown.<br/>"
            "Permet l'édition, la recherche/remplacement, et l'annotation des documents."
            "</p>"
        )
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description_label)
        
        tech_label = QLabel(
            "<p align='center'><small>"
            "Développé avec PyQt6 et PyMuPDF"
            "</small></p>"
        )
        tech_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tech_label)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def _open_search_replace(self):
        """Affiche/masque la barre de recherche/remplacement"""
        if not self.file_pattern:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord charger un dossier Markdown.")
            return
        
        # Créer la barre si elle n'existe pas
        if self.search_replace_bar is None:
            self.search_replace_bar = SearchReplaceBar(self.file_pattern, self)
            self.search_replace_bar.matchFound.connect(self._on_search_match_found)
            self.search_replace_bar.replaceRequested.connect(self._on_replace_requested)
            self.search_replace_bar.replaceAllRequested.connect(self._on_replace_all_requested)
            
            # Ajouter la barre au layout principal
            central_widget = self.centralWidget()
            main_layout = central_widget.layout()
            main_layout.addWidget(self.search_replace_bar)
        
        # Afficher/masquer la barre
        if self.search_replace_bar.isVisible():
            self.search_replace_bar.hide()
        else:
            self.search_replace_bar.show()
    
    def _on_search_match_found(self, page_num: int, start_pos: int, end_pos: int):
        """Appelé quand une occurrence de recherche est trouvée"""
        # Calculer la page PDF correspondante (en tenant compte du décalage)
        pdf_page = page_num - self.page_offset - 1
        if pdf_page >= 0 and pdf_page < self.pdf_viewer.get_page_count():
            self.pdf_viewer.go_to_page(pdf_page)
        
        # Charger le fichier Markdown
        file_path = self.file_pattern.get_filepath(page_num)
        if file_path and file_path.exists():
            self.markdown_editor.load_file(str(file_path))
            
            # Attendre un peu pour que le fichier soit chargé
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self._select_text_in_editor(start_pos, end_pos))
    
    def _on_replace_requested(self, page_num: int, start_pos: int, end_pos: int, replace_text: str):
        """Remplace l'occurrence actuellement sélectionnée"""
        # Charger le fichier si nécessaire
        file_path = self.file_pattern.get_filepath(page_num)
        if not file_path or not file_path.exists():
            return
        
        # S'assurer que le fichier est chargé dans l'éditeur
        if self.markdown_editor.current_file_path != str(file_path):
            self.markdown_editor.load_file(str(file_path))
        
        # Attendre que le fichier soit chargé
        from PyQt6.QtCore import QTimer
        def do_replace():
            content = self.markdown_editor.get_content()
            
            # Remplacer dans le contenu
            before = content[:start_pos]
            after = content[end_pos:]
            new_content = before + replace_text + after
            
            # Mettre à jour l'éditeur
            self.markdown_editor.set_content(new_content)
            
            # Sauvegarder (la sauvegarde auto le fera, mais on peut forcer)
            self.markdown_editor.save_file(str(file_path))
        
        QTimer.singleShot(150, do_replace)
    
    def _on_replace_all_requested(self, search_text: str, replace_text: str, is_regex: bool):
        """Remplace toutes les occurrences dans tous les fichiers"""
        import re
        
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
        
        for page_num in range(1, self.file_pattern.get_total_pages() + 1):
            file_path = self.file_pattern.get_filepath(page_num)
            if not file_path or not file_path.exists():
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remplacer toutes les occurrences
                if is_regex:
                    # Pour regex, utiliser sub() qui supporte les références de groupes (\g<1>, etc.)
                    new_content = pattern.sub(replace_text, content)
                else:
                    new_content = content.replace(search_text, replace_text)
                
                # Sauvegarder seulement si le contenu a changé
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    matches_in_file = len(pattern.findall(content))
                    replaced_count += matches_in_file
                    files_modified += 1
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Erreur lors du remplacement dans {file_path.name}: {e}")
        
        # Afficher le résultat
        QMessageBox.information(
            self, "Remplacement terminé",
            f"{replaced_count} occurrence(s) remplacée(s) dans {files_modified} fichier(s)."
        )
        
        # Rafraîchir la recherche si la barre est visible
        if self.search_replace_bar and self.search_replace_bar.isVisible():
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(200, self.search_replace_bar._search_all)
    
    def _select_text_in_editor(self, start_pos: int, end_pos: int):
        """Sélectionne le texte dans l'éditeur avec les couleurs des préférences"""
        from color_utils import list_to_color, get_contrast_text_color
        
        # Obtenir les couleurs des préférences
        search_bg_list = self.preferences.get('search_highlight_color', [255, 255, 0])
        search_txt_list = self.preferences.get('search_text_color')
        auto_search = self.preferences.get('auto_search_text_color', True)
        
        # Convertir en QColor
        search_bg = list_to_color(search_bg_list) if isinstance(search_bg_list, list) else search_bg_list
        
        if auto_search or search_txt_list is None:
            search_txt = get_contrast_text_color(search_bg)
        else:
            search_txt = list_to_color(search_txt_list) if isinstance(search_txt_list, list) else search_txt_list
        
        # Utiliser la méthode de l'éditeur pour surligner
        self.markdown_editor.highlight_search_match(start_pos, end_pos, search_bg, search_txt)
    
    def _update_custom_buttons(self):
        """Met à jour les boutons personnalisés dans la barre d'outils"""
        # Supprimer les anciens boutons
        if hasattr(self, 'toolbar') and self.toolbar:
            for action in self.custom_buttons_widgets:
                self.toolbar.removeAction(action)
            self.custom_buttons_widgets.clear()
            
            # Ajouter les nouveaux boutons
            custom_buttons = self.preferences.get('custom_buttons', [])
            for button_config in custom_buttons:
                name = button_config.get('name', '')
                text = button_config.get('text', '')
                
                if name and text:
                    action = self.toolbar.addAction(name)
                    tooltip_text = text.replace('\n', '\\n')
                    if len(tooltip_text) > 50:
                        tooltip_text = tooltip_text[:50] + "..."
                    action.setToolTip(f"Insérer: {tooltip_text}")
                    action.triggered.connect(lambda checked, t=text: self._insert_custom_text(t))
                    self.custom_buttons_widgets.append(action)
    
    def _insert_custom_text(self, text: str):
        """Insère le texte personnalisé dans l'éditeur Markdown"""
        cursor = self.markdown_editor.text_edit.textCursor()
        cursor.insertText(text)
        self.markdown_editor.text_edit.setTextCursor(cursor)
    
    def _toggle_show_line_breaks(self, enabled: bool):
        """Affiche/masque les sauts de ligne dans l'éditeur Markdown"""
        self.markdown_editor.set_show_line_breaks(enabled)
    
    def _toggle_show_spaces(self, enabled: bool):
        """Affiche/masque les espaces dans l'éditeur Markdown"""
        self.markdown_editor.set_show_spaces(enabled)
    
    def _toggle_invert_pdf_colors(self, enabled: bool):
        """Active/désactive l'inversion des couleurs du PDF"""
        self.pdf_viewer.set_invert_colors(enabled)
    
    def _apply_invisible_chars_color(self):
        """Applique la couleur des caractères invisibles depuis les préférences"""
        invisible_color_list = self.preferences.get('invisible_chars_color', [128, 128, 128])
        self.markdown_editor.set_invisible_chars_color(invisible_color_list)
    
    def _open_shortcuts_manager(self):
        """Ouvre le gestionnaire de raccourcis"""
        shortcuts = self.preferences.get('shortcuts', {})
        custom_buttons = self.preferences.get('custom_buttons', [])
        dialog = ShortcutsManagerDialog(shortcuts, custom_buttons, self)
        dialog.shortcutsChanged.connect(self._on_shortcuts_changed)
        dialog.exec()
    
    def _on_shortcuts_changed(self, shortcuts: dict):
        """Appelé quand les raccourcis changent"""
        self.preferences['shortcuts'] = shortcuts
        self.config_storage.set_preferences(self.preferences)
        self._apply_custom_shortcuts()
    
    def _apply_custom_shortcuts(self):
        """Applique les raccourcis personnalisés"""
        # Supprimer les anciens raccourcis personnalisés
        for shortcut in self.custom_shortcuts.values():
            shortcut.setEnabled(False)
            shortcut.deleteLater()
        self.custom_shortcuts.clear()
        
        shortcuts = self.preferences.get('shortcuts', {})
        
        # Appliquer les raccourcis aux actions
        action_map = {
            'show_line_breaks': (self.show_line_breaks_action, self._toggle_show_line_breaks),
            'show_spaces': (self.show_spaces_action, self._toggle_show_spaces),
            'invert_pdf_colors': (self.invert_pdf_colors_action, self._toggle_invert_pdf_colors),
            'zoom_pdf_in': (None, self._zoom_pdf_in),
            'zoom_pdf_out': (None, self._zoom_pdf_out),
            'font_larger': (None, self._markdown_font_larger),
            'font_smaller': (None, self._markdown_font_smaller),
            'search_replace': (None, self._open_search_replace),
            'new_project': (None, self._new_project),
            'open_project': (None, self._open_project),
            'save_project': (None, self._save_project),
            'text_cleaner_panel': (None, lambda: self._toggle_text_cleaner_panel(not (self.text_cleaner_panel and self.text_cleaner_panel.isVisible()))),
        }
        
        for action_id, shortcut_str in shortcuts.items():
            if not shortcut_str:
                continue
            
            try:
                key_sequence = QKeySequence(shortcut_str)
                if key_sequence.isEmpty():
                    continue
                
                # Si c'est une action de toolbar, mettre à jour son raccourci
                if action_id in action_map:
                    action, callback = action_map[action_id]
                    if action:
                        action.setShortcut(key_sequence)
                    else:
                        # Créer un QShortcut pour les actions sans widget
                        shortcut = QShortcut(key_sequence, self)
                        shortcut.activated.connect(callback)
                        self.custom_shortcuts[action_id] = shortcut
                
                # Gérer les boutons personnalisés
                elif action_id.startswith('custom_button_'):
                    try:
                        button_index = int(action_id.replace('custom_button_', ''))
                        custom_buttons = self.preferences.get('custom_buttons', [])
                        if 0 <= button_index < len(custom_buttons):
                            button_config = custom_buttons[button_index]
                            text = button_config.get('text', '')
                            shortcut = QShortcut(key_sequence, self)
                            shortcut.activated.connect(lambda checked, t=text: self._insert_custom_text(t))
                            self.custom_shortcuts[action_id] = shortcut
                    except (ValueError, IndexError):
                        pass
            except Exception as e:
                print(f"Erreur lors de l'application du raccourci {action_id}: {e}")
