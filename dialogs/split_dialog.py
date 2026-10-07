"""
split_dialog.py - Dialog to split or extract pages from a PDF document
"""

import os
import pymupdf
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QRadioButton, QLineEdit, QFileDialog, QMessageBox, QButtonGroup, QGroupBox
)


class SplitDialog(QDialog):
    def __init__(self, current_doc_path: str = None, total_pages: int = 0, parent=None):
        super().__init__(parent)
        self.doc_path = current_doc_path
        self.total_pages = total_pages
        self.setWindowTitle("Split & Extract Pages / تقسيم واستخراج الصفحات")
        self.setFixedSize(480, 320)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        lbl_info = QLabel(f"Document has <b>{self.total_pages}</b> pages.")
        lbl_info.setStyleSheet("font-size: 13px;")
        layout.addWidget(lbl_info)

        # Mode Selection
        grp = QGroupBox("Split Mode")
        grp_layout = QVBoxLayout(grp)

        self.radio_range = QRadioButton("Extract specific pages (e.g. 1-3, 5, 8)")
        self.radio_range.setChecked(True)
        grp_layout.addWidget(self.radio_range)

        self.txt_range = QLineEdit()
        self.txt_range.setPlaceholderText(f"e.g. 1-{min(self.total_pages, 3)}, {self.total_pages}")
        grp_layout.addWidget(self.txt_range)

        grp_layout.addSpacing(6)
        self.radio_all = QRadioButton("Split every page into a separate PDF file")
        grp_layout.addWidget(self.radio_all)

        layout.addWidget(grp)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_layout.addStretch()

        self.btn_split = QPushButton("Split / تقسيم")
        self.btn_split.setObjectName("primaryBtn")
        self.btn_split.clicked.connect(self._execute_split)
        btn_layout.addWidget(self.btn_split)

        layout.addLayout(btn_layout)

    def _parse_ranges(self, text: str):
        pages = set()
        parts = [p.strip() for p in text.split(",") if p.strip()]
        for part in parts:
            if "-" in part:
                sub = part.split("-")
                start = int(sub[0])
                end = int(sub[1])
                for p in range(start, end + 1):
                    pages.add(p)
            else:
                pages.add(int(part))
        return sorted([p - 1 for p in pages if 1 <= p <= self.total_pages])

    def _execute_split(self):
        if not self.doc_path or not os.path.exists(self.doc_path):
            QMessageBox.warning(self, "Error", "No valid document to split.")
            return

        try:
            doc = pymupdf.open(self.doc_path)

            if self.radio_range.isChecked():
                raw = self.txt_range.text().strip()
                if not raw:
                    QMessageBox.warning(self, "Input Error", "Please enter page numbers or ranges to extract.")
                    return

                page_indices = self._parse_ranges(raw)
                if not page_indices:
                    QMessageBox.warning(self, "Input Error", "No valid page numbers found in the specified range.")
                    return

                save_path, _ = QFileDialog.getSaveFileName(
                    self, "Save Extracted Pages As", "extracted_pages.pdf", "PDF Files (*.pdf)"
                )
                if not save_path:
                    return

                new_doc = pymupdf.open()
                for idx in page_indices:
                    new_doc.insert_pdf(doc, from_page=idx, to_page=idx)
                new_doc.save(save_path)
                new_doc.close()

                QMessageBox.information(
                    self, "Success", f"Extracted {len(page_indices)} pages successfully!\nSaved to: {save_path}"
                )
                self.accept()

            else:
                # Split all pages
                folder = QFileDialog.getExistingDirectory(self, "Select Folder to Save Split Pages")
                if not folder:
                    return

                base_name = os.path.splitext(os.path.basename(self.doc_path))[0]
                for idx in range(len(doc)):
                    p_doc = pymupdf.open()
                    p_doc.insert_pdf(doc, from_page=idx, to_page=idx)
                    out_name = os.path.join(folder, f"{base_name}_page_{idx + 1}.pdf")
                    p_doc.save(out_name)
                    p_doc.close()

                QMessageBox.information(
                    self, "Success", f"Split {len(doc)} pages into separate files successfully in:\n{folder}"
                )
                self.accept()

            doc.close()

        except Exception as e:
            QMessageBox.critical(self, "Split Error", f"Failed to split PDF:\n{str(e)}")
