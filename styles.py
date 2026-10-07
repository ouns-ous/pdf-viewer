"""
styles.py - WPS PDF inspired Ribbon UI & Modern Home Dashboard styling
Soft, clean, modern styling with subtle border-radius and signature WPS colors.
Strictly NO emojis.
"""

WPS_THEME = """
/* Global Application Style */
* {
    font-family: 'Segoe UI Variable Text', 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif;
}

QMainWindow, QDialog {
    background-color: #f8fafc;
    color: #1e293b;
    font-size: 12px;
}

QWidget {
    color: #334155;
    font-size: 12px;
}

/* ==========================================================
   WPS Top Title Bar (Document Tabs & Quick Access)
   ========================================================== */
QFrame#wpsTitleBar {
    background-color: #e2e8f0;
    border-bottom: 1px solid #cbd5e1;
    padding: 0px 8px;
    min-height: 38px;
    max-height: 38px;
}

/* Blue Home Tab Pill */
QPushButton#wpsHomePill {
    background-color: #2563eb;
    color: #ffffff;
    font-weight: 600;
    font-size: 12px;
    border: none;
    border-radius: 6px;
    padding: 4px 16px;
}

QPushButton#wpsHomePill:hover {
    background-color: #1d4ed8;
}

QPushButton#wpsHomePill:pressed {
    background-color: #1e40af;
}

/* Document Tab (White card style) */
QFrame#wpsDocTab {
    background-color: #ffffff;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border: 1px solid #cbd5e1;
    border-bottom: none;
    padding: 2px 12px;
    min-width: 150px;
    max-width: 280px;
}

QLabel#wpsDocTabTitle {
    color: #1e293b;
    font-size: 12px;
    font-weight: 600;
}

QToolButton#wpsDocTabClose {
    background: transparent;
    border: none;
    color: #94a3b8;
    font-size: 13px;
    font-weight: bold;
    border-radius: 10px;
    padding: 1px 4px;
    min-width: 18px;
    min-height: 18px;
}

QToolButton#wpsDocTabClose:hover {
    background-color: #fee2e2;
    color: #ef4444;
}

/* New Tab / Plus Button */
QToolButton#wpsNewTabBtn {
    background: transparent;
    border: none;
    color: #64748b;
    font-size: 16px;
    font-weight: bold;
    border-radius: 6px;
    padding: 2px 8px;
}

QToolButton#wpsNewTabBtn:hover {
    background-color: #cbd5e1;
    color: #0f172a;
}

/* ==========================================================
   WPS Menu & Ribbon Tab Bar
   ========================================================== */
QFrame#wpsNavRow {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 2px 10px;
    min-height: 36px;
    max-height: 36px;
}

/* Menu Dropdown Button */
QPushButton#wpsMenuBtn {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton#wpsMenuBtn:hover {
    background-color: #f8fafc;
    border-color: #94a3b8;
    color: #0f172a;
}

QPushButton#wpsMenuBtn::menu-indicator {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    padding-right: 2px;
}

/* Quick Access Icons */
QToolButton#wpsQuickBtn {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 4px;
}

QToolButton#wpsQuickBtn:hover {
    background-color: #f1f5f9;
    border-color: #e2e8f0;
}

/* Ribbon Tab Buttons (Home, Edit, Comment, Page, Tools) */
QPushButton#wpsRibbonTab {
    background: transparent;
    border: none;
    color: #475569;
    font-size: 12px;
    font-weight: 500;
    padding: 7px 16px;
    border-bottom: 2.5px solid transparent;
}

QPushButton#wpsRibbonTab:hover {
    color: #ea580c;
    background-color: #fff7ed;
}

QPushButton#wpsRibbonTab:checked {
    color: #ea580c;
    font-weight: 700;
    border-bottom: 2.5px solid #ea580c;
    background-color: transparent;
}

/* ==========================================================
   WPS Ribbon Body (Tool Panel)
   ========================================================== */
QFrame#wpsRibbonBody {
    background-color: #ffffff;
    border-bottom: 1px solid #cbd5e1;
    min-height: 48px;
    max-height: 48px;
    padding: 0px 8px;
}

/* Ribbon Vertical Separators */
QFrame#ribbonSep {
    color: #e2e8f0;
    margin: 8px 4px;
}

/* Ribbon Tool Buttons */
QToolButton {
    background-color: transparent;
    color: #334155;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 500;
    min-height: 28px;
}

QToolButton:hover {
    background-color: #f1f5f9;
    border-color: #e2e8f0;
    color: #0f172a;
}

QToolButton:checked {
    background-color: #fff7ed;
    color: #ea580c;
    border: 1px solid #fdba74;
    font-weight: 600;
}

QToolButton:pressed {
    background-color: #ffedd5;
}

/* Standard Buttons */
QPushButton {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 500;
    min-height: 28px;
}

QPushButton:hover {
    background-color: #f8fafc;
    border-color: #94a3b8;
    color: #0f172a;
}

QPushButton:pressed {
    background-color: #f1f5f9;
}

QPushButton#primaryBtn {
    background-color: #ea580c;
    color: #ffffff;
    border: 1px solid #c2410c;
    border-radius: 6px;
    font-weight: 600;
    padding: 6px 16px;
}

QPushButton#primaryBtn:hover {
    background-color: #f97316;
}

QPushButton#primaryBtn:pressed {
    background-color: #c2410c;
}

/* Inputs, Spinners & Combos */
QComboBox, QSpinBox, QLineEdit {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 11px;
}

QComboBox:hover, QSpinBox:hover, QLineEdit:hover {
    border-color: #94a3b8;
}

QComboBox:focus, QSpinBox:focus, QLineEdit:focus {
    border-color: #ea580c;
}

QComboBox::drop-down {
    border: none;
    width: 16px;
}

/* ==========================================================
   WPS Modern Home Dashboard
   ========================================================== */
QWidget#homeDashboard {
    background-color: #f8fafc;
}

QFrame#homeNavRail {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
    min-width: 210px;
    max-width: 210px;
    padding: 20px 12px;
}

QPushButton#homeNavBtn {
    background-color: transparent;
    color: #475569;
    font-size: 13px;
    font-weight: 500;
    text-align: left;
    padding: 10px 14px;
    border: none;
    border-radius: 8px;
}

QPushButton#homeNavBtn:hover {
    background-color: #f1f5f9;
    color: #0f172a;
}

QPushButton#homeNavBtn:checked {
    background-color: #fff7ed;
    color: #ea580c;
    font-weight: 600;
}

/* Quick Action Cards */
QFrame#quickActionCard {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
}

QFrame#quickActionCard:hover {
    border-color: #ea580c;
    background-color: #fffcf9;
}

QLabel#cardTitle {
    font-size: 13px;
    font-weight: 600;
    color: #0f172a;
}

QLabel#cardDesc {
    font-size: 11px;
    color: #64748b;
}

/* Recent Documents List */
QListWidget#recentFilesList {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget#recentFilesList::item {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 6px;
    color: #1e293b;
}

QListWidget#recentFilesList::item:hover {
    background-color: #f8fafc;
    border-color: #cbd5e1;
}

QListWidget#recentFilesList::item:selected {
    background-color: #fff7ed;
    border: 1px solid #fed7aa;
    color: #c2410c;
}

/* Modern Drag & Drop Zone */
QFrame#modernDropZone {
    background-color: #ffffff;
    border: 2px dashed #cbd5e1;
    border-radius: 12px;
    padding: 30px;
}

QFrame#modernDropZone:hover {
    background-color: #fff7ed;
    border-color: #ea580c;
}

/* ==========================================================
   Left Navigation Rail & Sidebar (In Workspace)
   ========================================================== */
QFrame#wpsLeftRail {
    background-color: #f8fafc;
    border-right: 1px solid #e2e8f0;
    min-width: 44px;
    max-width: 44px;
    padding-top: 8px;
}

QToolButton#wpsRailBtn {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px;
    margin-bottom: 6px;
}

QToolButton#wpsRailBtn:hover {
    background-color: #f1f5f9;
    border-color: #cbd5e1;
}

QToolButton#wpsRailBtn:checked {
    background-color: #fff7ed;
    border-color: #fed7aa;
}

#sidebarWidget {
    background-color: #f8fafc;
    border-right: 1px solid #cbd5e1;
}

QListWidget {
    background-color: #f8fafc;
    border: none;
    outline: none;
    padding: 6px;
}

QListWidget::item {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 4px;
    margin: 4px 6px;
    color: #475569;
}

QListWidget::item:hover {
    background-color: #f1f5f9;
    border-color: #cbd5e1;
}

QListWidget::item:selected {
    background-color: #fff7ed;
    border: 2px solid #ea580c;
    color: #c2410c;
    font-weight: 600;
}

/* ==========================================================
   Document Viewport & Canvas
   ========================================================== */
QGraphicsView {
    background-color: #3e4756; /* WPS Dark Slate Canvas */
    border: none;
}

/* Clean Slim Scrollbars */
QScrollBar:vertical {
    background: #3e4756;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #64748b;
    min-height: 28px;
    border-radius: 5px;
    margin: 1px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar:horizontal {
    background: #3e4756;
    height: 10px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #64748b;
    min-width: 28px;
    border-radius: 5px;
    margin: 1px;
}

QScrollBar::handle:horizontal:hover {
    background: #94a3b8;
}

QScrollBar::add-line, QScrollBar::sub-line {
    width: 0;
    height: 0;
}

/* ==========================================================
   Bottom Status Bar
   ========================================================== */
QStatusBar {
    background-color: #ffffff;
    color: #64748b;
    border-top: 1px solid #e2e8f0;
    padding: 2px 10px;
    font-size: 11px;
}

/* Floating Fullscreen Banner */
QFrame#edgeFullscreenBanner {
    background-color: rgba(15, 23, 42, 0.94);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 20px;
    padding: 6px 20px;
}

QFrame#edgeFullscreenBanner QLabel {
    color: #f8fafc;
    font-size: 12px;
    font-weight: 500;
}

/* Splitter */
QSplitter::handle {
    background-color: #cbd5e1;
    width: 2px;
}

QSplitter::handle:hover {
    background-color: #ea580c;
}

/* Clean Menus */
QMenu {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 6px 22px 6px 12px;
    border-radius: 5px;
    font-size: 12px;
}

QMenu::item:selected {
    background-color: #fff7ed;
    color: #ea580c;
    font-weight: 500;
}

QMenu::separator {
    height: 1px;
    background: #f1f5f9;
    margin: 4px 6px;
}
"""
