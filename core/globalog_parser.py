"""Parse and validate a GlobaLog CSV export.

GlobaLog file structure:
  Line 1: load_id, name  (user ID row)
  Line 2: "id", "name"   (user data)
  Line 3: blank
  Line 4: column headers
  Line 5+: data rows
  Footer:  lines starting with '---'
"""

import pandas as pd
from pathlib import Path


REQUIRED_COLUMNS = {
    "date_of_flight", "call_sign", "departure_airport",
    "off_block", "take_off", "destination_airport",
    "landing", "on_block", "aircraft_registration",
    "airtime", "block_time", "role_on_flight", "flying_pilot",
}


class GlobaLogParseError(Exception):
    pass


def load(path: str | Path) -> pd.DataFrame:
    """Load and validate a GlobaLog CSV. Returns a cleaned DataFrame."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError as exc:
        raise GlobaLogParseError(f"Cannot read file: {exc}") from exc

    # Strip footer lines (start with '---') and trailing blank lines
    data_lines = [l for l in lines if not l.strip().startswith("---")]

    # Header is on line 4 (index 3); skip lines 0-2
    if len(data_lines) < 4:
        raise GlobaLogParseError("File is too short to be a valid GlobaLog export.")

    data_lines = data_lines[3:]  # drop user-info lines 0-2

    from io import StringIO
    try:
        df = pd.read_csv(StringIO("".join(data_lines)), dtype=str, keep_default_na=False)
    except Exception as exc:
        raise GlobaLogParseError(f"Cannot parse GlobaLog data: {exc}") from exc

    df.columns = df.columns.str.strip().str.strip('"')
    df = df.apply(lambda col: col.str.strip() if col.dtype == object else col)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise GlobaLogParseError(
            f"File does not look like a GlobaLog export.\n"
            f"Missing columns: {', '.join(sorted(missing))}"
        )

    # Parse date
    df["_date"] = pd.to_datetime(df["date_of_flight"], format="%d/%m/%Y", errors="coerce")

    # Parse timestamp columns (format: DD/MM/YYYY HH:MM)
    for col in ("off_block", "take_off", "landing", "on_block"):
        df[f"_{col}"] = pd.to_datetime(df[col], format="%d/%m/%Y %H:%M", errors="coerce")

    df["_flying_pilot"] = df["flying_pilot"].str.lower() == "yes"

    return df
