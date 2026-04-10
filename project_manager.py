"""
Gestionnaire de projets pour sauvegarder/charger les projets
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any


class ProjectManager:
    """Gère la sauvegarde et le chargement des projets"""
    
    def __init__(self):
        self.current_project_path: Optional[Path] = None
    
    def save_project(self, project_path: str, data: Dict[str, Any]) -> bool:
        """
        Sauvegarde un projet dans un fichier JSON
        
        Args:
            project_path: Chemin du fichier de projet (.comparator ou .json)
            data: Dictionnaire contenant les données du projet
        
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            path = Path(project_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.current_project_path = path
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du projet: {e}")
            return False
    
    def load_project(self, project_path: str) -> Optional[Dict[str, Any]]:
        """
        Charge un projet depuis un fichier JSON
        
        Args:
            project_path: Chemin du fichier de projet
        
        Returns:
            Dictionnaire contenant les données du projet, ou None en cas d'erreur
        """
        try:
            path = Path(project_path)
            if not path.exists():
                return None
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.current_project_path = path
            return data
        except Exception as e:
            print(f"Erreur lors du chargement du projet: {e}")
            return None
    
    def get_default_project_data(self) -> Dict[str, Any]:
        """Retourne la structure par défaut d'un projet"""
        return {
            "pdf_path": "",
            "markdown_directory": "",
            "markdown_pattern": "",
            "page_offset": 0,
            "synchronized": True,
            "highlight_patterns": [],
            "zoom_level": 1.0,
            "font_size": 12
        }
    
    def export_project_data(self, pdf_path: str, markdown_dir: str, 
                           markdown_pattern: str, page_offset: int,
                           synchronized: bool, highlight_patterns: list,
                           zoom_level: float = 1.0, font_size: int = 12) -> Dict[str, Any]:
        """
        Crée un dictionnaire de données de projet à partir des paramètres
        
        Returns:
            Dictionnaire avec toutes les données du projet
        """
        return {
            "pdf_path": pdf_path,
            "markdown_directory": markdown_dir,
            "markdown_pattern": markdown_pattern,
            "page_offset": page_offset,
            "synchronized": synchronized,
            "highlight_patterns": highlight_patterns,
            "zoom_level": zoom_level,
            "font_size": font_size
        }
