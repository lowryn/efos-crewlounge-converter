"""Parse and validate the EFOS MySectors CSV export."""

import csv
import pandas as pd
from pathlib import Path


REQUIRED_COLUMNS = {
    "Date", "Status", "Flight No.", "STD", "STA", "ATD", "ATA",
    "Airborne", "Landing", "From", "To", "A/C Type", "A/C Reg",
    "Depart Airfield ICAO", "Arrive Airfield ICAO",
    "Take-Off Pilot", "Landing Pilot",
    "DeadHeading", "PIC", "Captain", "FO", "Intructor",
    "Operating Crew", "ActualFlightTime",
    "Left-Hand Seat Pilot", "Right-Hand Seat Pilot",
}


class EFOSParseError(Exception):
    pass


def load(path: str | Path) -> pd.DataFrame:
    """Load and validate an EFOS MySectors CSV. Returns a cleaned DataFrame."""
    try:
        # EFOS CSVs have a trailing empty column on every data row but not the header.
        # Detect the header column count and read only that many columns.
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            n_cols = len(next(csv.reader(f)))
        df = pd.read_csv(
            path, dtype=str, keep_default_na=False,
            usecols=range(n_cols),
        )
    except Exception as exc:
        raise EFOSParseError(f"Cannot read file: {exc}") from exc

    df.columns = df.columns.str.strip()
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise EFOSParseError(
            f"File does not look like an EFOS MySectors export.\n"
            f"Missing columns: {', '.join(sorted(missing))}"
        )

    # Strip whitespace from all string values
    df = df.apply(lambda col: col.str.strip() if col.dtype == object else col)

    # Parse STD and STA (always populated) – used as authoritative flight date
    df["_STD"] = pd.to_datetime(df["STD"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    df["_STA"] = pd.to_datetime(df["STA"], format="%d/%m/%Y %H:%M:%S", errors="coerce")

    bad_std = df["_STD"].isna().sum()
    if bad_std > 0:
        raise EFOSParseError(
            f"{bad_std} rows have an unparseable STD value. "
            "The file may be corrupted or in an unexpected format."
        )

    # Parse optional actual time columns (may be empty)
    for col in ("ATD", "ATA", "Airborne", "Landing"):
        df[f"_{col}"] = pd.to_datetime(df[col], format="%d/%m/%Y %H:%M:%S", errors="coerce")

    # Boolean columns – treat any truthy string as True
    for col in ("DeadHeading", "PIC", "Captain", "FO", "Intructor"):
        df[f"_{col}"] = df[col].str.lower() == "true"

    return df
