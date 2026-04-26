@echo off
echo ========================================
echo Building Advanced Uninstaller EXE
echo ========================================
echo.

echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building executable...
pyinstaller --onefile --windowed --name "AdvancedUninstaller" --icon=NONE uninstaller.py

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Your executable is located at:
echo dist\AdvancedUninstaller.exe
echo.
pause
