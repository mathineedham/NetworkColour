from .model import HighlighterModel
from .view import HighlighterView


class HighlighterController:
    """Coordinates events between the HighlighterView and HighlighterModel."""

    def __init__(self, model: HighlighterModel, view: HighlighterView):
        self.model = model
        self.view = view

        self._bind_events()
        self.view.log_message("System initialized. Select files and click 'Go'.")

    def _bind_events(self) -> None:
        self.view.browse_pdf_btn.config(command=self.handle_browse_pdf)
        self.view.browse_txt_btn.config(command=self.handle_browse_txt)
        self.view.go_btn.config(command=self.handle_go)

    def handle_browse_pdf(self) -> None:
        path = self.view.select_file(
            "Select PDF file", [("PDF files", "*.pdf")]
        )
        if path:
            self.model.pdf_path = path
            self.view.pdf_var.set(path)

    def handle_browse_txt(self) -> None:
        path = self.view.select_file(
            "Select Text file", [("Text files", "*.txt")]
        )
        if path:
            self.model.txt_path = path
            self.view.txt_var.set(path)

    def handle_go(self) -> None:
        self.model.pdf_path = self.view.pdf_var.get().strip()
        self.model.txt_path = self.view.txt_var.get().strip()
        self.model.include_test_points = self.view.test_points_var.get()

        is_valid, err_msg = self.model.validate_inputs()
        if not is_valid:
            self.view.log_message(err_msg, is_error=True)
            return

        self.view.log_message(
            f"Starting process...\n PDF: {self.model.pdf_path}\n"
            f" TXT: {self.model.txt_path}\n"
            f" Include Test Points: {self.model.include_test_points}"
        )

        try:
            success, result_msg = self.model.process_pdf()
            self.view.log_message(result_msg, is_error=not success)
        except Exception as e:
            self.view.log_message(
                f"An error occurred: {str(e)}", is_error=True
            )