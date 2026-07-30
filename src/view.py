import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.scrolledtext import ScrolledText
from typing import List, Optional, Tuple
from .information_panel import InfoWindow


class HighlighterView(tk.Tk):
    """!
    @brief Manages GUI window layout, widgets, and user visual output.
    """

    def __init__(self) -> None:
        """!
        @brief Initializes the main application window and configures default window dimensions.
        """
        super().__init__()
        self.title("Network names highlighter")
        self.geometry("600x480")
        self.minsize(500, 400)

        self._init_ui()

    def _init_ui(self) -> None:
        """!
        @brief Initializes and arranges all primary GUI frames and component groups.
        """
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self._create_file_selection_frame(main_frame)
        self._create_controls_frame(main_frame)
        self._create_log_frame(main_frame)

    def _create_file_selection_frame(self, parent: ttk.Frame) -> None:
        """!
        @brief Creates the file selector inputs for the target PDF and network text file.

        @param parent Parent Tkinter widget container.
        """
        # Create a container frame for the LabelFrame title + info icon
        title_container = ttk.Frame(parent)
        
        ttk.Label(
            title_container, 
            text="Files Selection", 
            font=("TkDefaultFont", 9, "bold")
        ).pack(side=tk.LEFT)

        # Subtle, modern circular icon button
        self.info_btn = tk.Label(
            title_container,
            text=" ⓘ ",
            font=("TkDefaultFont", 10, "bold"),
            foreground="#0078d4",
            cursor="hand2"
        )
        self.info_btn.pack(side=tk.LEFT)

        # Pass title_container directly as the LabelFrame's labelwidget
        files_frame = ttk.LabelFrame(parent, labelwidget=title_container, padding="10")
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

    def show_info_window(self) -> InfoWindow:
        """!
        @brief Spawns and returns the file format info window.
        """
        return InfoWindow(self)

    def _create_controls_frame(self, parent: ttk.Frame) -> None:
        """!
        @brief Creates action controls including the option checkbox and execution button.

        @param parent Parent Tkinter widget container.
        """
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        self.test_points_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            controls_frame,
            text="with test point numbers",
            variable=self.test_points_var,
        ).pack(side=tk.LEFT, padx=(0, 15))

        self.go_btn = ttk.Button(controls_frame, text="Go")
        self.go_btn.pack(side=tk.LEFT)

    def _create_log_frame(self, parent: ttk.Frame) -> None:
        """!
        @brief Creates the scrollable logging console and configures text tags.

        @param parent Parent Tkinter widget container.
        """
        log_title = ttk.Label(
            parent,
            text=" Status / Error Log ",
            font=("TkDefaultFont", 9, "bold")
        )

        log_frame = ttk.LabelFrame(
            parent, labelwidget=log_title, padding="5"
        )
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_area = ScrolledText(log_frame, state="disabled", height=10)
        self.log_area.pack(fill=tk.BOTH, expand=True)

        self.log_area.tag_config("error", foreground="red")
        self.log_area.tag_config("info", foreground="black")

    def select_file(
        self, title: str, filetypes: List[Tuple[str, str]]
    ) -> Optional[str]:
        """!
        @brief Displays a native system file selection dialog and returns the chosen file path.

        @param title The title bar text displayed on the file picker dialog box.
        @param filetypes A list of permitted file extension tuples, e.g., [("PDF files", "*.pdf")].
        @return The absolute string path of the selected file, or None if cancelled.
        """
        return filedialog.askopenfilename(title=title, filetypes=filetypes) or None

    def log_message(self, message: str, is_error: bool = False) -> None:
        """!
        @brief Appends a status or error message to the read-only log window.

        @param message The text content to append to the log console.
        @param is_error If True, prefixes entry with '[ERROR]' in red text; otherwise '[INFO]'. Defaults to False.
        """
        self.log_area.config(state="normal")

        prefix = "[ERROR] " if is_error else "[INFO] "
        tag = "error" if is_error else "info"

        self.log_area.insert(tk.END, prefix + message + "\n", tag)
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")