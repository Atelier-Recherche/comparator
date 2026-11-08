<div align="center" id="head">


<table>
<tr>
<td><img src="readme-media/logo_comparator.png" alt="Comparator" width="140" /></td>
<td align="left">
<h1 style="margin:0">Comparator</h1>
<p style="margin:0.25em 0 0"><strong>PDF-↔-Markdown-Vergleich · Korrekturlesen · PyQt6</strong><br/>Desktop-App · seitenweise Sync · Markdown-Bearbeitung</p>
</td>
</tr>
</table>

<a href="https://atelier.atechnologie.fr/" title="l'Atelier – Verein für Buchherstellung und Forschungswerkzeuge"><img src="https://raw.githubusercontent.com/Atelier-Recherche/.github/main/profile/logo.jpg" alt="l'Atelier" width="200" /></a>  
<sub>Entwickelt von <a href="https://atelier.atechnologie.fr/">l'Atelier</a> — Buchherstellung und Forschungswerkzeuge (EHESS)</sub>

<p>
🇫🇷 <a href="README.md">Français</a> ·
🇬🇧 <a href="README.en.md">English</a> ·
🇩🇪 <a href="README.de.md"><b>Deutsch</b></a> ·
🇪🇸 <a href="README.es.md">Español</a>
</p>

<p>
<a href="https://atelier.atechnologie.fr/"><img src="https://img.shields.io/badge/🌐_l'Atelier-atelier.atechnologie.fr-2d5016?style=for-the-badge" alt="Website l'Atelier" /></a>
<a href="https://github.com/Atelier-Recherche/comparator"><img src="https://img.shields.io/badge/📦_Repository-GitHub-181717?style=for-the-badge&logo=github" alt="GitHub-Repository" /></a>
</p>

</div>

---

## 📸 Übersicht

| Nebeneinander-Ansicht | Markdown-Bearbeitung |
| :---: | :---: |
| <img src="readme-media/screen1.jpg" alt="PDF- und Markdown-Vergleich" width="400" /> | <img src="readme-media/screen2.jpg" alt="Bearbeitung und Suche im Markdown" width="400" /> |

---

## 📖 Über die Anwendung

Eine Python-Desktop-Anwendung (PyQt6) zum Vergleich eines PDF-Dokuments mit einer Reihe von Markdown-Dateien **Seite für Seite**.

Gedacht für Korrekturlese- / Korrektur-Workflows: synchronisierte Navigation PDF ↔ Markdown, direkte Markdown-Bearbeitung, globale Suche/Ersetzen und Bereinigungs-Utilities.

## 🌟 Hauptfunktionen

- PDF-Ansicht und Markdown-Editor nebeneinander.
- Sync der PDF-/Markdown-Seiten mit konfigurierbarem Versatz.
- Erkennung (oder manuelle Konfiguration) von Markdown-Dateinamensmustern (`page001.md`, `doc - 0007.md`, usw.).
- Markdown-Bearbeitung mit Speichern und Schriftverwaltung.
- Suche / Ersetzen im gesamten Markdown-Ordner (Klartext oder Regex).
- Konfigurierbares Highlighting (eigene Patterns) und dynamisches Highlight zwischen PDF-Auswahl und Markdown-Text.
- Textbereinigungs-Panel und Panel für verwaiste Paare.
- Projektverwaltung (`.comparator` / `.json`) zum schnellen Wiederherstellen einer Sitzung.
- Persistente Einstellungen (Geometrie, sichtbare Panels, Farben, eigene Shortcuts, letztes Projekt usw.).

## 📦 Voraussetzungen

- Python 3.10+ (empfohlen)
- pip

Python-Abhängigkeiten:

- `PyQt6>=6.6.0`
- `PyMuPDF>=1.23.0`

## ⬇️ Installation

Im Projektstamm:

```bash
python -m venv .venv
```

Virtuelle Umgebung aktivieren:

- Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

- macOS / Linux:

```bash
source .venv/bin/activate
```

Abhängigkeiten installieren:

```bash
pip install -r requirements.txt
```

## 🚀 Start

```bash
python main.py
```

## 🧭 Schnellstart

1. Anwendung öffnen.
2. PDF laden über `Fichier > Charger PDF...` / `File > Load PDF...`.
3. Markdown-Seitenordner laden über `Fichier > Charger dossier Markdown...`.
4. `Décalage` / `Offset` anpassen, wenn PDF-Seite N nicht zu Markdown-Seite N passt.
5. Mit `Page Up / Page Down` navigieren und Markdown bearbeiten.
6. Sitzung als Projekt speichern über `Fichier > Enregistrer projet`.

## 💾 Projektdateien

Projekte speichern Sitzungsdaten (PDF, Markdown-Ordner, Pattern, Offset, Sync, Zoom, Schrift, Einstellungen usw.) in:

- `*.comparator`
- `*.json`

## 🗂️ Struktur (Überblick)

- `main.py`: Einstiegspunkt der Anwendung.
- `main_window.py`: Hauptfenster und Koordinationslogik.
- `pdf_viewer.py`: PDF-Anzeige und Interaktionen.
- `markdown_editor.py`: Bearbeitung der Markdown-Dateien.
- `search_replace_bar.py` / `search_replace_dialog.py`: Suche / Ersetzen.
- `project_manager.py`: Speichern / Laden von Projekten.
- `config_storage.py`: Persistenz der Benutzereinstellungen.

## ⚠️ Hinweise

- GUI-orientierte Anwendung (kein eigener CLI-Modus).
- PDF-Annotationen und Markdown-Änderungen betreffen die Quelldateien: bei sensiblen Dokumenten mit einer Kopie arbeiten.

## 🔗 Ressourcen

| | |
| --- | --- |
| 🌐 **l'Atelier** | [atelier.atechnologie.fr](https://atelier.atechnologie.fr/) |
| 📦 **Repository** | [github.com/Atelier-Recherche/comparator](https://github.com/Atelier-Recherche/comparator) |

---

<div align="center">

<sub><a href="README.md">🇫🇷 Français</a> · <a href="README.en.md">🇬🇧 English</a> · <b>🇩🇪 Deutsch</b> · <a href="README.es.md">🇪🇸 Español</a></sub>

</div>
