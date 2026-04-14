# EFOS → CrewLounge PilotLog Converter

## Project Specification v1.0

---

## 1. Overview

A cross-platform desktop application that combines flight data from two CSV sources (EFOS "MySectors" and GlobaLog), transforms it, and outputs a CSV file compatible with the CrewLounge PilotLog Import Wizard (PIW).

**Target users:** Jet2 pilots (non-technical) who need to batch-populate their CrewLounge PilotLog with historical and ongoing flight data.

---

## 2. Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.11+ | Cross-platform, excellent CSV/date handling, mature packaging |
| GUI | CustomTkinter | Modern-looking tkinter wrapper, no heavy dependencies, single-file packaging friendly |
| CSV processing | pandas | Robust CSV parsing, merge/join, date handling |
| Date handling | Python datetime / pandas Timestamp | Native support for the date formats in both CSVs |
| Packaging | PyInstaller | Produces standalone .exe (Windows) and .app (macOS) with no Python install required |

---

## 3. Input File Specifications

### 3.1 EFOS MySectors CSV

The primary flight data source. One row per sector (flight leg).

**Key columns:**

| Column | Description | Notes |
|--------|-------------|-------|
| `Date` | Date of flight | Format: `DD-MMM-YYYY` (e.g., `05-JUL-2023`). **Can be empty** — see cancelled/incomplete flights |
| `Status` | Sector status | Always `IncompleteSector` in sample data |
| `Flight No.` | Flight number | e.g., `LS717` |
| `STD` / `STA` | Scheduled departure/arrival | Format: `DD/MM/YYYY HH:MM:SS` |
| `ATD` / `ATA` | Actual departure/arrival (block times) | **Empty when times are missing** (recent flights, cancelled flights) |
| `Airborne` | Actual takeoff time | **Empty when times are missing** |
| `Landing` | Actual landing time | **Empty when times are missing** |
| `From` / `To` | IATA airport codes | e.g., `EDI`, `PMI` |
| `A/C Type` | Aircraft type | e.g., `737 800` |
| `A/C Reg` | Aircraft registration | e.g., `GJZHZ` (no hyphen) |
| `Depart Airfield ICAO` / `Arrive Airfield ICAO` | ICAO codes | e.g., `EGPH`, `LEPA` |
| `Take-Off Pilot` | Name of pilot who flew the takeoff | |
| `Landing Pilot` | Name of pilot who flew the landing | |
| `DeadHeading` | Boolean string | `True` / `False` |
| `PIC` | Is the user PIC? | `True` / `False` |
| `Captain` | Is the user the Captain? | `True` / `False` |
| `FO` | Is the user the First Officer? | `True` / `False` |
| `Intructor` | Is the user an instructor? | `True` / `False` (note: typo in source data — `Intructor` not `Instructor`) |
| `Operating Crew` | Crew surnames | e.g., `MALLIS,LOWRY` |
| `Planned Flight Time` | Planned duration | Format: `HH:MM` |
| `ActualFlightTime` | Actual duration | Format: `HH:MM`. **Empty when times are missing** |
| `Left-Hand Seat Pilot` | LHS pilot name | Usually the Captain |
| `Right-Hand Seat Pilot` | RHS pilot name | Usually the FO |

**Critical observations:**

1. **Missing times pattern:** Recent flights (approx. late 2025 onward in this dataset, but the transition point will vary per user) have empty `Date`, `ATD`, `ATA`, `Airborne`, `Landing`, and `ActualFlightTime` fields. These times must be sourced from GlobaLog.
2. **Cancelled flight pattern:** Row 13 in the sample — `Date` is empty, `ATD`/`ATA`/`Airborne`/`Landing` are all empty, `ActualFlightTime` is empty, AND `Take-Off Pilot` and `Landing Pilot` are also empty. This is the distinguishing feature vs. "missing times" rows where Take-Off/Landing Pilot are still populated.
3. **The user appears on every flight** — they are identifiable as the person whose name appears in every row (in `Operating Crew`, `Right-Hand Seat Pilot`, or `Left-Hand Seat Pilot`).

### 3.2 GlobaLog CSV

The supplementary time data source. Provides accurate actual times for flights where EFOS has missing data.

**File structure:** Header row is on line 4 (lines 1-2 contain user ID/name, line 3 is blank). Footer lines start with `---` and contain report metadata — must be stripped.

**Key columns:**

| Column | Description | Notes |
|--------|-------------|-------|
| `date_of_flight` | Date | Format: `DD/MM/YYYY` |
| `call_sign` | Flight number | e.g., `LS381` |
| `departure_airport` | ICAO code | e.g., `EGAA` |
| `off_block` | Actual off-block (departure) time | Format: `DD/MM/YYYY HH:MM` |
| `take_off` | Actual takeoff time | Format: `DD/MM/YYYY HH:MM` |
| `destination_airport` | ICAO code | e.g., `GCTS` |
| `landing` | Actual landing time | Format: `DD/MM/YYYY HH:MM` |
| `on_block` | Actual on-block (arrival) time | Format: `DD/MM/YYYY HH:MM` |
| `aircraft_registration` | Reg (no hyphen) | e.g., `GDRTF` |
| `airtime` | Airborne duration | Format: `H:MM` |
| `block_time` | Block duration | Format: `H:MM` |
| `day_time` | Day flying time | Format: `H:MM` |
| `night_time` | Night flying time | Format: `H:MM` |
| `night_landing` | Day or night landing | `day` or `night` |
| `capt_on_flight` | Captain name(s) | May contain multiple names comma-separated |
| `role_on_flight` | User's role | e.g., `FO` |
| `flying_pilot` | Was user PF? | `Yes` or `No` |

**Critical observations:**

1. GlobaLog only contains flights that have actually occurred with recorded times — it will NOT contain the cancelled LS178 from Aug 2023.
2. GlobaLog may contain flights not yet in EFOS with times (future-operated flights that EFOS hasn't updated yet).
3. The `call_sign` in GlobaLog may differ slightly from EFOS `Flight No.` (e.g., GlobaLog has `LS6` while EFOS has `LS006C`). The join logic must account for this.

---

## 4. Join/Merge Logic

### 4.1 Matching key

Flights are matched between EFOS and GlobaLog using a **composite key**:

1. **Date** — derived from `STD` in EFOS (always populated even when `Date` is empty) and `date_of_flight` in GlobaLog
2. **Flight number** — `Flight No.` (EFOS) vs `call_sign` (GlobaLog). Normalise both: strip leading zeros from numeric portion, uppercase, strip spaces.
3. **Departure airport** — `Depart Airfield ICAO` (EFOS) vs `departure_airport` (GlobaLog)
4. **Destination airport** — `Arrive Airfield ICAO` (EFOS) vs `destination_airport` (GlobaLog)

If flight number matching fails, fall back to **date + departure ICAO + destination ICAO + registration** as the composite key.

### 4.2 Time field priority

For each flight in the output:

1. **If EFOS has actual times** (`ATD`, `ATA`, `Airborne`, `Landing` are all non-empty): **use EFOS times**.
2. **If EFOS is missing actual times** (the recent-flight pattern): **use GlobaLog times** (`off_block`, `on_block`, `take_off`, `landing`).
3. **If neither source has times** (cancelled/un-operated flight): **skip the flight** (do not include in output). Log it to a skipped-flights report.

### 4.3 Additional fields from GlobaLog

When GlobaLog is used for times, pull:
- `off_block` / `on_block` → for `TIME_DEP` / `TIME_ARR`
- `take_off` / `landing` → for `TIME_TO` / `TIME_LDG`
- `block_time` → for `TIME_TOTAL`
- `airtime` → for `TIME_AIR`

Night time, day/night takeoff/landing splits, and cross-country time are intentionally left blank — CrewLounge recalculates these after import.

---

## 5. Role & Capacity Logic

### 5.1 Identifying the user

On first run (or when processing a new pair of files), the app must identify who "the user" is. This is determined automatically:

- **Method:** Find the name that appears on every single flight in the EFOS data. Check `Right-Hand Seat Pilot` and `Left-Hand Seat Pilot` columns — the user's name will appear in one of these on every row.
- **Confirmation:** Display the detected name to the user and ask them to confirm.
- **Self-naming preference:** The user chooses how their name appears in the output. Options: their actual name (as detected) or `SELF`. Default: `SELF`.

### 5.2 Determining the other pilot (Captain/Commander)

The other pilot on each flight is the one who is NOT the user. This person goes in `PILOT1_NAME` (Pilot 1 = Captain/Commander position in CrewLounge).

- If `Captain = True` in EFOS → the user IS the captain → the other pilot is the FO
- If `FO = True` in EFOS → the user IS the FO → the other pilot is the captain
- The other pilot's name = `Left-Hand Seat Pilot` (when user is RHS) or vice versa

### 5.3 Role/capacity logic for function times

| EFOS Fields | Meaning | TIME_PIC | TIME_PICUS | TIME_SIC | TIME_INSTRUCTOR | PILOT1 (Capt) | PILOT2 (FO/User) | PF |
|-------------|---------|----------|------------|----------|-----------------|---------------|-------------------|----|
| `PIC = True` | User is PIC | = TIME_TOTAL | | | | Other pilot | User (SELF) | Based on Landing Pilot |
| `FO = True`, user is Landing Pilot | FO, handled the landing | | = TIME_TOTAL | | | Other pilot (Captain) | User (SELF) | PF |
| `FO = True`, user is NOT Landing Pilot | FO, did not land | | | = TIME_TOTAL | | Other pilot (Captain) | User (SELF) | PM |
| `Captain = True`, `PIC = False` | User is Captain seat but not PIC (line training scenario?) | | | = TIME_TOTAL | | User (SELF) | Other pilot | Based on Landing Pilot |
| `Intructor = True` | User is instructor | = TIME_TOTAL | | | = TIME_TOTAL | Situational | Situational | Based on Landing Pilot |
| `DeadHeading = True` | Positioning as passenger | **SKIP — exclude from output entirely** | | | | | | |

**Instructor time clarification:**
When `Intructor = True`, the user's function is 100% PIC. `TIME_INSTRUCTOR` is an overlay/qualifier — it records that instruction was being given during the flight, NOT an additional block of hours. Both `TIME_PIC` and `TIME_INSTRUCTOR` are set to the same value as `TIME_TOTAL`. They are not additive. The sum of function times (PIC + PICUS + SIC + Dual + Relief) must still equal `TIME_TOTAL`, and in this case PIC alone covers it. Example: a 3:00 flight → TIME_TOTAL=3:00, TIME_PIC=3:00, TIME_INSTRUCTOR=3:00. Total function time is 3:00 (not 6:00).

**Landing Pilot logic for PF/PM:**
- If `Landing Pilot` == user's name → user was PF (at least for the landing; we log PF=True)
- If `Take-Off Pilot` == user's name AND `Landing Pilot` != user's name → user was PF for takeoff but PM for landing. Log PF based on landing pilot (industry convention for logging).
- Actually, simplify: **PF = True if user is the Landing Pilot**. This is the standard logging convention.

**PICUS vs SIC (when FO = True):**
- If the user (FO) was the **Landing Pilot** → log as **PICUS** (PIC Under Supervision — the FO was acting as PF under the Captain's supervision)
- If the user (FO) was **NOT the Landing Pilot** → log as **SIC** (Second in Command — the FO was PM)

### 5.4 Takeoff/Landing counts

For each flight, log one takeoff and one landing. **Leave day/night split blank** — CrewLounge can recalculate these automatically after import using airport coordinates, flight date, and block times (via the Multiselect feature). This avoids us needing sunrise/sunset calculations.

- `TO_DAY` / `TO_NIGHT`: Leave blank
- `LDG_DAY` / `LDG_NIGHT`: Leave blank

CrewLounge will populate these correctly post-import.

---

## 6. Output File Specification

### 6.1 CrewLounge PIW CSV format

The output CSV must use the CrewLounge column headers. **Mandatory columns are marked with (M).**

| Output Column | Source | Mapping |
|---------------|--------|---------|
| `PILOTLOG_DATE` **(M)** | EFOS `Date` or derived from `STD` | Format: `YYYY-MM-DD` |
| `FLIGHTNUMBER` | EFOS `Flight No.` | As-is, e.g., `LS717` |
| `AF_DEP` **(M)** | EFOS `Depart Airfield ICAO` | 4-char ICAO code |
| `AF_ARR` **(M)** | EFOS `Arrive Airfield ICAO` | 4-char ICAO code |
| `TIME_DEP` | EFOS `ATD` or GlobaLog `off_block` | Format: `HH:MM` (time only, UTC) |
| `TIME_ARR` | EFOS `ATA` or GlobaLog `on_block` | Format: `HH:MM` |
| `TIME_DEPSCH` | EFOS `STD` | Format: `HH:MM` |
| `TIME_ARRSCH` | EFOS `STA` | Format: `HH:MM` |
| `TIME_TO` | EFOS `Airborne` or GlobaLog `take_off` | Format: `HH:MM` |
| `TIME_LDG` | EFOS `Landing` or GlobaLog `landing` | Format: `HH:MM` |
| `TIME_TOTAL` **(M)** | EFOS `ActualFlightTime` or GlobaLog `block_time` | Format: `H:MM` |
| `TIME_AIR` | Calculated from takeoff→landing or GlobaLog `airtime` | Format: `H:MM` |
| `TIME_PIC` | See role logic §5.3 | = TIME_TOTAL when PIC or Instructor, else empty |
| `TIME_PICUS` | See role logic §5.3 | = TIME_TOTAL when PICUS, else empty |
| `TIME_SIC` | See role logic §5.3 | = TIME_TOTAL when SIC, else empty |
| `TIME_INSTRUCTOR` | See role logic §5.3 | = TIME_TOTAL when Instructor, else empty |
| `TIME_NIGHT` | Leave blank | CrewLounge recalculates from airport coords + date + block times |
| `TIME_IFR` | = TIME_TOTAL (all Jet2 ops are IFR) | Format: `H:MM` |
| `AC_MODEL` **(M)** | EFOS `A/C Type` | Normalise: `737 800` → `B737` |
| `AC_VARIANT` | EFOS `A/C Type` | `800` |
| `AC_REG` **(M)** | EFOS `A/C Reg` | Add hyphen: `GJZHZ` → `G-JZHZ` |
| `AC_MAKE` | Hardcoded | `BOEING` |
| `AC_ENGTYPE` | Hardcoded | `JET ENGINE` |
| `AC_ME` | Hardcoded | `True` (multi-engine) |
| `AC_MP` | Hardcoded | `True` (multi-pilot) |
| `PILOT1_NAME` | Captain/Commander name | See §5.2 |
| `PILOT2_NAME` | FO/other pilot name | See §5.2 |
| `PF` | Based on Landing Pilot | `PF` or `PM` |
| `OPERATOR` | Hardcoded | `Jet2` |
| `REMARKS` | Optional | Could include source info, e.g., `EFOS` or `EFOS+GlobaLog` |

**Note:** `LDG_DAY`, `LDG_NIGHT`, `TO_DAY`, `TO_NIGHT`, `TIME_NIGHT`, `TIME_XC`, and `APP_1/APP_2/APP_3` are intentionally omitted. CrewLounge recalculates takeoff/landing day-night splits and cross-country time from airport coordinates after import. Approach types are not recorded in EFOS or GlobaLog.

### 6.2 Aircraft type normalisation

EFOS stores `737 800`. CrewLounge expects a model code and optionally a variant.

| EFOS `A/C Type` | `AC_MODEL` | `AC_VARIANT` |
|------------------|------------|--------------|
| `737 800` | `B737` | `800` |

If other types appear in future EFOS data, the app should have a configurable mapping table. For now, `737 800` is the only type in the data.

### 6.3 Registration formatting

EFOS stores registrations without hyphens (e.g., `GJZHZ`). CrewLounge expects the standard format with hyphen. All Jet2 aircraft are UK-registered (UK AOC), so insert hyphen after `G`: `GJZHZ` → `G-JZHZ`.

---

## 7. Cancelled / Skipped Flight Handling

A flight is considered **cancelled or un-operated** when:
- `Take-Off Pilot` and `Landing Pilot` are BOTH empty in EFOS
- AND all actual times (`ATD`, `ATA`, `Airborne`, `Landing`) are empty
- AND `ActualFlightTime` is empty

This is reliable because EFOS does not allow submission of operated flights with missing data — if the times and pilot fields are empty, the flight did not operate. The user may or may not have flown a replacement flight; that's a separate EFOS row if it exists.

**No GlobaLog check is needed for cancellation detection** — the EFOS data alone is sufficient.

These flights are **excluded from the output** and logged to a separate skipped-flights report (displayed in the GUI) so the user can review what was dropped.

The cancelled LS178 from 28-AUG-2023 (row 13 in EFOS) is an example. A replacement flight LS1780 operated on 29-AUG-2023 (row 14), but this is not always the case — sometimes a cancellation is just a cancellation with no replacement.

---

## 8. Date Filtering

The user specifies a date range for the output:
- **From date** (inclusive)
- **To date** (inclusive)

Only flights within this range are included in the output CSV. The date used for filtering is derived from `STD` (scheduled departure) in EFOS — this is always populated even when `Date` is empty.

**Default behaviour:** If no date range is specified, process all flights.

---

## 9. User Interface Design

### 9.1 Main window layout

```
┌─────────────────────────────────────────────────────────┐
│  EFOS → CrewLounge Converter                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  EFOS File (MySectors.csv):                             │
│  [________________________] [Browse...]                  │
│                                                         │
│  GlobaLog File:                                         │
│  [________________________] [Browse...]                  │
│                                                         │
│  ─── Date Range ───────────────────────                 │
│  From: [DD/MM/YYYY]    To: [DD/MM/YYYY]                 │
│  [ ] Process all dates (ignore range)                   │
│                                                         │
│  ─── User Settings ────────────────────                 │
│  Detected user: Nigel LOWRY                             │
│  Name in output: (●) SELF  ( ) Use actual name          │
│  Operator:       [Jet2___________]                      │
│                                                         │
│  ─── Output ───────────────────────────                 │
│  Output file:                                           │
│  [________________________] [Browse...]                  │
│                                                         │
│  [        Convert        ]                              │
│                                                         │
│  ─── Status ───────────────────────────                 │
│  Progress: [██████████████░░░░░░] 70%                   │
│  Processed: 245 flights                                 │
│  Skipped: 3 (cancelled/no times/deadhead)                │
│  Warnings: 1                                            │
│                                                         │
│  [View Skipped Flights]  [View Warnings]                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 9.2 Workflow

1. User selects EFOS file → app reads headers, validates format
2. User selects GlobaLog file → app reads headers, validates format
3. App auto-detects the user's name (appears on every EFOS flight) and displays it
4. User confirms name and preferences
5. User sets date range (or selects "process all")
6. User clicks "Convert"
7. App processes, shows progress, produces output CSV
8. Summary shown: X flights processed, Y skipped, Z warnings
9. User can view skipped flights and warnings in a popup table

### 9.3 Validation & warnings

| Condition | Severity | Action |
|-----------|----------|--------|
| File doesn't match expected format | Error | Block processing, show message |
| EFOS flight has DeadHeading = True | Info | Skip flight, add to skipped report |
| EFOS flight has no times AND no GlobaLog match | Info | Skip flight, add to skipped report |
| EFOS flight has no times but GlobaLog match found | Normal | Use GlobaLog times, note in remarks |
| GlobaLog flight exists with no EFOS match | Warning | Ignore (GlobaLog-only flights not included) |
| Flight number mismatch during join | Warning | Log for user review |
| `PIC`, `FO`, `Captain` all False (and not deadheading) | Warning | Cannot determine role — flag for manual review |
| `ActualFlightTime` differs significantly from GlobaLog `block_time` | Warning | Use EFOS value but flag discrepancy |

---

## 10. Configuration & Persistence

Store user preferences in a JSON config file alongside the executable (or in the user's home directory):

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

---

## 11. Project Structure

```
efos-crewlounge-converter/
├── main.py                  # Entry point, GUI setup
├── gui/
│   ├── __init__.py
│   ├── app.py               # Main application window (CustomTkinter)
│   ├── dialogs.py           # Popup dialogs (skipped flights, warnings)
│   └── widgets.py           # Custom widgets (date picker, file selector)
├── core/
│   ├── __init__.py
│   ├── efos_parser.py       # Parse and validate EFOS CSV
│   ├── globalog_parser.py   # Parse and validate GlobaLog CSV (handle header offset, footer)
│   ├── merger.py            # Join EFOS + GlobaLog data
│   ├── role_engine.py       # Determine PIC/PICUS/SIC/PF/PM logic
│   ├── transformer.py       # Map merged data → CrewLounge PIW format
│   ├── user_detector.py     # Auto-detect the user from EFOS data
│   └── validators.py        # Input validation, output sanity checks
├── config/
│   ├── __init__.py
│   ├── settings.py          # Config load/save
│   └── defaults.py          # Default values, AC type mappings
├── tests/
│   ├── test_efos_parser.py
│   ├── test_globalog_parser.py
│   ├── test_merger.py
│   ├── test_role_engine.py
│   ├── test_transformer.py
│   └── test_data/           # Sample CSV snippets for testing
├── requirements.txt         # pandas, customtkinter
├── build.py                 # PyInstaller build script
└── README.md
```

---

## 12. Edge Cases & Known Issues

### 12.1 The cancelled LS178 (28-AUG-2023)
- EFOS row 13: Date empty, all actual times empty, Take-Off Pilot and Landing Pilot empty
- No corresponding GlobaLog record
- **Handling:** Skip. The replacement flight LS1780 on 29-AUG-2023 (row 14) operated and has full data.

### 12.2 Flight number normalisation
- GlobaLog `LS6` vs EFOS `LS006C` — these need fuzzy matching or a normalisation step
- Proposed: Strip leading zeros from the numeric portion. If that still doesn't match, fall back to date + ICAO route + registration matching.
- `LS006C` → `LS6C` after zero-strip. Still doesn't match `LS6`. May need to strip trailing alpha characters too, or just rely on the fallback composite key.

### 12.3 Flights spanning midnight
- EFOS example: LS372 departs 15/03/2026 19:40, arrives 16/03/2026 00:15
- GlobaLog: same flight, `on_block` shows `16/03/2026 00:00`
- **Handling:** Use the departure date for `PILOTLOG_DATE`. CrewLounge handles multi-day flights fine.

### 12.4 Multiple captains in GlobaLog
- GlobaLog `capt_on_flight` can contain multiple names: `Allen CLAGUE, Enda RICE`
- This likely indicates a training scenario or crew swap
- **Handling:** Use EFOS `Left-Hand Seat Pilot` as the primary captain for output (it's flight-specific rather than aggregated)

### 12.5 Name format mismatches between systems
- EFOS: `Colin O'NEILL` vs GlobaLog: `Colin ONEILL` (apostrophe stripped)
- EFOS: `Jonny MCKEOWN` vs GlobaLog: `Jonathan MCKEOWN`
- **Handling:** Names are not used as join keys, so this doesn't affect matching. For output, use EFOS names (more complete).

### 12.6 EFOS rows with empty Date but valid STD
- Recent flights (rows 320+) have empty `Date` field but `STD` is populated
- **Handling:** Derive the flight date from `STD` when `Date` is empty

### 12.7 DeadHeading flights
- `DeadHeading = True` → the user was positioning as a passenger
- **Handling:** **Skip entirely.** Do not include deadhead flights in the output.

### 12.8 Future/upcoming flights in EFOS
- EFOS contains scheduled future flights with no actual times (rows 330-331 show 11-APR-2026 flights, some with empty Take-Off/Landing Pilot)
- If these are within the date range AND have no GlobaLog match AND no actual times → skip
- If they're within the date range AND DO have a GlobaLog match → include (the flight has operated)

---

## 13. Testing Strategy

### 13.1 Unit tests
- EFOS parser: handles all date formats, empty fields, cancelled flights
- GlobaLog parser: handles header offset (data starts line 4), footer stripping, time formats
- Merger: correct join on composite key, fallback matching, no duplicate outputs
- Role engine: all PIC/FO/Captain/Instructor combinations
- Transformer: output matches CrewLounge PIW format exactly

### 13.2 Integration tests
- Full pipeline with sample data → compare output against manually verified expected output
- Edge case file with: cancelled flight, midnight-spanning flight, missing times, deadhead

### 13.3 Validation against CrewLounge
- Upload test output to CrewLounge PIW (test account) to verify it accepts the format without errors

---

## 14. Resolved Design Decisions

| # | Question | Decision |
|---|----------|----------|
| 1 | DeadHeading flights | **Skip entirely.** Do not include in output. |
| 2 | Instructor flights | Log as **PIC + Instructor time** (TIME_PIC = TIME_TOTAL, TIME_INSTRUCTOR = TIME_TOTAL). Instructors normally operate as PIC. |
| 3 | IFR time | **Yes**, all Jet2 flights are IFR. TIME_IFR = TIME_TOTAL for every flight. |
| 4 | Night time | **Leave blank.** CrewLounge recalculates from airport coordinates + date + block times after import. |
| 5 | Approach types | **Leave blank.** Not recorded in EFOS or GlobaLog. |
| 6 | Cross-country time | **Leave blank.** CrewLounge auto-calculates from airport coordinates (>50 NM = XC). |
| 7 | Non-UK registrations | **No.** Jet2 operates under a UK AOC. All registrations are G-prefix. Hyphen insertion rule: `G` + `-` + remaining characters. |

---

## 15. Build & Distribution

### 15.1 PyInstaller build

```bash
# Windows
pyinstaller --onefile --windowed --name "EFOS-CrewLounge-Converter" main.py

# macOS
pyinstaller --onefile --windowed --name "EFOS-CrewLounge-Converter" main.py
```

### 15.2 Distribution
- Single executable file per platform
- No installer needed — just download and run
- Config file created on first run in the same directory as the executable (or `~/.efos-converter/config.json`)

---

## 16. Future Enhancements (Out of Scope for v1)

- Auto-detection of the "transition point" where EFOS times stop being reliable
- Support for other airlines (different EFOS formats)
- Direct API integration with CrewLounge (if they ever offer one)
- Batch processing of multiple crew members' files
- Dark mode / light mode toggle
