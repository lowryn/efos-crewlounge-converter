"""Determine pilot role and function times for each flight.

Returns a dict of function-time fields and PF flag for a single row.
All times are returned as integer minutes.
"""


def _hhmm_to_minutes(value: str) -> int | None:
    """Convert 'H:MM' or 'HH:MM' string to total minutes. Returns None on failure."""
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    if ":" not in value:
        return None
    parts = value.split(":")
    try:
        return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, IndexError):
        return None


def compute(row: dict, user_name: str) -> dict:
    """
    Args:
        row:       dict-like row from the merged DataFrame
        user_name: the detected user name (used to check Landing Pilot)

    Returns dict with keys:
        time_pic, time_picus, time_sic, time_instructor (int minutes, 0 if not applicable)
        pf (bool)
        skip (bool) — True if this flight should be excluded from output
        skip_reason (str) — human-readable reason if skip=True
    """
    result = {
        "time_pic": 0,
        "time_picus": 0,
        "time_sic": 0,
        "time_instructor": 0,
        "pf": False,
        "skip": False,
        "skip_reason": "",
    }

    # --- Deadhead: skip entirely ---
    if str(row.get("DeadHeading", "")).lower() == "true":
        result["skip"] = True
        result["skip_reason"] = "Deadhead (positioning)"
        return result

    # --- Cancelled / un-operated ---
    take_off_pilot = str(row.get("Take-Off Pilot", "")).strip()
    landing_pilot = str(row.get("Landing Pilot", "")).strip()
    atd = row.get("_ATD")
    ata = row.get("_ATA")
    airborne = row.get("_Airborne")
    landing = row.get("_Landing")
    actual_ft = str(row.get("ActualFlightTime", "")).strip()

    efos_has_times = all([
        atd is not None and not _is_nat(atd),
        ata is not None and not _is_nat(ata),
        airborne is not None and not _is_nat(airborne),
        landing is not None and not _is_nat(landing),
        actual_ft != "",
    ])

    gl_has_times = _gl_has_times(row)

    cancelled = (
        not take_off_pilot and not landing_pilot and not efos_has_times
    )
    if cancelled:
        result["skip"] = True
        result["skip_reason"] = "Cancelled / un-operated (no pilots, no times)"
        return result

    if not efos_has_times and not gl_has_times:
        result["skip"] = True
        result["skip_reason"] = "No actual times in EFOS or GlobaLog — flight not yet operated"
        return result

    # --- Determine total time (minutes) ---
    total_mins = _resolve_total(row, efos_has_times)
    if total_mins is None or total_mins <= 0:
        result["skip"] = True
        result["skip_reason"] = "Could not determine block time"
        return result

    # --- PF: user is PF if they are the Landing Pilot ---
    result["pf"] = (landing_pilot.upper() == user_name.upper()) if landing_pilot else False

    # --- Function time logic ---
    is_pic = str(row.get("PIC", "")).lower() == "true"
    is_fo = str(row.get("FO", "")).lower() == "true"
    is_captain = str(row.get("Captain", "")).lower() == "true"
    is_instructor = str(row.get("Intructor", "")).lower() == "true"  # note: typo in source

    if is_instructor:
        # Instructor = PIC + Instructor overlay (not additive)
        result["time_pic"] = total_mins
        result["time_instructor"] = total_mins

    elif is_pic:
        result["time_pic"] = total_mins

    elif is_fo:
        if result["pf"]:
            # FO was landing pilot → PICUS
            result["time_picus"] = total_mins
        else:
            result["time_sic"] = total_mins

    elif is_captain and not is_pic:
        # Captain seat but not PIC (e.g. line training under supervision)
        result["time_sic"] = total_mins

    else:
        # Cannot determine role — flag as warning but still include
        result["skip_reason"] = "WARNING: Could not determine role (PIC/FO/Captain all False)"

    return result


def _is_nat(value) -> bool:
    """Return True if value is NaT or None."""
    import pandas as pd
    return value is None or (hasattr(value, "isnot") is False and pd.isnull(value))


def _gl_has_times(row: dict) -> bool:
    """Check if the merged GlobaLog data provides usable times."""
    for key in ("gl__off_block", "gl__on_block"):
        val = row.get(key)
        if val is not None and not _is_nat(val):
            return True
    return False


def _resolve_total(row: dict, efos_has_times: bool) -> int | None:
    """Return total block time in minutes, preferring EFOS then GlobaLog."""
    if efos_has_times:
        mins = _hhmm_to_minutes(str(row.get("ActualFlightTime", "")))
        if mins:
            return mins

    # GlobaLog block_time
    bt = str(row.get("gl_block_time", "")).strip()
    return _hhmm_to_minutes(bt)
