"""
home_dashboard.py - Modern WPS Office inspired Home Dashboard & Start Screen
Features quick action cards, recent files history, search, and drag-and-drop.
Strictly NO emojis.
"""

import os
import json
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QListWidget, QListWidgetItem, QLineEdit, QStackedWidget,
    QFileDialog, QGridLayout, QSizePolicy
)
from PyQt6.QtGui import QIcon, QFont, QColor, QCursor
from PyQt6.QtCore import Qt, pyqtSignal, QSize

from icons import (
    icon_wps_logo, icon_open_folder, icon_add_page, icon_merge,
    icon_split, icon_compress, icon_export_images, icon_recent_clock,
    icon_document_pdf, icon_cloud_upload, icon_tools_gear, icon_search,
    icon_text
)


RECENT_HISTORY_FILE = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "pdf_studio_recent_files.json"
)


class RecentFilesManager:
    """Manages persistent history of recently opened PDF files."""
    @staticmethod
    def load_recent() -> list[dict]:
        try:
            if os.path.exists(RECENT_HISTORY_FILE):
                with open(RECENT_HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Filter only existing files
                    return [item for item in data if os.path.exists(item.get("path", ""))]
        except Exception:
            pass
        return []

    @staticmethod
    def add_file(file_path: str):
        if not file_path or not os.path.exists(file_path):
            return
        try:
            recent = RecentFilesManager.load_recent()
            # Remove existing entry if present
            recent = [r for r in recent if os.path.abspath(r.get("path", "")) != os.path.abspath(file_path)]

            stat = os.stat(file_path)
            size_mb = stat.st_size / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 1.0 else f"{stat.st_size / 1024:.0f} KB"
            date_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(stat.st_mtime))

            entry = {
                "name": os.path.basename(file_path),
                "path": os.path.abspath(file_path),
                "size": size_str,
                "date": date_str
            }
            recent.insert(0, entry)
            recent = recent[:20]  # Keep up to 20 recent files

            with open(RECENT_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(recent, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def clear():
        try:
            if os.path.exists(RECENT_HISTORY_FILE):
                os.remove(RECENT_HISTORY_FILE)
        except Exception:
            pass


class QuickActionCard(QFrame):
    """Modern soft card for Quick Tools on the WPS Home Dashboard."""
    clicked = pyqtSignal()

    def __init__(self, icon: QIcon, title: str, description: str, parent=None):
        super().__init__(parent)
        self.setObjectName("quickActionCard")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(82)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        # Icon badge
        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon.pixmap(32, 32))
        layout.addWidget(icon_lbl)

        # Text vertical layout
        text_v = QVBoxLayout()
        text_v.setContentsMargins(0, 0, 0, 0)
        text_v.setSpacing(2)
        text_v.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        lbl_t = QLabel(title)
        lbl_t.setObjectName("cardTitle")
        lbl_d = QLabel(description)
        lbl_d.setObjectName("cardDesc")

        text_v.addWidget(lbl_t)
        text_v.addWidget(lbl_d)
        layout.addLayout(text_v)
        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class WPSHomeDashboardWidget(QWidget):
    """Full-featured modern WPS Office Start Dashboard."""
    open_file_requested = pyqtSignal(str)
    new_blank_requested = pyqtSignal()
    open_dialog_requested = pyqtSignal()
    merge_requested = pyqtSignal()
    split_requested = pyqtSignal()
    compress_requested = pyqtSignal()
    export_images_requested = pyqtSignal()
    extract_text_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("homeDashboard")
        self.setAcceptDrops(True)
        self._init_ui()
        self.refresh_recent_files()

    def _init_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ---------------- 1. Left Navigation Rail ----------------
        self.nav_rail = QFrame()
        self.nav_rail.setObjectName("homeNavRail")
        rail_layout = QVBoxLayout(self.nav_rail)
        rail_layout.setContentsMargins(14, 20, 14, 20)
        rail_layout.setSpacing(8)
        rail_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Brand header
        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        logo_lbl = QLabel()
        logo_lbl.setPixmap(icon_wps_logo(28).pixmap(28, 28))
        brand_title = QLabel("WPS PDF")
        brand_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0f172a;")
        brand_row.addWidget(logo_lbl)
        brand_row.addWidget(brand_title)
        brand_row.addStretch()
        rail_layout.addLayout(brand_row)

        rail_layout.addSpacing(16)

        # Prominent New Blank Button
        btn_new_prominent = QPushButton("+ New PDF")
        btn_new_prominent.setObjectName("primaryBtn")
        btn_new_prominent.setFixedHeight(36)
        btn_new_prominent.clicked.connect(self.new_blank_requested.emit)
        rail_layout.addWidget(btn_new_prominent)

        rail_layout.addSpacing(12)

        # Navigation Links
        self.btn_nav_recent = QPushButton("Recent Files")
        self.btn_nav_recent.setObjectName("homeNavBtn")
        self.btn_nav_recent.setIcon(icon_recent_clock(18))
        self.btn_nav_recent.setCheckable(True)
        self.btn_nav_recent.setChecked(True)
        self.btn_nav_recent.clicked.connect(lambda: self._switch_view(0))
        rail_layout.addWidget(self.btn_nav_recent)

        self.btn_nav_tools = QPushButton("PDF Tools")
        self.btn_nav_tools.setObjectName("homeNavBtn")
        self.btn_nav_tools.setIcon(icon_tools_gear(18))
        self.btn_nav_tools.setCheckable(True)
        self.btn_nav_tools.clicked.connect(lambda: self._switch_view(1))
        rail_layout.addWidget(self.btn_nav_tools)

        self.btn_nav_open = QPushButton("Open Local File")
        self.btn_nav_open.setObjectName("homeNavBtn")
        self.btn_nav_open.setIcon(icon_open_folder(18))
        self.btn_nav_open.clicked.connect(self.open_dialog_requested.emit)
        rail_layout.addWidget(self.btn_nav_open)

        rail_layout.addStretch()

        # Bottom subtle hint
        lbl_version = QLabel("Studio Pro • Vector High-DPI")
        lbl_version.setStyleSheet("color: #94a3b8; font-size: 11px;")
        rail_layout.addWidget(lbl_version)

        root_layout.addWidget(self.nav_rail)

        # ---------------- 2. Central Content Stack ----------------
        self.content_stack = QStackedWidget()

        # Page 0: Main Hub (Quick Cards + Recent Files)
        self.content_stack.addWidget(self._create_main_hub_page())

        # Page 1: PDF Tools Hub
        self.content_stack.addWidget(self._create_tools_hub_page())

        root_layout.addWidget(self.content_stack)

    def _switch_view(self, idx: int):
        self.btn_nav_recent.setChecked(idx == 0)
        self.btn_nav_tools.setChecked(idx == 1)
        self.content_stack.setCurrentIndex(idx)

    # ------------------ Main Hub View ------------------

    def _create_main_hub_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(20)

        # Top Greeting
        header_v = QVBoxLayout()
        header_v.setSpacing(4)
        title = QLabel("Welcome to WPS PDF")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #0f172a;")
        subtitle = QLabel("Choose a tool to begin, or pick up where you left off")
        subtitle.setStyleSheet("color: #64748b; font-size: 13px;")
        header_v.addWidget(title)
        header_v.addWidget(subtitle)
        layout.addLayout(header_v)

        # Quick Action Cards (Grid of 6 modern cards)
        cards_grid = QGridLayout()
        cards_grid.setSpacing(12)

        c_blank = QuickActionCard(icon_add_page(28, "#ea580c"), "Blank PDF", "Create a fresh A4 document")
        c_blank.clicked.connect(self.new_blank_requested.emit)

        c_open = QuickActionCard(icon_open_folder(28, "#2563eb"), "Open Document", "Browse PDF files from disk")
        c_open.clicked.connect(self.open_dialog_requested.emit)

        c_merge = QuickActionCard(icon_merge(28, "#7c3aed"), "Merge PDFs", "Combine multiple files into one")
        c_merge.clicked.connect(self.merge_requested.emit)

        c_split = QuickActionCard(icon_split(28, "#ea580c"), "Split PDF", "Extract & divide page ranges")
        c_split.clicked.connect(self.split_requested.emit)

        c_compress = QuickActionCard(icon_compress(28, "#0d9488"), "PDF Compressor", "Optimize and reduce file size")
        c_compress.clicked.connect(self.compress_requested.emit)

        c_export = QuickActionCard(icon_export_images(28, "#16a34a"), "PDF to Picture", "Export pages as PNG images")
        c_export.clicked.connect(self.export_images_requested.emit)

        cards_grid.addWidget(c_blank, 0, 0)
        cards_grid.addWidget(c_open, 0, 1)
        cards_grid.addWidget(c_merge, 0, 2)
        cards_grid.addWidget(c_split, 1, 0)
        cards_grid.addWidget(c_compress, 1, 1)
        cards_grid.addWidget(c_export, 1, 2)
        layout.addLayout(cards_grid)

        # Recent Files Section Header
        recent_header = QHBoxLayout()
        lbl_recent = QLabel("Recent Documents")
        lbl_recent.setStyleSheet("font-size: 15px; font-weight: 600; color: #0f172a;")
        recent_header.addWidget(lbl_recent)

        recent_header.addStretch()

        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("Search recent files...")
        self.txt_filter.setFixedWidth(220)
        self.txt_filter.setFixedHeight(30)
        self.txt_filter.textChanged.connect(self._filter_recent_files)
        recent_header.addWidget(self.txt_filter)

        btn_clear = QPushButton("Clear")
        btn_clear.setFixedHeight(30)
        btn_clear.clicked.connect(self._clear_recent_files)
        recent_header.addWidget(btn_clear)

        layout.addLayout(recent_header)

        # Recent Files List Container
        self.recent_stack = QStackedWidget()

        # 1. Populated list
        self.list_recent = QListWidget()
        self.list_recent.setObjectName("recentFilesList")
        self.list_recent.itemDoubleClicked.connect(self._on_recent_item_double_clicked)
        self.recent_stack.addWidget(self.list_recent)

        # 2. Empty Drag & Drop Zone
        self.drop_zone = QFrame()
        self.drop_zone.setObjectName("modernDropZone")
        dz_l = QVBoxLayout(self.drop_zone)
        dz_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dz_l.setSpacing(10)

        cloud_lbl = QLabel()
        cloud_lbl.setPixmap(icon_cloud_upload(42, "#94a3b8").pixmap(42, 42))
        cloud_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dz_title = QLabel("No Recent Documents")
        dz_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #334155;")
        dz_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dz_desc = QLabel("Drag & drop any PDF file here to start reading and editing")
        dz_desc.setStyleSheet("color: #64748b; font-size: 12px;")
        dz_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_browse = QPushButton("Browse Files")
        btn_browse.setObjectName("primaryBtn")
        btn_browse.setFixedHeight(34)
        btn_browse.clicked.connect(self.open_dialog_requested.emit)

        dz_l.addWidget(cloud_lbl)
        dz_l.addWidget(dz_title)
        dz_l.addWidget(dz_desc)
        dz_l.addSpacing(6)
        dz_l.addWidget(btn_browse, alignment=Qt.AlignmentFlag.AlignCenter)

        self.recent_stack.addWidget(self.drop_zone)
        layout.addWidget(self.recent_stack, 1)

        return page

    # ------------------ Tools Hub View ------------------

    def _create_tools_hub_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(20)

        title = QLabel("PDF Tools & Utilities")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #0f172a;")
        subtitle = QLabel("Professional document management, compression, and conversion tools")
        subtitle.setStyleSheet("color: #64748b; font-size: 13px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(16)

        # Card 1: Compressor
        c1 = self._create_tool_card(
            icon_compress(32, "#0d9488"), "PDF Compressor",
            "Optimize streams and deflate images to significantly reduce PDF file size.",
            "Compress PDF", self.compress_requested.emit
        )
        # Card 2: Merge
        c2 = self._create_tool_card(
            icon_merge(32, "#7c3aed"), "Merge PDFs",
            "Select multiple PDF files, reorder pages, and assemble into a single document.",
            "Merge Files", self.merge_requested.emit
        )
        # Card 3: Split
        c3 = self._create_tool_card(
            icon_split(32, "#ea580c"), "Split PDF",
            "Divide an existing document into multiple files by exact page ranges.",
            "Split Pages", self.split_requested.emit
        )
        # Card 4: PDF to Picture
        c4 = self._create_tool_card(
            icon_export_images(32, "#16a34a"), "PDF to Picture",
            "Export pages as crystal-clear PNG images in high resolution.",
            "Export PNG", self.export_images_requested.emit
        )
        # Card 5: Extract Text
        c5 = self._create_tool_card(
            icon_text(32, "#2563eb"), "Extract Text",
            "Extract all text content from the entire document into an editable text file.",
            "Extract Text", self.extract_text_requested.emit
        )
        # Card 6: New Blank
        c6 = self._create_tool_card(
            icon_add_page(32, "#ea580c"), "Blank Document",
            "Create a clean white PDF document ready for text and annotations.",
            "Create Blank", self.new_blank_requested.emit
        )

        grid.addWidget(c1, 0, 0)
        grid.addWidget(c2, 0, 1)
        grid.addWidget(c3, 1, 0)
        grid.addWidget(c4, 1, 1)
        grid.addWidget(c5, 2, 0)
        grid.addWidget(c6, 2, 1)

        layout.addLayout(grid)
        layout.addStretch()
        return page

    def _create_tool_card(self, icon: QIcon, title: str, desc: str, btn_text: str, callback) -> QFrame:
        card = QFrame()
        card.setObjectName("quickActionCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon.pixmap(36, 36))
        layout.addWidget(icon_lbl)

        text_v = QVBoxLayout()
        text_v.setSpacing(3)
        t_lbl = QLabel(title)
        t_lbl.setObjectName("cardTitle")
        d_lbl = QLabel(desc)
        d_lbl.setObjectName("cardDesc")
        d_lbl.setWordWrap(True)
        text_v.addWidget(t_lbl)
        text_v.addWidget(d_lbl)
        layout.addLayout(text_v, 1)

        btn = QPushButton(btn_text)
        btn.setFixedHeight(32)
        btn.clicked.connect(callback)
        layout.addWidget(btn)

        return card

    # ------------------ Recent Files Logic ------------------

    def refresh_recent_files(self):
        recent = RecentFilesManager.load_recent()
        self._populate_list(recent)

    def _populate_list(self, files: list[dict]):
        self.list_recent.clear()
        if not files:
            self.recent_stack.setCurrentIndex(1)  # Show drop zone
            return

        self.recent_stack.setCurrentIndex(0)  # Show list
        for item in files:
            name = item.get("name", "Document.pdf")
            path = item.get("path", "")
            size = item.get("size", "")
            date = item.get("date", "")

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(4, 2, 4, 2)
            row_layout.setSpacing(12)

            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon_document_pdf(22).pixmap(22, 22))
            row_layout.addWidget(icon_lbl)

            info_v = QVBoxLayout()
            info_v.setContentsMargins(0, 0, 0, 0)
            info_v.setSpacing(2)

            name_lbl = QLabel(name)
            name_lbl.setStyleSheet("font-weight: 600; font-size: 13px; color: #0f172a;")
            path_lbl = QLabel(path)
            path_lbl.setStyleSheet("font-size: 11px; color: #64748b;")
            info_v.addWidget(name_lbl)
            info_v.addWidget(path_lbl)
            row_layout.addLayout(info_v, 1)

            size_lbl = QLabel(size)
            size_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; min-width: 60px;")
            size_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(size_lbl)

            date_lbl = QLabel(date)
            date_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; min-width: 110px;")
            date_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(date_lbl)

            list_item = QListWidgetItem(self.list_recent)
            list_item.setSizeHint(row_widget.sizeHint())
            list_item.setData(Qt.ItemDataRole.UserRole, path)
            self.list_recent.setItemWidget(list_item, row_widget)

    def _filter_recent_files(self, text: str):
        query = text.strip().lower()
        recent = RecentFilesManager.load_recent()
        if not query:
            self._populate_list(recent)
        else:
            filtered = [r for r in recent if query in r.get("name", "").lower() or query in r.get("path", "").lower()]
            self._populate_list(filtered)

    def _clear_recent_files(self):
        RecentFilesManager.clear()
        self.refresh_recent_files()

    def _on_recent_item_double_clicked(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and os.path.exists(path):
            self.open_file_requested.emit(path)

    # ------------------ Drag & Drop ------------------

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".pdf"):
                self.open_file_requested.emit(file_path)
                event.acceptProposedAction()
                return
