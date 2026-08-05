# Network Names Highlighter

A Python Tkinter application for matching, highlighting, and labeling network names within PDF documents using PyMuPDF.

## Quick Start

### 1. Installation
This application uses Python 3.14.6
Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Running the Application 

#### Using Python
Launch the graphical interface
```bash
python main.py
```
#### Using .exe
##### Running the Pre-built Executable
1. Navigate to the dist/ directory in the project root.
2. Double-click 'main.exe' to launch the application directly.
3. No Python installation or command line is required for end users running this file.
*Italic* Note: Windows Defender or SmartScreen may show a warning when running the executable for the first time on a new system. Click *bold*More info*bold*$\rightarrow$*bold*Run anyway*bold*.*Italic*
##### Regenerating the Executable
If you make changes to any source code in `src/` or `main.py`, you will need to rebuild the executable:

1. Ensure PyInstaller is installed in your Python environment:
   ```bash
   pip install pyinstaller
   ```
2. Build the single-file executable with GUI mode enabled (hides the black console window):
```bash
pyinstaller --onefile --noconsole --paths=src main.py
```
3. The newly generated executable will replace the previous build in the `dist/` directory.
> **Build Specifications:**
> - **Entry Point:** `main.py`
> - **Source Folder:** `src/` (included via `--paths=src`)
> - **Packaging Mode:** Single Executable (`--onefile`)
> - **Console Window:** Hidden (`--noconsole`)
> - **Target OS:** Built specifically for Windows 64-bit systems

### 3. Running Tests
Run the automated test suite:
```bash
python -m unittest discover -s tests
```
## File Format Requirements
- PDF File: Target schematic or board PDF document (.pdf).
- Network Names File: UTF-8 encoded text file (.txt) containing net names.
    - Without test points: One net name per line (e.g., NET_A).
    - With test points: Net name and point number separated by a semicolon (e.g., NET_A;101).