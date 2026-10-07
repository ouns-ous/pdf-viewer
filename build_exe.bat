@echo off
echo ========================================================
echo        Building PDF Studio Pro (.exe) for Windows
echo ========================================================

python -m PyInstaller --noconfirm --clean PDF_Studio_Pro.spec

echo.
echo ========================================================
echo Build finished! The executable is located at:
echo dist\PDF_Studio_Pro.exe
echo ========================================================
echo.
pause
