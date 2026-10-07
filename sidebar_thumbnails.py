"""
sidebar_thumbnails.py - Page thumbnails sidebar with clean, soft controls
"""

import pymupdf
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QMenu, QMessageBox, QApplication
)
from PyQt6.QtGui import QPixmap, QImage, QIcon
from PyQt6.QtCore import Qt, QSize, pyqtSignal


class PageThumbnailsSidebar(QWidget):
    page_selected = pyqtSignal(int)
    page_deleted = pyqtSignal(int)
    page_rotated = pyqtSignal(int, int)
    pages_reordered = pyqtSignal(int, int)
    blank_page_added = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(205)
        self.current_doc = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        lbl_pages = QLabel("Pages")
        lbl_pages.setStyleSheet("font-weight: 600; font-size: 13px; color: #475569;")
        layout.addWidget(lbl_pages)

        # Action Buttons (Clean text, no emojis)
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(5)

        self.btn_rotate_cw = QPushButton("Rotate")
        self.btn_rotate_cw.setToolTip("Rotate Page Clockwise (90°)")
        self.btn_rotate_cw.clicked.connect(lambda: self._rotate_current(90))

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setToolTip("Delete Selected Page")
        self.btn_delete.clicked.connect(self._delete_current)

        self.btn_add_blank = QPushButton("+ Page")
        self.btn_add_blank.setToolTip("Add Blank Page")
        self.btn_add_blank.clicked.connect(self._add_blank)

        btn_bar.addWidget(self.btn_rotate_cw)
        btn_bar.addWidget(self.btn_delete)
        btn_bar.addWidget(self.btn_add_blank)
        layout.addLayout(btn_bar)

        # Thumbnail List
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(120, 160))
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setMovement(QListWidget.Movement.Static)
        self.list_widget.setSpacing(8)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.list_widget.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self.list_widget)

    def load_thumbnails(self, doc: pymupdf.Document, select_page: int = 0):
        self.current_doc = doc
        self.list_widget.blockSignals(True)
        self.list_widget.clear()

        for idx, page in enumerate(doc):
            pix = page.get_pixmap(dpi=28)
            fmt = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
            qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
            qpixmap = QPixmap.fromImage(qimg)

            item = QListWidgetItem(QIcon(qpixmap), f"Page {idx + 1}")
            item.setSizeHint(QSize(160, 180))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_widget.addItem(item)

            if idx > 0 and idx % 4 == 0:
                QApplication.processEvents()

        self.list_widget.blockSignals(False)

        if 0 <= select_page < self.list_widget.count():
            self.list_widget.setCurrentRow(select_page)

    def set_current_page(self, index: int):
        if 0 <= index < self.list_widget.count():
            self.list_widget.blockSignals(True)
            self.list_widget.setCurrentRow(index)
            self.list_widget.blockSignals(False)

    def _on_row_changed(self, row: int):
        if row >= 0:
            self.page_selected.emit(row)

    def _rotate_current(self, deg: int):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.page_rotated.emit(row, deg)

    def _delete_current(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            if self.list_widget.count() <= 1:
                QMessageBox.warning(self, "Delete Page", "Cannot delete the only page in the document.")
                return
            reply = QMessageBox.question(
                self, "Confirm Delete", f"Are you sure you want to delete Page {row + 1}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.page_deleted.emit(row)

    def _add_blank(self):
        self.blank_page_added.emit()

    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return

        row = self.list_widget.row(item)
        menu = QMenu(self)

        act_rot_cw = menu.addAction("Rotate 90° Clockwise")
        act_rot_ccw = menu.addAction("Rotate 90° Counter-Clockwise")
        menu.addSeparator()

        act_up = menu.addAction("Move Page Up")
        act_down = menu.addAction("Move Page Down")
        menu.addSeparator()

        act_del = menu.addAction("Delete Page")

        action = menu.exec(self.list_widget.mapToGlobal(pos))
        if action == act_rot_cw:
            self.page_rotated.emit(row, 90)
        elif action == act_rot_ccw:
            self.page_rotated.emit(row, -90)
        elif action == act_up and row > 0:
            self.pages_reordered.emit(row, row - 1)
        elif action == act_down and row < self.list_widget.count() - 1:
            self.pages_reordered.emit(row, row + 1)
        elif action == act_del:
            self._delete_current()
