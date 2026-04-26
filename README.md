# Advanced Application Uninstaller

A Windows application that helps you completely uninstall programs and clean up leftover files.

## Features

- **List Installed Applications**: Scans Windows registry to show all installed programs
- **Uninstall Apps**: Launches the native uninstaller for selected applications
- **Scan for Leftovers**: Searches common locations for residual files and folders
- **Clean Up**: Removes leftover files after uninstallation

## Requirements

- Windows OS
- Python 3.6 or higher
- Administrator privileges (recommended for full functionality)

## Installation

### Option 1: Use the EXE file (Recommended)
1. Download `AdvancedUninstaller.exe` from the `dist` folder
2. Right-click and select "Run as Administrator"
3. That's it! No Python installation needed

### Option 2: Run from Python source
1. Make sure Python is installed on your system
2. No additional packages needed (uses built-in libraries)
3. Run: `python uninstaller.py`

## Building the EXE yourself

If you want to build the executable from source:

1. Install Python 3.6 or higher
2. Double-click `build_exe.bat` (or run it from command prompt)
3. Wait for the build to complete
4. Find your executable in the `dist` folder

**Manual build command:**
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "AdvancedUninstaller" uninstaller.py
```

## Usage

1. Run the application (either the .exe or Python script)
2. **Important:** Right-click and "Run as Administrator" for full functionality

2. **To uninstall an application:**
   - Select an app from the list
   - Click "Uninstall Selected"
   - Complete the uninstaller wizard that appears
   - After uninstallation, click "Scan for Leftovers"

3. **To scan for leftovers:**
   - Click "Scan for Leftovers"
   - Enter the application name if prompted
   - Review found items and confirm deletion

## Locations Scanned

The tool searches for leftover files in:
- `%APPDATA%` (User application data)
- `%LOCALAPPDATA%` (Local application data)
- `%PROGRAMDATA%` (Program data)
- `%PROGRAMFILES%` (Program Files)
- `%PROGRAMFILES(X86)%` (Program Files x86)

## Important Notes

- **Run as Administrator** for best results
- Always review items before deleting
- Some system files may require special permissions
- Create a system restore point before major cleanups

## Safety

The tool only deletes items that match the application name. However:
- Always backup important data
- Review the log before confirming deletion
- Some files may be in use and cannot be deleted

## Troubleshooting

**"Access Denied" errors:**
- Run the application as Administrator
- Close the application you're trying to uninstall

**Application not listed:**
- Click "Refresh List"
- Some portable apps don't register in Windows

**Can't delete some files:**
- Files may be in use by another process
- Restart your computer and try again
