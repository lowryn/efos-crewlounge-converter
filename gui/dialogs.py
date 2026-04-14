"""Popup dialogs for skipped flights and warnings."""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk


class FlightTableDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, rows: list[tuple], columns: list[str]):
        super().__init__(parent)
        self.title(title)
        self.geometry("700x400")
        self.resizable(True, True)
        self.grab_set()

        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
        )
        vsb.configure(command=tree.yview)
        hsb.configure(command=tree.xview)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=180, minwidth=80)

        for row in rows:
            tree.insert("", "end", values=row)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        ctk.CTkButton(self, text="Close", command=self.destroy).pack(pady=(0, 10))
