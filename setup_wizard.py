"""
setup_wizard.py - Modern Windows Setup Wizard for PDF Studio Pro
"""

import sys
import os
import shutil
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QProgressBar, QFileDialog, QFrame,
    QMessageBox
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

INSTALLER_STYLES = """
* {
    font-family: 'Segoe UI Variable Text', 'Segoe UI', 'Inter', -apple-system, sans-serif;
}
QWizard {
    background-color: #f8fafc;
}
QLabel {
    color: #1e293b;
    font-size: 13px;
}
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
}
QPushButton {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #f1f5f9;
    border-color: #94a3b8;
}
QPushButton#primaryBtn {
    background-color: #ea580c;
    color: #ffffff;
    border: 1px solid #c2410c;
    font-weight: 600;
}
QPushButton#primaryBtn:hover {
    background-color: #f97316;
}
QProgressBar {
    background-color: #e2e8f0;
    border: none;
    border-radius: 6px;
    text-align: center;
    color: #0f172a;
    font-weight: 600;
    height: 18px;
}
QProgressBar::chunk {
    background-color: #ea580c;
    border-radius: 6px;
}
QCheckBox {
    font-size: 13px;
    color: #334155;
}
"""


def create_windows_shortcut(target_exe: str, shortcut_path: str, description="PDF Studio Pro"):
    """Create Windows .lnk shortcut using PowerShell without external dependencies."""
    ps_cmd = (
        f"$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut('{shortcut_path}'); "
        f"$s.TargetPath = '{target_exe}'; "
        f"$s.WorkingDirectory = '{os.path.dirname(target_exe)}'; "
        f"$s.Description = '{description}'; "
        f"$s.Save()"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)


class WelcomePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Welcome to PDF Studio Pro Setup")
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        desc = QLabel(
            "This wizard will install PDF Studio Pro on your computer.\n\n"
            "PDF Studio Pro is a clean, modern, and high-performance PDF editor "
            "for viewing, annotating, and managing PDF files.\n\n"
            "Click Next to continue."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)


class DirectoryPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Select Installation Folder")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        lbl = QLabel("PDF Studio Pro will be installed in the following folder:")
        layout.addWidget(lbl)

        row = QHBoxLayout()
        default_dir = os.path.join(os.environ.get("LOCALAPPDATA", "C:\\"), "Programs", "PDF Studio Pro")
        self.txt_dir = QLineEdit(default_dir)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse)

        row.addWidget(self.txt_dir)
        row.addWidget(btn_browse)
        layout.addLayout(row)

        layout.addSpacing(10)
        self.chk_desktop = QCheckBox("Create a Desktop shortcut")
        self.chk_desktop.setChecked(True)
        self.chk_start = QCheckBox("Create a Start Menu shortcut")
        self.chk_start.setChecked(True)

        layout.addWidget(self.chk_desktop)
        layout.addWidget(self.chk_start)

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Install Folder", self.txt_dir.text())
        if folder:
            self.txt_dir.setText(os.path.join(folder, "PDF Studio Pro"))

    def get_install_dir(self):
        return self.txt_dir.text().strip()


class InstallWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, target_dir: str, create_desktop: bool, create_start: bool):
        super().__init__()
        self.target_dir = target_dir
        self.create_desktop = create_desktop
        self.create_start = create_start

    def run(self):
        try:
            self.progress.emit(15, "Preparing directories...")
            os.makedirs(self.target_dir, exist_ok=True)

            # Find source PDF_Studio_Pro.exe
            # Check current script directory or bundled sys._MEIPASS
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            src_exe = os.path.join(base_dir, "PDF_Studio_Pro.exe")
            if not os.path.exists(src_exe):
                # Fallback to parent dir or current dir
                candidates = [
                    os.path.join(os.getcwd(), "PDF_Studio_Pro.exe"),
                    os.path.join(os.getcwd(), "dist", "PDF_Studio_Pro.exe")
                ]
                for c in candidates:
                    if os.path.exists(c):
                        src_exe = c
                        break

            if not os.path.exists(src_exe):
                self.finished.emit(False, "Could not find PDF_Studio_Pro.exe source payload.")
                return

            self.progress.emit(40, "Copying application binaries...")
            dest_exe = os.path.join(self.target_dir, "PDF_Studio_Pro.exe")
            shutil.copy2(src_exe, dest_exe)

            self.progress.emit(70, "Creating shortcuts...")
            if self.create_desktop:
                desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
                if os.path.exists(desktop):
                    shortcut_path = os.path.join(desktop, "PDF Studio Pro.lnk")
                    create_windows_shortcut(dest_exe, shortcut_path)

            if self.create_start:
                start_menu = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs")
                if os.path.exists(start_menu):
                    shortcut_path = os.path.join(start_menu, "PDF Studio Pro.lnk")
                    create_windows_shortcut(dest_exe, shortcut_path)

            # Create an uninstaller script
            uninstaller_path = os.path.join(self.target_dir, "uninstall.bat")
            with open(uninstaller_path, "w", encoding="utf-8") as f:
                f.write(
                    '@echo off\n'
                    'taskkill /F /IM PDF_Studio_Pro.exe >nul 2>&1\n'
                    f'del "{os.path.join(os.environ.get("USERPROFILE", ""), "Desktop", "PDF Studio Pro.lnk")}" >nul 2>&1\n'
                    f'del "{os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "PDF Studio Pro.lnk")}" >nul 2>&1\n'
                    'echo PDF Studio Pro shortcuts removed.\n'
                    'echo To complete uninstallation, delete this folder.\n'
                    'pause\n'
                )

            self.progress.emit(100, "Installation completed!")
            self.finished.emit(True, dest_exe)

        except Exception as e:
            self.finished.emit(False, str(e))


class ProgressPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Installing PDF Studio Pro")
        self.is_done = False
        self.installed_exe = None

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        self.lbl_status = QLabel("Ready to install...")
        layout.addWidget(self.lbl_status)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        layout.addWidget(self.bar)

    def initializePage(self):
        # Disable Next/Back while installing
        self.wizard().button(QWizard.WizardButton.BackButton).setEnabled(False)
        self.wizard().button(QWizard.WizardButton.NextButton).setEnabled(False)

        dir_page = self.wizard().page(1)
        target_dir = dir_page.get_install_dir()
        create_desk = dir_page.chk_desktop.isChecked()
        create_start = dir_page.chk_start.isChecked()

        self.worker = InstallWorker(target_dir, create_desk, create_start)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, val: int, msg: str):
        self.bar.setValue(val)
        self.lbl_status.setText(msg)

    def _on_finished(self, success: bool, msg: str):
        if success:
            self.is_done = True
            self.installed_exe = msg
            self.lbl_status.setText("PDF Studio Pro was successfully installed on your system.")
            self.wizard().button(QWizard.WizardButton.NextButton).setEnabled(True)
            self.wizard().next()
        else:
            QMessageBox.critical(self, "Installation Failed", f"An error occurred during install:\n{msg}")

    def isComplete(self):
        return self.is_done


class FinishedPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Completing PDF Studio Pro Setup")
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        lbl = QLabel(
            "PDF Studio Pro has been installed on your computer.\n\n"
            "You can launch it anytime from your Desktop or Start Menu."
        )
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.chk_launch = QCheckBox("Launch PDF Studio Pro now")
        self.chk_launch.setChecked(True)
        layout.addWidget(self.chk_launch)


class SetupWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Studio Pro Setup")
        self.resize(520, 380)
        self.setStyleSheet(INSTALLER_STYLES)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

        self.page_welcome = WelcomePage(self)
        self.page_dir = DirectoryPage(self)
        self.page_prog = ProgressPage(self)
        self.page_finish = FinishedPage(self)

        self.addPage(self.page_welcome)
        self.addPage(self.page_dir)
        self.addPage(self.page_prog)
        self.addPage(self.page_finish)

        self.button(QWizard.WizardButton.FinishButton).clicked.connect(self._on_finish)

    def _on_finish(self):
        if self.page_finish.chk_launch.isChecked() and self.page_prog.installed_exe:
            if os.path.exists(self.page_prog.installed_exe):
                subprocess.Popen([self.page_prog.installed_exe])


def main():
    app = QApplication(sys.argv)
    font = QFont()
    font.setFamilies(["Segoe UI Variable Text", "Segoe UI", "Inter", "sans-serif"])
    font.setPointSize(9)
    app.setFont(font)
    wizard = SetupWizard()
    wizard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
