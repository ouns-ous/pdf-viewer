# WPS PDF Studio Pro

A modern, fast, and feature-rich Windows PDF Reader & Editor inspired by **WPS Office PDF** and **Microsoft Edge PDF**. Built with Python, PyQt6, and PyMuPDF.

---

## Highlights

- **WPS Ribbon Interface**: Clean 48px horizontal action bar with segmented tabs (`Home`, `Edit`, `Comment`, `Page`, `Tools`).
- **High-DPI Vector Canvas**: Crystal-clear vector rendering with dynamic high-resolution rasterization on zoom.
- **Pure Vector SVG Icons**: Feather & Lucide vector paths with built-in LRU caching for 60 FPS performance and zero emojis.
- **WPS Home Hub**: Start screen with quick action cards, recent files manager, search, and drag-and-drop zone.
- **Modern Windows Typography**: Designed with `Segoe UI Variable Text` / `Segoe UI` and `Inter` sans-serif typography.
- **PDF Power Tools**:
  - **Edit & Annotate**: Freehand drawing, highlighter, text notes, geometric shapes, and image insertion.
  - **Digital Signatures**: Dedicated signature pad with smoothing and transparency export.
  - **Page Organization**: Reorder, rotate (90°, 180°, 270°), extract, insert blank pages, and delete.
  - **Batch Utilities**: Merge PDF, Split PDF, PDF Compressor, and PDF to PNG export.
  - **Fullscreen View**: Immersive distraction-free viewing with `F11` and quick `Esc` overlay.

---

## Installation & Running

### 1. Run from Source
```bash
# Clone the repository
git clone https://github.com/ouns-ous/pdf-viewer.git
cd pdf-viewer

# Install dependencies
pip install -r requirements.txt

# Launch application
python app.py
```

### 2. Build Windows Executable (.exe)
```bash
build_exe.bat
```
This builds standalone binaries using PyInstaller and packages the Windows installer.

---

## Project Architecture

```text
├── app.py                  # Main application window, ribbon tabs & document orchestrator
├── pdf_canvas.py           # High-DPI graphics view with vector annotations & zoom
├── home_dashboard.py       # WPS Office style start dashboard with recent files
├── sidebar_thumbnails.py   # Non-blocking page thumbnails sidebar
├── icons.py                # Pure SVG vector icon engine with LRU caching
├── styles.py               # Soft, modern WPS styling theme
├── setup_wizard.py         # Native Windows Setup Wizard installer
├── dialogs/
│   ├── merge_dialog.py     # PDF Merge utility with drag reordering
│   ├── split_dialog.py     # Range & individual page split utility
│   └── signature_dialog.py # Interactive signature capture pad
└── requirements.txt        # Project dependencies
```

---

## License

MIT License. Designed and developed by [ouns-ous](https://github.com/ouns-ous).
