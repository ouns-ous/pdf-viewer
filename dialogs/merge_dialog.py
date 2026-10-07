"""
merge_dialog.py - Dialog to merge multiple PDF files
"""

import os
import pymupdf
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt


class MergeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Merge PDF Files")
        self.resize(540, 420)
        self.files = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("Add and arrange PDF files to merge into a single document:")
        header.setStyleSheet("font-weight: 600; font-size: 13px; color: #1e293b;")
        layout.addWidget(header)

        # File List
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.list_widget)

        # Action Buttons (Clean text, no emojis)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_add = QPushButton("Add Files")
        btn_add.clicked.connect(self._add_files)
        btn_remove = QPushButton("Remove")
        btn_remove.clicked.connect(self._remove_selected)
        btn_up = QPushButton("Move Up")
        btn_up.clicked.connect(self._move_up)
        btn_down = QPushButton("Move Down")
        btn_down.clicked.connect(self._move_down)
        btn_clear = QPushButton("Clear All")
        btn_clear.clicked.connect(self._clear_all)

        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_remove)
        btn_row.addWidget(btn_up)
        btn_row.addWidget(btn_down)
        btn_row.addWidget(btn_clear)
        layout.addLayout(btn_row)

        self.lbl_info = QLabel("Total: 0 files")
        self.lbl_info.setStyleSheet("color: #64748b; font-size: 12px;")
        layout.addWidget(self.lbl_info)

        # Dialog Footer Buttons
        action_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        action_row.addWidget(btn_cancel)

        action_row.addStretch()

        self.btn_merge = QPushButton("Merge & Save")
        self.btn_merge.setObjectName("primaryBtn")
        self.btn_merge.clicked.connect(self._execute_merge)
        action_row.addWidget(self.btn_merge)

        layout.addLayout(action_row)

    def _add_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files to Merge", "", "PDF Files (*.pdf)"
        )
        if file_paths:
            for path in file_paths:
                if path not in self.files:
                    try:
                        doc = pymupdf.open(path)
                        page_count = len(doc)
                        doc.close()
                        self.files.append(path)
                        item = QListWidgetItem(f"{os.path.basename(path)}  ({page_count} pages)")
                        item.setData(Qt.ItemDataRole.UserRole, path)
                        self.list_widget.addItem(item)
                    except Exception as e:
                        QMessageBox.warning(self, "Error opening file", f"Could not read {path}: {str(e)}")
            self._update_info()

    def _remove_selected(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.list_widget.takeItem(row)
            del self.files[row]
            self._update_info()

    def _move_up(self):
        row = self.list_widget.currentRow()
        if row > 0:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row - 1, item)
            self.list_widget.setCurrentRow(row - 1)
            self.files[row], self.files[row - 1] = self.files[row - 1], self.files[row]

    def _move_down(self):
        row = self.list_widget.currentRow()
        if 0 <= row < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row + 1, item)
            self.list_widget.setCurrentRow(row + 1)
            self.files[row], self.files[row + 1] = self.files[row + 1], self.files[row]

    def _clear_all(self):
        self.list_widget.clear()
        self.files.clear()
        self._update_info()

    def _update_info(self):
        self.lbl_info.setText(f"Total: {len(self.files)} files selected")

    def _execute_merge(self):
        if len(self.files) < 2:
            QMessageBox.information(self, "Merge PDFs", "Please add at least 2 PDF files to merge.")
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Save Merged PDF As", "merged_document.pdf", "PDF Files (*.pdf)"
        )
        if not out_path:
            return

        try:
            merged_doc = pymupdf.open()
            for path in self.files:
                doc = pymupdf.open(path)
                merged_doc.insert_pdf(doc)
                doc.close()

            merged_doc.save(out_path)
            merged_doc.close()

            QMessageBox.information(
                self, "Success", f"PDFs merged successfully!\nSaved to: {out_path}"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Merge Error", f"Failed to merge PDF files:\n{str(e)}")
