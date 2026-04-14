"""Orchestrate the full conversion pipeline.

Ties together: parse → merge → filter → role → transform → write.
"""

import pandas as pd
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable

from core import efos_parser, globalog_parser, merger, role_engine, transformer
from config.defaults import OUTPUT_COLUMNS


@dataclass
class ConversionResult:
    processed: int = 0
    skipped: list = field(default_factory=list)   # list of (flight_no, date, reason)
    warnings: list = field(default_factory=list)  # list of (flight_no, date, message)


def run(
    efos_path: str,
    globalog_path: str,
    output_path: str,
    output_format: str,          # "csv" or "xlsx"
    user_name: str,
    self_label: str,             # "SELF" or actual name
    operator: str,
    date_from: pd.Timestamp | None,
    date_to: pd.Timestamp | None,
    progress_cb: Callable[[int, int], None] | None = None,
) -> ConversionResult:
    result = ConversionResult()

    # 1. Parse inputs
    efos_df = efos_parser.load(efos_path)
    gl_df = globalog_parser.load(globalog_path)

    # 2. Date filter
    if date_from is not None:
        efos_df = efos_df[efos_df["_STD"] >= date_from]
    if date_to is not None:
        efos_df = efos_df[efos_df["_STD"] <= date_to + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)]

    if efos_df.empty:
        return result

    # 3. Merge and sort chronologically
    merged = merger.merge(efos_df, gl_df)
    merged = merged.sort_values("_STD").reset_index(drop=True)

    # 4. Process rows
    output_rows = []
    total = len(merged)

    for idx, (_, row) in enumerate(merged.iterrows()):
        row_dict = row.to_dict()

        role = role_engine.compute(row_dict, user_name)

        flight_id = str(row_dict.get("Flight No.", "")).strip()
        std = row_dict.get("_STD")
        date_str = std.strftime("%Y-%m-%d") if std and not pd.isnull(std) else ""

        if role["skip"]:
            result.skipped.append((flight_id, date_str, role["skip_reason"]))
        else:
            if role.get("skip_reason", "").startswith("WARNING"):
                result.warnings.append((flight_id, date_str, role["skip_reason"]))

            # Attach resolved total for transformer
            role["_total_mins"] = role_engine._resolve_total(row_dict, transformer._efos_has_times(row_dict))

            out = transformer.transform_row(row_dict, role, user_name, self_label, operator)
            if out:
                output_rows.append(out)
                result.processed += 1

        if progress_cb:
            progress_cb(idx + 1, total)

    # 5. Write output
    if output_rows:
        out_df = pd.DataFrame(output_rows, columns=OUTPUT_COLUMNS)
        _write(out_df, output_path, output_format)

    return result


def _write(df: pd.DataFrame, path: str, fmt: str) -> None:
    p = Path(path)
    if fmt == "xlsx":
        p = p.with_suffix(".xlsx")
        df.to_excel(p, index=False)
    else:
        p = p.with_suffix(".csv")
        df.to_csv(p, index=False, sep=";")
