import unittest
from pathlib import Path
import tempfile
import os

# Import your model class
from src.model import HighlighterModel


class TestHighlighterModel(unittest.TestCase):

    def setUp(self):
        """Runs before each test method."""
        self.model = HighlighterModel()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Runs after each test method."""
        self.temp_dir.cleanup()

    #  Tests for 'load_and_clean_nets' (add_points_number=False) 

    def test_load_nets_without_points_success(self):
        """Test valid file loading without point numbers."""
        txt_file = self.temp_path / "valid_nets.txt"
        txt_file.write_text("NET_A\nNET_LONG_NAME\nNET_B\n", encoding="utf-8")

        points, nets = self.model.load_and_clean_nets(txt_file, add_points_number=False)

        self.assertEqual(points, {})
        self.assertEqual(nets, ["NET_LONG_NAME", "NET_A", "NET_B"])

    def test_load_nets_without_points_raises_on_invalid_lines(self):
        """Test that invalid lines raise ValueError when add_points_number=False."""
        bad_lines = [
            "name1;nb1",
            "name2;",
            "name3,",
            "name4, name5",
            "name6])",
        ]

        for bad_line in bad_lines:
            with self.subTest(line=bad_line):
                txt_file = self.temp_path / "invalid_net.txt"
                txt_file.write_text(f"VALID_NET_1\n{bad_line}\nVALID_NET_2", encoding="utf-8")

                with self.assertRaises(ValueError):
                    self.model.load_and_clean_nets(txt_file, add_points_number=False)

    #  Tests for 'load_and_clean_nets' (add_points_number=True) 

    def test_load_nets_with_points_success(self):
        """Test valid file loading with test point numbers."""
        txt_file = self.temp_path / "valid_points.txt"
        txt_file.write_text("NET_A;10\nNET_LONG;20\n", encoding="utf-8")

        points, nets = self.model.load_and_clean_nets(txt_file, add_points_number=True)

        self.assertEqual(points, {"NET_A": 10, "NET_LONG": 20})
        self.assertEqual(nets, ["NET_LONG", "NET_A"])

    def test_load_nets_with_points_raises_on_invalid_lines(self):
        """Test that invalid lines raise ValueError when add_points_number=True."""
        bad_lines = [
            ";10",                 # Missing net name
            "name2;",              # Missing point number
            "name3,10",            # Missing ';' separator
            "[name4]; 10",         # Invalid boundary character '[' in net name
            "name5;10;extra",      # Extra ';' causes invalid net name 'name5;10' or non-digit point
            "name6;abc",           # Point number is not a digit
            "name7;-2",            # Point number is negative
        ]

        for bad_line in bad_lines:
            with self.subTest(line=bad_line):
                txt_file = self.temp_path / "invalid_point_line.txt"
                txt_file.write_text(f"valid_net;100\n{bad_line}\nvalid_net2;200", encoding="utf-8")

                with self.assertRaises(ValueError):
                    self.model.load_and_clean_nets(txt_file, add_points_number=True)


    def test_validate_inputs_empty(self):
        """Test validation fails when file paths are missing."""
        is_valid, msg = self.model.validate_inputs()
        self.assertFalse(is_valid)
        self.assertIn("Please select", msg)


if __name__ == "__main__":
    unittest.main()