"""Join EFOS and GlobaLog DataFrames on a composite key.

Primary key:  date + normalised flight number + departure ICAO + arrival ICAO
Fallback key: date + departure ICAO + arrival ICAO + registration
"""

import re
import pandas as pd


def _normalise_flight_number(fn: str) -> str:
    """Strip leading zeros from numeric portion, uppercase, no spaces.

    Examples:
        LS717  -> LS717
        LS006C -> LS6C
        LS6    -> LS6
    """
    fn = fn.upper().replace(" ", "")
    m = re.match(r"^([A-Z]+)0*(\d+)(.*)$", fn)
    if m:
        return m.group(1) + m.group(2) + m.group(3)
    return fn


def _build_efos_keys(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_key_date"] = df["_STD"].dt.date
    df["_key_fn"] = df["Flight No."].fillna("").apply(_normalise_flight_number)
    df["_key_dep"] = df["Depart Airfield ICAO"].fillna("").str.upper()
    df["_key_arr"] = df["Arrive Airfield ICAO"].fillna("").str.upper()
    df["_key_reg"] = df["A/C Reg"].fillna("").str.upper()
    df["_primary_key"] = (
        df["_key_date"].astype(str) + "|" + df["_key_fn"] + "|"
        + df["_key_dep"] + "|" + df["_key_arr"]
    )
    df["_fallback_key"] = (
        df["_key_date"].astype(str) + "|" + df["_key_dep"] + "|"
        + df["_key_arr"] + "|" + df["_key_reg"]
    )
    return df


def _build_globalog_keys(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_key_date"] = df["_date"].dt.date
    df["_key_fn"] = df["call_sign"].fillna("").apply(_normalise_flight_number)
    df["_key_dep"] = df["departure_airport"].fillna("").str.upper()
    df["_key_arr"] = df["destination_airport"].fillna("").str.upper()
    df["_key_reg"] = df["aircraft_registration"].fillna("").str.upper()
    df["_primary_key"] = (
        df["_key_date"].astype(str) + "|" + df["_key_fn"] + "|"
        + df["_key_dep"] + "|" + df["_key_arr"]
    )
    df["_fallback_key"] = (
        df["_key_date"].astype(str) + "|" + df["_key_dep"] + "|"
        + df["_key_arr"] + "|" + df["_key_reg"]
    )
    return df


def merge(efos: pd.DataFrame, globalog: pd.DataFrame) -> pd.DataFrame:
    """Return EFOS rows enriched with matched GlobaLog data.

    Adds columns prefixed with 'gl_' for each GlobaLog field used downstream.
    Also adds '_match_type': 'primary', 'fallback', or 'none'.
    """
    efos = _build_efos_keys(efos)
    gl = _build_globalog_keys(globalog)

    # Columns to pull from GlobaLog (excluding join keys)
    gl_data_cols = [
        "_off_block", "_take_off", "_landing", "_on_block",
        "airtime", "block_time", "night_landing",
        "role_on_flight", "_flying_pilot",
    ]
    gl_data_rename = {c: f"gl_{c}" for c in gl_data_cols}

    # Build slim GlobaLog tables for each join strategy
    gl_primary = (
        gl[["_primary_key"] + gl_data_cols]
        .rename(columns={**{"_primary_key": "gl__primary_key"}, **gl_data_rename})
    )
    gl_fallback = (
        gl[["_fallback_key"] + gl_data_cols]
        .rename(columns={**{"_fallback_key": "gl__fallback_key"}, **gl_data_rename})
    )

    # Primary join
    merged = efos.merge(gl_primary, left_on="_primary_key", right_on="gl__primary_key", how="left")
    merged["_match_type"] = merged["gl__primary_key"].notna().map({True: "primary", False: "none"})

    # Fallback join for unmatched rows
    unmatched_mask = merged["_match_type"] == "none"
    if unmatched_mask.any():
        gl_cols_to_drop = [c for c in merged.columns if c.startswith("gl_")]
        unmatched = merged.loc[unmatched_mask].drop(columns=gl_cols_to_drop)
        fb_merged = unmatched.merge(
            gl_fallback, left_on="_fallback_key", right_on="gl__fallback_key", how="left"
        )
        fb_merged["_match_type"] = fb_merged["gl__fallback_key"].notna().map(
            {True: "fallback", False: "none"}
        )
        merged = pd.concat([merged.loc[~unmatched_mask], fb_merged], ignore_index=True)

    return merged
