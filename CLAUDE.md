# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A cross-platform desktop application that converts Jet2 pilot flight data from two CSV sources (EFOS MySectors and GlobaLog) into a CSV compatible with the **CrewLounge PilotLog Import Wizard (PIW)**. Target users are non-technical Jet2 pilots. The full specification is in `EFOS_CREWLOUNGE_CONVERTER_SPEC.md`.

## Tech Stack

- **Python 3.11+**, **CustomTkinter** (GUI), **pandas** (CSV/data processing), **PyInstaller** (packaging)
- Output: single standalone `.exe` (Windows) / `.app` (macOS) — no Python install required

## Project Structure

```
efos-crewlounge-converter/
├── main.py                  # Entry point, GUI setup
├── gui/
│   ├── app.py               # Main application window (CustomTkinter)
│   ├── dialogs.py           # Popup dialogs (skipped flights, warnings)
│   └── widgets.py           # Custom widgets (date picker, file selector)
├── core/
│   ├── efos_parser.py       # Parse and validate EFOS CSV
│   ├── globalog_parser.py   # Parse GlobaLog CSV (header on line 4, strip footer)
│   ├── merger.py            # Join EFOS + GlobaLog on composite key
│   ├── role_engine.py       # PIC/PICUS/SIC/Instructor/PF logic
│   ├── transformer.py       # Map merged data → CrewLounge PIW format
│   ├── user_detector.py     # Auto-detect user from EFOS data
│   └── validators.py        # Input validation, sanity checks
├── config/
│   ├── settings.py          # Config load/save (JSON)
│   └── defaults.py          # Default values, AC type mappings
└── tests/
    ├── test_*.py            # Unit tests per module
    └── test_data/           # Sample CSV snippets
```

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py

# Run tests
pytest tests/

# Run a single test file
pytest tests/test_role_engine.py -v

# Build standalone executable
python build.py
# Or directly:
pyinstaller --onefile --windowed --name "EFOS-CrewLounge-Converter" main.py
```

## Critical Domain Logic

### Input Data Sources

**EFOS MySectors CSV** (`MySectors.csv`):
- Header on row 0, one row per flight sector
- Date format: `DD-MMM-YYYY` (e.g., `05-JUL-2023`) — **can be empty** on recent/cancelled flights
- Timestamps: `DD/MM/YYYY HH:MM:SS` (STD, STA, ATD, ATA, Airborne, Landing)
- **Note:** `Intructor` column name is a typo in the source — one `r`, not two
- `STD` is always populated even when `Date` is empty — use it as the authoritative flight date

**GlobaLog CSV** (e.g., `globalog_logbook_*.csv`):
- Header row is on **line 4** (lines 1–2: user ID/name, line 3: blank) — must skip when parsing
- Footer lines starting with `---` must be stripped
- Date format: `DD/MM/YYYY`, timestamps: `DD/MM/YYYY HH:MM`

### Flight Matching (EFOS ↔ GlobaLog)

Primary composite key: **date + normalised flight number + departure ICAO + arrival ICAO**

Flight number normalisation: strip leading zeros from numeric portion, uppercase, strip spaces.
Example: `LS006C` → `LS6C`. If still no match, fall back to: **date + departure ICAO + arrival ICAO + registration**.

### Time Priority Rules

1. EFOS has actual times (`ATD`, `ATA`, `Airborne`, `Landing` all non-empty) → **use EFOS times**
2. EFOS missing times but GlobaLog match found → **use GlobaLog times**
3. Neither source has times → **skip the flight** (log to skipped-flights report)

### Flight Exclusion Rules

**Skip entirely (exclude from output):**
- `DeadHeading = True` (positioning as passenger)
- Cancelled/un-operated: both `Take-Off Pilot` AND `Landing Pilot` empty AND all actual times empty
- No times from either EFOS or GlobaLog (not yet operated, no data)

### Role/Function Time Logic

| EFOS Fields | TIME_PIC | TIME_PICUS | TIME_SIC | TIME_INSTRUCTOR |
|-------------|----------|------------|----------|-----------------|
| `PIC = True` | = TIME_TOTAL | — | — | — |
| `FO = True` + user is Landing Pilot | — | = TIME_TOTAL | — | — |
| `FO = True` + user is NOT Landing Pilot | — | — | = TIME_TOTAL | — |
| `Intructor = True` | = TIME_TOTAL | — | — | = TIME_TOTAL (overlay, not additive) |

`PF` field: `PF` if user is the Landing Pilot, otherwise `PM`.

`TIME_IFR` = `TIME_TOTAL` for every flight (all Jet2 ops are IFR).

`TIME_NIGHT`, `TO_DAY/NIGHT`, `LDG_DAY/NIGHT`, `TIME_XC`, approach types → **leave blank**. CrewLounge recalculates post-import from airport coordinates.

### Output Field Transformations

- `AC_REG`: insert hyphen after `G` prefix — `GJZHZ` → `G-JZHZ` (all Jet2 aircraft are UK-registered)
- `AC_MODEL` / `AC_VARIANT`: `737 800` → `B737` / `800`; `AC_MAKE` → `BOEING`; hardcode `AC_ENGTYPE=JET ENGINE`, `AC_ME=True`, `AC_MP=True`
- `PILOTLOG_DATE` format: `YYYY-MM-DD`
- `TIME_DEP/ARR/TO/LDG`: `HH:MM` (time only, UTC)
- `OPERATOR`: `Jet2`

### User Auto-Detection

The user is the pilot whose name appears in `Right-Hand Seat Pilot` or `Left-Hand Seat Pilot` on **every** EFOS row. The app detects this automatically and asks the user to confirm, then lets them choose between displaying their real name or `SELF` in output.

### Config Persistence

JSON config file stored alongside the executable or in `~/.efos-converter/config.json`:
```json
{
  "self_name_preference": "SELF",
  "operator": "Jet2",
  "last_efos_directory": "",
  "last_globalog_directory": "",
  "last_output_directory": "",
  "ac_type_mapping": {
    "737 800": {"model": "B737", "variant": "800", "make": "BOEING"}
  }
}
```

## Key Edge Cases

- **Cancelled flights**: EFOS row has empty `Date`, empty actual times, AND empty `Take-Off Pilot` / `Landing Pilot` — skip and report
- **Recent flights with missing EFOS times**: `Date` empty, times empty, but `Take-Off Pilot` / `Landing Pilot` still populated — get times from GlobaLog
- **Flights spanning midnight**: use departure date as `PILOTLOG_DATE`
- **Multiple captains in GlobaLog `capt_on_flight`**: prefer EFOS `Left-Hand Seat Pilot` for output
- **Flight number fuzzy match**: `LS006C` (EFOS) vs `LS6` (GlobaLog) — strip leading zeros; if still no match, use fallback composite key

## Testing Strategy

- Unit tests per module in `tests/` using pytest
- Integration test: full pipeline with sample data, compare output against manually verified expected CSV
- Validate final output by uploading to CrewLounge PIW test account
