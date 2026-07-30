from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple
import fitz

VALID_BOUNDARIES = set("\n\t\r ()[]{}<>\"")
DEFAULT_HIGHLIGHT_COLOR = (0.0, 1.0, 0.0) 

@dataclass(slots=True)
class HighlightReport:
    """!
    @brief Data container for tracking PDF highlighting execution metrics and errors.
    """
    counts: Dict[str, int] = field(default_factory=dict)
    unmatched_counts: int = 0
    unmatched_details: List[str] = field(default_factory=list)

class HighlighterModel:
    """!
    @brief Manages application state, input validation, and PyMuPDF text highlighting logic.
    """

    def __init__(self):
        """!
        @brief Initializes default model state variables.
        """
        self.pdf_path: str = ""
        self.txt_path: str = ""
        self.include_test_points: bool = False

    def validate_inputs(self) -> Tuple[bool, str]:
        """!
        @brief Validates selected file paths before starting PDF processing.

        @return A tuple of (is_valid, error_message).
        """
        if not self.pdf_path:
            return False, "Please select a PDF file."
        if not self.txt_path:
            return False, "Please select a .txt file containing network names."

        pdf = Path(self.pdf_path)
        txt = Path(self.txt_path)

        if not pdf.is_file():
            return False, f"PDF file not found: {self.pdf_path}"
        if not txt.is_file():
            return False, f"Text file not found: {self.txt_path}"

        return True, ""

    def load_and_clean_nets(
        self, txt_path: Path, add_points_number: bool = False
    ) -> Tuple[Dict[str, int], List[str]]:
        """!
        @brief Reads net names from a text file, removes duplicates, and sorts them by length.

        @param txt_path File path to the network names text file.
        @param add_points_number Flag indicating whether to include test point numbers in the search.
        @return A tuple of (points_number, nets), where points_number is a dictionary mapping point names to test point numbers,
                and nets is a list of unique net names sorted in descending order of character length.
        @raises ValueError If a line fails to follow the expected format.
        """
        points_number: Dict[str, int] = {}
        raw_nets: List[str] = []

        lines = txt_path.read_text(encoding="utf-8").splitlines()

        for line_idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line:
                continue

            if not add_points_number:
                if ";" in line:
                    raise ValueError(
                        f"Format error on line {line_idx} in '{txt_path.name}': "
                        f"Unexpected semicolon found in '{line}'. "
                        "Expected only network names when add_points_number=False."
                    )
                raw_nets.append(line)

            else:
                if ";" not in line:
                    raise ValueError(
                        f"Format error on line {line_idx} in '{txt_path.name}': "
                        f"Missing ';' separator in '{line}'. Expected format 'network name;point number'."
                    )

                net, pt = line.rsplit(";", 1)
                net, pt = net.strip(), pt.strip()

                if not net:
                    raise ValueError(
                        f"Format error on line {line_idx} in '{txt_path.name}': "
                        f"Net name cannot be empty."
                    )

                if not pt.isdigit():
                    raise ValueError(
                        f"Format error on line {line_idx} in '{txt_path.name}': "
                        f"Point number must be a digit, got '{pt}'."
                    )

                raw_nets.append(net)
                points_number[net] = int(pt)

        unique_nets = list(set(raw_nets))

        return points_number, sorted(unique_nets, key=len, reverse=True)

    @staticmethod
    def is_valid_boundary(char: str) -> bool:
        """!
        @brief Determines whether a surrounding character counts as a valid boundary.

        @param char The adjacent character to test.
        @return True if character is a valid boundary or empty string, False otherwise.
        """
        if not char:
            return True
        return char in VALID_BOUNDARIES

    def _is_valid_net_match(self, word_text: str, net: str, start_idx: int) -> bool:
        """!
        @brief Verifies whether a substring match within a word has valid boundary characters.

        @param word_text Full string containing the potential match.
        @param net The target net string.
        @param start_idx Starting character index of the match inside word_text.
        @return True if surrounding characters are valid boundaries, False otherwise.
        """
        char_before = word_text[start_idx - 1] if start_idx > 0 else ""
        end_idx = start_idx + len(net)
        char_after = word_text[end_idx] if end_idx < len(word_text) else ""

        return self.is_valid_boundary(char_before) and self.is_valid_boundary(char_after)

    def _process_page_words(
        self,
        page: fitz.Page,
        target_nets: List[str],
        summary: Dict[str, int],
        color: Tuple[float, float, float] = DEFAULT_HIGHLIGHT_COLOR,
    ) -> None:
        """!
        @brief Extracts words from a single PDF page and highlights matched target nets.

        @param page The PyMuPDF page object to process.
        @param target_nets List of target net names to search for.
        @param summary Dictionary tracking hit counts per net, modified in-place.
        @param color RGB color tuple for the highlight annotation.
        """
        words = page.get_text("words")

        for w in words:
            word_text = w[4]
            word_rect = fitz.Rect(w[:4])

            for net in target_nets:
                if net not in word_text:
                    continue

                if word_text == net:
                    annot = page.add_highlight_annot(word_rect)
                    annot.set_colors(stroke=color)
                    annot.update()
                    summary[net] += 1
                    break

                idx = word_text.find(net)
                match_found = False

                while idx != -1:
                    if self._is_valid_net_match(word_text, net, idx):
                        sub_matches = page.search_for(net, clip=word_rect)
                        target_rect = sub_matches[0] if sub_matches else word_rect

                        annot = page.add_highlight_annot(target_rect)
                        annot.set_colors(stroke=color)
                        annot.update()
                        summary[net] += 1
                        match_found = True
                        break
                    idx = word_text.find(net, idx + len(net))

                if match_found:
                    break

    def process_pdf(self, add_points_number: bool = False) -> Tuple[bool, str]:
        """!
        @brief Executes the net highlighting pipeline on the configured PDF.

        @param add_points_number Flag indicating whether to include test point numbers in the search, default is False.

        @return A tuple of (success_flag, summary_log_message).
        """
        input_pdf = Path(self.pdf_path)
        txt_path = Path(self.txt_path)
        output_pdf = input_pdf.with_name(f"{input_pdf.stem}_highlighted{input_pdf.suffix}")

        # --- FIX HERE: Unpack both points_number AND target_nets ---
        points_number, target_nets = self.load_and_clean_nets(txt_path, add_points_number=add_points_number)
        
        if not target_nets:
            return False, "No valid net names found in the text file."

        summary = {net: 0 for net in target_nets}

        with fitz.open(input_pdf) as doc:
            for page in doc:
                self._process_page_words(page, target_nets, summary)

            doc.save(output_pdf, garbage=4, clean=True)

        total_matches = sum(summary.values())
        unmatched = [net for net, count in summary.items() if count == 0]

        report_msg = f"Done! Highlighted {total_matches} net occurrences.\nSaved to: {output_pdf.name}"
        if unmatched:
            report_msg += f"\nWarning: {len(unmatched)} nets were not found in PDF."

        return True, report_msg