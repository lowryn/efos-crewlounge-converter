# EFOS → CrewLounge Converter — User Guide

This tool takes your EFOS flight history and GlobaLog data and converts it into a file you can import directly into CrewLounge PilotLog.

---

## What you need before you start

1. **Your EFOS MySectors CSV** — exported from the EFOS crew portal
2. **Your GlobaLog CSV** — exported from the GlobaLog website
3. **The converter app** — either the standalone `.app` (macOS) or `.exe` (Windows), or run from source (see README)

---

## Step 1 — Export your EFOS MySectors file

1. Log in to the EFOS crew portal
2. Navigate to **My Sectors** (or equivalent flight history page)
3. Export / download as **CSV**
4. Save it somewhere you can find it (e.g. your Desktop)

The file will be named something like `MySectors.csv`.

---

## Step 2 — Export your GlobaLog file

1. Log in to [GlobaLog](https://www.globalog.aero)
2. Go to your logbook / flight records
3. Export as **CSV**
4. Save it alongside your EFOS file
5. You only need Globalog data covering the change in EFOS since flight times are not recorded.

The filename will look like `globalog_logbook_ls00000_20260414_....csv`.

---

## Step 3 — Run the converter

Open the **EFOS → CrewLounge Converter** app.

### Load your files

- Click **Browse…** next to *EFOS MySectors CSV* and select your MySectors file
- The app will read the file and show your detected name (e.g. *Detected user: Nigel LOWRY*) — confirm this looks right
- Click **Browse…** next to *GlobaLog CSV* and select your GlobaLog file

### Date range (optional)

- If you want to convert **all flights**, leave *Process all dates* ticked
- To convert a specific period only, untick that box and enter **From** and **To** dates in DD/MM/YYYY format
- If you overlap dates already in your logbook you will get the flight in twice.  Be careful to limit this to flights not already existing in your logbook.

### User settings

- **Name in output** — choose *SELF* (recommended) or your actual name. CrewLounge uses SELF to identify your own entries.
- **Operator** — defaults to `Jet2`. Change this if needed.

### Output file

- Click **Browse…** next to *Output file* and choose where to save the converted file and what to call it
- Choose **Format**: `csv` (recommended for PIW) or `xlsx`

### Convert

- Click **Convert**
- The progress bar will fill as flights are processed
- When done, you'll see a summary: *X flights processed, Y skipped, Z warnings*

### Review skipped flights and warnings

- Click **View Skipped Flights** to see any flights that were excluded (cancelled sectors, deadhead, no times available)
- Click **View Warnings** to see any flights that need manual attention after import

---

## Step 4 — Import into CrewLounge

1. Open **CrewLounge PilotLog** on your device
2. Go to **Tools → Import Old Flight Data** (or the Import Wizard)
3. Select **Generic TXT / CSV file** (V01)
4. Select your converted output file
5. Work through the wizard steps:
   - **Step 1** — File structure verification (should say OK)
   - **Step 2** — Airfield verification (should say OK)
   - **Step 3** — Test mode parsing — review any warnings, then click *Continue SAVE Mode*
   - **Step 4** — Save mode parsing
   - **Step 5** - Review the added flights in the 'flights' page for accuracy
   - **Step 6** - Go to **Tools → Import Old Flight Data** and accept the last import or roll back as required.

> **Tip:** Run the wizard in **Test Mode** first (Steps 1–3) to check for any issues before committing the import.

---

## What gets imported

| Field | Source |
|-------|--------|
| Date, route, flight number | EFOS |
| Block times, air times | EFOS (or GlobaLog for recent flights) |
| PIC / PICUS / SIC time | Calculated from your EFOS role (PIC, FO, Captain, Instructor flags) |
| IFR time | Set equal to block time (all Jet2 ops are IFR) |
| Aircraft (B737, registration) | EFOS |
| Crew names | EFOS (captain and you) |
| PF / PM | Based on who the Landing Pilot was |

**Not imported** (CrewLounge calculates these after import):
- Night time
- Day/night takeoff and landing splits
- Cross-country time
- Approach types

---

## What gets skipped

The converter automatically excludes:

- **Cancelled / un-operated flights** — where EFOS shows no actual times and no pilots recorded
- **Deadhead sectors** — where you were positioning as a passenger
- **Future flights with no data** — scheduled flights that haven't operated yet and have no GlobaLog record

You can review all skipped flights in the app after conversion.

---

## Troubleshooting

**"Could not auto-detect user"**
— Make sure you selected the correct EFOS MySectors file. The file must contain your name in the seat pilot columns on every row.

**PIW says "Previous Experience" on some records**
— Ensure the B737 aircraft is set up as **Multi Pilot** in your CrewLounge aircraft list before importing. If it isn't, add it manually first, then re-run the import.

**PIW says "Task forced to PF on a Single-Pilot Aircraft"**
— Same fix as above: set up the B737 as Multi Pilot in CrewLounge before importing.

**A flight you expected is missing from the output**
— Check the *View Skipped Flights* list in the app. It will show the reason each flight was excluded.

**Times look wrong on a recent flight**
— Recent flights (where EFOS hasn't updated actual times yet) are sourced from GlobaLog. If that flight isn't in your GlobaLog export, it will be skipped. Make sure your GlobaLog export covers the same date range as your EFOS file.
