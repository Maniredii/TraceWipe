@echo off
echo ========================================
echo Building TraceWipe EXE
echo ========================================
echo.

echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building executable...
pyinstaller --onefile --windowed --name "TraceWipe" --icon=NONE uninstaller.py

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Your executable is located at:
echo dist\TraceWipe.exe
echo.
pause
