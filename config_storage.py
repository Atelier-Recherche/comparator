"""
Gestion du stockage de la configuration de l'application
(dernier projet ouvert, préférences, etc.)
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any


class ConfigStorage:
    """Gère le stockage de la configuration de l'application"""
    
    def __init__(self, config_file: str = "app_config.json"):
        """
        Args:
            config_file: Nom du fichier de configuration (dans le répertoire utilisateur)
        """
        # Utiliser le répertoire de l'application ou un répertoire de config
        config_dir = Path.home() / ".comparator"
        config_dir.mkdir(exist_ok=True)
        self.config_path = config_dir / config_file
    
    def get_last_project_path(self) -> Optional[str]:
        """Retourne le chemin du dernier projet ouvert"""
        config = self._load_config()
        return config.get('last_project_path')
    
    def set_last_project_path(self, project_path: str):
        """Définit le chemin du dernier projet ouvert"""
        config = self._load_config()
        config['last_project_path'] = project_path
        self._save_config(config)
    
    def get_preferences(self) -> Dict[str, Any]:
        """Retourne les préférences par défaut de l'application"""
        config = self._load_config()
        default_prefs = {
            'search_highlight_color': [255, 255, 0],
            'search_text_color': None,
            'auto_search_text_color': True,
            'custom_buttons': [],
            'invisible_chars_color': [128, 128, 128],  # Gris par défaut
            'shortcuts': {}  # Raccourcis personnalisés
        }
        prefs = config.get('preferences', default_prefs)
        # S'assurer que custom_buttons existe même si les préférences existent mais sans cette clé
        if 'custom_buttons' not in prefs:
            prefs['custom_buttons'] = []
        return prefs
    
    def set_preferences(self, preferences: Dict[str, Any]):
        """Sauvegarde les préférences"""
        config = self._load_config()
        config['preferences'] = preferences
        self._save_config(config)
    
    def get_last_pdf_page(self, pdf_path: str) -> Optional[int]:
        """Retourne le numéro de la dernière page PDF affichée pour un PDF donné"""
        config = self._load_config()
        pdf_pages = config.get('pdf_pages', {})
        return pdf_pages.get(pdf_path)
    
    def set_last_pdf_page(self, pdf_path: str, page_num: int):
        """Sauvegarde le numéro de la dernière page PDF affichée"""
        config = self._load_config()
        if 'pdf_pages' not in config:
            config['pdf_pages'] = {}
        config['pdf_pages'][pdf_path] = page_num
        self._save_config(config)
    
    def get_splitter_sizes(self) -> dict:
        """Retourne les tailles sauvegardées des splitters"""
        config = self._load_config()
        return config.get('splitter_sizes', {
            'main': [500, 500],  # PDF, Zone droite
            'right': [600, 400]  # Markdown, Panneau nettoyage
        })
    
    def set_splitter_sizes(self, main_sizes: list = None, right_sizes: list = None):
        """Sauvegarde les tailles des splitters"""
        config = self._load_config()
        if 'splitter_sizes' not in config:
            config['splitter_sizes'] = {}
        
        if main_sizes is not None:
            config['splitter_sizes']['main'] = main_sizes
        if right_sizes is not None:
            config['splitter_sizes']['right'] = right_sizes
        
        self._save_config(config)
    
    def get_window_geometry(self) -> Optional[Dict[str, int]]:
        """Retourne la géométrie sauvegardée de la fenêtre"""
        config = self._load_config()
        return config.get('window_geometry')
    
    def set_window_geometry(self, x: int, y: int, width: int, height: int):
        """Sauvegarde la géométrie de la fenêtre"""
        config = self._load_config()
        config['window_geometry'] = {
            'x': x,
            'y': y,
            'width': width,
            'height': height
        }
        self._save_config(config)
    
    def get_text_cleaner_panel_visible(self) -> bool:
        """Retourne si le panneau de nettoyage était visible"""
        config = self._load_config()
        return config.get('text_cleaner_panel_visible', False)
    
    def set_text_cleaner_panel_visible(self, visible: bool):
        """Sauvegarde l'état de visibilité du panneau de nettoyage"""
        config = self._load_config()
        config['text_cleaner_panel_visible'] = visible
        self._save_config(config)
    
    def get_orphan_couples_panel_visible(self) -> bool:
        """Retourne si le panneau couplages orphelins était visible"""
        config = self._load_config()
        return config.get('orphan_couples_panel_visible', False)
    
    def set_orphan_couples_panel_visible(self, visible: bool):
        """Sauvegarde l'état de visibilité du panneau couplages orphelins"""
        config = self._load_config()
        config['orphan_couples_panel_visible'] = visible
        self._save_config(config)
    
    def get_show_pdf_context(self) -> bool:
        """Retourne si le contexte des pages adjacentes PDF est activé"""
        config = self._load_config()
        return config.get('show_pdf_context', False)
    
    def set_show_pdf_context(self, show: bool):
        """Sauvegarde l'état du contexte des pages adjacentes PDF"""
        config = self._load_config()
        config['show_pdf_context'] = show
        self._save_config(config)
    
    def get_show_markdown_context(self) -> bool:
        """Retourne si le contexte des pages adjacentes Markdown est activé"""
        config = self._load_config()
        return config.get('show_markdown_context', False)
    
    def set_show_markdown_context(self, show: bool):
        """Sauvegarde l'état du contexte des pages adjacentes Markdown"""
        config = self._load_config()
        config['show_markdown_context'] = show
        self._save_config(config)
    
    def get_dynamic_highlight_enabled(self) -> bool:
        """Retourne si le mode surlignement dynamique est activé"""
        config = self._load_config()
        return config.get('dynamic_highlight_enabled', False)
    
    def set_dynamic_highlight_enabled(self, enabled: bool):
        """Sauvegarde l'état du mode surlignement dynamique"""
        config = self._load_config()
        config['dynamic_highlight_enabled'] = enabled
        self._save_config(config)
    
    def _load_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis le fichier"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
        
        return {}
    
    def _save_config(self, config: Dict[str, Any]):
        """Sauvegarde la configuration dans le fichier"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")
