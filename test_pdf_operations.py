"""
test_pdf_operations.py - Automated testing of PDF manipulation and rendering
"""

import os
import pymupdf
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QColor, QPixmap, QImage, QPainter
from PyQt6.QtCore import Qt, QPointF

from pdf_canvas import PDFCanvas, MovableTextItem, MovableImageItem, ToolMode


def test_pdf_workflow():
    app = QApplication.instance()
    if not app:
        app = QApplication([])

    print("1. Creating test PDF...")
    doc = pymupdf.open()
    page1 = doc.new_page(width=595, height=842)
    page1.insert_text((50, 50), "Hello Original PDF Text", fontsize=16)
    page2 = doc.new_page(width=595, height=842)
    page2.insert_text((50, 50), "Page 2 Original Text", fontsize=16)

    test_pdf_path = "test_input.pdf"
    doc.save(test_pdf_path)
    doc.close()
    assert os.path.exists(test_pdf_path)
    print("   Created test_input.pdf successfully.")

    print("2. Testing canvas rendering & annotations...")
    doc = pymupdf.open(test_pdf_path)
    canvas = PDFCanvas()
    canvas.render_page(doc[0], 0)

    # Add text item
    txt_item = MovableTextItem("Added Annotation Text", QFont("Arial", 18), QColor(255, 0, 0))
    txt_item.setPos(QPointF(100, 150))
    canvas.scene.addItem(txt_item)
    canvas._record_action(txt_item)

    # Add signature image
    sig_img = QImage(120, 60, QImage.Format.Format_ARGB32)
    sig_img.fill(Qt.GlobalColor.transparent)
    painter = QPainter(sig_img)
    painter.setPen(QColor(13, 71, 161))
    painter.drawText(sig_img.rect(), Qt.AlignmentFlag.AlignCenter, "My Signature")
    painter.end()

    canvas.add_image_item(QPixmap.fromImage(sig_img))

    # Burn and save
    print("3. Testing annotation burn into PDF...")
    canvas.save_all_to_doc(doc)
    output_pdf_path = "test_output.pdf"
    doc.save(output_pdf_path)
    doc.close()
    assert os.path.exists(output_pdf_path)
    print("   Saved test_output.pdf successfully.")

    print("4. Verifying output PDF contents...")
    doc_out = pymupdf.open(output_pdf_path)
    assert len(doc_out) == 2
    extracted_text = doc_out[0].get_text()
    print("   Extracted text from page 1:\n", repr(extracted_text))
    assert "Added Annotation Text" in extracted_text
    image_list = doc_out[0].get_images()
    print(f"   Embedded images on page 1: {len(image_list)}")
    assert len(image_list) >= 1
    doc_out.close()

    print("5. Testing Page Operations (Rotate, Delete, Move)...")
    doc_ops = pymupdf.open(test_pdf_path)
    # Rotate
    doc_ops[0].set_rotation(90)
    assert doc_ops[0].rotation == 90

    # Add page
    doc_ops.new_page(width=595, height=842)
    assert len(doc_ops) == 3

    # Delete page
    doc_ops.delete_page(2)
    assert len(doc_ops) == 2

    # Move page
    doc_ops.move_page(0, 1)
    doc_ops.close()

    # Cleanup test files
    if os.path.exists(test_pdf_path):
        os.remove(test_pdf_path)
    if os.path.exists(output_pdf_path):
        os.remove(output_pdf_path)

    print("ALL TESTS PASSED SUCCESSFULLY! [OK]")


if __name__ == "__main__":
    test_pdf_workflow()
