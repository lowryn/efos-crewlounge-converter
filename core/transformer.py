"""Map merged EFOS+GlobaLog rows to CrewLounge PIW output format.

Output is semicolon-delimited. Duration times are integer minutes.
Clock times (DEP/ARR/TO/LDG) are HH:MM strings.
Dates are DD/MM/YYYY.
"""

import pandas as pd
from config.defaults import OUTPUT_COLUMNS, AC_TYPE_MAP


def _hhmm_to_minutes(value: str) -> int | None:
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


def _ts_to_hhmm(ts) -> str:
    """Convert a pandas Timestamp to 'HH:MM' string, or '' if NaT/None."""
    if ts is None or (hasattr(ts, "isnot") is False and pd.isnull(ts)):
        return ""
    try:
        return ts.strftime("%H:%M")
    except Exception:
        return ""


def _reg_format(reg: str) -> str:
    """Insert hyphen after G prefix: GJZHZ -> G-JZHZ."""
    reg = reg.strip().upper()
    if reg.startswith("G") and "-" not in reg and len(reg) > 1:
        return "G-" + reg[1:]
    return reg


def _ac_info(ac_type: str) -> dict:
    info = AC_TYPE_MAP.get(ac_type.strip(), {})
    if not info:
        # Best-effort fallback
        return {"model": ac_type.strip(), "variant": "", "make": "", "rating": ""}
    return info


def _other_pilot_name(row: dict, user_name: str) -> str:
    lhs = str(row.get("Left-Hand Seat Pilot", "")).strip()
    rhs = str(row.get("Right-Hand Seat Pilot", "")).strip()
    if lhs.upper() == user_name.upper():
        return rhs
    return lhs


def _crewlist(pilot1_name: str, pilot2_name: str) -> str:
    """Build CREWLIST string matching the real export format."""
    parts = []
    if pilot2_name:
        parts.append(f"SELF - {pilot2_name}")
    if pilot1_name:
        parts.append(pilot1_name)
    return "|".join(parts)


def transform_row(
    row: dict,
    role: dict,
    user_name: str,
    self_label: str,
    operator: str,
) -> dict | None:
    """
    Convert one merged row + role dict into a CrewLounge output record.

    Returns None if the row should be skipped (role.skip == True).
    role dict comes from role_engine.compute().
    """
    if role.get("skip"):
        return None

    efos_has_times = _efos_has_times(row)

    # --- Dates ---
    std_ts = row.get("_STD")
    flight_date = std_ts.strftime("%Y-%m-%d") if std_ts and not pd.isnull(std_ts) else ""

    # --- Clock times ---
    if efos_has_times:
        time_dep = _ts_to_hhmm(row.get("_ATD"))
        time_arr = _ts_to_hhmm(row.get("_ATA"))
        time_to  = _ts_to_hhmm(row.get("_Airborne"))
        time_ldg = _ts_to_hhmm(row.get("_Landing"))
    else:
        time_dep = _ts_to_hhmm(row.get("gl__off_block"))
        time_arr = _ts_to_hhmm(row.get("gl__on_block"))
        time_to  = _ts_to_hhmm(row.get("gl__take_off"))
        time_ldg = _ts_to_hhmm(row.get("gl__landing"))

    time_depsch = _ts_to_hhmm(row.get("_STD"))
    time_arrsch = _ts_to_hhmm(row.get("_STA"))

    # --- Duration times (minutes) ---
    total_mins = role.get("_total_mins", 0)

    # Air time: from EFOS airborne→landing or GlobaLog airtime
    air_mins = None
    if efos_has_times:
        ab = row.get("_Airborne")
        ld = row.get("_Landing")
        if ab and ld and not pd.isnull(ab) and not pd.isnull(ld):
            air_mins = int((ld - ab).total_seconds() / 60)
    if air_mins is None:
        air_mins = _hhmm_to_minutes(str(row.get("gl_airtime", "")))

    # IFR = Total (all Jet2 ops are IFR)
    time_ifr = total_mins if total_mins else ""

    # --- Aircraft ---
    ac_type = str(row.get("A/C Type", "")).strip()
    ac_info = _ac_info(ac_type)
    ac_reg = _reg_format(str(row.get("A/C Reg", "")))

    # --- Pilots ---
    other_pilot = _other_pilot_name(row, user_name)
    is_captain = str(row.get("Captain", "")).lower() == "true"

    if is_captain:
        # User is Captain (LHS) → user is PILOT1 (captain position), other is PILOT2
        pilot1_name = self_label
        pilot2_name = other_pilot
    else:
        # User is FO (RHS) → other pilot is PILOT1 (captain), user is PILOT2
        pilot1_name = other_pilot
        pilot2_name = self_label

    # --- CAPACITY (pilot role on this flight) ---
    if role["time_instructor"] > 0:
        capacity = "INS"
    elif role["time_pic"] > 0:
        capacity = "P1"
    elif role["time_picus"] > 0:
        capacity = "PICUS"
    else:
        capacity = "P2"

    # --- Remarks ---
    source = "EFOS" if efos_has_times else "EFOS+GlobaLog"
    if role.get("skip_reason", "").startswith("WARNING"):
        remarks = f"{source} | {role['skip_reason']}"
    else:
        remarks = source

    out = {col: "" for col in OUTPUT_COLUMNS}
    out.update({
        "PILOTLOG_DATE":   flight_date,
        "IS_PREVEXP":      "FALSE",
        "AC_ISSIM":        "FALSE",
        "FLIGHTNUMBER":    str(row.get("Flight No.", "")).strip(),
        "AF_DEP":          str(row.get("Depart Airfield ICAO", "")).strip(),
        "AF_ARR":          str(row.get("Arrive Airfield ICAO", "")).strip(),
        "TIME_DEP":        time_dep,
        "TIME_DEPSCH":     time_depsch,
        "TIME_ARR":        time_arr,
        "TIME_ARRSCH":     time_arrsch,
        "TIME_TO":         time_to,
        "TIME_LDG":        time_ldg,
        "TIME_AIR":        air_mins if air_mins is not None else "",
        "TIME_MODE":       "UTC",
        "TIME_TOTAL":      total_mins if total_mins else "",
        "TIME_PIC":        role["time_pic"],
        "TIME_SIC":        role["time_sic"],
        "TIME_DUAL":       0,
        "TIME_PICUS":      role["time_picus"],
        "TIME_INSTRUCTOR": role["time_instructor"],
        "TIME_EXAMINER":   0,
        "TIME_NIGHT":      0,
        "TIME_XC":         0,
        "TIME_IFR":        time_ifr,
        "TIME_HOOD":       0,
        "TIME_ACTUAL":     0,
        "TIME_RELIEF":     0,
        "CAPACITY":        capacity,
        "OPERATOR":        operator,
        "PILOT1_NAME":     pilot1_name,
        "PILOT2_NAME":     pilot2_name,
        "PF":              "TRUE" if role["pf"] else "FALSE",
        "REMARKS":         remarks[:50],
        "CREWLIST":        _crewlist(pilot1_name, pilot2_name),
        "AC_MAKE":         ac_info.get("make", ""),
        "AC_MODEL":        ac_info.get("model", ""),
        "AC_VARIANT":      ac_info.get("variant", ""),
        "AC_REG":          ac_reg,
        "AC_RATING":       ac_info.get("rating", ""),
        "AC_SP":           "FALSE",
        "AC_MP":           total_mins if total_mins else "TRUE",  # time value → MP classification
        "AC_ME":           "TRUE",
        "AC_SPSE":         "FALSE",
        "AC_SPME":         "FALSE",
        "AC_CLASS":        "Aeroplane",
        "AC_ENGINES":      "Multi",
        "AC_ENGTYPE":      "Turbofan",
        "AC_HEAVY":        "TRUE",
    })
    return out


def _efos_has_times(row: dict) -> bool:
    for key in ("_ATD", "_ATA", "_Airborne", "_Landing"):
        val = row.get(key)
        if val is None or (hasattr(val, "isnot") is False and pd.isnull(val)):
            return False
    return bool(str(row.get("ActualFlightTime", "")).strip())
