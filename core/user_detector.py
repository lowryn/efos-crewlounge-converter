"""Detect the user's name from EFOS data.

The user is the pilot whose name appears in Left-Hand Seat Pilot or
Right-Hand Seat Pilot on every row. We find the name with the highest
frequency across both columns combined.
"""

import pandas as pd
from collections import Counter


def detect(df: pd.DataFrame) -> str | None:
    """Return the detected user name, or None if detection fails."""
    counts: Counter = Counter()
    for col in ("Left-Hand Seat Pilot", "Right-Hand Seat Pilot"):
        if col in df.columns:
            counts.update(df[col].dropna().str.strip().loc[lambda s: s != ""].tolist())

    if not counts:
        return None

    # The user appears on (nearly) every flight
    total_rows = len(df)
    threshold = total_rows * 0.8  # present on ≥80% of rows
    candidates = [name for name, count in counts.items() if count >= threshold]

    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        # Return the most frequent
        return max(candidates, key=lambda n: counts[n])
    return None
