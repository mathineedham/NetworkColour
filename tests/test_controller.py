"""!
@file test_controller.py
@brief Unit test suite for HighlighterController using unittest and mock objects.
"""

import unittest
from unittest.mock import MagicMock, patch
from src.controller import HighlighterController


class TestHighlighterController(unittest.TestCase):
    """!
    @brief Test cases covering controller event handling, model-view interaction, and thread execution.
    """

    def setUp(self) -> None:
        """!
        @brief Instantiates mock objects for Model and View, initializes the Controller, and resets mock call histories.
        """
        self.mock_model = MagicMock()
        self.mock_view = MagicMock()

        # Set default return values for StringVars and UI methods
        self.mock_view.pdf_var.get.return_value = "C:/test.pdf"
        self.mock_view.txt_var.get.return_value = "C:/nets.txt"
        self.mock_view.test_points_var.get.return_value = False
        self.mock_view.get_selected_rgb_normalized.return_value = (0.0, 1.0, 0.0)

        # Initialize controller with mocked dependencies
        self.controller = HighlighterController(self.mock_model, self.mock_view)

        # Clear initial call history logged during controller.__init__()
        self.mock_view.reset_mock()

    def test_init_logs_system_ready(self) -> None:
        """!
        @brief Verifies that initializing the controller logs the default status message.
        """
        fresh_view = MagicMock()
        HighlighterController(self.mock_model, fresh_view)
        fresh_view.log_message.assert_called_with(
            "System initialized. Select files and click 'Go'."
        )

    def test_handle_browse_pdf_user_selects_file(self) -> None:
        """!
        @brief Verifies PDF browsing updates model path and view StringVar upon valid selection.
        """
        self.mock_view.select_file.return_value = "/path/to/doc.pdf"
        self.controller.handle_browse_pdf()

        self.assertEqual(self.mock_model.pdf_path, "/path/to/doc.pdf")
        self.mock_view.pdf_var.set.assert_called_once_with("/path/to/doc.pdf")

    def test_handle_browse_pdf_user_cancels(self) -> None:
        """!
        @brief Verifies PDF browsing makes no updates when dialog is cancelled.
        """
        self.mock_view.select_file.return_value = None
        self.controller.handle_browse_pdf()

        self.mock_view.pdf_var.set.assert_not_called()

    def test_handle_browse_txt_user_selects_file(self) -> None:
        """!
        @brief Verifies text file browsing updates model path and view StringVar upon selection.
        """
        self.mock_view.select_file.return_value = "/path/to/nets.txt"
        self.controller.handle_browse_txt()

        self.assertEqual(self.mock_model.txt_path, "/path/to/nets.txt")
        self.mock_view.txt_var.set.assert_called_once_with("/path/to/nets.txt")

    def test_handle_go_invalid_input(self) -> None:
        """!
        @brief Verifies validation failures abort execution and display error message in log.
        """
        self.mock_model.validate_inputs.return_value = (False, "PDF not found")
        self.controller.handle_go()

        self.mock_view.log_message.assert_called_once_with("PDF not found", is_error=True)
        self.mock_view.go_btn.config.assert_not_called()

    @patch("threading.Thread")
    def test_handle_go_starts_thread_on_valid_input(self, mock_thread_class: MagicMock) -> None:
        """!
        @brief Verifies valid inputs disable the Go button and launch background execution thread.

        @param mock_thread_class Mocked threading.Thread object injected by patch.
        """
        self.mock_model.validate_inputs.return_value = (True, "")

        self.controller.handle_go()

        self.mock_view.go_btn.config.assert_called_with(state="disabled")
        mock_thread_class.assert_called_once()
        mock_thread_class.return_value.start.assert_called_once()

    def test_handle_show_info(self) -> None:
        """!
        @brief Verifies clicking info trigger calls view popup generator.
        """
        self.controller.handle_show_info()
        self.mock_view.show_info_window.assert_called_once()

if __name__ == "__main__":
    unittest.main()