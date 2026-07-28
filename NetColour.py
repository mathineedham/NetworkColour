from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
import fitz  # PyMuPDF

# --- Constants & Configuration ---
VALID_BOUNDARIES = set("\n\t\r ()[]{}<>\"")  # Characters that can act as boundaries
DEFAULT_HIGHLIGHT_COLOR = (0.0, 1.0, 0.0)  # Pure Green (RGB)


@dataclass(slots=True)
class HighlightReport:
    counts: Dict[str, int] = field(default_factory=dict)
    unmatched_counts: int = 0
    unmatched_details: List[str] = field(default_factory=list)


def load_and_clean_nets(txt_path: Path) -> List[str]:
    """Reads, deduplicates, and sorts target net names by descending length."""
    if not txt_path.is_file():
        raise FileNotFoundError(f"Text file not found: {txt_path}")

    nets = {
        line.strip()
        for line in txt_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    # Sort descending by length to match multi-char nets before substrings
    return sorted(nets, key=len, reverse=True)


def is_valid_boundary(char: str) -> bool:
    """Checks if an adjacent character acts as a valid net boundary."""
    if not char:
        return True
    return char in VALID_BOUNDARIES


def highlight_nets(
    input_pdf: Path,
    output_pdf: Path,
    target_nets: List[str],
    color: Tuple[float, float, float] = DEFAULT_HIGHLIGHT_COLOR,
) -> Dict[str, int]:
    if not input_pdf.is_file():
        raise FileNotFoundError(f"PDF file not found: {input_pdf}")

    summary = {net: 0 for net in target_nets}

    with fitz.open(input_pdf) as doc:
        for page in doc:
            # Extract all word blocks on the page: (x0, y0, x1, y1, "word_string", ...)
            words = page.get_text("words")

            for w in words:
                word_text = w[4]
                word_rect = fitz.Rect(w[:4])

                for net in target_nets:
                    if net not in word_text:
                        continue

                    # Exact full match (e.g. word is "0V")
                    if word_text == net:
                        annot = page.add_highlight_annot(word_rect)
                        annot.set_colors(stroke=color)
                        annot.update()
                        summary[net] += 1
                        break  # Found match for this word

                    # Substring match (e.g. word is "(0V)" or "0V;")
                    idx = word_text.find(net)
                    while idx != -1:
                        char_before = word_text[idx - 1] if idx > 0 else ""
                        char_after = (
                            word_text[idx + len(net)]
                            if (idx + len(net)) < len(word_text)
                            else ""
                        )

                        if is_valid_boundary(char_before) and is_valid_boundary(char_after):
                            # For substring matches inside punctuation like (0V), 
                            # search specifically within the word's bounding rect
                            sub_matches = page.search_for(net, clip=word_rect)
                            target_rect = sub_matches[0] if sub_matches else word_rect
                            
                            annot = page.add_highlight_annot(target_rect)
                            annot.set_colors(stroke=color)
                            annot.update()
                            summary[net] += 1
                            break
                        
                        # Continue searching in case net appears again in word
                        idx = word_text.find(net, idx + len(net))

        doc.save(output_pdf, garbage=4, clean=True)

    return summary
def is_green_annotation(color: Optional[Tuple[float, ...]]) -> bool:
    """Checks whether an annotation stroke color is predominantly green."""
    if not color or len(color) < 3:
        return False
    r, g, b = color[:3]
    return g > r and g > b

def count_highlighted_nets(
    pdf_path: Path, target_nets: List[str]
) -> HighlightReport:
    """Extracts and counts text inside green highlights from an existing PDF."""
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    report = HighlightReport(counts=Counter({net: 0 for net in target_nets}))
    target_set = set(target_nets)

    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc, start=1):
            words = page.get_text("words")

            for annot in page.annots() or []:
                if annot.type[0] != fitz.PDF_ANNOT_HIGHLIGHT:
                    continue

                if not is_green_annotation(annot.colors.get("stroke")):
                    continue

                # Collect distinct word text strings intersecting this annotation
                matched_words_in_annot = set()

                # Get individual quads if available (handles multi-line highlights precisely)
                quads = annot.vertices
                highlight_rects = []
                if quads and len(quads) >= 4:
                    # Group vertices into individual 4-point rects/quads
                    for i in range(0, len(quads), 4):
                        highlight_rects.append(fitz.Quad(quads[i : i + 4]).rect)
                else:
                    highlight_rects.append(annot.rect)

                # Check words against all quadrilaterals of this specific highlight
                for w in words:
                    word_rect = fitz.Rect(w[:4])
                    # Check if word falls inside ANY quad of this highlight
                    if any(rect.intersects(word_rect) for rect in highlight_rects):
                        clean_word = w[4].strip()
                        if clean_word in target_set:
                            matched_words_in_annot.add(clean_word)

                # Count each unique target net found in this highlight ONCE
                if matched_words_in_annot:
                    for net in matched_words_in_annot:
                        report.counts[net] += 1
                else:
                    # Fallback for unrecognized text inside highlight
                    raw_text = " ".join(
                        w[4].strip()
                        for w in words
                        if any(
                            r.intersects(fitz.Rect(w[:4]))
                            for r in highlight_rects
                        )
                    ).strip()

                    if raw_text:
                        report.unmatched_counts += 1
                        report.unmatched_details.append(
                            f"Page {page_num}: '{raw_text}'"
                        )

    return report
def display_comparison(
    target_nets: List[str],
    generated_counts: Dict[str, int],
    reference_report: HighlightReport,
) -> None:
    """Prints a comparison table of net counts between generated and reference PDFs."""
    col_w = (30, 15, 15)
    header = f"{'Net Name':<{col_w[0]}} | {'Generated PDF':<{col_w[1]}} | {'Reference PDF':<{col_w[2]}}"

    print("=" * len(header))
    print(header)
    print("=" * len(header))

    for net in sorted(target_nets):
        gen_cnt = generated_counts.get(net, 0)
        ref_cnt = reference_report.counts.get(net, 0)

        if gen_cnt!=ref_cnt and (gen_cnt > 0 or ref_cnt > 0):
            print(f"{net:<{col_w[0]}} | {gen_cnt:<{col_w[1]}} | {ref_cnt:<{col_w[2]}}")

    print("-" * len(header))
    if reference_report.unmatched_counts > 0:
        print(f"Unmatched ('OTHER') Highlights: {reference_report.unmatched_counts}")

    if reference_report.unmatched_details:
        print("\n--- Unrecognized Highlights Details ---")
        for detail in reference_report.unmatched_details:
            print(f"  - {detail}")


def main() -> None:
    txt_input = Path("Imported_Nets_NoPointNb.txt")
    input_schematic = Path("Input_Schematic.pdf")
    output_schematic = Path("Highlighted_Schematic.pdf")
    example_result = Path("Example_colored_result.pdf")

    # Pipeline Processing
    target_nets = load_and_clean_nets(txt_input)
    generated_counts = highlight_nets(input_schematic, output_schematic, target_nets)
    reference_report = count_highlighted_nets(example_result, target_nets)

    # Summary Display
    display_comparison(target_nets, generated_counts, reference_report)


if __name__ == "__main__":
    main()