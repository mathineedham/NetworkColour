"""!
@file model.py
@brief Defines the core business logic and data structures for PDF net highlighting.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import math
import tempfile
import fitz

## Valid boundary characters surrounding net names in text streams
VALID_BOUNDARIES = set("\n\t\r ()[]{}<>\",")

## Default green highlight color in RGB (0.0 - 1.0)
DEFAULT_HIGHLIGHT_COLOR: Tuple[float, float, float] = (0.0, 1.0, 0.0)

## Batch size for processing pages in the PDF 
BATCH_SIZE = 5  # Number of pages to process in one batch for performance


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
    ) -> Tuple[Dict[str, str], List[str]]:
        """!
        @brief Reads net names from a text file, validates formatting, and sorts them by length.

        @param txt_path Path object pointing to the text file.
        @param add_points_number Flag indicating whether lines contain point numbers separated by ';'.
        @return Tuple containing (points_number_dict, sorted_net_names_list).
        @raises ValueError If a line violates expected formatting rules.
        """
        points_number: Dict[str, str] = {}
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
                if net in points_number.keys():
                    points_number[net] += f",{pt}"
                else:
                    points_number[net] = pt
                raw_nets.append(net)

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

    def _parse_points_line(self, line: str, line_idx: int, file_name: str) -> Tuple[str, str]:
        """!
        @brief Helper to parse and validate 'net;point(s)' lines as string.
        @param[in] line Line string to parse.
        @param[in] line_idx Current line number in source file.
        @param[in] file_name File name string for exception messaging.
        @raises ValueError If the line does not follow the expected format.
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

        if not pt:
            raise ValueError(
                f"Format error on line {line_idx} in '{file_name}': "
                "Point number cannot be empty."
            )

        forbidden_chars = VALID_BOUNDARIES | {";"}
        found_invalid = [char for char in net if char in forbidden_chars]
        if found_invalid:
            raise ValueError(
                f"Format error on line {line_idx} in '{file_name}': "
                f"Invalid character '{found_invalid[0]}' found in net name '{net}'."
            )

        return net, pt

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
        pt_label: str,
        dir_vector: Tuple[float, float] = (1.0, 0.0),
        fontsize: float = 10.0,
        color: Tuple[float, float, float] = DEFAULT_HIGHLIGHT_COLOR,
    ) -> None:
        """!
        @brief Inserts the test point string label at the top-right corner matching text orientation.

        @param page PyMuPDF page object.
        @param rect Bounding rectangle of the highlighted net text.
        @param pt_label The test point string to insert.
        @param dir_vector Direction vector of the text line for rotation alignment.
        @param fontsize Font size for the inserted label.
        @param color RGB color tuple for the label text.
        """
        dx, dy = dir_vector

        # Calculate exact angle in degrees counter-clockwise from horizontal right
        angle_rad = math.atan2(dy, dx)
        angle_deg = int(round(math.degrees(angle_rad))) % 360

        # Flip vertical reading directions (90 <-> 270) to match bottom-to-top layout
        if angle_deg == 90:
            angle_deg = 270
        elif angle_deg == 270:
            angle_deg = 90

        # Position at the top-right corner of the target rectangle
        if angle_deg == 270:  # Vertical bottom-to-top (places label above the top end of the net)
            point = fitz.Point(rect.x1 + 3, rect.y0)
        elif angle_deg == 90:   # Top-to-Bottom
            point = fitz.Point(rect.x1 + 3, rect.y0)
        elif angle_deg == 180:  # Horizontal (Right-to-Left)
            point = fitz.Point(rect.x1 + 3, rect.y0 - 2)
        else:                   # Horizontal (Left-to-Right / 0 deg)
            point = fitz.Point(rect.x1 + 3, rect.y0)

        page.insert_text(
            point, 
            pt_label, 
            fontsize=fontsize, 
            color=color, 
            rotate=angle_deg
        )
    
    def _process_page_words(
        self,
        page: fitz.Page,
        points_number: Dict[str, str],
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
        page_dict = page.get_text("dict")

        for block in page_dict.get("blocks", []):
            if "lines" not in block:
                continue

            for line in block["lines"]:
                dir_vector = line.get("dir", (1.0, 0.0))

                for span in line.get("spans", []):
                    span_text = span.get("text", "")
                    if not span_text:
                        continue

                    span_bbox = span.get("bbox")
                    span_rect = fitz.Rect(span_bbox)

                    for net in target_nets:
                        if net not in span_text:
                            continue

                        target_rect: Optional[fitz.Rect] = None

                        if span_text == net:
                            target_rect = span_rect
                        else:
                            idx = span_text.find(net)
                            while idx != -1:
                                if self._is_valid_net_match(span_text, net, idx):
                                    sub_matches = page.search_for(net, clip=span_rect)
                                    target_rect = sub_matches[0] if sub_matches else span_rect
                                    break
                                idx = span_text.find(net, idx + len(net))

                        if target_rect:
                            annot = page.add_highlight_annot(target_rect)
                            annot.set_colors(stroke=color)
                            annot.update()
                            summary[net] += 1

                            if add_points_number and points_number and net in points_number:
                                self._add_point_label(
                                    page=page,
                                    rect=target_rect,
                                    pt_label=points_number[net],
                                    dir_vector=dir_vector,
                                    color=color,
                                )
                            break

    def process_pdf(
        self,
        add_points_number: bool = False,
        color: Tuple[float, float, float] = DEFAULT_HIGHLIGHT_COLOR,
    ) -> Tuple[bool, str]:
        """!
        @brief Executes the net highlighting pipeline in small batches via temp files,  then merges them into a single final document.
        @param add_points_number Flag indicating whether test points should be labeled.
        @param color RGB color tuple for highlights and annotations.
        @return Tuple containing (success: bool, message: str).
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

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_files = self._process_batches(
                input_pdf, Path(temp_dir), points_number, target_nets, summary, add_points_number, color
            )
            self._merge_and_save(temp_files, output_pdf)

        return True, self._build_report(summary, output_pdf.name)

    def _process_batches(
        self,
        input_pdf: Path,
        temp_dir: Path,
        points_number: Any,
        target_nets: list,
        summary: dict,
        add_points_number: bool,
        color: Tuple[float, float, float],
    ) -> list[Path]:
        """Processes PDF pages in chunks and saves them to temporary PDF files.
        @param input_pdf Path to the source PDF file.
        @param temp_dir Path to the temporary directory for storing chunk PDFs.
        @param points_number Dictionary mapping net names to test point numbers.
        @param target_nets List of target net names to highlight.
        @param summary Dictionary tracking hit counts per net, updated in-place.
        @param add_points_number Flag indicating whether test points should be labeled.
        @param color RGB color tuple for highlights and annotations.
        @return List of temporary PDF file paths for each processed batch.
        """
        temp_files = []
        with fitz.open(input_pdf) as src_doc:
            total_pages = len(src_doc)

            for start_page in range(0, total_pages, BATCH_SIZE):
                end_page = min(start_page + BATCH_SIZE, total_pages)
                temp_path = temp_dir / f"part_{start_page}.pdf"

                self._process_single_batch(
                    src_doc, start_page, end_page, points_number, target_nets, summary, add_points_number, color, temp_path
                )
                temp_files.append(temp_path)

        return temp_files

    def _process_single_batch(
        self,
        src_doc: fitz.Document,
        start_page: int,
        end_page: int,
        points_number: Any,
        target_nets: list,
        summary: dict,
        add_points_number: bool,
        color: Tuple[float, float, float],
        temp_path: Path,
    ) -> None:
        """Processes a single page range and saves it to a temp path.
        @param src_doc The source PDF document.
        @param start_page The starting page index (inclusive).
        @param end_page The ending page index (exclusive).
        @param points_number Dictionary mapping net names to test point numbers.
        @param target_nets List of target net names to highlight.
        @param summary Dictionary tracking hit counts per net, updated in-place.
        @param add_points_number Flag indicating whether test points should be labeled.
        @param color RGB color tuple for highlights and annotations.
        @param temp_path Path to save the processed batch PDF.
        """
        batch_doc = fitz.open()
        batch_doc.insert_pdf(src_doc, from_page=start_page, to_page=end_page - 1)

        for page in batch_doc:
            self._process_page_words(
                page,
                points_number,
                target_nets,
                summary,
                add_points_number=add_points_number,
                color=color,
            )

        batch_doc.save(temp_path, garbage=1)
        batch_doc.close()

    def _merge_and_save(self, temp_files: list[Path], output_pdf: Path) -> None:
        """Merges temporary chunk PDFs into the final output document.
        @param temp_files List of temporary PDF file paths.
        @param output_pdf Path to save the final merged PDF.
        """
        final_doc = fitz.open()
        for temp_file in temp_files:
            with fitz.open(temp_file) as chunk:
                final_doc.insert_pdf(chunk)

        final_doc.save(output_pdf, garbage=3, deflate=True)
        final_doc.close()

    def _build_report(self, summary: dict, output_filename: str) -> str:
        """Builds the final summary status message.
        @param summary Dictionary tracking hit counts per net.
        @param output_filename Name of the output PDF file.
        @return Formatted report string.
        """
        total_matches = sum(summary.values())
        unmatched = [net for net, count in summary.items() if count == 0]

        report_msg = f"Done! Highlighted {total_matches} net occurrences.\nSaved to: {output_filename}"
        if unmatched:
            report_msg += f"\nWarning: {len(unmatched)} nets were not found in PDF."

        return report_msg