"""
signature_dialog.py - Electronic Signature creator with freehand drawing or image upload
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QColorDialog, QFileDialog, QRadioButton, QButtonGroup, QFrame
)
from PyQt6.QtGui import QPainter, QPen, QColor, QImage, QPainterPath
from PyQt6.QtCore import Qt, QPoint, QSize


class SignatureCanvas(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(500, 220)
        self.setStyleSheet("""
            SignatureCanvas {
                background-color: #ffffff;
                border: 2px dashed #536dfe;
                border-radius: 8px;
            }
        """)
        self.pen_color = QColor("#0d47a1")  # Blue ink
        self.pen_width = 3
        self.paths = []  # List of tuples: (QPainterPath, QColor, width)
        self.current_path = None
        self.custom_image = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.custom_image = None  # Clear uploaded image if drawing
            self.current_path = QPainterPath()
            self.current_path.moveTo(event.position())
            self.paths.append((self.current_path, self.pen_color, self.pen_width))
            self.update()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.current_path:
            self.current_path.lineTo(event.position())
            self.update()

    def mouseReleaseEvent(self, event):
        self.current_path = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Baseline indicator
        pen_guide = QPen(QColor(220, 220, 230), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen_guide)
        painter.drawLine(30, 170, 470, 170)

        # Watermark text if empty
        if not self.paths and not self.custom_image:
            painter.setPen(QColor(180, 180, 190))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Sign here with your mouse or stylus...")

        if self.custom_image:
            scaled = self.custom_image.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawImage(x, y, scaled)
            return

        for path, color, width in self.paths:
            pen = QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawPath(path)

    def clear(self):
        self.paths.clear()
        self.custom_image = None
        self.update()

    def get_transparent_image(self) -> QImage:
        """Render signature on a transparent background."""
        img = QImage(self.size(), QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)

        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.custom_image:
            scaled = self.custom_image.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawImage(x, y, scaled)
        else:
            for path, color, width in self.paths:
                pen = QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawPath(path)
        painter.end()

        # Crop transparent borders for a clean tight bounding box
        return self._crop_transparent(img)

    def _crop_transparent(self, image: QImage) -> QImage:
        rect = image.rect()
        left, top, right, bottom = rect.width(), rect.height(), 0, 0
        has_content = False

        for y in range(rect.height()):
            for x in range(rect.width()):
                if (image.pixelColor(x, y).alpha()) > 10:
                    has_content = True
                    if x < left: left = x
                    if x > right: right = x
                    if y < top: top = y
                    if y > bottom: bottom = y

        if not has_content or left > right or top > bottom:
            return image

        # Add a 6px margin
        left = max(0, left - 6)
        top = max(0, top - 6)
        right = min(rect.width() - 1, right + 6)
        bottom = min(rect.height() - 1, bottom + 6)

        return image.copy(left, top, right - left + 1, bottom - top + 1)


class SignatureDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Signature / إضافة توقيع")
        self.setFixedSize(540, 380)
        self.signature_image = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Draw your signature or upload an image file:")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Canvas
        self.canvas = SignatureCanvas(self)
        layout.addWidget(self.canvas, alignment=Qt.AlignmentFlag.AlignCenter)

        # Color & Stroke controls
        controls_layout = QHBoxLayout()

        # Ink Color Presets
        controls_layout.addWidget(QLabel("Ink Color:"))
        self.btn_blue = QPushButton("Blue")
        self.btn_blue.setStyleSheet("background-color: #0d47a1; color: white; font-weight: bold;")
        self.btn_blue.clicked.connect(lambda: self._set_color("#0d47a1"))

        self.btn_black = QPushButton("Black")
        self.btn_black.setStyleSheet("background-color: #111111; color: white; font-weight: bold;")
        self.btn_black.clicked.connect(lambda: self._set_color("#111111"))

        self.btn_red = QPushButton("Red")
        self.btn_red.setStyleSheet("background-color: #b71c1c; color: white; font-weight: bold;")
        self.btn_red.clicked.connect(lambda: self._set_color("#b71c1c"))

        controls_layout.addWidget(self.btn_blue)
        controls_layout.addWidget(self.btn_black)
        controls_layout.addWidget(self.btn_red)

        controls_layout.addSpacing(15)

        # Pen Width
        controls_layout.addWidget(QLabel("Width:"))
        self.slider_width = QSlider(Qt.Orientation.Horizontal)
        self.slider_width.setRange(1, 8)
        self.slider_width.setValue(3)
        self.slider_width.setFixedWidth(80)
        self.slider_width.valueChanged.connect(self._set_width)
        controls_layout.addWidget(self.slider_width)

        controls_layout.addStretch()

        # Upload image button
        btn_upload = QPushButton("Upload Image...")
        btn_upload.clicked.connect(self._upload_image)
        controls_layout.addWidget(btn_upload)

        layout.addLayout(controls_layout)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self.canvas.clear)
        btn_layout.addWidget(btn_clear)

        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_ok = QPushButton("Use Signature / استعمال")
        btn_ok.setObjectName("primaryBtn")
        btn_ok.clicked.connect(self._accept_signature)
        btn_layout.addWidget(btn_ok)

        layout.addLayout(btn_layout)

    def _set_color(self, hex_color: str):
        self.canvas.pen_color = QColor(hex_color)

    def _set_width(self, width: int):
        self.canvas.pen_width = width

    def _upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Signature Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            img = QImage(file_path)
            if not img.isNull():
                self.canvas.custom_image = img
                self.canvas.paths.clear()
                self.canvas.update()

    def _accept_signature(self):
        img = self.canvas.get_transparent_image()
        if not img.isNull() and (self.canvas.paths or self.canvas.custom_image):
            self.signature_image = img
            self.accept()
        else:
            self.reject()
