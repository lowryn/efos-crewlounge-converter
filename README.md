# EFOS → CrewLounge Converter

Converts Jet2 pilot flight data from two CSV sources — **EFOS MySectors** and **GlobaLog** — into a CSV file ready for import into **CrewLounge PilotLog** via the Import Wizard (PIW).

Built for Jet2 pilots who need to batch-populate their CrewLounge logbook with historical and ongoing flight data.

---

## What it does

- Reads your EFOS MySectors export and GlobaLog export
- Automatically detects which pilot is you
- Matches flights between the two sources using date, flight number, and route
- Uses EFOS times where available, falls back to GlobaLog for recent flights
- Determines PIC / PICUS / SIC / Instructor time from your EFOS role flags
- Skips cancelled flights and deadhead sectors
- Outputs a semicolon-delimited CSV (or XLSX) in the exact format CrewLounge PIW expects

---

## Running from source

Requires Python 3.11+.

```bash
# Clone and set up
git clone https://github.com/lowryn/efos-crewlounge-converter.git
cd efos-crewlounge-converter

python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run
python main.py
```

---

## Building a standalone app

```bash
# macOS
pyinstaller --onefile --windowed --name "EFOS-CrewLounge-Converter" main.py

# Windows (run from a Windows machine)
pyinstaller --onefile --windowed --name "EFOS-CrewLounge-Converter" main.py
```

The output will be in the `dist/` folder — a single file that needs no Python installation.

---

## Usage

See [USER_GUIDE.md](USER_GUIDE.md) for step-by-step instructions aimed at non-technical users.

---

## Project structure

```
core/           Parsing, merging, role logic, transformation
gui/            CustomTkinter application window and dialogs
config/         Settings persistence and defaults
tests/          Unit tests (pytest)
main.py         Entry point
```

---

## Tech stack

| Component | Library |
|-----------|---------|
| GUI | CustomTkinter |
| CSV processing | pandas |
| Packaging | PyInstaller |
| Tests | pytest |
