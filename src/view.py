import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.scrolledtext import ScrolledText
from typing import List, Optional, Tuple


class HighlighterView(tk.Tk):
    """Manages GUI window layout, widgets, and user visual output."""

    def __init__(self):
        super().__init__()
        self.title("Network names highlighter")
        self.geometry("600x480")
        self.minsize(500, 400)

        self._init_ui()

    def _init_ui(self) -> None:
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        files_frame = ttk.LabelFrame(main_frame, text=" Files ", padding="10")
        files_frame.pack(fill=tk.X, pady=(0, 10))
        files_frame.columnconfigure(1, weight=1)

        ttk.Label(files_frame, text="PDF File:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.pdf_var = tk.StringVar()
        ttk.Entry(files_frame, textvariable=self.pdf_var, width=50).grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.EW
        )
        self.browse_pdf_btn = ttk.Button(files_frame, text="Browse...")
        self.browse_pdf_btn.grid(row=0, column=2, pady=5)

        ttk.Label(files_frame, text="Network Names (.txt):").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.txt_var = tk.StringVar()
        ttk.Entry(files_frame, textvariable=self.txt_var, width=50).grid(
            row=1, column=1, padx=5, pady=5, sticky=tk.EW
        )
        self.browse_txt_btn = ttk.Button(files_frame, text="Browse...")
        self.browse_txt_btn.grid(row=1, column=2, pady=5)

        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        self.test_points_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            controls_frame,
            text="with test point numbers",
            variable=self.test_points_var,
        ).pack(side=tk.LEFT, padx=(0, 15))

        self.go_btn = ttk.Button(controls_frame, text="Go")
        self.go_btn.pack(side=tk.LEFT)

        log_frame = ttk.LabelFrame(
            main_frame, text=" Status / Error Log ", padding="5"
        )
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_area = ScrolledText(log_frame, state="disabled", height=10)
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def select_file(
        self, title: str, filetypes: List[Tuple[str, str]]
    ) -> Optional[str]:
        return filedialog.askopenfilename(title=title, filetypes=filetypes) or None

    def log_message(self, message: str, is_error: bool = False) -> None:
        self.log_area.config(state="normal")
        prefix = "[ERROR] " if is_error else "[INFO] "
        self.log_area.insert(tk.END, prefix + message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")