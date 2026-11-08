<div align="center" id="head">


<table>
<tr>
<td><img src="readme-media/logo_comparator.png" alt="Comparator" width="140" /></td>
<td align="left">
<h1 style="margin:0">Comparator</h1>
<p style="margin:0.25em 0 0"><strong>Comparaison PDF ↔ Markdown · relecture · PyQt6</strong><br/>application desktop · sync page à page · édition Markdown</p>
</td>
</tr>
</table>

<a href="https://atelier.atechnologie.fr/" title="l'Atelier – Association de fabrication de livres et d'outils de recherche"><img src="https://raw.githubusercontent.com/Atelier-Recherche/.github/main/profile/logo.jpg" alt="l'Atelier" width="200" /></a>  
<sub>Développé par <a href="https://atelier.atechnologie.fr/">l'Atelier</a> — fabrication de livres et outils de recherche (EHESS)</sub>

<p>
🇫🇷 <a href="README.md"><b>Français</b></a> ·
🇬🇧 <a href="README.en.md">English</a> ·
🇩🇪 <a href="README.de.md">Deutsch</a> ·
🇪🇸 <a href="README.es.md">Español</a>
</p>

<p>
<a href="https://atelier.atechnologie.fr/"><img src="https://img.shields.io/badge/🌐_l'Atelier-atelier.atechnologie.fr-2d5016?style=for-the-badge" alt="Site l'Atelier" /></a>
<a href="https://github.com/Atelier-Recherche/comparator"><img src="https://img.shields.io/badge/📦_Dépôt-GitHub-181717?style=for-the-badge&logo=github" alt="Dépôt GitHub" /></a>
</p>

</div>

---

## 📸 Aperçu

| Vue côte à côte | Édition Markdown |
| :---: | :---: |
| <img src="readme-media/screen1.jpg" alt="Comparaison PDF et Markdown" width="400" /> | <img src="readme-media/screen2.jpg" alt="Édition et recherche dans le Markdown" width="400" /> |

---

## 📖 À propos

Application desktop en Python (PyQt6) pour comparer un document PDF avec une série de fichiers Markdown **page par page**.

L’outil est conçu pour les workflows de relecture / correction : navigation synchronisée PDF ↔ Markdown, édition directe du texte Markdown, recherche / remplacement global et utilitaires de nettoyage.

## 🌟 Fonctionnalités principales

- Affichage côte à côte du PDF et de l’éditeur Markdown.
- Synchronisation des pages PDF / Markdown avec décalage configurable.
- Détection (ou configuration manuelle) du pattern de nommage des fichiers Markdown (`page001.md`, `doc - 0007.md`, etc.).
- Édition Markdown avec sauvegarde et gestion de la police.
- Recherche / remplacement dans l’ensemble du dossier Markdown (texte simple ou regex).
- Surlignage configurable (patterns personnalisés) et mode de surlignage dynamique entre sélection PDF et texte Markdown.
- Panneau de nettoyage de texte et panneau de couplages orphelins.
- Gestion de projets (`.comparator` / `.json`) pour restaurer rapidement une session.
- Préférences persistantes (géométrie, panneaux visibles, couleurs, raccourcis personnalisés, dernier projet, etc.).

## 📦 Prérequis

- Python 3.10+ (recommandé)
- pip

Dépendances Python :

- `PyQt6>=6.6.0`
- `PyMuPDF>=1.23.0`

## ⬇️ Installation

Depuis la racine du projet :

```bash
python -m venv .venv
```

Activation de l’environnement virtuel :

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

## 🚀 Lancement

```bash
python main.py
```

## 🧭 Utilisation rapide

1. Ouvrir l’application.
2. Charger un PDF via `Fichier > Charger PDF...`.
3. Charger le dossier de pages Markdown via `Fichier > Charger dossier Markdown...`.
4. Ajuster le `Décalage` si la page PDF N ne correspond pas à la page Markdown N.
5. Naviguer avec `Page Up / Page Down` et éditer le Markdown.
6. Enregistrer la session en projet via `Fichier > Enregistrer projet`.

## 💾 Fichiers de projet

Les projets sauvegardent les informations de session (PDF, dossier Markdown, pattern, offset, synchronisation, zoom, police, préférences, etc.) dans des fichiers :

- `*.comparator`
- `*.json`

## 🗂️ Structure (aperçu)

- `main.py` : point d’entrée de l’application.
- `main_window.py` : interface principale et logique de coordination.
- `pdf_viewer.py` : affichage et interactions PDF.
- `markdown_editor.py` : édition des fichiers Markdown.
- `search_replace_bar.py` / `search_replace_dialog.py` : recherche / remplacement.
- `project_manager.py` : sauvegarde / chargement des projets.
- `config_storage.py` : persistance de la configuration utilisateur.

## ⚠️ Notes

- Application orientée interface graphique (pas de mode CLI dédié).
- Les annotations PDF et les modifications Markdown impactent les fichiers source : travailler sur une copie est recommandé pour les documents sensibles.

## 🔗 Ressources

| | |
| --- | --- |
| 🌐 **l'Atelier** | [atelier.atechnologie.fr](https://atelier.atechnologie.fr/) |
| 📦 **Dépôt** | [github.com/Atelier-Recherche/comparator](https://github.com/Atelier-Recherche/comparator) |

---

<div align="center">

<sub><b>🇫🇷 Français</b> · <a href="README.en.md">🇬🇧 English</a> · <a href="README.de.md">🇩🇪 Deutsch</a> · <a href="README.es.md">🇪🇸 Español</a></sub>

</div>
