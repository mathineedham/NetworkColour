from typing import Tuple


class HighlighterModel:
    """Manages application state, validation, and processing logic."""

    def __init__(self):
        self.pdf_path: str = ""
        self.txt_path: str = ""
        self.include_test_points: bool = False

    def validate_inputs(self) -> Tuple[bool, str]:
        if not self.pdf_path:
            return False, "Please select a PDF file."
        if not self.txt_path:
            return False, "Please select a .txt file containing network names."
        return True, ""

    def process_pdf(self) -> Tuple[bool, str]:
        # PDF highlighting processing logic (e.g., PyMuPDF/fitz) goes here.
        return True, "Processing completed successfully!"