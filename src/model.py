"""!
@file model.py
@brief Defines the core business logic and data structures for PDF net highlighting.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import fitz

## Valid boundary characters surrounding net names in text streams
VALID_BOUNDARIES = set("\n\t\r ()[]{}<>\",")

## Default green highlight color in RGB (0.0 - 1.0)
DEFAULT_HIGHLIGHT_COLOR: Tuple[float, float, float] = (0.0, 1.0, 0.0)


@dataclass(slots=True)
class HighlightReport:
    """!
    @brief Data container tracking execution metrics and unmatched target nets.
    """
    counts: Dict[str, int] = field(default_factory=dict)
    unmatched_counts: int = 0
    unmatched_details: List[str] = field(default_factory=list)


class HighlighterModel:
    """!
    @brief Core class managing input validation, text extraction, and PDF annotation.
    """

    def __init__(self) -> None:
        """!
        @brief Initializes default model state variables.
        """
        self.pdf_path: str = ""
        self.txt_path: str = ""
        self.include_test_points: bool = False

    def validate_inputs(self) -> Tuple[bool, str]:
        """!
        @brief Validates selected file paths before starting PDF processing.

        @return A tuple containing (is_valid: bool, error_message: str).
        """
        pdf_str = (self.pdf_path or "").strip()
        txt_str = (self.txt_path or "").strip()

        if not pdf_str:
            return False, "Please select a PDF file."
        if not txt_str:
            return False, "Please select a .txt file containing network names."

        pdf = Path(pdf_str)
        txt = Path(txt_str)

        if not pdf.is_file():
            return False, f"PDF file not found: {pdf_str}"
        if not txt.is_file():
            return False, f"Text file not found: {txt_str}"

        if pdf.suffix.lower() != ".pdf":
            return False, f"Selected PDF file must have a .pdf extension: {pdf_str}"
        if txt.suffix.lower() != ".txt":
            return False, f"Selected text file must have a .txt extension: {txt_str}"

        return True, ""

    def load_and_clean_nets(
        self, txt_path: Path, add_points_number: bool = False
    ) -> Tuple[Dict[str, int], List[str]]:
        """!
        @brief Reads net names from a text file, validates formatting, and sorts them by length.

        @param txt_path Path object pointing to the text file.
        @param add_points_number Flag indicating whether lines contain point numbers separated by ';'.
        @return Tuple containing (points_number_dict, sorted_net_names_list).
        @raises ValueError If a line violates expected formatting rules.
        """
        points_number: Dict[str, int] = {}
        raw_nets: List[str] = []

        lines = txt_path.read_text(encoding="utf-8").splitlines()

        for line_idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line:
                continue

            if not add_points_number:
                self._validate_no_points_line(line, line_idx, txt_path.name)
                raw_nets.append(line)
            else:
                net, pt = self._parse_points_line(line, line_idx, txt_path.name)
                raw_nets.append(net)
                points_number[net] = pt

        unique_nets = list(set(raw_nets))
        unique_nets.sort()
        unique_nets.sort(key=len, reverse=True)

        return points_number, unique_nets

    def _validate_no_points_line(self, line: str, line_idx: int, file_name: str) -> None:
        """!
        @brief Helper to validate lines when test points are disabled.

        @param line Line string to validate.
        @param line_idx Current line number in source file.
        @param file_name File name string for exception messaging.
        @raises ValueError If forbidden boundary characters or semicolons are present.
        """
        forbidden_chars = VALID_BOUNDARIES | {";"}
        found_invalid = [char for char in line if char in forbidden_chars]
        if found_invalid:
            raise ValueError(
                f"Format error on line {line_idx} in '{file_name}': "
                f"Unexpected semicolon found in '{line}'. "
                "Expected only network names when add_points_number=False."
            )

    def _parse_points_line(self, line: str, line_idx: int, file_name: str) -> Tuple[str, int]:
        """!
        @brief Helper to parse and validate 'net;point' lines.

        @param line Line string to parse.
        @param line_idx Current line number in source file.
        @param file_name File name string for exception messaging.
        @return Tuple of parsed (net_name, point_number).
        @raises ValueError If parsing fails due to bad separators or non-numeric digits.
        """
        if ";" not in line:
            raise ValueError(
                f"Format error on line {line_idx} in '{file_name}': "
                f"Missing ';' separator in '{line}'. "
                "Expected format 'net_name;point_number'."
            )

        net, pt = line.rsplit(";", 1)
        net, pt = net.strip(), pt.strip()

        if not net:
            raise ValueError(
                f"Format error on line {line_idx} in '{file_name}': "
                "Net name cannot be empty."
            )

        forbidden_chars = VALID_BOUNDARIES | {";", ","}
        found_invalid = [char for char in net if char in forbidden_chars]
        if found_invalid:
            raise ValueError(
                f"Format error on line {line_idx} in '{file_name}': "
                f"Invalid character '{found_invalid[0]}' found in net name '{net}'."
            )

        if not pt.isdigit():
            raise ValueError(
                f"Format error on line {line_idx} in '{file_name}': "
                f"Point number must be a digit, got '{pt}'."
            )

        return net, int(pt)

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
        @param net Target net string.
        @param start_idx Starting character index of the match inside word_text.
        @return True if surrounding characters are valid boundaries, False otherwise.
        """
        char_before = word_text[start_idx - 1] if start_idx > 0 else ""
        end_idx = start_idx + len(net)
        char_after = word_text[end_idx] if end_idx < len(word_text) else ""

        return self.is_valid_boundary(char_before) and self.is_valid_boundary(char_after)

    def _add_point_label(
        self,
        page: fitz.Page,
        rect: fitz.Rect,
        pt_num: int,
        position: str = "bottom_right",
        fontsize: float = 6.0,
        color: Tuple[float, float, float] = DEFAULT_HIGHLIGHT_COLOR,
    ) -> None:
        """!
        @brief Inserts the test point number label adjacent to a highlighted area.

        @param page PyMuPDF page object.
        @param rect Bounding rectangle of the highlighted text.
        @param pt_num Test point integer label.
        @param position Label placement: 'bottom_right', 'bottom_left', 'top_right', or 'top_left'.
        @param fontsize Text size for the point label.
        @param color RGB color tuple for text rendering.
        """
        label = f"{pt_num}"

        if position == "bottom_right":
            point = fitz.Point(rect.x1 + 4, rect.y1)
        elif position == "bottom_left":
            point = fitz.Point(rect.x0, rect.y1 + fontsize)
        elif position == "top_right":
            point = fitz.Point(rect.x1 + 4, rect.y0 + fontsize)
        else:  # top_left
            point = fitz.Point(rect.x0, rect.y0 - 4)

        page.insert_text(point, label, fontsize=fontsize, color=color)

    def _process_page_words(
        self,
        page: fitz.Page,
        points_number: Dict[str, int],
        target_nets: List[str],
        summary: Dict[str, int],
        add_points_number: bool = False,
        color: Tuple[float, float, float] = DEFAULT_HIGHLIGHT_COLOR,
    ) -> None:
        """!
        @brief Extracts words from a single PDF page and highlights matched target nets.

        @param page PyMuPDF page object.
        @param points_number Dictionary mapping net names to test point numbers.
        @param target_nets Target net names to search for.
        @param summary Dictionary tracking hit counts per net, updated in-place.
        @param add_points_number Flag indicating whether test points should be labeled.
        @param color RGB color tuple for highlights and annotations.
        """
        words = page.get_text("words")

        for w in words:
            word_text = w[4]
            word_rect = fitz.Rect(w[:4])

            for net in target_nets:
                if net not in word_text:
                    continue

                target_rect: Optional[fitz.Rect] = None

                if word_text == net:
                    target_rect = word_rect
                else:
                    idx = word_text.find(net)
                    while idx != -1:
                        if self._is_valid_net_match(word_text, net, idx):
                            sub_matches = page.search_for(net, clip=word_rect)
                            target_rect = sub_matches[0] if sub_matches else word_rect
                            break
                        idx = word_text.find(net, idx + len(net))

                if target_rect:
                    annot = page.add_highlight_annot(target_rect)
                    annot.set_colors(stroke=color)
                    annot.update()
                    summary[net] += 1

                    if add_points_number and points_number and net in points_number:
                        self._add_point_label(
                            page=page,
                            rect=target_rect,
                            pt_num=points_number[net],
                            position="bottom_right",
                            color=color,
                        )
                    break

    def process_pdf(
        self,
        add_points_number: bool = False,
        color: Tuple[float, float, float] = DEFAULT_HIGHLIGHT_COLOR,
    ) -> Tuple[bool, str]:
        """!
        @brief Executes the complete net highlighting pipeline on the configured PDF file.

        @param add_points_number Flag indicating whether to attach test point labels.
        @param color RGB color tuple for highlighting annotations.
        @return Tuple containing (success_flag: bool, message: str).
        """
        is_valid, err_msg = self.validate_inputs()
        if not is_valid:
            return False, err_msg

        input_pdf = Path(self.pdf_path)
        txt_path = Path(self.txt_path)
        output_pdf = input_pdf.with_name(f"{input_pdf.stem}_highlighted{input_pdf.suffix}")

        try:
            points_number, target_nets = self.load_and_clean_nets(
                txt_path, add_points_number=add_points_number
            )
        except ValueError as exc:
            return False, str(exc)

        if not target_nets:
            return False, "No valid net names found in the text file."

        summary = {net: 0 for net in target_nets}

        with fitz.open(input_pdf) as doc:
            for page in doc:
                self._process_page_words(
                    page,
                    points_number,
                    target_nets,
                    summary,
                    add_points_number=add_points_number,
                    color=color,
                )

            doc.save(output_pdf, garbage=4, clean=True)

        total_matches = sum(summary.values())
        unmatched = [net for net, count in summary.items() if count == 0]

        report_msg = f"Done! Highlighted {total_matches} net occurrences.\nSaved to: {output_pdf.name}"
        if unmatched:
            report_msg += f"\nWarning: {len(unmatched)} nets were not found in PDF."

        return True, report_msg