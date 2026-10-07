"""
app.py - WPS PDF Clone (Ribbon UI, Modern Soft Design, No Emojis)
Faithfully implements the WPS Office PDF Reader & Editor interface.
"""

import sys
import os
import pymupdf
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStatusBar, QFileDialog, QMessageBox, QLabel,
    QSpinBox, QComboBox, QColorDialog, QSplitter, QStackedWidget,
    QPushButton, QFrame, QMenu, QToolButton, QButtonGroup, QSlider, QInputDialog
)
from PyQt6.QtGui import QAction, QActionGroup, QIcon, QKeySequence, QColor, QFont, QPixmap, QPainter, QPen, QBrush, QCursor
from PyQt6.QtCore import Qt, QSize, QTimer

from styles import WPS_THEME
from icons import (
    icon_wps_logo, icon_hand, icon_select, icon_text, icon_highlight,
    icon_pen, icon_eraser, icon_rect, icon_image, icon_sign,
    icon_rotate_cw, icon_rotate_ccw, icon_delete, icon_add_page,
    icon_merge, icon_split, icon_compress, icon_print, icon_undo, icon_redo,
    icon_open_folder, icon_save_disk, icon_fit_width, icon_fit_page,
    icon_zoom_actual, icon_zoom_in, icon_zoom_out, icon_fullscreen, icon_export_images, icon_sidebar, icon_search
)
from home_dashboard import WPSHomeDashboardWidget, RecentFilesManager
from pdf_canvas import PDFCanvas, ToolMode, MovableImageItem, MovableTextItem
from sidebar_thumbnails import PageThumbnailsSidebar
from dialogs.signature_dialog import SignatureDialog
from dialogs.merge_dialog import MergeDialog
from dialogs.split_dialog import SplitDialog


def make_color_dot_icon(color: QColor, size=14) -> QIcon:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(color)
    painter.setPen(QPen(QColor("#cbd5e1"), 1))
    painter.drawEllipse(1, 1, size - 2, size - 2)
    painter.end()
    return QIcon(pix)


def create_ribbon_sep() -> QFrame:
    """Helper to create a sleek vertical divider between ribbon tool sections."""
    sep = QFrame()
    sep.setObjectName("ribbonSep")
    sep.setFrameShape(QFrame.Shape.VLine)
    sep.setFrameShadow(QFrame.Shadow.Plain)
    return sep





class FullscreenOverlayBanner(QFrame):
    """Floating banner for Fullscreen Mode."""
    def __init__(self, parent_app):
        super().__init__(parent_app)
        self.app = parent_app
        self.setObjectName("edgeFullscreenBanner")
        self.setFixedHeight(40)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(10)

        lbl = QLabel("To exit full screen, press")
        lbl.setStyleSheet("color: #f1f5f9; font-size: 12px; font-weight: 500;")

        badge = QLabel("Esc")
        badge.setStyleSheet("""
            background-color: #334155;
            color: #ffffff;
            font-weight: 600;
            font-size: 11px;
            border-radius: 4px;
            padding: 2px 8px;
            border: 1px solid #475569;
        """)

        btn_exit = QPushButton("Exit")
        btn_exit.setFixedHeight(24)
        btn_exit.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.15);
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.28);
            }
        """)
        btn_exit.clicked.connect(self.app.toggle_fullscreen)

        layout.addWidget(lbl)
        layout.addWidget(badge)
        layout.addSpacing(6)
        layout.addWidget(btn_exit)


class PDFEditorApp(QMainWindow):
    def __init__(self, initial_file=None):
        super().__init__()
        self.setWindowTitle("WPS PDF - Studio Pro")
        self.setWindowIcon(icon_wps_logo(32))
        self.resize(1360, 880)
        self.setAcceptDrops(True)

        self.doc = None
        self.current_file_path = None
        self.current_page_idx = 0
        self.is_fullscreen_mode = False

        self._init_ui()

        if initial_file and os.path.exists(initial_file):
            self.load_pdf(initial_file)
        else:
            self.show_home_dashboard()

    def _init_ui(self):
        self.setStyleSheet(WPS_THEME)

        modern_font = QFont()
        modern_font.setFamilies(["Segoe UI Variable Text", "Segoe UI", "Inter", "sans-serif"])
        modern_font.setPointSize(9)
        modern_font.setStyleHint(QFont.StyleHint.SansSerif)
        self.setFont(modern_font)

        # Central Root Layout
        root_widget = QWidget()
        self.root_layout = QVBoxLayout(root_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        self.setCentralWidget(root_widget)

        # Core Components (Initialized early for action wiring)
        self.canvas = PDFCanvas(self)
        self.sidebar = PageThumbnailsSidebar(self)
        self.sidebar.setObjectName("sidebarWidget")

        # Build WPS Header Elements
        self._create_actions()
        self._create_wps_top_titlebar()
        self._create_wps_nav_row()
        self._create_wps_ribbon_body()

        # Workspace Stack: [0: Home Dashboard, 1: Main PDF Document]
        self.central_stack = QStackedWidget()

        # Modern WPS Home Dashboard
        self.home_dashboard = WPSHomeDashboardWidget(self)
        self.home_dashboard.open_file_requested.connect(self.load_pdf)
        self.home_dashboard.new_blank_requested.connect(self.new_blank_document)
        self.home_dashboard.open_dialog_requested.connect(self.open_pdf_dialog)
        self.home_dashboard.merge_requested.connect(self._open_merge_dialog)
        self.home_dashboard.split_requested.connect(self._open_split_dialog)
        self.home_dashboard.compress_requested.connect(self.compress_pdf)
        self.home_dashboard.export_images_requested.connect(self.export_as_images)
        self.home_dashboard.extract_text_requested.connect(self.extract_text)
        self.central_stack.addWidget(self.home_dashboard)

        # Main Document Workspace with Left Rail, Sidebar & Canvas
        doc_container = QWidget()
        doc_layout = QHBoxLayout(doc_container)
        doc_layout.setContentsMargins(0, 0, 0, 0)
        doc_layout.setSpacing(0)

        # WPS Left Navigation Rail (Vertical strip with icon buttons)
        self.left_rail = QFrame()
        self.left_rail.setObjectName("wpsLeftRail")
        rail_layout = QVBoxLayout(self.left_rail)
        rail_layout.setContentsMargins(4, 8, 4, 8)
        rail_layout.setSpacing(8)
        rail_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.btn_rail_thumbs = QToolButton()
        self.btn_rail_thumbs.setObjectName("wpsRailBtn")
        self.btn_rail_thumbs.setIcon(icon_sidebar(20, "#475569"))
        self.btn_rail_thumbs.setToolTip("Page Thumbnails")
        self.btn_rail_thumbs.setCheckable(True)
        self.btn_rail_thumbs.setChecked(True)
        self.btn_rail_thumbs.clicked.connect(self._toggle_sidebar)

        self.btn_rail_search = QToolButton()
        self.btn_rail_search.setObjectName("wpsRailBtn")
        self.btn_rail_search.setIcon(icon_search(20, "#475569"))
        self.btn_rail_search.setToolTip("Search in Document (Ctrl+F)")
        self.btn_rail_search.clicked.connect(self._find_text_dialog)

        rail_layout.addWidget(self.btn_rail_thumbs)
        rail_layout.addWidget(self.btn_rail_search)
        doc_layout.addWidget(self.left_rail)

        # Splitter: Sidebar + Canvas
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.canvas)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        doc_layout.addWidget(self.splitter)

        self.central_stack.addWidget(doc_container)
        self.root_layout.addWidget(self.central_stack)

        # Fullscreen Banner
        self.banner = FullscreenOverlayBanner(self)
        self.banner.hide()

        # Connect Sidebar & Canvas
        self.sidebar.page_selected.connect(self.go_to_page)
        self.sidebar.page_rotated.connect(self.rotate_page)
        self.sidebar.page_deleted.connect(self.delete_page)
        self.sidebar.pages_reordered.connect(self.reorder_pages)
        self.sidebar.blank_page_added.connect(self.add_blank_page)

        self.canvas.zoom_changed.connect(self._on_zoom_changed)
        self.canvas.status_message.connect(self._show_status_message)

        # WPS Status Bar
        self._create_wps_statusbar()

    def _create_actions(self):
        # File Operations
        self.act_new = QAction(icon_add_page(16), "New Blank Document", self, triggered=self.new_blank_document)
        self.act_new.setShortcut(QKeySequence.StandardKey.New)

        self.act_open = QAction(icon_open_folder(16), "Open...", self, triggered=self.open_pdf_dialog)
        self.act_open.setShortcut(QKeySequence.StandardKey.Open)

        self.act_save = QAction(icon_save_disk(16), "Save", self, triggered=self.save_document)
        self.act_save.setShortcut(QKeySequence.StandardKey.Save)

        self.act_save_as = QAction("Save As...", self, triggered=self.save_document_as)
        self.act_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)

        self.act_export_images = QAction(icon_export_images(16), "Export Pages as PNG...", self, triggered=self.export_as_images)
        self.act_extract_text = QAction("Extract Text to File...", self, triggered=self.extract_text)
        self.act_print = QAction(icon_print(16), "Print...", self, triggered=self.print_document)
        self.act_print.setShortcut(QKeySequence.StandardKey.Print)

        self.act_close_doc = QAction("Close Document", self, triggered=self.show_welcome_screen)
        self.act_close_doc.setShortcut(QKeySequence.StandardKey.Close)

        # Undo / Redo
        self.act_undo = QAction(icon_undo(16), "Undo", self, triggered=self.canvas.undo)
        self.act_undo.setShortcut(QKeySequence.StandardKey.Undo)

        self.act_redo = QAction(icon_redo(16), "Redo", self, triggered=self.canvas.redo)
        self.act_redo.setShortcut(QKeySequence.StandardKey.Redo)

        # Full Screen
        self.act_fullscreen = QAction(icon_fullscreen(16), "Fullscreen", self, triggered=self.toggle_fullscreen)
        self.act_fullscreen.setShortcut(QKeySequence("F11"))

        # Mutually Exclusive Editing Tools
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)

        self.act_select = QAction(icon_select(16), "Select Tool", self, checkable=True, triggered=lambda: self._switch_tool(ToolMode.SELECT))
        self.act_select.setChecked(True)
        self.tool_group.addAction(self.act_select)

        self.act_hand = QAction(icon_hand(16), "Hand Tool", self, checkable=True, triggered=lambda: self._switch_tool(ToolMode.HAND))
        self.tool_group.addAction(self.act_hand)

        self.act_text = QAction(icon_text(16), "Edit Text", self, checkable=True, triggered=lambda: self._switch_tool(ToolMode.TEXT))
        self.tool_group.addAction(self.act_text)

        self.act_pen = QAction(icon_pen(16), "Pen", self, checkable=True, triggered=lambda: self._switch_tool(ToolMode.PEN))
        self.tool_group.addAction(self.act_pen)

        self.act_highlight = QAction(icon_highlight(16), "Annotate", self, checkable=True, triggered=lambda: self._switch_tool(ToolMode.HIGHLIGHTER))
        self.tool_group.addAction(self.act_highlight)

        self.act_eraser = QAction(icon_eraser(16), "Eraser", self, checkable=True, triggered=lambda: self._switch_tool(ToolMode.ERASER))
        self.tool_group.addAction(self.act_eraser)

        self.act_rect = QAction(icon_rect(16), "Rectangle", self, checkable=True, triggered=lambda: self._switch_tool(ToolMode.RECTANGLE))
        self.tool_group.addAction(self.act_rect)

        # Actions
        self.act_sign = QAction(icon_sign(16), "Sign", self, triggered=self._insert_signature_dialog)
        self.act_image = QAction(icon_image(16), "Edit Picture", self, triggered=self._insert_image_dialog)

        # Page Actions
        self.act_rot_cw = QAction(icon_rotate_cw(16), "Clockwise", self, triggered=self.rotate_clockwise)
        self.act_rot_ccw = QAction(icon_rotate_ccw(16), "Anticlockwise", self, triggered=self.rotate_anticlockwise)
        self.act_rot_180 = QAction(icon_rotate_cw(16), "Rotate 180°", self, triggered=self.rotate_180)
        self.act_delete_page = QAction(icon_delete(16), "Delete Pages", self, triggered=lambda: self.delete_page(self.current_page_idx))
        self.act_add_page = QAction(icon_add_page(16), "Insert Pages", self, triggered=self.add_blank_page)
        self.act_extract_page = QAction(icon_add_page(16), "Extract Page", self, triggered=self.extract_current_page)

        # Utilities
        self.act_compress = QAction(icon_compress(16), "PDF Compressor", self, triggered=self.compress_pdf)
        self.act_merge = QAction(icon_merge(16), "Merge PDF", self, triggered=self._open_merge_dialog)
        self.act_split = QAction(icon_split(16), "Split PDF", self, triggered=self._open_split_dialog)

        # Zoom
        self.act_zoom_in = QAction(icon_zoom_in(16), "Zoom In", self, triggered=self.canvas.zoom_in)
        self.act_zoom_in.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.act_zoom_out = QAction(icon_zoom_out(16), "Zoom Out", self, triggered=self.canvas.zoom_out)
        self.act_zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.act_zoom_actual = QAction(icon_zoom_actual(16), "1:1", self, triggered=self.canvas.reset_zoom)
        self.act_fit_width = QAction(icon_fit_width(16), "Fit Width", self, triggered=self.canvas.fit_width)
        self.act_fit_page = QAction(icon_fit_page(16), "Fit Page", self, triggered=self.canvas.fit_page)

    def _create_wps_top_titlebar(self):
        """Top Bar 1: Home Pill Tab, Document Tab [P Title x], and [+] New Tab."""
        self.top_titlebar = QFrame()
        self.top_titlebar.setObjectName("wpsTitleBar")
        layout = QHBoxLayout(self.top_titlebar)
        layout.setContentsMargins(6, 4, 6, 0)
        layout.setSpacing(6)

        # 1. Blue Home Pill Tab
        self.btn_home_pill = QPushButton("Home")
        self.btn_home_pill.setObjectName("wpsHomePill")
        self.btn_home_pill.clicked.connect(self._on_home_pill_clicked)
        layout.addWidget(self.btn_home_pill)

        # 2. Document Tab (WPS Office style card)
        self.tab_doc_card = QFrame()
        self.tab_doc_card.setObjectName("wpsDocTab")
        self.tab_doc_card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.tab_doc_card.mousePressEvent = lambda ev: self.show_workspace() if self.doc else None
        card_l = QHBoxLayout(self.tab_doc_card)
        card_l.setContentsMargins(8, 2, 8, 2)
        card_l.setSpacing(6)

        logo_lbl = QLabel()
        logo_lbl.setPixmap(icon_wps_logo(16).pixmap(16, 16))
        card_l.addWidget(logo_lbl)

        self.lbl_doc_title = QLabel("PDF Studio Pro")
        self.lbl_doc_title.setObjectName("wpsDocTabTitle")
        card_l.addWidget(self.lbl_doc_title)

        self.btn_tab_close = QToolButton()
        self.btn_tab_close.setObjectName("wpsDocTabClose")
        self.btn_tab_close.setText("×")
        self.btn_tab_close.setToolTip("Close Document")
        self.btn_tab_close.clicked.connect(self.close_current_document)
        card_l.addWidget(self.btn_tab_close)

        layout.addWidget(self.tab_doc_card)

        # 3. Plus Button [+]
        btn_plus = QToolButton()
        btn_plus.setObjectName("wpsNewTabBtn")
        btn_plus.setText("+")
        btn_plus.setToolTip("Open New Document")
        btn_plus.clicked.connect(self.open_pdf_dialog)
        layout.addWidget(btn_plus)

        layout.addStretch()

        self.root_layout.addWidget(self.top_titlebar)

    def _create_wps_nav_row(self):
        """Top Bar 2: Menu Dropdown, Quick Access Icons, and Ribbon Tabs."""
        self.nav_row = QFrame()
        self.nav_row.setObjectName("wpsNavRow")
        layout = QHBoxLayout(self.nav_row)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        # 1. ☰ Menu ▾ Button
        self.btn_menu = QPushButton("Menu")
        self.btn_menu.setObjectName("wpsMenuBtn")
        self.btn_menu.setMenu(self._create_main_menu())
        layout.addWidget(self.btn_menu)

        # Quick separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet("color: #e2e8f0; margin: 4px 2px;")
        layout.addWidget(sep1)

        # 2. Quick Access Icons
        btn_q_open = QToolButton(); btn_q_open.setObjectName("wpsQuickBtn"); btn_q_open.setDefaultAction(self.act_open)
        btn_q_save = QToolButton(); btn_q_save.setObjectName("wpsQuickBtn"); btn_q_save.setDefaultAction(self.act_save)
        btn_q_undo = QToolButton(); btn_q_undo.setObjectName("wpsQuickBtn"); btn_q_undo.setDefaultAction(self.act_undo)
        btn_q_redo = QToolButton(); btn_q_redo.setObjectName("wpsQuickBtn"); btn_q_redo.setDefaultAction(self.act_redo)
        btn_q_print = QToolButton(); btn_q_print.setObjectName("wpsQuickBtn"); btn_q_print.setDefaultAction(self.act_print)

        layout.addWidget(btn_q_open)
        layout.addWidget(btn_q_save)
        layout.addWidget(btn_q_undo)
        layout.addWidget(btn_q_redo)
        layout.addWidget(btn_q_print)

        # Separator before tabs
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("color: #e2e8f0; margin: 4px 4px;")
        layout.addWidget(sep2)

        # 3. WPS Ribbon Tabs (Home, Edit, Comment, Page, Tools)
        self.ribbon_tab_group = QButtonGroup(self)
        self.ribbon_tab_group.setExclusive(True)

        tab_names = ["Home", "Edit", "Comment", "Page", "Tools"]
        for idx, name in enumerate(tab_names):
            btn = QPushButton(name)
            btn.setObjectName("wpsRibbonTab")
            btn.setCheckable(True)
            if idx == 0:
                btn.setChecked(True)
            self.ribbon_tab_group.addButton(btn, idx)
            layout.addWidget(btn)

        layout.addStretch()

        # Fullscreen on right
        btn_fs = QToolButton()
        btn_fs.setObjectName("wpsQuickBtn")
        btn_fs.setDefaultAction(self.act_fullscreen)
        layout.addWidget(btn_fs)

        self.root_layout.addWidget(self.nav_row)

    def _create_wps_ribbon_body(self):
        """Ribbon Toolbar Body (QStackedWidget switched by Ribbon Tabs)."""
        self.ribbon_stack = QStackedWidget()
        self.ribbon_stack.setObjectName("wpsRibbonBody")
        self.ribbon_stack.setFixedHeight(48)

        # Add Tab Panels in matching order
        self.ribbon_stack.addWidget(self._create_ribbon_home())
        self.ribbon_stack.addWidget(self._create_ribbon_edit())
        self.ribbon_stack.addWidget(self._create_ribbon_comment())
        self.ribbon_stack.addWidget(self._create_ribbon_page())
        self.ribbon_stack.addWidget(self._create_ribbon_tools())

        self.ribbon_tab_group.idClicked.connect(self.ribbon_stack.setCurrentIndex)
        self.root_layout.addWidget(self.ribbon_stack)

    # ------------------ Ribbon Tab Panels ------------------

    def _create_ribbon_home(self) -> QWidget:
        """Home Tab: Tools, Edit & Content, Inline Zoom Controls."""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(4)

        # Section 1: Navigation Tools
        btn_hand = QToolButton(); btn_hand.setDefaultAction(self.act_hand)
        btn_hand.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_sel = QToolButton(); btn_sel.setDefaultAction(self.act_select)
        btn_sel.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        layout.addWidget(btn_hand)
        layout.addWidget(btn_sel)
        layout.addWidget(create_ribbon_sep())

        # Section 2: Edit & Content
        btn_txt = QToolButton(); btn_txt.setDefaultAction(self.act_text)
        btn_txt.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_img = QToolButton(); btn_img.setDefaultAction(self.act_image)
        btn_img.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_exp = QToolButton(); btn_exp.setDefaultAction(self.act_export_images)
        btn_exp.setText("PDF to Picture")
        btn_exp.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_anno = QToolButton(); btn_anno.setDefaultAction(self.act_highlight)
        btn_anno.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_sign = QToolButton(); btn_sign.setDefaultAction(self.act_sign)
        btn_sign.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        layout.addWidget(btn_txt)
        layout.addWidget(btn_img)
        layout.addWidget(btn_exp)
        layout.addWidget(btn_anno)
        layout.addWidget(btn_sign)
        layout.addWidget(create_ribbon_sep())

        # Section 3: Inline Zoom & View Controls (No squashed dots, crisp and spacious)
        btn_z_out = QToolButton(); btn_z_out.setDefaultAction(self.act_zoom_out)
        btn_z_out.setToolTip("Zoom Out (Ctrl+-)")

        self.combo_zoom = QComboBox()
        self.combo_zoom.setFixedWidth(92)
        self.combo_zoom.setFixedHeight(28)
        self.combo_zoom.addItems(["50%", "75%", "100%", "125%", "150%", "200%", "300%", "Fit Width", "Fit Page"])
        self.combo_zoom.setCurrentText("100%")
        self.combo_zoom.currentTextChanged.connect(self._on_combo_zoom_selected)

        btn_z_in = QToolButton(); btn_z_in.setDefaultAction(self.act_zoom_in)
        btn_z_in.setToolTip("Zoom In (Ctrl++)")

        btn_11 = QToolButton(); btn_11.setDefaultAction(self.act_zoom_actual)
        btn_11.setToolTip("Original Size (1:1)")

        btn_fw = QToolButton(); btn_fw.setDefaultAction(self.act_fit_width)
        btn_fw.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_fp = QToolButton(); btn_fp.setDefaultAction(self.act_fit_page)
        btn_fp.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_rot = QToolButton(); btn_rot.setDefaultAction(self.act_rot_cw)
        btn_rot.setText("Rotate")
        btn_rot.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        layout.addWidget(btn_z_out)
        layout.addWidget(self.combo_zoom)
        layout.addWidget(btn_z_in)
        layout.addWidget(btn_11)
        layout.addWidget(btn_fw)
        layout.addWidget(btn_fp)
        layout.addWidget(btn_rot)

        layout.addStretch()
        return panel

    def _create_ribbon_edit(self) -> QWidget:
        """Edit Tab: Insert Text, Insert Picture, Sign, Formatting, History."""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(4)

        # Section 1: Insert Content
        btn_txt = QToolButton(); btn_txt.setDefaultAction(self.act_text)
        btn_txt.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_img = QToolButton(); btn_img.setDefaultAction(self.act_image)
        btn_img.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_sign = QToolButton(); btn_sign.setDefaultAction(self.act_sign)
        btn_sign.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        layout.addWidget(btn_txt)
        layout.addWidget(btn_img)
        layout.addWidget(btn_sign)
        layout.addWidget(create_ribbon_sep())

        # Section 2: Format & Color
        btn_col = QPushButton("Color ▾")
        btn_col.setFixedHeight(28)
        btn_col.setMenu(self._create_color_menu())

        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(8, 72)
        self.spin_font_size.setValue(14)
        self.spin_font_size.setPrefix("Size: ")
        self.spin_font_size.setFixedHeight(28)
        self.spin_font_size.valueChanged.connect(self._change_font_size)

        layout.addWidget(btn_col)
        layout.addWidget(self.spin_font_size)
        layout.addWidget(create_ribbon_sep())

        # Section 3: History
        btn_undo = QToolButton(); btn_undo.setDefaultAction(self.act_undo)
        btn_undo.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_redo = QToolButton(); btn_redo.setDefaultAction(self.act_redo)
        btn_redo.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        layout.addWidget(btn_undo)
        layout.addWidget(btn_redo)

        layout.addStretch()
        return panel

    def _create_ribbon_comment(self) -> QWidget:
        """Comment Tab: Highlight, Pen, Eraser, Rectangle, Color Palette."""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(4)

        # Section 1: Markup
        btn_hi = QToolButton(); btn_hi.setDefaultAction(self.act_highlight)
        btn_hi.setText("Highlighter")
        btn_hi.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_pen = QToolButton(); btn_pen.setDefaultAction(self.act_pen)
        btn_pen.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_era = QToolButton(); btn_era.setDefaultAction(self.act_eraser)
        btn_era.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        layout.addWidget(btn_hi)
        layout.addWidget(btn_pen)
        layout.addWidget(btn_era)
        layout.addWidget(create_ribbon_sep())

        # Section 2: Annotations
        btn_box = QToolButton(); btn_box.setDefaultAction(self.act_rect)
        btn_box.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_txt = QToolButton(); btn_txt.setDefaultAction(self.act_text)
        btn_txt.setText("Text Note")
        btn_txt.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        layout.addWidget(btn_box)
        layout.addWidget(btn_txt)
        layout.addWidget(create_ribbon_sep())

        # Section 3: Palette
        btn_col = QPushButton("Palette ▾")
        btn_col.setFixedHeight(28)
        btn_col.setMenu(self._create_color_menu())
        layout.addWidget(btn_col)

        layout.addStretch()
        return panel

    def _create_ribbon_page(self) -> QWidget:
        """Page Tab: Rotate CCW, Rotate CW, Rotate 180, Delete, Insert, Extract."""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(4)

        # Section 1: Rotate
        btn_ccw = QToolButton(); btn_ccw.setDefaultAction(self.act_rot_ccw)
        btn_ccw.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_cw = QToolButton(); btn_cw.setDefaultAction(self.act_rot_cw)
        btn_cw.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_180 = QToolButton(); btn_180.setDefaultAction(self.act_rot_180)
        btn_180.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        layout.addWidget(btn_ccw)
        layout.addWidget(btn_cw)
        layout.addWidget(btn_180)
        layout.addWidget(create_ribbon_sep())

        # Section 2: Organize Pages
        btn_add = QToolButton(); btn_add.setDefaultAction(self.act_add_page)
        btn_add.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_ext = QToolButton(); btn_ext.setDefaultAction(self.act_extract_page)
        btn_ext.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_del = QToolButton(); btn_del.setDefaultAction(self.act_delete_page)
        btn_del.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        layout.addWidget(btn_add)
        layout.addWidget(btn_ext)
        layout.addWidget(btn_del)

        layout.addStretch()
        return panel

    def _create_ribbon_tools(self) -> QWidget:
        """Tools Tab: PDF Compressor, Merge PDF, Split PDF, Extract Text, Batch Print, Fullscreen."""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(4)

        # Section 1: PDF Utilities
        btn_comp = QToolButton(); btn_comp.setDefaultAction(self.act_compress)
        btn_comp.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_merge = QToolButton(); btn_merge.setDefaultAction(self.act_merge)
        btn_merge.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        btn_split = QToolButton(); btn_split.setDefaultAction(self.act_split)
        btn_split.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        layout.addWidget(btn_comp)
        layout.addWidget(btn_merge)
        layout.addWidget(btn_split)
        layout.addWidget(create_ribbon_sep())

        # Section 2: Convert & Print
        btn_text = QPushButton("Extract Text")
        btn_text.setIcon(icon_text(16, "#475569"))
        btn_text.clicked.connect(self.extract_text)

        btn_print = QToolButton(); btn_print.setDefaultAction(self.act_print)
        btn_print.setText("Batch Printing")
        btn_print.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        layout.addWidget(btn_text)
        layout.addWidget(btn_print)
        layout.addWidget(create_ribbon_sep())

        # Section 3: View Mode
        btn_fs = QToolButton(); btn_fs.setDefaultAction(self.act_fullscreen)
        btn_fs.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        layout.addWidget(btn_fs)

        layout.addStretch()
        return panel

    def _create_main_menu(self) -> QMenu:
        """Office-style Menu dropdown."""
        menu = QMenu(self)
        menu.addAction(self.act_new)
        menu.addAction(self.act_open)
        menu.addAction(self.act_save)
        menu.addAction(self.act_save_as)
        menu.addSeparator()
        menu.addAction(self.act_print)
        menu.addAction(self.act_compress)
        menu.addAction(self.act_merge)
        menu.addAction(self.act_split)
        menu.addAction(self.act_export_images)
        menu.addAction(self.act_extract_text)
        menu.addSeparator()
        menu.addAction(self.act_close_doc)
        menu.addAction(QAction("Exit", self, triggered=self.close))
        return menu

    def _create_color_menu(self) -> QMenu:
        menu = QMenu(self)
        menu.addAction(QAction(make_color_dot_icon(QColor("#ea580c")), "WPS Orange", self, triggered=lambda: self._set_active_color("#ea580c")))
        menu.addAction(QAction(make_color_dot_icon(QColor("#2563eb")), "Royal Blue", self, triggered=lambda: self._set_active_color("#2563eb")))
        menu.addAction(QAction(make_color_dot_icon(QColor("#dc2626")), "Crimson Red", self, triggered=lambda: self._set_active_color("#dc2626")))
        menu.addAction(QAction(make_color_dot_icon(QColor("#0f172a")), "Charcoal Black", self, triggered=lambda: self._set_active_color("#0f172a")))
        menu.addAction(QAction(make_color_dot_icon(QColor("#16a34a")), "Forest Green", self, triggered=lambda: self._set_active_color("#16a34a")))
        menu.addAction(QAction(make_color_dot_icon(QColor("#eab308")), "Amber Yellow", self, triggered=lambda: self._set_active_color("#eab308")))
        menu.addSeparator()
        menu.addAction(QAction("Custom Color...", self, triggered=self._choose_custom_color))
        return menu

    def _create_wps_statusbar(self):
        """WPS-style Bottom Status Bar: Doc info, Page Jumper, Zoom controls."""
        sb = self.statusBar()

        # Left: Doc info
        self.lbl_status_file = QLabel("Ready")
        sb.addWidget(self.lbl_status_file, 1)

        # Center: Page Jumper (WPS Style: ‹ Page 1 of N ›)
        page_widget = QWidget()
        page_layout = QHBoxLayout(page_widget)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(4)

        btn_p_prev = QPushButton("‹")
        btn_p_prev.setFixedSize(22, 22)
        btn_p_prev.clicked.connect(self.prev_page)

        self.spin_page = QSpinBox()
        self.spin_page.setRange(1, 1)
        self.spin_page.setValue(1)
        self.spin_page.setFixedWidth(52)
        self.spin_page.setFixedHeight(22)
        self.spin_page.valueChanged.connect(lambda v: self.go_to_page(v - 1))

        self.lbl_page_total = QLabel("/ 1")
        self.lbl_page_total.setStyleSheet("color: #64748b; font-size: 11px;")

        btn_p_next = QPushButton("›")
        btn_p_next.setFixedSize(22, 22)
        btn_p_next.clicked.connect(self.next_page)

        page_layout.addWidget(btn_p_prev)
        page_layout.addWidget(self.spin_page)
        page_layout.addWidget(self.lbl_page_total)
        page_layout.addWidget(btn_p_next)
        sb.addPermanentWidget(page_widget)

        # Right: Zoom Slider & Quick Zoom Buttons
        zoom_widget = QWidget()
        zoom_layout = QHBoxLayout(zoom_widget)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        zoom_layout.setSpacing(6)

        btn_z_out = QPushButton("-")
        btn_z_out.setFixedSize(20, 20)
        btn_z_out.clicked.connect(self.canvas.zoom_out)

        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(20, 400)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(100)
        self.zoom_slider.valueChanged.connect(self._on_slider_zoom_changed)

        btn_z_in = QPushButton("+")
        btn_z_in.setFixedSize(20, 20)
        btn_z_in.clicked.connect(self.canvas.zoom_in)

        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setStyleSheet("font-weight: 600; color: #ea580c; font-size: 11px; min-width: 38px;")

        btn_fit_w = QPushButton("Width")
        btn_fit_w.setFixedHeight(22)
        btn_fit_w.clicked.connect(self.canvas.fit_width)

        btn_fit_p = QPushButton("Page")
        btn_fit_p.setFixedHeight(22)
        btn_fit_p.clicked.connect(self.canvas.fit_page)

        zoom_layout.addWidget(btn_z_out)
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(btn_z_in)
        zoom_layout.addWidget(self.lbl_zoom)
        zoom_layout.addWidget(btn_fit_w)
        zoom_layout.addWidget(btn_fit_p)
        sb.addPermanentWidget(zoom_widget)

    def _show_status_message(self, msg: str):
        self.statusBar().showMessage(msg, 3500)

    # ------------------ Navigation & Fullscreen ------------------

    def _on_home_pill_clicked(self):
        """Toggle between Home Dashboard and Document Workspace."""
        if self.central_stack.currentIndex() == 0 and self.doc:
            self.show_workspace()
        else:
            self.show_home_dashboard()

    def toggle_fullscreen(self):
        if not self.is_fullscreen_mode:
            self.is_fullscreen_mode = True
            self.top_titlebar.hide()
            self.nav_row.hide()
            self.ribbon_stack.hide()
            self.statusBar().hide()
            self.left_rail.hide()
            self.sidebar.hide()
            self.showFullScreen()
            self.banner.show()
            self._position_banner()
            self.canvas.fit_page()
            QTimer.singleShot(3500, self.banner.hide)
        else:
            self.is_fullscreen_mode = False
            self.banner.hide()
            self.top_titlebar.show()
            self.nav_row.show()
            self.ribbon_stack.show()
            self.statusBar().show()
            self.left_rail.show()
            if self.btn_rail_thumbs.isChecked():
                self.sidebar.show()
            self.showNormal()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.is_fullscreen_mode and self.banner.isVisible():
            self._position_banner()

    def _position_banner(self):
        w = self.width()
        banner_w = self.banner.sizeHint().width()
        x = (w - banner_w) // 2
        y = 20
        self.banner.move(max(20, x), y)
        self.banner.raise_()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self.is_fullscreen_mode:
            self.toggle_fullscreen()
            return
        elif event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen()
            return
        elif event.matches(QKeySequence.StandardKey.Find):
            self._find_text_dialog()
            return
        super().keyPressEvent(event)

    # ------------------ View & Tools ------------------

    def show_home_dashboard(self):
        self.central_stack.setCurrentIndex(0)
        self.nav_row.hide()
        self.ribbon_stack.hide()
        self.statusBar().hide()
        self.btn_home_pill.setStyleSheet("background-color: #1d4ed8; font-weight: 700; border-radius: 6px;")
        if self.doc:
            self.tab_doc_card.show()
            self.tab_doc_card.setStyleSheet("background-color: #e2e8f0; border: 1px solid #cbd5e1; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px;")
        else:
            self.tab_doc_card.hide()
        self.setWindowTitle("WPS PDF - Studio Pro")

    def show_welcome_screen(self):
        self.show_home_dashboard()

    def show_workspace(self):
        if not self.doc:
            return
        self.central_stack.setCurrentIndex(1)
        self.nav_row.show()
        self.ribbon_stack.show()
        self.statusBar().show()
        self.tab_doc_card.show()
        self.tab_doc_card.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px;")
        self.btn_home_pill.setStyleSheet("")
        base_name = os.path.basename(self.current_file_path) if self.current_file_path else "Untitled.pdf"
        self.setWindowTitle(f"WPS PDF - {base_name}")

    def close_current_document(self):
        if self.doc:
            self.doc.close()
            self.doc = None
        self.current_file_path = None
        self.canvas.page_annotations.clear()
        self.show_home_dashboard()

    def _toggle_sidebar(self):
        is_visible = not self.sidebar.isVisible()
        self.sidebar.setVisible(is_visible)
        self.btn_rail_thumbs.setChecked(is_visible)

    def _switch_tool(self, tool_mode: str):
        self.canvas.set_tool(tool_mode)

    def _set_active_color(self, hex_code: str):
        col = QColor(hex_code)
        self.canvas.pen_color = col
        self.canvas.text_color = col
        if self.canvas.current_tool == ToolMode.HIGHLIGHTER:
            self.canvas.highlighter_color = QColor(col.red(), col.green(), col.blue(), 110)
        for item in self.canvas.scene.selectedItems():
            if isinstance(item, MovableTextItem):
                item.setDefaultTextColor(col)
        self._show_status_message(f"Selected Color: {hex_code}")

    def _choose_custom_color(self):
        col = QColorDialog.getColor(self.canvas.pen_color, self, "Select Color")
        if col.isValid():
            self._set_active_color(col.name())

    def _change_font_size(self, size: int):
        self.canvas.font_size = size
        for item in self.canvas.scene.selectedItems():
            if isinstance(item, MovableTextItem):
                font = item.font()
                font.setPointSize(size)
                item.setFont(font)

    def _on_slider_zoom_changed(self, value: int):
        target_zoom = value / 100.0
        if abs(self.canvas.zoom_factor - target_zoom) > 0.02:
            self.canvas.set_zoom(target_zoom)

    def _on_combo_zoom_selected(self, text: str):
        if text == "Fit Width":
            self.canvas.fit_width()
        elif text == "Fit Page":
            self.canvas.fit_page()
        else:
            try:
                val = int(text.replace("%", ""))
                self.canvas.set_zoom(val / 100.0)
            except ValueError:
                pass

    def _on_zoom_changed(self, zoom: float):
        pct = int(zoom * 100)
        self.lbl_zoom.setText(f"{pct}%")
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(max(20, min(pct, 400)))
        self.zoom_slider.blockSignals(False)

        # Update combo text if present
        self.combo_zoom.blockSignals(True)
        self.combo_zoom.setCurrentText(f"{pct}%")
        self.combo_zoom.blockSignals(False)

    # ------------------ Document Operations ------------------

    def new_blank_document(self):
        if self.doc:
            self.doc.close()
        self.doc = pymupdf.open()
        self.doc.new_page(width=595, height=842)
        self.current_file_path = None
        self.current_page_idx = 0
        self.canvas.page_annotations.clear()
        self.show_workspace()
        self._refresh_ui()
        self.lbl_doc_title.setText("Untitled.pdf")
        self._show_status_message("Created new blank PDF.")

    def open_pdf_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "", "PDF Files (*.pdf)")
        if path:
            self.load_pdf(path)

    def load_pdf(self, path: str):
        try:
            if self.doc:
                self.doc.close()
            self.doc = pymupdf.open(path)
            self.current_file_path = path
            self.current_page_idx = 0
            self.canvas.page_annotations.clear()
            RecentFilesManager.add_file(path)
            self.home_dashboard.refresh_recent_files()
            self.show_workspace()
            self._refresh_ui()
            base_name = os.path.basename(path)
            self.setWindowTitle(f"WPS PDF - {base_name}")
            self.lbl_doc_title.setText(base_name)
            self._show_status_message(f"Opened: {base_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error opening PDF", f"Failed to open PDF file:\n{str(e)}")

    def _refresh_ui(self):
        if not self.doc or len(self.doc) == 0:
            return
        total = len(self.doc)
        self.spin_page.blockSignals(True)
        self.spin_page.setRange(1, total)
        self.spin_page.setValue(self.current_page_idx + 1)
        self.spin_page.blockSignals(False)
        self.lbl_page_total.setText(f"/ {total}")

        fname = os.path.basename(self.current_file_path) if self.current_file_path else "Untitled"
        page = self.doc[self.current_page_idx]
        rect = page.rect
        self.lbl_status_file.setText(f"{fname} • Page {self.current_page_idx + 1} of {total} • ({int(rect.width)} × {int(rect.height)} pt)")

        self.sidebar.load_thumbnails(self.doc, self.current_page_idx)
        self._render_current_page()

    def _render_current_page(self):
        if self.doc and 0 <= self.current_page_idx < len(self.doc):
            page = self.doc[self.current_page_idx]
            self.canvas.render_page(page, self.current_page_idx)

    def go_to_page(self, index: int):
        if not self.doc or index < 0 or index >= len(self.doc):
            return
        self.current_page_idx = index
        self.spin_page.blockSignals(True)
        self.spin_page.setValue(index + 1)
        self.spin_page.blockSignals(False)
        self.sidebar.set_current_page(index)
        self._render_current_page()

        total = len(self.doc)
        fname = os.path.basename(self.current_file_path) if self.current_file_path else "Untitled"
        page = self.doc[index]
        self.lbl_status_file.setText(f"{fname} • Page {index + 1} of {total} • ({int(page.rect.width)} × {int(page.rect.height)} pt)")

    def prev_page(self):
        if self.current_page_idx > 0:
            self.go_to_page(self.current_page_idx - 1)

    def next_page(self):
        if self.doc and self.current_page_idx < len(self.doc) - 1:
            self.go_to_page(self.current_page_idx + 1)

    def rotate_clockwise(self):
        self.rotate_page(self.current_page_idx, 90)

    def rotate_anticlockwise(self):
        self.rotate_page(self.current_page_idx, -90)

    def rotate_180(self):
        self.rotate_page(self.current_page_idx, 180)

    def rotate_page(self, page_idx: int, deg: int):
        if not self.doc or page_idx >= len(self.doc):
            return
        page = self.doc[page_idx]
        page.set_rotation((page.rotation + deg) % 360)
        self.sidebar.load_thumbnails(self.doc, self.current_page_idx)
        self._render_current_page()
        self._show_status_message(f"Rotated page {page_idx + 1}")

    def delete_page(self, page_idx: int):
        if not self.doc or len(self.doc) <= 1:
            QMessageBox.warning(self, "Cannot Delete", "The document must contain at least one page.")
            return
        self.doc.delete_page(page_idx)
        if page_idx in self.canvas.page_annotations:
            del self.canvas.page_annotations[page_idx]
        self.current_page_idx = min(self.current_page_idx, len(self.doc) - 1)
        self._refresh_ui()
        self._show_status_message(f"Deleted page {page_idx + 1}")

    def reorder_pages(self, from_idx: int, to_idx: int):
        if not self.doc or from_idx == to_idx:
            return
        self.doc.move_page(from_idx, to_idx)
        self.current_page_idx = to_idx
        self._refresh_ui()
        self._show_status_message(f"Moved page {from_idx + 1} to {to_idx + 1}")

    def add_blank_page(self):
        if not self.doc:
            return
        insert_at = self.current_page_idx + 1
        self.doc.new_page(insert_at, width=595, height=842)
        self.current_page_idx = insert_at
        self._refresh_ui()
        self._show_status_message("Added blank page.")

    def extract_current_page(self):
        if not self.doc or len(self.doc) == 0:
            return
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Extract Page to Standalone PDF", f"page_{self.current_page_idx + 1}.pdf", "PDF Files (*.pdf)"
        )
        if save_path:
            try:
                new_doc = pymupdf.open()
                new_doc.insert_pdf(self.doc, from_page=self.current_page_idx, to_page=self.current_page_idx)
                new_doc.save(save_path)
                new_doc.close()
                QMessageBox.information(self, "Page Extracted", f"Page {self.current_page_idx + 1} extracted successfully:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Extraction Error", f"Failed to extract page:\n{str(e)}")

    def compress_pdf(self):
        """WPS-style PDF Compressor: Compresses PDF streams, cleans unused objects, reports savings."""
        if not self.doc:
            return
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Compressed PDF",
            (self.current_file_path or "compressed_document.pdf").replace(".pdf", "_compressed.pdf"),
            "PDF Files (*.pdf)"
        )
        if save_path:
            try:
                orig_size = os.path.getsize(self.current_file_path) if self.current_file_path and os.path.exists(self.current_file_path) else 0
                self.doc.save(save_path, garbage=4, deflate=True, clean=True)
                new_size = os.path.getsize(save_path)

                if orig_size > 0:
                    saved_kb = (orig_size - new_size) / 1024
                    saved_pct = ((orig_size - new_size) / orig_size) * 100
                    QMessageBox.information(
                        self, "PDF Compression",
                        f"PDF Compressed Successfully!\n\n"
                        f"Original Size: {orig_size / 1024:.1f} KB\n"
                        f"Compressed Size: {new_size / 1024:.1f} KB\n"
                        f"Space Saved: {max(0, saved_kb):.1f} KB ({max(0, saved_pct):.1f}%)"
                    )
                else:
                    QMessageBox.information(self, "PDF Compression", f"Saved compressed PDF:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Compression Error", f"Failed to compress PDF:\n{str(e)}")

    def extract_text(self):
        """Extracts text from all pages into a clean .txt file."""
        if not self.doc:
            return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Extracted Text", "extracted_text.txt", "Text Files (*.txt)")
        if save_path:
            try:
                pages_text = []
                for idx, page in enumerate(self.doc):
                    pages_text.append(f"--- PAGE {idx + 1} ---\n" + page.get_text())
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write("\n\n".join(pages_text))
                QMessageBox.information(self, "Text Extracted", f"Successfully extracted text to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error Extracting Text", str(e))

    def print_document(self):
        """Invoke Windows system print dialog for the current document."""
        if not self.current_file_path or not os.path.exists(self.current_file_path):
            QMessageBox.information(self, "Print Notice", "Please save the document before printing.")
            return
        try:
            os.startfile(self.current_file_path, "print")
        except Exception as e:
            QMessageBox.information(self, "Print Notice", f"Windows printing initiated. ({str(e)})")

    def _find_text_dialog(self):
        """Quick text search across document pages."""
        if not self.doc:
            return
        query, ok = QInputDialog.getText(self, "Find in Document", "Enter text to search:")
        if ok and query.strip():
            query = query.strip().lower()
            matching_pages = []
            for idx, page in enumerate(self.doc):
                if query in page.get_text().lower():
                    matching_pages.append(idx)
            if matching_pages:
                # Go to first match
                first_match = matching_pages[0]
                self.go_to_page(first_match)
                self._show_status_message(f"Found '{query}' on {len(matching_pages)} page(s). First match: Page {first_match + 1}")
            else:
                QMessageBox.information(self, "Find", f"No occurrences of '{query}' found.")

    # ------------------ Save & Export ------------------

    def save_document(self):
        if not self.current_file_path:
            self.save_document_as()
            return
        self._perform_save(self.current_file_path)

    def save_document_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF As", self.current_file_path or "edited_document.pdf", "PDF Files (*.pdf)"
        )
        if path:
            self._perform_save(path)
            self.current_file_path = path
            base_name = os.path.basename(path)
            self.setWindowTitle(f"WPS PDF - {base_name}")
            self.lbl_doc_title.setText(base_name)

    def _perform_save(self, path: str):
        try:
            self.canvas.save_all_to_doc(self.doc)

            temp_path = path + ".tmp.pdf"
            self.doc.save(temp_path, garbage=3, deflate=True)
            self.doc.close()

            if os.path.exists(path):
                os.remove(path)
            os.replace(temp_path, path)

            self.doc = pymupdf.open(path)
            self._render_current_page()
            RecentFilesManager.add_file(path)
            self.home_dashboard.refresh_recent_files()

            QMessageBox.information(self, "Saved", f"Document saved successfully!\n{path}")
            self._show_status_message("Saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save document:\n{str(e)}")

    def export_as_images(self):
        if not self.doc:
            return
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Export Images")
        if not folder:
            return
        try:
            base = os.path.splitext(os.path.basename(self.current_file_path or "page"))[0]
            for idx, page in enumerate(self.doc):
                pix = page.get_pixmap(dpi=200)
                pix.save(os.path.join(folder, f"{base}_page_{idx + 1}.png"))
            QMessageBox.information(self, "Success", f"Exported {len(self.doc)} pages to:\n{folder}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export images:\n{str(e)}")

    # ------------------ Dialogs ------------------

    def _insert_image_dialog(self):
        img_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image to Insert", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if img_path:
            pix = QPixmap(img_path)
            if not pix.isNull():
                if pix.width() > 400 or pix.height() > 400:
                    pix = pix.scaled(350, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.canvas.add_image_item(pix)
                self.act_select.setChecked(True)

    def _insert_signature_dialog(self):
        dlg = SignatureDialog(self)
        if dlg.exec():
            img = dlg.signature_image
            if img:
                pix = QPixmap.fromImage(img)
                if pix.width() > 300:
                    pix = pix.scaledToWidth(250, Qt.TransformationMode.SmoothTransformation)
                self.canvas.add_image_item(pix)
                self.act_select.setChecked(True)

    def _open_merge_dialog(self):
        dlg = MergeDialog(self)
        dlg.exec()

    def _open_split_dialog(self):
        if not self.current_file_path or not os.path.exists(self.current_file_path):
            QMessageBox.information(self, "Notice", "Please open or save a PDF on disk first before splitting.")
            return
        dlg = SplitDialog(self.current_file_path, len(self.doc), self)
        dlg.exec()

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
                self.load_pdf(file_path)
                event.acceptProposedAction()
                return


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("WPS PDF Studio Pro")
    app.setOrganizationName("WPSStyle")

    # Global modern typography
    modern_font = QFont()
    modern_font.setFamilies(["Segoe UI Variable Text", "Segoe UI", "Inter", "sans-serif"])
    modern_font.setPointSize(9)
    modern_font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(modern_font)

    initial_pdf = sys.argv[1] if len(sys.argv) > 1 else None
    window = PDFEditorApp(initial_pdf)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
