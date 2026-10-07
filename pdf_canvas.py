"""
pdf_canvas.py - Ultra-sharp vector rendering PDF canvas with dynamic high-DPI zoom
"""

import pymupdf
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsPixmapItem,
    QGraphicsTextItem, QGraphicsPathItem, QGraphicsRectItem,
    QGraphicsDropShadowEffect
)
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPixmap, QImage,
    QPainterPath, QCursor, QTransform
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QByteArray, QBuffer, QTimer


class ToolMode:
    SELECT = "select"
    HAND = "hand"
    TEXT = "text"
    PEN = "pen"
    HIGHLIGHTER = "highlighter"
    RECTANGLE = "rectangle"
    IMAGE = "image"
    SIGNATURE = "signature"
    ERASER = "eraser"


class MovableTextItem(QGraphicsTextItem):
    """Draggable and inline-editable text annotation."""
    def __init__(self, text: str, font: QFont, color: QColor, parent=None):
        super().__init__(text, parent)
        self.setFont(font)
        self.setDefaultTextColor(color)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
        )
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setZValue(10)

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self.isSelected() or self.hasFocus():
            painter.setPen(QPen(QColor(229, 37, 42), 1.5, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect().adjusted(-2, -2, 2, 2))


class MovableImageItem(QGraphicsPixmapItem):
    """Draggable and resizable image/signature."""
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(pixmap, parent)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
        )
        self.setZValue(10)
        self.original_pixmap = pixmap
        self.current_scale = 1.0

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.setPen(QPen(QColor(229, 37, 42), 2, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r = self.boundingRect()
            painter.drawRect(r)

            handle_size = 8
            painter.setBrush(QColor(229, 37, 42))
            painter.drawRect(QRectF(r.right() - handle_size, r.bottom() - handle_size, handle_size, handle_size))

    def resize_by_factor(self, factor: float):
        self.current_scale = max(0.15, min(self.current_scale * factor, 5.0))
        new_w = max(20, int(self.original_pixmap.width() * self.current_scale))
        new_h = max(20, int(self.original_pixmap.height() * self.current_scale))
        scaled = self.original_pixmap.scaled(
            new_w, new_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled)


class PDFCanvas(QGraphicsView):
    """Ultra-sharp PDF Viewport with dynamic vector re-rendering on zoom."""
    zoom_changed = pyqtSignal(float)
    status_message = pyqtSignal(str)
    item_selected = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform |
            QPainter.RenderHint.TextAntialiasing
        )
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet("background-color: #525659; border: none;")

        # Active Tool & Styling
        self.current_tool = ToolMode.SELECT
        self.pen_color = QColor(229, 37, 42)
        self.pen_width = 3
        self.highlighter_color = QColor(250, 204, 21, 110)
        self.text_font = QFont("Arial", 14)
        self.text_color = QColor(17, 24, 39)
        self.zoom_factor = 1.0

        # Page Reference for Dynamic Re-rendering
        self.current_page = None
        self.current_page_idx = 0
        self.page_rect_pdf = None
        self.bg_item = None

        # Debounced Timer for dynamic sharp re-rendering
        self.sharp_timer = QTimer(self)
        self.sharp_timer.setSingleShot(True)
        self.sharp_timer.timeout.connect(self._re_render_sharp_page)

        # Drawing In-Progress
        self.current_path_item = None
        self.current_painter_path = None
        self.start_point = None
        self.active_rect_item = None

        # Per-Page Storage
        self.page_annotations = {}
        self.undo_stack = {}
        self.redo_stack = {}

        self.scene.selectionChanged.connect(self._on_selection_changed)

    def set_tool(self, tool: str):
        self.current_tool = tool
        if tool == ToolMode.HAND:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif tool == ToolMode.SELECT:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)
        elif tool == ToolMode.TEXT:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.IBeamCursor)
        elif tool in (ToolMode.PEN, ToolMode.HIGHLIGHTER):
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif tool == ToolMode.RECTANGLE:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif tool == ToolMode.ERASER:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def render_page(self, page: pymupdf.Page, page_index: int):
        """Render page in native PDF points with high-DPI sharp rasterization."""
        self._save_current_page_items()
        self.current_page = page
        self.current_page_idx = page_index
        self.page_rect_pdf = page.rect
        self.scene.clear()

        # Render high-resolution pixmap
        render_scale = max(1.5, min(self.zoom_factor * 1.5, 3.5))
        mat = pymupdf.Matrix(render_scale, render_scale)
        pix = page.get_pixmap(matrix=mat)

        fmt = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        qpixmap = QPixmap.fromImage(qimg)

        self.bg_item = QGraphicsPixmapItem(qpixmap)
        self.bg_item.setPos(0, 0)
        self.bg_item.setZValue(0)

        # Map pixmap exactly onto physical PDF point dimensions
        sx = qpixmap.width() / page.rect.width
        sy = qpixmap.height() / page.rect.height
        self.bg_item.setTransform(QTransform().scale(1.0 / sx, 1.0 / sy))

        self.scene.addItem(self.bg_item)

        # Crisp paper border (0ms overhead, replaces heavy 24px Gaussian blur)
        self.scene.addRect(
            0, 0, page.rect.width, page.rect.height,
            QPen(QColor(0, 0, 0, 45), 1),
            QBrush(Qt.BrushStyle.NoBrush)
        )

        # Margins around physical page
        margin = 35
        self.scene.setSceneRect(-margin, -margin, page.rect.width + (margin * 2), page.rect.height + (margin * 2))

        # Restore annotations
        self._restore_page_items(page_index)

    def _re_render_sharp_page(self):
        """Re-rasterize at higher vector scale when user zooms in, ensuring crystal clarity."""
        if not self.current_page or not self.bg_item or not self.page_rect_pdf:
            return

        render_scale = max(1.5, min(self.zoom_factor * 1.5, 3.5))
        mat = pymupdf.Matrix(render_scale, render_scale)
        pix = self.current_page.get_pixmap(matrix=mat)

        fmt = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        qpixmap = QPixmap.fromImage(qimg)

        self.bg_item.setPixmap(qpixmap)
        sx = qpixmap.width() / self.page_rect_pdf.width
        sy = qpixmap.height() / self.page_rect_pdf.height
        self.bg_item.setTransform(QTransform().scale(1.0 / sx, 1.0 / sy))

    def _save_current_page_items(self):
        items = []
        for item in self.scene.items():
            if item == self.bg_item:
                continue
            if isinstance(item, (MovableTextItem, MovableImageItem, QGraphicsPathItem, QGraphicsRectItem)):
                items.append(item)
        self.page_annotations[self.current_page_idx] = items

    def _restore_page_items(self, page_index: int):
        if page_index in self.page_annotations:
            for item in self.page_annotations[page_index]:
                if item.scene() != self.scene:
                    self.scene.addItem(item)

    # ------------------ Zoom & Wheel Events ------------------

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
            event.accept()
        else:
            selected = self.scene.selectedItems()
            if selected and isinstance(selected[0], MovableImageItem) and event.modifiers() == Qt.KeyboardModifier.AltModifier:
                delta = event.angleDelta().y()
                factor = 1.1 if delta > 0 else 0.9
                selected[0].resize_by_factor(factor)
                event.accept()
                return
            super().wheelEvent(event)

    def zoom_in(self):
        self.set_zoom(self.zoom_factor * 1.18)

    def zoom_out(self):
        self.set_zoom(self.zoom_factor / 1.18)

    def reset_zoom(self):
        self.set_zoom(1.0)

    def set_zoom(self, factor: float):
        factor = max(0.2, min(factor, 4.5))
        scale_change = factor / self.zoom_factor
        self.zoom_factor = factor
        self.scale(scale_change, scale_change)
        self.zoom_changed.emit(self.zoom_factor)

        # Trigger sharp re-render debounce (120ms after zoom stops)
        self.sharp_timer.start(120)

    def fit_width(self):
        if self.page_rect_pdf:
            view_width = self.viewport().width() - 80
            if self.page_rect_pdf.width > 0:
                target_zoom = view_width / self.page_rect_pdf.width
                self.resetTransform()
                self.zoom_factor = 1.0
                self.set_zoom(target_zoom)

    def fit_page(self):
        if self.page_rect_pdf:
            view_width = self.viewport().width() - 80
            view_height = self.viewport().height() - 80
            if self.page_rect_pdf.width > 0 and self.page_rect_pdf.height > 0:
                zoom_x = view_width / self.page_rect_pdf.width
                zoom_y = view_height / self.page_rect_pdf.height
                target_zoom = min(zoom_x, zoom_y)
                self.resetTransform()
                self.zoom_factor = 1.0
                self.set_zoom(target_zoom)

    # ------------------ Drawing & Annotating ------------------

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())

        if self.current_tool == ToolMode.TEXT:
            if event.button() == Qt.MouseButton.LeftButton:
                text_item = MovableTextItem("Type text here...", self.text_font, self.text_color)
                text_item.setPos(scene_pos)
                self.scene.addItem(text_item)
                text_item.setFocus()
                cursor = text_item.textCursor()
                cursor.select(cursor.SelectionType.Document)
                text_item.setTextCursor(cursor)
                self._record_action(text_item)
                self.status_message.emit("Text placed.")
                return

        elif self.current_tool == ToolMode.PEN:
            if event.button() == Qt.MouseButton.LeftButton:
                self.current_painter_path = QPainterPath(scene_pos)
                pen = QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                self.current_path_item = QGraphicsPathItem(self.current_painter_path)
                self.current_path_item.setPen(pen)
                self.current_path_item.setZValue(5)
                self.scene.addItem(self.current_path_item)
                return

        elif self.current_tool == ToolMode.HIGHLIGHTER:
            if event.button() == Qt.MouseButton.LeftButton:
                self.current_painter_path = QPainterPath(scene_pos)
                pen = QPen(self.highlighter_color, 18, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.BevelJoin)
                self.current_path_item = QGraphicsPathItem(self.current_painter_path)
                self.current_path_item.setPen(pen)
                self.current_path_item.setOpacity(0.45)
                self.current_path_item.setZValue(4)
                self.scene.addItem(self.current_path_item)
                return

        elif self.current_tool == ToolMode.RECTANGLE:
            if event.button() == Qt.MouseButton.LeftButton:
                self.start_point = scene_pos
                pen = QPen(self.pen_color, self.pen_width)
                self.active_rect_item = QGraphicsRectItem(QRectF(scene_pos, scene_pos))
                self.active_rect_item.setPen(pen)
                self.active_rect_item.setZValue(5)
                self.scene.addItem(self.active_rect_item)
                return

        elif self.current_tool == ToolMode.ERASER:
            item = self.itemAt(event.pos())
            if item and item != self.bg_item:
                self.scene.removeItem(item)
                self.status_message.emit("Annotation erased.")
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())

        if self.current_tool in (ToolMode.PEN, ToolMode.HIGHLIGHTER) and self.current_painter_path:
            self.current_painter_path.lineTo(scene_pos)
            self.current_path_item.setPath(self.current_painter_path)
            return

        elif self.current_tool == ToolMode.RECTANGLE and self.active_rect_item and self.start_point:
            rect = QRectF(self.start_point, scene_pos).normalized()
            self.active_rect_item.setRect(rect)
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.current_tool in (ToolMode.PEN, ToolMode.HIGHLIGHTER) and self.current_path_item:
            self._record_action(self.current_path_item)
            self.current_path_item = None
            self.current_painter_path = None
            return

        elif self.current_tool == ToolMode.RECTANGLE and self.active_rect_item:
            self._record_action(self.active_rect_item)
            self.active_rect_item = None
            self.start_point = None
            return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            selected = self.scene.selectedItems()
            has_deleted = False
            for item in selected:
                if item != self.bg_item:
                    if isinstance(item, MovableTextItem) and item.hasFocus():
                        continue
                    self.scene.removeItem(item)
                    has_deleted = True
            if has_deleted:
                self.status_message.emit("Item removed.")
                return

        selected = self.scene.selectedItems()
        if selected and isinstance(selected[0], MovableImageItem):
            if event.key() == Qt.Key.Key_Plus or event.text() == "+":
                selected[0].resize_by_factor(1.15)
                return
            elif event.key() == Qt.Key.Key_Minus or event.text() == "-":
                selected[0].resize_by_factor(0.85)
                return

        super().keyPressEvent(event)

    def _on_selection_changed(self):
        selected = self.scene.selectedItems()
        if selected and selected[0] != self.bg_item:
            self.item_selected.emit(selected[0])
        else:
            self.item_selected.emit(None)

    def _record_action(self, item):
        if self.current_page_idx not in self.undo_stack:
            self.undo_stack[self.current_page_idx] = []
        self.undo_stack[self.current_page_idx].append(item)

    def undo(self):
        if self.current_page_idx in self.undo_stack and self.undo_stack[self.current_page_idx]:
            item = self.undo_stack[self.current_page_idx].pop()
            self.scene.removeItem(item)
            if self.current_page_idx not in self.redo_stack:
                self.redo_stack[self.current_page_idx] = []
            self.redo_stack[self.current_page_idx].append(item)
            self.status_message.emit("Undo performed.")

    def redo(self):
        if self.current_page_idx in self.redo_stack and self.redo_stack[self.current_page_idx]:
            item = self.redo_stack[self.current_page_idx].pop()
            self.scene.addItem(item)
            self.undo_stack[self.current_page_idx].append(item)
            self.status_message.emit("Redo performed.")

    def add_image_item(self, pixmap: QPixmap):
        if not self.bg_item or not self.page_rect_pdf:
            return
        item = MovableImageItem(pixmap)
        center_x = (self.page_rect_pdf.width - pixmap.width()) / 2
        center_y = (self.page_rect_pdf.height - pixmap.height()) / 2
        item.setPos(max(20, center_x), max(20, center_y))
        self.scene.addItem(item)
        self.scene.clearSelection()
        item.setSelected(True)
        self._record_action(item)
        self.set_tool(ToolMode.SELECT)
        self.status_message.emit("Placed on page. Drag or resize with +/-.")

    # ------------------ 1:1 Vector Save to PDF ------------------

    def save_all_to_doc(self, doc: pymupdf.Document):
        """Save all elements directly into the PDF using exact 1:1 PDF point coordinates."""
        self._save_current_page_items()

        for page_idx, items in self.page_annotations.items():
            if page_idx >= len(doc):
                continue

            page = doc[page_idx]

            for item in items:
                # Text Item
                if isinstance(item, MovableTextItem):
                    pos = item.pos()
                    txt = item.toPlainText().strip()
                    if txt:
                        font_size_pt = max(6, item.font().pointSize())
                        c = item.defaultTextColor()
                        color_rgb = (c.redF(), c.greenF(), c.blueF())

                        lines = txt.split("\n")
                        cur_y = pos.y() + font_size_pt
                        for line in lines:
                            if line:
                                page.insert_text(
                                    pymupdf.Point(pos.x(), cur_y),
                                    line,
                                    fontsize=font_size_pt,
                                    color=color_rgb,
                                    fontname="helv"
                                )
                            cur_y += font_size_pt * 1.25

                # Image or Signature
                elif isinstance(item, MovableImageItem):
                    pos = item.pos()
                    pix = item.pixmap()

                    byte_arr = QByteArray()
                    buf = QBuffer(byte_arr)
                    buf.open(QBuffer.OpenModeFlag.WriteOnly)
                    pix.save(buf, "PNG")
                    png_bytes = byte_arr.data()

                    target_rect = pymupdf.Rect(pos.x(), pos.y(), pos.x() + pix.width(), pos.y() + pix.height())
                    page.insert_image(target_rect, stream=png_bytes)

                # Freehand Pen Path or Highlighter
                elif isinstance(item, QGraphicsPathItem):
                    path = item.path()
                    color = item.pen().color()
                    pen_w = item.pen().width()
                    opacity = item.opacity()

                    pts = []
                    for i in range(path.elementCount()):
                        el = path.elementAt(i)
                        pts.append(pymupdf.Point(el.x, el.y))

                    if len(pts) >= 2:
                        shape = page.new_shape()
                        shape.draw_polyline(pts)
                        shape.finish(
                            color=(color.redF(), color.greenF(), color.blueF()),
                            width=max(1.0, float(pen_w)),
                            stroke_opacity=opacity
                        )
                        shape.commit()

                # Rectangle Shape
                elif isinstance(item, QGraphicsRectItem):
                    r = item.rect()
                    pos = item.pos()
                    color = item.pen().color()
                    pen_w = item.pen().width()
                    target_rect = pymupdf.Rect(
                        r.x() + pos.x(),
                        r.y() + pos.y(),
                        r.x() + pos.x() + r.width(),
                        r.y() + pos.y() + r.height()
                    )
                    shape = page.new_shape()
                    shape.draw_rect(target_rect)
                    shape.finish(
                        color=(color.redF(), color.greenF(), color.blueF()),
                        width=max(1.0, float(pen_w))
                    )
                    shape.commit()
