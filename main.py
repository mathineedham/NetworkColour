from src.controller import HighlighterController
from src.model import HighlighterModel
from src.view import HighlighterView


class Application:
    """Main application launcher class."""
    def __init__(self):
        self.model = HighlighterModel()
        self.view = HighlighterView()
        self.controller = HighlighterController(self.model, self.view)

    def run(self) -> None:
        self.view.mainloop()


if __name__ == "__main__":
    app = Application()
    app.run()