# Network Names Highlighter

A Python Tkinter application for matching, highlighting, and labeling network names within PDF documents using PyMuPDF.

## Quick Start

### 1. Installation
Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Running the Application
Launch the graphical interface
```bash
python main.py
```
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