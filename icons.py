"""
icons.py - Professional SVG vector icon generator for WPS PDF clone.
Uses standard Lucide vector paths rendered via QtSvg for pixel-perfect clarity.
Zero emojis, 100% clean vector icons.
"""

from functools import lru_cache
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtSvg import QSvgRenderer


@lru_cache(maxsize=128)
def _svg_icon(path_data: str, color: str = "#475569", size: int = 20, stroke_width: float = 2.0) -> QIcon:
    """Renders a standard 24x24 SVG path into a crisp QIcon with LRU caching."""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" 
             fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
             {path_data}
             </svg>"""
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return QIcon(pix)


@lru_cache(maxsize=16)
def icon_wps_logo(size: int = 24) -> QIcon:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24">
             <rect width="24" height="24" rx="5" fill="#ea580c"/>
             <path d="M5.5 8L9 16L12 10.5L15 16L18.5 8" fill="none" stroke="#ffffff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
             </svg>"""
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    renderer.render(p)
    p.end()
    return QIcon(pix)


# Navigation & Cursor Tools
def icon_hand(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"/>
               <path d="M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2"/>
               <path d="M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8"/>
               <path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_select(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<path d="m3 3 7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/>
               <path d="m13 13 6 6"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


# Content & Editing Tools
def icon_text(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<polyline points="4 7 4 4 20 4 20 7"/>
               <line x1="9" x2="15" y1="20" y2="20"/>
               <line x1="12" x2="12" y1="4" y2="20"/>"""
    return _svg_icon(paths, color, size, stroke_width=2.0)


def icon_image(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>
               <circle cx="9" cy="9" r="2"/>
               <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_highlight(size: int = 20, color: str = "#ea580c") -> QIcon:
    paths = """<path d="m9 11-6 6v3h3l6-6"/>
               <path d="m22 12-4.6 4.6a2 2 0 0 1-2.8 0l-5.2-5.2a2 2 0 0 1 0-2.8L14 4"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_pen(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<path d="M12 19l7-7 3 3-7 7-3-3z"/>
               <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18"/>
               <path d="M2 2l7.586 7.586"/>
               <circle cx="11" cy="11" r="2"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_eraser(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<path d="m7 21-4.3-4.3c-1-1-1-2.5 0-3.4l9.6-9.6c1-1 2.5-1 3.4 0l5.6 5.6c1 1 1 2.5 0 3.4L13 21"/>
               <path d="M22 21H7"/>
               <path d="m5 11 9 9"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_rect(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<rect width="18" height="18" x="3" y="3" rx="2"/>"""
    return _svg_icon(paths, color, size, stroke_width=2.0)


def icon_sign(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<path d="M20 19.5c-3-1-5.5-2.5-8-2.5s-4 1.5-6 1.5-3-1-3-2 1.5-2.5 3-2.5 3 2 4.5 2 2.5-2 4-2c2 0 3 2 5.5 3.5"/>
               <path d="m14 5 3-3 5 5-3 3z"/>
               <path d="m14 5-9 9v4h4l9-9"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


# Page Operations
def icon_rotate_cw(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/>
               <path d="M21 3v5h-5"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_rotate_ccw(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
               <path d="M3 3v5h5"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_delete(size: int = 20, color: str = "#dc2626") -> QIcon:
    paths = """<path d="M3 6h18"/>
               <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
               <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
               <line x1="10" x2="10" y1="11" y2="17"/>
               <line x1="14" x2="14" y1="11" y2="17"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_add_page(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
               <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
               <path d="M9 15h6"/>
               <path d="M12 12v6"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


# File & Utilities
def icon_merge(size: int = 20, color: str = "#7c3aed") -> QIcon:
    paths = """<circle cx="18" cy="18" r="3"/>
               <circle cx="6" cy="6" r="3"/>
               <path d="M6 21V9a9 9 0 0 0 9 9"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_split(size: int = 20, color: str = "#ea580c") -> QIcon:
    paths = """<circle cx="6" cy="6" r="3"/>
               <path d="M6 9v12"/>
               <path d="M20 4 8.12 15.88"/>
               <circle cx="6" cy="18" r="3"/>
               <path d="M14.8 14.8 20 20"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_compress(size: int = 20, color: str = "#0d9488") -> QIcon:
    paths = """<path d="m4 14 6-6"/>
               <path d="M4 8h6v6"/>
               <path d="m20 10-6 6"/>
               <path d="M20 16h-6v-6"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_print(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<polyline points="6 9 6 2 18 2 18 9"/>
               <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
               <rect width="12" height="8" x="6" y="14"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_save_disk(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<path d="M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/>
               <path d="M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7"/>
               <path d="M7 3v4a1 1 0 0 0 1 1h7"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_open_folder(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<path d="m6 14 1.45-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.55 6a2 2 0 0 1-1.94 1.5H4a2 2 0 0 1-2-2V5c0-1.1.9-2 2-2h3.93a2 2 0 0 1 1.66.9l.82 1.2a2 2 0 0 0 1.66.9H18a2 2 0 0 1 2 2v2"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_undo(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<path d="M3 7v6h6"/>
               <path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_redo(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<path d="M21 7v6h-6"/>
               <path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3l3 2.7"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


# Zoom & View
def icon_fit_width(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<path d="M3 4v16"/>
               <path d="M21 4v16"/>
               <path d="M7 12h10"/>
               <path d="m14 9 3 3-3 3"/>
               <path d="m10 9-3 3 3 3"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_fit_page(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<rect width="14" height="18" x="5" y="3" rx="2"/>
               <path d="m9 9-2 2 2 2"/>
               <path d="m15 9 2 2-2 2"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_zoom_in(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<circle cx="11" cy="11" r="8"/>
               <line x1="21" x2="16.65" y1="21" y2="16.65"/>
               <line x1="11" x2="11" y1="8" y2="14"/>
               <line x1="8" x2="14" y1="11" y2="11"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_zoom_out(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<circle cx="11" cy="11" r="8"/>
               <line x1="21" x2="16.65" y1="21" y2="16.65"/>
               <line x1="8" x2="14" y1="11" y2="11"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_zoom_actual(size: int = 20, color: str = "#475569") -> QIcon:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24">
             <rect width="20" height="16" x="2" y="4" rx="3" fill="none" stroke="{color}" stroke-width="1.8"/>
             <text x="12" y="15" text-anchor="middle" font-family="Segoe UI, sans-serif" font-weight="bold" font-size="9" fill="{color}">1:1</text>
             </svg>"""
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    renderer.render(p)
    p.end()
    return QIcon(pix)


def icon_fullscreen(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<path d="M8 3H5a2 2 0 0 0-2 2v3"/>
               <path d="M21 8V5a2 2 0 0 0-2-2h-3"/>
               <path d="M3 16v3a2 2 0 0 0 2 2h3"/>
               <path d="M16 21h3a2 2 0 0 0 2-2v-3"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_export_images(size: int = 20, color: str = "#16a34a") -> QIcon:
    paths = """<rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>
               <circle cx="9" cy="9" r="2"/>
               <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>
               <path d="m14 19 4 0"/>
               <path d="m18 15 4 4-4 4"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_sidebar(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<rect width="18" height="18" x="3" y="3" rx="2"/>
               <path d="M9 3v18"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_search(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<circle cx="11" cy="11" r="8"/>
               <line x1="21" x2="16.65" y1="21" y2="16.65"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


# Home Dashboard Icons
def icon_recent_clock(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<circle cx="12" cy="12" r="10"/>
               <polyline points="12 6 12 12 16 14"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_document_pdf(size: int = 20, color: str = "#ea580c") -> QIcon:
    paths = """<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
               <polyline points="14 2 14 8 20 8"/>
               <path d="M9 13h2a1.5 1.5 0 0 0 0-3H9v6"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_cloud_upload(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/>
               <path d="M12 12v9"/>
               <path d="m16 16-4-4-4 4"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)


def icon_tools_gear(size: int = 20, color: str = "#475569") -> QIcon:
    paths = """<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
               <circle cx="12" cy="12" r="3"/>"""
    return _svg_icon(paths, color, size, stroke_width=1.8)
