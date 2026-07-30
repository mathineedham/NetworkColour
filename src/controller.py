import threading
from .model import HighlighterModel
from .view import HighlighterView


class HighlighterController:
    """!
    @brief Coordinates user interactions from HighlighterView with processing logic in HighlighterModel.
    """

    def __init__(self, model: HighlighterModel, view: HighlighterView) -> None:
        """!
        @brief Binds GUI component listeners and initializes default status log.

        @param model Reference to the application HighlighterModel instance.
        @param view Reference to the application HighlighterView instance.
        """
        self.model = model
        self.view = view

        self._bind_events()
        self.view.log_message("System initialized. Select files and click 'Go'.")

    def _bind_events(self) -> None:
        """!
        @brief Registers controller handler functions to view button commands.
        """
        self.view.browse_pdf_btn.config(command=self.handle_browse_pdf)
        self.view.browse_txt_btn.config(command=self.handle_browse_txt)
        self.view.go_btn.config(command=self.handle_go)
        self.view.info_btn.bind("<Button-1>", lambda event: self.handle_show_info())
    
    def handle_browse_pdf(self) -> None:
        """!
        @brief Opens the PDF file dialog and updates the model and view state with the selection.
        """
        path = self.view.select_file(
            "Select PDF file", [("PDF files", "*.pdf")]
        )
        if path:
            self.model.pdf_path = path
            self.view.pdf_var.set(path)

    def handle_browse_txt(self) -> None:
        """!
        @brief Opens the TXT file dialog and updates the model and view state with the selection.
        """
        path = self.view.select_file(
            "Select Text file", [("Text files", "*.txt")]
        )
        if path:
            self.model.txt_path = path
            self.view.txt_var.set(path)

    def handle_go(self) -> None:
        """!
        @brief Validates inputs and runs the PDF processing routine in a non-blocking background thread.
        """
        self.model.pdf_path = self.view.pdf_var.get().strip()
        self.model.txt_path = self.view.txt_var.get().strip()
        self.model.include_test_points = self.view.test_points_var.get()

        is_valid, err_msg = self.model.validate_inputs()
        if not is_valid:
            self.view.log_message(err_msg, is_error=True)
            return

        self.view.go_btn.config(state="disabled")
        self.view.log_message(f"Processing PDF: {self.model.pdf_path}...")

        def run_process():
            try:
                success, result_msg = self.model.process_pdf(add_points_number=self.model.include_test_points)
                self.view.after(
                    0, lambda: self.view.log_message(result_msg, is_error=not success)
                )
            except Exception as e:
                error_msg = f"An error occurred: {str(e)}"
                self.view.after(0, lambda: self.view.log_message(error_msg, is_error=True))
            finally:
                self.view.after(0, lambda: self.view.go_btn.config(state="normal"))

        threading.Thread(target=run_process, daemon=True).start()

    def handle_show_info(self) -> None:
        """!
        @brief Handles user clicking the info button by triggering the view popup.
        """
        info_win = self.view.show_info_window()