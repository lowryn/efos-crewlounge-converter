"""Main application window."""

import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import customtkinter as ctk
import pandas as pd

from core import efos_parser, globalog_parser, user_detector, converter
from config import settings
from gui.dialogs import FlightTableDialog


ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("EFOS → CrewLounge Converter")
        self.geometry("600x680")
        self.resizable(False, False)

        self.config = settings.load()
        self._result = None

        self._build_ui()

    # ------------------------------------------------------------------ #
    #  UI construction                                                     #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        pad = {"padx": 16, "pady": 4}

        # ── File inputs ──────────────────────────────────────────────────
        self._section("Input Files")

        self.efos_var = tk.StringVar()
        self._file_row("EFOS MySectors CSV:", self.efos_var,
                       self.config.get("last_efos_directory", ""),
                       self._on_efos_selected)

        self.gl_var = tk.StringVar()
        self._file_row("GlobaLog CSV:", self.gl_var,
                       self.config.get("last_globalog_directory", ""),
                       self._on_gl_selected)

        # ── Date range ───────────────────────────────────────────────────
        self._section("Date Range")

        date_frame = ctk.CTkFrame(self, fg_color="transparent")
        date_frame.pack(fill="x", **pad)

        ctk.CTkLabel(date_frame, text="From (DD/MM/YYYY):").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.date_from_var = tk.StringVar()
        ctk.CTkEntry(date_frame, textvariable=self.date_from_var, width=120).grid(row=0, column=1, padx=(0, 24))

        ctk.CTkLabel(date_frame, text="To (DD/MM/YYYY):").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.date_to_var = tk.StringVar()
        ctk.CTkEntry(date_frame, textvariable=self.date_to_var, width=120).grid(row=0, column=3)

        self.all_dates_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self, text="Process all dates (ignore range)",
            variable=self.all_dates_var,
            command=self._toggle_dates,
        ).pack(anchor="w", **pad)
        self._toggle_dates()

        # ── User settings ────────────────────────────────────────────────
        self._section("User Settings")

        self.detected_name_var = tk.StringVar(value="(load EFOS file first)")
        ctk.CTkLabel(self, textvariable=self.detected_name_var, font=("", 13, "bold")).pack(anchor="w", **pad)

        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.pack(fill="x", **pad)
        ctk.CTkLabel(name_frame, text="Name in output:").pack(side="left", padx=(0, 12))
        self.name_pref_var = tk.StringVar(value=self.config.get("self_name_preference", "SELF"))
        ctk.CTkRadioButton(name_frame, text="SELF", variable=self.name_pref_var, value="SELF").pack(side="left", padx=4)
        ctk.CTkRadioButton(name_frame, text="Actual name", variable=self.name_pref_var, value="actual").pack(side="left", padx=4)

        op_frame = ctk.CTkFrame(self, fg_color="transparent")
        op_frame.pack(fill="x", **pad)
        ctk.CTkLabel(op_frame, text="Operator:").pack(side="left", padx=(0, 12))
        self.operator_var = tk.StringVar(value=self.config.get("operator", "Jet2"))
        ctk.CTkEntry(op_frame, textvariable=self.operator_var, width=160).pack(side="left")

        # ── Output ───────────────────────────────────────────────────────
        self._section("Output")

        self.output_var = tk.StringVar()
        self._file_row("Output file:", self.output_var,
                       self.config.get("last_output_directory", ""),
                       self._browse_output, save=True)

        fmt_frame = ctk.CTkFrame(self, fg_color="transparent")
        fmt_frame.pack(fill="x", **pad)
        ctk.CTkLabel(fmt_frame, text="Format:").pack(side="left", padx=(0, 12))
        self.format_var = tk.StringVar(value=self.config.get("output_format", "csv"))
        ctk.CTkOptionMenu(
            fmt_frame,
            variable=self.format_var,
            values=["csv", "xlsx"],
            width=100,
        ).pack(side="left")

        # ── Convert button ───────────────────────────────────────────────
        ctk.CTkButton(
            self, text="Convert", height=40, font=("", 15, "bold"),
            command=self._start_conversion,
        ).pack(fill="x", padx=16, pady=12)

        # ── Status ───────────────────────────────────────────────────────
        self._section("Status")

        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(fill="x", padx=16, pady=4)
        self.progress_bar.set(0)

        self.status_var = tk.StringVar(value="Ready.")
        ctk.CTkLabel(self, textvariable=self.status_var).pack(anchor="w", padx=16)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=4)

        self.skipped_btn = ctk.CTkButton(
            btn_frame, text="View Skipped Flights",
            command=self._show_skipped, state="disabled",
        )
        self.skipped_btn.pack(side="left", padx=(0, 8))

        self.warnings_btn = ctk.CTkButton(
            btn_frame, text="View Warnings",
            command=self._show_warnings, state="disabled",
        )
        self.warnings_btn.pack(side="left")

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _section(self, label: str):
        ctk.CTkLabel(self, text=f" {label} ", font=("", 11), fg_color=("gray85", "gray25"),
                     corner_radius=4).pack(fill="x", padx=16, pady=(10, 2))

    def _file_row(self, label: str, var: tk.StringVar, initial_dir: str,
                  callback, save: bool = False):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=16, pady=2)
        ctk.CTkLabel(frame, text=label, width=160, anchor="w").pack(side="left")
        ctk.CTkEntry(frame, textvariable=var, width=300).pack(side="left", padx=4)
        ctk.CTkButton(frame, text="Browse…", width=80,
                      command=lambda: callback(initial_dir, save)).pack(side="left")

    def _toggle_dates(self):
        state = "disabled" if self.all_dates_var.get() else "normal"
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                for w in child.winfo_children():
                    if isinstance(w, ctk.CTkEntry) and w.cget("textvariable") in (
                        str(self.date_from_var), str(self.date_to_var)
                    ):
                        w.configure(state=state)

    # ------------------------------------------------------------------ #
    #  File browsing                                                       #
    # ------------------------------------------------------------------ #

    def _on_efos_selected(self, initial_dir, _save):
        path = filedialog.askopenfilename(
            initialdir=initial_dir or Path.home(),
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        self.efos_var.set(path)
        self.config["last_efos_directory"] = str(Path(path).parent)
        self._auto_detect_user(path)

    def _on_gl_selected(self, initial_dir, _save):
        path = filedialog.askopenfilename(
            initialdir=initial_dir or Path.home(),
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        self.gl_var.set(path)
        self.config["last_globalog_directory"] = str(Path(path).parent)

    def _browse_output(self, initial_dir, _save):
        fmt = self.format_var.get()
        ext = ".xlsx" if fmt == "xlsx" else ".csv"
        path = filedialog.asksaveasfilename(
            initialdir=initial_dir or Path.home(),
            defaultextension=ext,
            filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.output_var.set(path)
            self.config["last_output_directory"] = str(Path(path).parent)

    # ------------------------------------------------------------------ #
    #  User auto-detection                                                 #
    # ------------------------------------------------------------------ #

    def _auto_detect_user(self, efos_path: str):
        try:
            df = efos_parser.load(efos_path)
            name = user_detector.detect(df)
            if name:
                self._detected_user = name
                self.detected_name_var.set(f"Detected user: {name}")
            else:
                self._detected_user = None
                self.detected_name_var.set("Could not auto-detect user — check file")
        except efos_parser.EFOSParseError as e:
            messagebox.showerror("EFOS File Error", str(e))
            self._detected_user = None

    # ------------------------------------------------------------------ #
    #  Conversion                                                          #
    # ------------------------------------------------------------------ #

    def _start_conversion(self):
        efos_path = self.efos_var.get().strip()
        gl_path = self.gl_var.get().strip()
        output_path = self.output_var.get().strip()

        if not efos_path or not gl_path:
            messagebox.showerror("Missing files", "Please select both EFOS and GlobaLog files.")
            return
        if not output_path:
            messagebox.showerror("Missing output", "Please specify an output file path.")
            return
        if not getattr(self, "_detected_user", None):
            messagebox.showerror("No user detected", "Load an EFOS file first so the user can be detected.")
            return

        date_from = date_to = None
        if not self.all_dates_var.get():
            try:
                if self.date_from_var.get().strip():
                    date_from = pd.to_datetime(self.date_from_var.get().strip(), format="%d/%m/%Y")
                if self.date_to_var.get().strip():
                    date_to = pd.to_datetime(self.date_to_var.get().strip(), format="%d/%m/%Y")
            except ValueError:
                messagebox.showerror("Date error", "Dates must be in DD/MM/YYYY format.")
                return

        user_name = self._detected_user
        self_label = "SELF" if self.name_pref_var.get() == "SELF" else user_name

        self._save_config()
        self.progress_bar.set(0)
        self.status_var.set("Converting…")
        self.skipped_btn.configure(state="disabled")
        self.warnings_btn.configure(state="disabled")

        def run():
            def progress(done, total):
                self.after(0, lambda: self.progress_bar.set(done / total))

            try:
                result = converter.run(
                    efos_path=efos_path,
                    globalog_path=gl_path,
                    output_path=output_path,
                    output_format=self.format_var.get(),
                    user_name=user_name,
                    self_label=self_label,
                    operator=self.operator_var.get().strip(),
                    date_from=date_from,
                    date_to=date_to,
                    progress_cb=progress,
                )
                self.after(0, lambda: self._on_done(result))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Conversion failed", str(exc)))
                self.after(0, lambda: self.status_var.set("Error — see dialog."))

        threading.Thread(target=run, daemon=True).start()

    def _on_done(self, result):
        self._result = result
        self.progress_bar.set(1)
        self.status_var.set(
            f"Done — {result.processed} flights processed, "
            f"{len(result.skipped)} skipped, "
            f"{len(result.warnings)} warning(s)."
        )
        if result.skipped:
            self.skipped_btn.configure(state="normal")
        if result.warnings:
            self.warnings_btn.configure(state="normal")

    # ------------------------------------------------------------------ #
    #  Result dialogs                                                      #
    # ------------------------------------------------------------------ #

    def _show_skipped(self):
        if not self._result:
            return
        FlightTableDialog(
            self,
            title="Skipped Flights",
            rows=self._result.skipped,
            columns=["Flight No.", "Date", "Reason"],
        )

    def _show_warnings(self):
        if not self._result:
            return
        FlightTableDialog(
            self,
            title="Warnings",
            rows=self._result.warnings,
            columns=["Flight No.", "Date", "Warning"],
        )

    # ------------------------------------------------------------------ #
    #  Config persistence                                                  #
    # ------------------------------------------------------------------ #

    def _save_config(self):
        self.config["self_name_preference"] = self.name_pref_var.get()
        self.config["operator"] = self.operator_var.get().strip()
        self.config["output_format"] = self.format_var.get()
        settings.save(self.config)
