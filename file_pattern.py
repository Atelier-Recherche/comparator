"""
Gestion des patterns de nommage pour les fichiers Markdown
"""

import re
import os
from pathlib import Path
from typing import Optional, List, Tuple


class FilePattern:
    """Gère la détection et l'utilisation des patterns de nommage de fichiers"""
    
    def __init__(self, directory: str, pattern: Optional[str] = None):
        self.directory = Path(directory)
        self.pattern = pattern
        self.files = []
        
        if pattern:
            self._validate_pattern()
        else:
            self._detect_pattern()
    
    def _detect_pattern(self):
        """Détecte automatiquement le pattern de nommage"""
        if not self.directory.exists():
            return
        
        # Récupérer tous les fichiers .md
        md_files = sorted([f for f in self.directory.iterdir() 
                          if f.is_file() and f.suffix.lower() == '.md'])
        
        if not md_files:
            return
        
        self.files = [f.name for f in md_files]
        
        # Analyser les noms pour détecter le pattern
        # Chercher des séquences numériques dans les noms
        patterns_found = []
        for filename in self.files:
            # Rechercher tous les nombres dans le nom avec leur position
            matches = list(re.finditer(r'\d+', filename))
            if matches:
                # Prendre le dernier nombre trouvé (généralement le numéro de page)
                last_match = matches[-1]
                num_str = last_match.group()
                num_width = len(num_str)
                
                prefix = filename[:last_match.start()]
                suffix = filename[last_match.end():]
                patterns_found.append((prefix, num_width, suffix))
        
        if not patterns_found:
            return
        
        # Prendre le pattern le plus commun (ou le premier si tous sont identiques)
        # Généralement tous les fichiers devraient avoir le même pattern
        prefix, num_width, suffix = patterns_found[0]
        
        # Construire le pattern
        # Format: "prefix{:0Nd}suffix" où N est la largeur du nombre
        self.pattern = f"{prefix}{{:0{num_width}d}}{suffix}"
    
    def _validate_pattern(self):
        """Valide que le pattern correspond aux fichiers existants"""
        if not self.directory.exists():
            return
        
        md_files = sorted([f for f in self.directory.iterdir() 
                          if f.is_file() and f.suffix.lower() == '.md'])
        
        # Tester si le pattern génère des noms de fichiers valides
        valid_files = []
        page_num = 1
        
        while True:
            try:
                filename = self.pattern.format(page_num)
                filepath = self.directory / filename
                
                if filepath.exists():
                    valid_files.append(filename)
                elif page_num > 100:  # Limite pour éviter les boucles infinies
                    break
                
                page_num += 1
            except (ValueError, KeyError):
                break
        
        self.files = valid_files
    
    def get_filename(self, page_number: int) -> str:
        """Génère le nom de fichier pour un numéro de page donné"""
        if not self.pattern:
            return ""
        try:
            return self.pattern.format(page_number)
        except (ValueError, KeyError):
            return ""
    
    def get_filepath(self, page_number: int) -> Path:
        """Retourne le chemin complet du fichier pour un numéro de page"""
        filename = self.get_filename(page_number)
        if not filename:
            return None
        return self.directory / filename
    
    def get_total_pages(self) -> int:
        """Retourne le nombre total de pages disponibles"""
        return len(self.files)
    
    def file_exists(self, page_number: int) -> bool:
        """Vérifie si un fichier existe pour un numéro de page donné"""
        filepath = self.get_filepath(page_number)
        return filepath and filepath.exists()
    
    def parse_page_number(self, filename: str) -> Optional[int]:
        """Extrait le numéro de page depuis un nom de fichier"""
        if not self.pattern:
            return None
        
        # Extraire les parties du pattern
        # Pattern format: "prefix{:0Nd}suffix"
        # On cherche le {:0Nd} dans le pattern
        pattern_match = re.search(r'\{:0(\d+)d\}', self.pattern)
        if not pattern_match:
            return None
        
        num_width = int(pattern_match.group(1))
        pattern_start = pattern_match.start()
        pattern_end = pattern_match.end()
        
        prefix = self.pattern[:pattern_start]
        suffix = self.pattern[pattern_end:]
        
        # Vérifier que le filename correspond au pattern
        if not filename.startswith(prefix) or not filename.endswith(suffix):
            return None
        
        # Extraire le nombre
        num_str = filename[len(prefix):len(filename)-len(suffix)]
        if len(num_str) != num_width:
            return None
        
        try:
            return int(num_str)
        except ValueError:
            return None
