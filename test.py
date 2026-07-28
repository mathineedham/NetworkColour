import os
from collections import Counter
import fitz  # PyMuPDF


def load_and_clean_nets(txt_file_path: str) -> list[str]:
    """Read net names from a text file as-is, remove duplicate entries,

    and sort them by length descending.
    """
    if not os.path.exists(txt_file_path):
        raise FileNotFoundError(f"Text file not found: {txt_file_path}")

    with open(txt_file_path, "r", encoding="utf-8") as f:
        # Keep exact lines/whitespace, only ignore empty lines
        nets = set(line.rstrip("\r\n") for line in f if line.rstrip("\r\n"))

    return sorted(list(nets), key=len, reverse=True)


def count_green_highlighted_nets(
    pdf_path: str, target_nets: list[str]
) -> tuple[dict[str, int], list[str]]:
    """Extracts text from green highlights in a PDF, counts target nets,

    and captures any unmatched/other text instances.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Initialize counter for target nets
    net_counts = Counter({net: 0 for net in target_nets})
    net_counts["OTHER"] = 0

    # Keep track of specific text strings logged under 'OTHER' for easy inspection
    other_details = []

    doc = fitz.open(pdf_path)

    for page_num, page in enumerate(doc, start=1):
        for annot in page.annots():
            # Check if annotation is a Highlight (type code 8)
            if annot.type[0] == 8:
                color = annot.colors.get("stroke")

                if color:
                    r, g, b = color
                    # Green dominant check
                    if g > r and g > b:
                        text = page.get_text("text", clip=annot.rect).strip()

                        if not text:
                            continue

                        matched = False
                        # Check extracted text against target nets
                        for net in target_nets:
                            if net in text:
                                count = text.count(net)
                                net_counts[net] += count
                                matched = True

                        # If the highlighted text didn't contain ANY net from the list
                        if not matched:
                            net_counts["OTHER"] += 1
                            other_details.append(f"Page {page_num}: '{text}'")

    return net_counts, other_details


def main():
    txt_path = "Imported_Nets_NoPointNb.txt"  # Path to your text file
    pdf_path = "Example_colored_result.pdf"  # Path to your PDF file

    # 1. Load target nets
    target_nets = load_and_clean_nets(txt_path)

    # 2. Count occurrences in green highlights
    results, other_items = count_green_highlighted_nets(pdf_path, target_nets)

    # 3. Print summary
    print("--- Exact Match Summary ---")
    for net, count in results.items():
        if count > 0:
            print(f"'{net}': {count} instance(s) highlighted")

    # Optional: Print what the 'OTHER' items were if any exist
    if other_items:
        print("\n--- Unrecognized ('OTHER') Highlights ---")
        for item in other_items:
            print(f"  - {item}")


if __name__ == "__main__":
    main()