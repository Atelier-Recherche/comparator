#!/usr/bin/env python3
"""
Point d'entrée de l'application Comparateur PDF-Markdown
"""

import sys
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Comparateur PDF-Markdown")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
