"""!
@file test_model.py
@brief Comprehensive test suite for HighLighterModel using PyMuPDF and unittest.
"""

import tempfile
import unittest
from pathlib import Path
import fitz

from src.model import HighlighterModel, HighlightReport


class TestHighlighterModel(unittest.TestCase):
    """!
    @brief Test cases covering validation, parsing, boundary matching, and PDF processing.
    """

    def setUp(self) -> None:
        """!
        @brief Prepares a fresh model instance and temporary workspace before each test run.
        """
        self.model = HighlighterModel()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        """!
        @brief Cleans up temporary resources after each test run.
        """
        self.temp_dir.cleanup()

    def _create_sample_pdf(self, filename: str, text: str) -> Path:
        """!
        @brief Helper function to generate dummy PDF files dynamically for test cases.
        """
        pdf_path = self.temp_path / filename
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(fitz.Point(50, 50), text)
        doc.save(pdf_path)
        doc.close()
        return pdf_path

    # Dataclass unit tests

    def test_highlight_report_dataclass(self) -> None:
        """Test HighlightReport instantiation and defaults."""
        report = HighlightReport(counts={"NET_A": 1}, unmatched_counts=1, unmatched_details=["NET_B"])
        self.assertEqual(report.counts["NET_A"], 1)
        self.assertEqual(report.unmatched_counts, 1)
        self.assertIn("NET_B", report.unmatched_details)

    # load_and_clean_nets (add_points_number=False)

    def test_load_nets_without_points_success(self) -> None:
        """Test valid file loading without point numbers."""
        txt_file = self.temp_path / "valid_nets.txt"
        txt_file.write_text("NET_A\nNET_LONG_NAME\nNET_B\n", encoding="utf-8")

        points, nets = self.model.load_and_clean_nets(txt_file, add_points_number=False)

        self.assertEqual(points, {})
        self.assertEqual(nets, ["NET_LONG_NAME", "NET_A", "NET_B"])

    def test_load_nets_without_points_raises_on_invalid_lines(self) -> None:
        """Test that invalid lines raise ValueError when add_points_number=False."""
        bad_lines = ["name1;nb1", "name2;", "name3,", "name4, name5", "name6])"]

        for bad_line in bad_lines:
            with self.subTest(line=bad_line):
                txt_file = self.temp_path / "invalid_net.txt"
                txt_file.write_text(f"VALID_NET_1\n{bad_line}\nVALID_NET_2", encoding="utf-8")

                with self.assertRaises(ValueError):
                    self.model.load_and_clean_nets(txt_file, add_points_number=False)

    # load_and_clean_nets (add_points_number=True)

    def test_load_nets_with_points_success(self) -> None:
        """Test valid file loading with single and multiple test point numbers as strings."""
        txt_file = self.temp_path / "valid_points.txt"
        txt_file.write_text("NET_A;nb1\nNET_LONG;nb1,nb2\nNET_MULT;10,20\n", encoding="utf-8")

        points, nets = self.model.load_and_clean_nets(txt_file, add_points_number=True)

        self.assertEqual(points, {"NET_A": "nb1", "NET_LONG": "nb1,nb2", "NET_MULT": "10,20"})
        self.assertEqual(nets, ["NET_LONG", "NET_MULT", "NET_A"])

    def test_load_nets_with_points_raises_on_invalid_lines(self) -> None:
        """Test that invalid lines raise ValueError when add_points_number=True."""
        bad_lines = [
            ";nb1",
            "name2;",
            "name3,nb1",
            "[name4]; nb1",
            "name5;nb1;extra",
        ]

        for bad_line in bad_lines:
            with self.subTest(line=bad_line):
                txt_file = self.temp_path / "invalid_point_line.txt"
                txt_file.write_text(f"valid_net;nb1\n{bad_line}\nvalid_net2;nb2", encoding="utf-8")

                with self.assertRaises(ValueError):
                    self.model.load_and_clean_nets(txt_file, add_points_number=True)

    # validate_inputs

    def test_validate_inputs_both_missing(self) -> None:
        """Test validation fails when both paths are empty."""
        self.model.pdf_path = ""
        self.model.txt_path = ""
        is_valid, msg = self.model.validate_inputs()
        self.assertFalse(is_valid)
        self.assertEqual(msg, "Please select a PDF file.")

    def test_validate_inputs_txt_missing(self) -> None:
        """Test validation fails when only txt_path is missing."""
        pdf_file = self.temp_path / "doc.pdf"
        pdf_file.touch()

        self.model.pdf_path = str(pdf_file)
        self.model.txt_path = ""
        is_valid, msg = self.model.validate_inputs()
        self.assertFalse(is_valid)
        self.assertEqual(msg, "Please select a .txt file containing network names.")

    def test_validate_inputs_file_not_found(self) -> None:
        """Test validation fails when paths point to non-existent files."""
        self.model.pdf_path = str(self.temp_path / "non_existent.pdf")
        self.model.txt_path = str(self.temp_path / "dummy.txt")
        is_valid, msg = self.model.validate_inputs()
        self.assertFalse(is_valid)
        self.assertIn("PDF file not found", msg)

    def test_validate_inputs_invalid_extension(self) -> None:
        """Test validation fails on invalid extensions."""
        wrong_pdf = self.temp_path / "doc.docx"
        wrong_pdf.touch()
        txt_file = self.temp_path / "nets.txt"
        txt_file.touch()

        self.model.pdf_path = str(wrong_pdf)
        self.model.txt_path = str(txt_file)
        is_valid, msg = self.model.validate_inputs()
        self.assertFalse(is_valid)
        self.assertIn("must have a .pdf extension", msg)

    def test_validate_inputs_success(self) -> None:
        """Test validation succeeds when files exist with valid extensions."""
        pdf_file = self.temp_path / "sample.pdf"
        pdf_file.touch()
        txt_file = self.temp_path / "nets.txt"
        txt_file.touch()

        self.model.pdf_path = str(pdf_file)
        self.model.txt_path = str(txt_file)
        is_valid, msg = self.model.validate_inputs()
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

    # Helper & boundary match tests

    def test_is_valid_boundary(self) -> None:
        """Test boundary checking method with valid and invalid characters."""
        self.assertTrue(self.model.is_valid_boundary(""))
        self.assertTrue(self.model.is_valid_boundary(" "))
        self.assertTrue(self.model.is_valid_boundary("\n"))
        self.assertFalse(self.model.is_valid_boundary("A"))

    def test_is_valid_net_match(self) -> None:
        """Test net match boundary verification within word strings."""
        word = "(NET_A)"
        self.assertTrue(self.model._is_valid_net_match(word, "NET_A", 1))
        self.assertFalse(self.model._is_valid_net_match("XNET_A", "NET_A", 1))

    # Complete pipeline processing tests (process_pdf)

    def test_process_pdf_success_without_points(self) -> None:
        """Test end-to-end PDF processing without test points."""
        pdf_path = self._create_sample_pdf("test.pdf", "Signal NET_A present on board.")
        txt_path = self.temp_path / "nets.txt"
        txt_path.write_text("NET_A\nNET_B\n", encoding="utf-8")

        self.model.pdf_path = str(pdf_path)
        self.model.txt_path = str(txt_path)

        success, msg = self.model.process_pdf(add_points_number=False)
        self.assertTrue(success)
        self.assertIn("Highlighted 1 net occurrences", msg)
        self.assertIn("Warning: 1 nets were not found", msg)

        # Check that output PDF exists and has annotations
        out_pdf = self.temp_path / "test_highlighted.pdf"
        self.assertTrue(out_pdf.exists())

        doc = fitz.open(out_pdf)
        annotations = list(doc[0].annots())
        self.assertEqual(len(annotations), 1)
        doc.close()

    def test_process_pdf_success_with_points_and_labels(self) -> None:
        """Test end-to-end PDF processing with test points and string labels."""
        pdf_path = self._create_sample_pdf("test_pts.pdf", "Connection NET_A is here.")
        txt_path = self.temp_path / "nets.txt"
        txt_path.write_text("NET_A;nb1,nb2\n", encoding="utf-8")

        self.model.pdf_path = str(pdf_path)
        self.model.txt_path = str(txt_path)

        success, msg = self.model.process_pdf(add_points_number=True)
        self.assertTrue(success)
        self.assertIn("Highlighted 1 net occurrences", msg)

        # Confirm point label placement by verifying text in the generated output PDF
        out_pdf = self.temp_path / "test_pts_highlighted.pdf"
        doc = fitz.open(out_pdf)
        text = doc[0].get_text()
        self.assertIn("nb1,nb2", text)
        doc.close()

    def test_process_pdf_returns_false_on_empty_nets(self) -> None:
        """Test process_pdf returns failure when text file contains no valid nets."""
        pdf_path = self._create_sample_pdf("empty.pdf", "Sample text")
        txt_path = self.temp_path / "empty.txt"
        txt_path.write_text("\n\n", encoding="utf-8")

        self.model.pdf_path = str(pdf_path)
        self.model.txt_path = str(txt_path)

        success, msg = self.model.process_pdf()
        self.assertFalse(success)
        self.assertEqual(msg, "No valid net names found in the text file.")


if __name__ == "__main__":
    unittest.main()