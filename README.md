# Comparateur PDF-Markdown

Application desktop en Python (PyQt6) pour comparer un document PDF avec une série de fichiers Markdown page par page.

L'outil est conçu pour les workflows de relecture/correction : navigation synchronisée PDF <-> Markdown, édition directe du texte Markdown, recherche/remplacement global et utilitaires de nettoyage.

## Fonctionnalités principales

- Affichage côte à côte du PDF et de l'éditeur Markdown.
- Synchronisation des pages PDF/Markdown avec décalage configurable.
- Détection (ou configuration manuelle) du pattern de nommage des fichiers Markdown (`page001.md`, `doc - 0007.md`, etc.).
- Édition Markdown avec sauvegarde et gestion de la police.
- Recherche/remplacement dans l'ensemble du dossier Markdown (texte simple ou regex).
- Surlignement configurable (patterns personnalisés) et mode de surlignement dynamique entre sélection PDF et texte Markdown.
- Panneau de nettoyage de texte et panneau de couplages orphelins.
- Gestion de projets (`.comparator` / `.json`) pour restaurer rapidement une session.
- Préférences persistantes (géométrie, panneaux visibles, couleurs, raccourcis personnalisés, dernier projet, etc.).

## Prérequis

- Python 3.10+ (recommandé)
- pip

Dépendances Python :

- `PyQt6>=6.6.0`
- `PyMuPDF>=1.23.0`

## Installation

Depuis la racine du projet :

```bash
python -m venv .venv
```

Activation de l'environnement virtuel :

- Windows (PowerShell) :

```powershell
.venv\Scripts\Activate.ps1
```

- macOS / Linux :

```bash
source .venv/bin/activate
```

Installation des dépendances :

```bash
pip install -r requirements.txt
```

## Lancement

```bash
python main.py
```

## Utilisation rapide

1. Ouvrir l'application.
2. Charger un PDF via `Fichier > Charger PDF...`.
3. Charger le dossier de pages Markdown via `Fichier > Charger dossier Markdown...`.
4. Ajuster le `Décalage` si la page PDF N ne correspond pas à la page Markdown N.
5. Naviguer avec `Page Up / Page Down` et éditer le Markdown.
6. Enregistrer la session en projet via `Fichier > Enregistrer projet`.

## Fichiers de projet

Les projets sauvegardent les informations de session (PDF, dossier Markdown, pattern, offset, synchronisation, zoom, police, préférences, etc.) dans des fichiers :

- `*.comparator`
- `*.json`

## Structure (aperçu)

- `main.py` : point d'entrée de l'application.
- `main_window.py` : interface principale et logique de coordination.
- `pdf_viewer.py` : affichage et interactions PDF.
- `markdown_editor.py` : édition des fichiers Markdown.
- `search_replace_bar.py` / `search_replace_dialog.py` : recherche/remplacement.
- `project_manager.py` : sauvegarde/chargement des projets.
- `config_storage.py` : persistance de la configuration utilisateur.

## Notes

- Cette application est orientée interface graphique (pas de mode CLI dédié).
- Les annotations PDF et les modifications Markdown impactent les fichiers source : travailler sur une copie est recommandé pour les documents sensibles.
