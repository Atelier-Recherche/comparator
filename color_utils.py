"""
Utilitaires pour le calcul de contraste et les couleurs
"""

from PyQt6.QtGui import QColor


def calculate_contrast_ratio(color1: QColor, color2: QColor) -> float:
    """
    Calcule le ratio de contraste entre deux couleurs (WCAG)
    Retourne une valeur entre 1 et 21
    """
    def get_luminance(color: QColor) -> float:
        """Calcule la luminance relative d'une couleur"""
        r = color.red() / 255.0
        g = color.green() / 255.0
        b = color.blue() / 255.0
        
        # Convertir en espace linéaire
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    lum1 = get_luminance(color1)
    lum2 = get_luminance(color2)
    
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    
    return (lighter + 0.05) / (darker + 0.05)


def get_contrast_text_color(background_color: QColor) -> QColor:
    """
    Calcule automatiquement la couleur de texte pour avoir le meilleur contraste
    avec la couleur de fond donnée
    
    Returns:
        QColor noir ou blanc selon celui qui a le meilleur contraste
    """
    white = QColor(255, 255, 255)
    black = QColor(0, 0, 0)
    
    contrast_white = calculate_contrast_ratio(background_color, white)
    contrast_black = calculate_contrast_ratio(background_color, black)
    
    return white if contrast_white > contrast_black else black


def color_to_list(color: QColor) -> list:
    """Convertit une QColor en liste [r, g, b]"""
    return [color.red(), color.green(), color.blue()]


def list_to_color(color_list: list) -> QColor:
    """Convertit une liste [r, g, b] en QColor"""
    return QColor(*color_list[:3])
