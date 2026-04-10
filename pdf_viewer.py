"""
Widget pour afficher un PDF avec support des annotations
"""

import fitz  # PyMuPDF
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QImage, QPixmap, QMouseEvent, QContextMenuEvent, QPainter, QColor
from PyQt6.QtWidgets import QWidget, QMenu, QVBoxLayout, QLabel, QScrollArea


class PDFImageWidget(QWidget):
    """
    Widget qui affiche un pixmap (scale to fit, centré) et expose une conversion
    souris → coords image en réutilisant exactement les mêmes scale/offset que le dessin.
    Évite tout décalage car on ne devine pas comment Qt dessine.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self.setMinimumSize(400, 600)
    
    def setPixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self.update()
    
    def pixmap(self):
        return self._pixmap
    
    def paintEvent(self, event):
        if self._pixmap is None or self._pixmap.isNull():
            return
        pw = self._pixmap.width()
        ph = self._pixmap.height()
        w = self.width()
        h = self.height()
        if pw <= 0 or ph <= 0 or w <= 0 or h <= 0:
            return
        scale = min(1.0, w / pw, h / ph)
        disp_w = pw * scale
        disp_h = ph * scale
        offset_x = (w - disp_w) / 2.0
        offset_y = (h - disp_h) / 2.0
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(
            QRect(int(offset_x), int(offset_y), int(disp_w), int(disp_h)),
            self._pixmap,
            QRect(0, 0, pw, ph)
        )
        painter.end()
    
    def mapGlobalToImage(self, global_pos: QPoint):
        """
        Convertit une position écran en (img_x, img_y) en coords image.
        Utilise exactement la même formule que paintEvent (scale to fit, centré).
        """
        if self._pixmap is None or self._pixmap.isNull():
            return None, None
        local = self.mapFromGlobal(global_pos)
        if not self.rect().contains(local):
            return None, None
        pw = self._pixmap.width()
        ph = self._pixmap.height()
        w = self.width()
        h = self.height()
        if pw <= 0 or ph <= 0 or w <= 0 or h <= 0:
            return None, None
        scale = min(1.0, w / pw, h / ph)
        disp_w = pw * scale
        disp_h = ph * scale
        offset_x = (w - disp_w) / 2.0
        offset_y = (h - disp_h) / 2.0
        rel_x = local.x() - offset_x
        rel_y = local.y() - offset_y
        if rel_x < 0 or rel_y < 0 or rel_x >= disp_w or rel_y >= disp_h:
            return None, None
        img_x = int(rel_x / scale + 0.5)
        img_y = int(rel_y / scale + 0.5)
        img_x = max(0, min(img_x, pw - 1))
        img_y = max(0, min(img_y, ph - 1))
        return img_x, img_y


class PDFViewer(QWidget):
    """Widget pour afficher une page PDF avec annotations"""
    
    pageChanged = pyqtSignal(int)  # Émis quand la page change
    annotationClicked = pyqtSignal(object)  # Émis quand une annotation est cliquée
    textSelected = pyqtSignal(str)  # Émis quand du texte est sélectionné (souris)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.doc = None
        self.current_page_num = 0
        self.zoom_level = 1.0
        self.page_image = None
        self.annotations = []
        self.invert_colors = False
        # Contexte des pages adjacentes : afficher bas page N-1 et haut page N+1
        self.show_adjacent_context = False
        self.adjacent_band_ratio = 0.2  # 20 % de la hauteur de page
        # Mots de la page courante (bbox en coord. PDF, texte) pour la sélection
        self._page_words = []  # list of (fitz.Rect, str)
        # Sélection par mots : indices début/fin (surlignage = bbox des mots, pas de rectangle dessiné)
        self._selection_start_index = None
        self._selection_end_index = None
        self._highlight_rects_pdf = []  # list of fitz.Rect (surlignage des mots sélectionnés ou depuis Markdown)
        self._composite_center_y0 = 0  # offset Y (pixels image) du début de la page courante en mode composite
        self._composite_center_y1 = 0  # fin Y de la page courante en mode composite
        self._selection_enabled = True  # désactivé si pas de couche texte
        
        # Widget de scroll pour permettre le zoom
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.image_label = PDFImageWidget()
        self.scroll_area.setWidget(self.image_label)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll_area)
        
        self.scroll_area.viewport().installEventFilter(self)
    
    def load_pdf(self, pdf_path: str):
        """Charge un fichier PDF"""
        try:
            self.doc = fitz.open(pdf_path)
            if self.doc.page_count > 0:
                self.current_page_num = 0
                self.display_page(0)
            return True
        except Exception as e:
            print(f"Erreur lors du chargement du PDF: {e}")
            return False
    
    def get_page_count(self) -> int:
        """Retourne le nombre de pages du PDF"""
        return self.doc.page_count if self.doc else 0
    
    def display_page(self, page_num: int):
        """Affiche une page spécifique du PDF (ou composite bas N-1 / page N / haut N+1 si mode contexte)."""
        if not self.doc or page_num < 0 or page_num >= self.doc.page_count:
            return
        
        self.current_page_num = page_num
        page = self.doc[page_num]
        zoom_matrix = fitz.Matrix(self.zoom_level, self.zoom_level)
        
        if self.show_adjacent_context:
            self.page_image = self._render_composite_page(page_num, zoom_matrix)
        else:
            pix = page.get_pixmap(matrix=zoom_matrix)
            img_data = pix.tobytes("png")
            self.page_image = QImage.fromData(img_data)
        
        if self.invert_colors:
            self.page_image.invertPixels()
        
        self._selection_start_index = None
        self._selection_end_index = None
        self._highlight_rects_pdf = []
        self._page_words = self._extract_page_words(page)
        self._selection_enabled = len(self._page_words) > 0
        
        if self.show_adjacent_context:
            self._set_composite_center_offsets(page_num, zoom_matrix)
        else:
            self._composite_center_y0 = 0
            self._composite_center_y1 = self.page_image.height() if self.page_image else 0
        
        self._update_pixmap_with_overlays()
        self.image_label.adjustSize()
        
        self.annotations = page.annots()
        self.pageChanged.emit(page_num)
        self.update()
    
    def _extract_page_words(self, page) -> list:
        """Retourne une liste de (fitz.Rect, texte) pour la page en coordonnées PDF."""
        try:
            words = page.get_text("words")
            return [(fitz.Rect(w[0], w[1], w[2], w[3]), w[4]) for w in words]
        except Exception:
            return []
    
    def _set_composite_center_offsets(self, page_num: int, zoom_matrix):
        """Remplit _composite_center_y0 et _composite_center_y1 (pixels dans l'image composite)."""
        sep_h = 2
        y = 0
        if page_num > 0:
            prev_page = self.doc[page_num - 1]
            r = prev_page.rect
            h_band = r.height * self.adjacent_band_ratio
            pix = prev_page.get_pixmap(matrix=zoom_matrix, clip=fitz.Rect(0, r.height - h_band, r.width, r.height))
            y += pix.height
            y += sep_h
        self._composite_center_y0 = y
        page = self.doc[page_num]
        pix = page.get_pixmap(matrix=zoom_matrix)
        y += pix.height
        self._composite_center_y1 = y
    
    def _update_pixmap_with_overlays(self):
        """Dessine les surlignages et la sélection sur l'image puis met à jour le label."""
        if self.page_image is None:
            return
        img = self.page_image.copy()
        painter = QPainter(img)
        # Surlignages (rectangles PDF → image)
        for r in self._highlight_rects_pdf:
            x0 = int(r.x0 * self.zoom_level)
            y0 = int(r.y0 * self.zoom_level)
            x1 = int(r.x1 * self.zoom_level)
            y1 = int(r.y1 * self.zoom_level)
            if self.show_adjacent_context:
                y0 += self._composite_center_y0
                y1 += self._composite_center_y0
            painter.fillRect(x0, y0, x1 - x0, y1 - y0, QColor(255, 255, 0, 120))
        painter.end()
        self.image_label.setPixmap(QPixmap.fromImage(img))
    
    def _global_pos_to_page_image_rect(self, global_pos) -> tuple:
        """Convertit une position écran en coords image via le widget qui dessine (même scale/offset que le rendu)."""
        if not self.image_label.isVisible() or not self.page_image:
            return None, None
        img_x, img_y = self.image_label.mapGlobalToImage(global_pos)
        if img_x is None or img_y is None:
            return None, None
        if self.show_adjacent_context:
            if img_y < self._composite_center_y0 or img_y >= self._composite_center_y1:
                return None, None
            img_y -= self._composite_center_y0
        return (img_x, img_y), (self.page_image.width(), self._composite_center_y1 - self._composite_center_y0)
    
    def _image_pos_to_pdf_point(self, img_x: int, img_y: int) -> tuple:
        """Convertit un point en coords image (page courante) en coords PDF (x, y)."""
        z = self.zoom_level
        pdf_x = img_x / z
        pdf_y = img_y / z
        return (pdf_x, pdf_y)
    
    def _word_index_at_pdf_point(self, pdf_x: float, pdf_y: float) -> int:
        """Retourne l'index du mot dont la bbox contient le point (pdf_x, pdf_y), ou -1."""
        for i, (r, _) in enumerate(self._page_words):
            if r.x0 <= pdf_x <= r.x1 and r.y0 <= pdf_y <= r.y1:
                return i
        return -1
    
    def _highlight_rects_for_word_range(self, start_idx: int, end_idx: int) -> list:
        """Retourne la liste des fitz.Rect pour les mots d'indice start_idx à end_idx (inclus)."""
        if start_idx < 0 or end_idx < 0 or not self._page_words:
            return []
        i0 = min(start_idx, end_idx)
        i1 = max(start_idx, end_idx)
        i0 = max(0, min(i0, len(self._page_words) - 1))
        i1 = max(0, min(i1, len(self._page_words) - 1))
        return [self._page_words[i][0] for i in range(i0, i1 + 1)]
    
    def _text_for_word_range(self, start_idx: int, end_idx: int) -> str:
        """Retourne le texte des mots d'indice start_idx à end_idx (inclus)."""
        if start_idx < 0 or end_idx < 0 or not self._page_words:
            return ""
        i0 = min(start_idx, end_idx)
        i1 = max(start_idx, end_idx)
        i0 = max(0, min(i0, len(self._page_words) - 1))
        i1 = max(0, min(i1, len(self._page_words) - 1))
        return " ".join(self._page_words[i][1] for i in range(i0, i1 + 1))
    
    def _event_global_pos(self, event):
        """Retourne la position globale de la souris (QPoint) pour un QMouseEvent."""
        if hasattr(event, 'globalPosition'):
            gp = event.globalPosition()
            return QPoint(int(gp.x()), int(gp.y()))
        return event.globalPos() if hasattr(event, 'globalPos') else QPoint(0, 0)
    
    def eventFilter(self, obj, event):
        """Sélection par mots : au clic/drag on détermine le mot sous le curseur et on surligne la plage (toujours aux bbox PDF)."""
        if obj != self.scroll_area.viewport() or not self.doc:
            return super().eventFilter(obj, event)
        from PyQt6.QtCore import QEvent
        etype = event.type()
        if etype == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self._highlight_rects_pdf = []
                self._selection_start_index = None
                self._selection_end_index = None
                if self._selection_enabled:
                    global_pos = self._event_global_pos(event)
                    pt, _ = self._global_pos_to_page_image_rect(global_pos)
                    if pt is not None:
                        pdf_x, pdf_y = self._image_pos_to_pdf_point(pt[0], pt[1])
                        idx = self._word_index_at_pdf_point(pdf_x, pdf_y)
                        if idx >= 0:
                            self._selection_start_index = idx
                            self._selection_end_index = idx
                            self._highlight_rects_pdf = self._highlight_rects_for_word_range(idx, idx)
                self._update_pixmap_with_overlays()
            return False
        if etype == QEvent.Type.MouseMove:
            if self._selection_start_index is not None:
                global_pos = self._event_global_pos(event)
                pt, _ = self._global_pos_to_page_image_rect(global_pos)
                if pt is not None:
                    pdf_x, pdf_y = self._image_pos_to_pdf_point(pt[0], pt[1])
                    idx = self._word_index_at_pdf_point(pdf_x, pdf_y)
                    if idx >= 0:
                        self._selection_end_index = idx
                        self._highlight_rects_pdf = self._highlight_rects_for_word_range(
                            self._selection_start_index, self._selection_end_index
                        )
                        self._update_pixmap_with_overlays()
            return False
        if etype == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton and self._selection_start_index is not None:
                global_pos = self._event_global_pos(event)
                pt, _ = self._global_pos_to_page_image_rect(global_pos)
                if pt is not None:
                    pdf_x, pdf_y = self._image_pos_to_pdf_point(pt[0], pt[1])
                    idx = self._word_index_at_pdf_point(pdf_x, pdf_y)
                    if idx >= 0:
                        self._selection_end_index = idx
                if self._selection_start_index is not None and self._selection_end_index is not None:
                    self._highlight_rects_pdf = self._highlight_rects_for_word_range(
                        self._selection_start_index, self._selection_end_index
                    )
                    text = self._text_for_word_range(self._selection_start_index, self._selection_end_index)
                    if text.strip():
                        self.textSelected.emit(text.strip())
                self._update_pixmap_with_overlays()
            return False
        return super().eventFilter(obj, event)
    
    def set_highlight_rects(self, rects: list):
        """Définit les rectangles à surligner sur la page (coords PDF). rects: liste de (x0,y0,x1,y1) ou fitz.Rect."""
        self._highlight_rects_pdf = []
        for r in rects:
            if hasattr(r, 'x0'):
                self._highlight_rects_pdf.append(fitz.Rect(r.x0, r.y0, r.x1, r.y1))
            else:
                self._highlight_rects_pdf.append(fitz.Rect(r[0], r[1], r[2], r[3]))
        self._update_pixmap_with_overlays()
    
    def clear_highlight_rects(self):
        """Efface les surlignages (venant de Markdown)."""
        self._highlight_rects_pdf = []
        self._update_pixmap_with_overlays()
    
    def find_text_rects_in_page(self, text: str) -> list:
        """Recherche le texte dans la page courante et retourne la liste des fitz.Rect correspondants."""
        if not self.doc or not text or not text.strip():
            return []
        page = self.doc[self.current_page_num]
        try:
            rects = page.search_for(text, quads=False)
            return list(rects) if rects else []
        except Exception:
            pass
        text_norm = self._normalize_text(text)
        rects = []
        for r, word in self._page_words:
            if self._normalize_text(word) == text_norm:
                rects.append(r)
        return rects
    
    @staticmethod
    def _normalize_text(s: str) -> str:
        import re
        s = s.replace("\r\n", "\n").replace("\r", "\n")
        s = re.sub(r'\s+', ' ', s).strip()
        return s
    
    def _render_composite_page(self, page_num: int, zoom_matrix) -> QImage:
        """Rend une image composite : bas page N-1, page N entière, haut page N+1."""
        parts = []
        sep_h = 2  # hauteur trait de séparation en pixels
        
        # Bas de la page précédente
        if page_num > 0:
            prev_page = self.doc[page_num - 1]
            r = prev_page.rect
            h_band = r.height * self.adjacent_band_ratio
            clip = fitz.Rect(0, r.height - h_band, r.width, r.height)
            pix = prev_page.get_pixmap(matrix=zoom_matrix, clip=clip)
            img_data = pix.tobytes("png")
            img = QImage.fromData(img_data)
            parts.append(img)
            parts.append(None)  # marqueur séparation
        # Page courante
        page = self.doc[page_num]
        pix = page.get_pixmap(matrix=zoom_matrix)
        img_data = pix.tobytes("png")
        center_img = QImage.fromData(img_data)
        parts.append(center_img)
        # Haut de la page suivante
        if page_num < self.doc.page_count - 1:
            parts.append(None)
            next_page = self.doc[page_num + 1]
            r = next_page.rect
            h_band = r.height * self.adjacent_band_ratio
            clip = fitz.Rect(0, 0, r.width, h_band)
            pix = next_page.get_pixmap(matrix=zoom_matrix, clip=clip)
            img_data = pix.tobytes("png")
            img = QImage.fromData(img_data)
            parts.append(img)
        
        total_w = max(p.width() for p in parts if p is not None)
        total_h = sum(p.height() if p is not None else sep_h for p in parts)
        composite = QImage(total_w, total_h, QImage.Format.Format_RGB32)
        composite.fill(0xFFE0E0E0)
        painter = QPainter(composite)
        y = 0
        for p in parts:
            if p is None:
                painter.fillRect(0, y, total_w, sep_h, QColor(192, 192, 192))
                y += sep_h
                continue
            img = p
            if img.width() != total_w:
                img = img.scaled(total_w, img.height(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.drawImage(0, y, img)
            y += img.height()
        painter.end()
        return composite
    
    def set_zoom(self, zoom: float):
        """Définit le niveau de zoom"""
        self.zoom_level = max(0.5, min(3.0, zoom))
        if self.doc:
            self.display_page(self.current_page_num)
    
    def zoom_in(self):
        """Augmente le zoom"""
        self.set_zoom(self.zoom_level + 0.1)
    
    def zoom_out(self):
        """Diminue le zoom"""
        self.set_zoom(self.zoom_level - 0.1)
    
    def get_zoom(self) -> float:
        """Retourne le niveau de zoom actuel"""
        return self.zoom_level
    
    def go_to_page(self, page_num: int):
        """Va à une page spécifique"""
        if self.doc:
            page_num = max(0, min(page_num, self.doc.page_count - 1))
            self.display_page(page_num)
    
    def next_page(self):
        """Page suivante"""
        if self.doc and self.current_page_num < self.doc.page_count - 1:
            self.go_to_page(self.current_page_num + 1)
    
    def previous_page(self):
        """Page précédente"""
        if self.current_page_num > 0:
            self.go_to_page(self.current_page_num - 1)
    
    def add_annotation(self, annotation_type: str = "text", content: str = "", 
                      rect: tuple = None):
        """
        Ajoute une annotation sur la page courante
        
        Args:
            annotation_type: Type d'annotation ("text", "highlight", "note", etc.)
            content: Contenu de l'annotation
            rect: Rectangle de l'annotation (x0, y0, x1, y1) - None pour la page entière
        """
        if not self.doc:
            return None
        
        page = self.doc[self.current_page_num]
        
        # Convertir les coordonnées si nécessaire (depuis l'interface Qt vers PyMuPDF)
        if rect:
            # Les coordonnées doivent être ajustées selon le zoom
            x0, y0, x1, y1 = rect
            x0 /= self.zoom_level
            y0 /= self.zoom_level
            x1 /= self.zoom_level
            y1 /= self.zoom_level
            annot_rect = fitz.Rect(x0, y0, x1, y1)
        else:
            # Par défaut, centré sur la page
            page_rect = page.rect
            center_x = page_rect.width / 2
            center_y = page_rect.height / 2
            annot_rect = fitz.Rect(center_x - 50, center_y - 10, 
                                   center_x + 50, center_y + 10)
        
        try:
            if annotation_type == "text" or annotation_type == "freetext":
                annot = page.add_freetext_annot(annot_rect, content)
            elif annotation_type == "highlight":
                annot = page.add_highlight_annot(annot_rect)
                if content:
                    annot.set_info(content=content)
            elif annotation_type == "note":
                annot = page.add_text_annot(annot_rect.top_left, content)
            else:
                annot = page.add_freetext_annot(annot_rect, content)
            
            annot.update()
            self.doc.save(self.doc.name, incremental=True)
            self.display_page(self.current_page_num)  # Recharger pour voir l'annotation
            return annot
        except Exception as e:
            print(f"Erreur lors de l'ajout d'annotation: {e}")
            return None
    
    def get_annotations(self):
        """Retourne la liste des annotations de la page courante"""
        if not self.doc:
            return []
        page = self.doc[self.current_page_num]
        return list(page.annots())
    
    def save_pdf(self, path: str = None):
        """Sauvegarde le PDF (avec les annotations)"""
        if not self.doc:
            return False
        
        try:
            save_path = path or self.doc.name
            self.doc.save(save_path, incremental=True)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
            return False
    
    def contextMenuEvent(self, event: QContextMenuEvent):
        """Menu contextuel pour ajouter des annotations"""
        if not self.doc:
            return
        
        menu = QMenu(self)
        
        add_text_action = menu.addAction("Ajouter annotation texte")
        add_highlight_action = menu.addAction("Ajouter surligneur")
        add_note_action = menu.addAction("Ajouter note")
        
        menu.addSeparator()
        view_annotations_action = menu.addAction("Voir annotations")
        
        action = menu.exec(event.globalPos())
        
        if action == add_text_action:
            self._show_add_annotation_dialog("text", event.pos())
        elif action == add_highlight_action:
            self._show_add_annotation_dialog("highlight", event.pos())
        elif action == add_note_action:
            self._show_add_annotation_dialog("note", event.pos())
        elif action == view_annotations_action:
            self._show_annotations_list()
    
    def _show_add_annotation_dialog(self, annot_type: str, pos):
        """Affiche un dialog pour ajouter une annotation"""
        # Pour l'instant, création simple
        # Dans une version complète, on pourrait utiliser QInputDialog
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Nouvelle annotation", 
                                       f"Contenu de l'annotation ({annot_type}):")
        if ok and text:
            # Convertir la position du clic en coordonnées PDF
            # C'est simplifié - il faudrait tenir compte du zoom et de la position de scroll
            rect = (pos.x() - 50, pos.y() - 10, pos.x() + 50, pos.y() + 10)
            self.add_annotation(annot_type, text, rect)
    
    def _show_annotations_list(self):
        """Affiche la liste des annotations"""
        annotations = self.get_annotations()
        if not annotations:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Annotations", 
                                   "Aucune annotation sur cette page.")
            return
        
        # Afficher les informations des annotations
        from PyQt6.QtWidgets import QMessageBox
        annot_list = "\n".join([f"- {annot.type_name}: {annot.info.get('content', '')}" 
                               for annot in annotations])
        QMessageBox.information(self, "Annotations", f"Annotations de la page:\n{annot_list}")
    
    def set_invert_colors(self, invert: bool):
        """Active/désactive l'inversion des couleurs (mode sombre)"""
        self.invert_colors = invert
        if self.doc:
            self.display_page(self.current_page_num)
    
    def get_invert_colors(self) -> bool:
        """Retourne si l'inversion des couleurs est activée"""
        return self.invert_colors
    
    def set_show_adjacent_context(self, show: bool):
        """Active/désactive l'affichage du bas de la page précédente et du haut de la suivante."""
        self.show_adjacent_context = show
        if self.doc:
            self.display_page(self.current_page_num)
    
    def get_show_adjacent_context(self) -> bool:
        """Retourne si le contexte des pages adjacentes est affiché."""
        return self.show_adjacent_context