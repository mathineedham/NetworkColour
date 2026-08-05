import tkinter as tk
from tkinter import ttk

# Pastel Palette Definitions
GREEN_BG = "#E8F5E9"
GREEN_FG = "#2E7D32"
GREEN_BORDER = "#A5D6A7"

RED_BG = "#FFEBEE"
RED_FG = "#C62828"
RED_BORDER = "#EF9A9A"


class InfoWindow(tk.Toplevel):
    """!
    @brief Pop-up window displaying side-by-side valid and invalid text file examples.
    """

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self.title("File Format Requirements")
        self.geometry("680x520")
        self.minsize(620, 500)
        self.transient(parent)

        self._init_ui()

    def _init_ui(self) -> None:
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Section 1: Without test point numbers
        self._create_section(
            parent=main_frame,
            title="Without Test Point Numbers",
            good_text="name1\nname2\nname3",
            bad_text="name1;nb1\nname2;\nname3,\nname4, name5\nname6])",
        )

        # Section 2: With test point numbers
        self._create_section(
            parent=main_frame,
            title="With Test Point Numbers",
            good_text="name1;nb1\nname2;nb1,nb2\nname3;10,20,30",    
            bad_text=";nb1\nname2;\nname3,10\n[name4]; nb1\nname5;nb1;extra",      
        )

        # Section 3: Notes at the bottom
        self._create_notes_section(
            parent=main_frame,
        )

    def _create_section(
        self, parent: ttk.Frame, title: str, good_text: str, bad_text: str
    ) -> None:
        """!
        @brief Builds a single section containing one good and one bad code snippet card side-by-side.
        """
        section_title = ttk.Label(
            parent, text=f" {title} ", font=("TkDefaultFont", 9, "bold")
        )
        frame = ttk.LabelFrame(parent, labelwidget=section_title, padding="10")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        # Left Column: Valid Example
        left_col = ttk.Frame(frame)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        ttk.Label(
            left_col,
            text="✔ Valid Format",
            font=("TkDefaultFont", 8, "bold"),
            foreground=GREEN_FG,
        ).pack(anchor="w", pady=(0, 2))

        self._create_card(
            parent=left_col,
            text=good_text,
            bg=GREEN_BG,
            fg=GREEN_FG,
            border=GREEN_BORDER,
        )

        right_col = ttk.Frame(frame)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        ttk.Label(
            right_col,
            text="✖ Invalid Formats",
            font=("TkDefaultFont", 8, "bold"),
            foreground=RED_FG,
        ).pack(anchor="w", pady=(0, 2))

        self._create_card(
            parent=right_col,
            text=bad_text,
            bg=RED_BG,
            fg=RED_FG,
            border=RED_BORDER,
        )

    def _create_notes_section(self, parent: ttk.Frame) -> None:
        """!
        @brief Creates a bottom notes section for user guidance and file rules.
        """
        section_title = ttk.Label(
            parent, text=" Important Formatting & Operational Rules ", font=("TkDefaultFont", 9, "bold")
        )
        notes_frame = ttk.LabelFrame(parent, labelwidget=section_title, padding="10")
        notes_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))

        notes = [
            "1. Case Sensitivity: Matching is exact. 'aBc' will NOT match 'ABC' in the PDF.",
            "2. Special Characters: Network names cannot contain spaces, brackets, or punctuation: ( ) [ ] { } < > \" , ;",
            "3. Active-Low Signals (~ Prefix): Prefixing a net name with '~' (e.g., ~RESET) will only match nets that have a physical line (overline) drawn above them in the PDF.",
            "4. Output File: A new PDF named '<original_name>_highlighted.pdf' will be saved in the same directory as your source PDF.",
            ]

        for idx, note in enumerate(notes):
            lbl = ttk.Label(
                notes_frame,
                text=note,
                font=("TkDefaultFont", 8),
                wraplength=540,
                justify="left",
            )
            lbl.pack(anchor="w", pady=(0, 3) if idx < len(notes) - 1 else 0)
        
    @staticmethod
    def _create_card(
        parent: ttk.Widget, text: str, bg: str, fg: str, border: str
    ) -> tk.Frame:
        """!
        @brief Helper function to construct styled pastel text boxes for code previews.
        """
        outer_box = tk.Frame(parent, bg=border, bd=1, relief="flat")
        outer_box.pack(fill=tk.BOTH, expand=True)

        inner_box = tk.Label(
            outer_box,
            text=text,
            font=("Consolas", 9),
            bg=bg,
            fg=fg,
            justify="left",
            anchor="nw",
            padx=10,
            pady=8,
        )
        inner_box.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        return outer_box