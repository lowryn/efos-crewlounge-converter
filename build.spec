# PyInstaller spec file for EFOS → CrewLounge Converter
# Run with: pyinstaller build.spec

import sys
import os
from pathlib import Path
import customtkinter

APP_NAME = "EFOS-CrewLounge-Converter"

# CustomTkinter must be bundled with its theme data
ctk_path = Path(customtkinter.__path__[0])

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        (str(ctk_path), "customtkinter"),
    ],
    hiddenimports=[
        "customtkinter",
        "tkinter",
        "tkinter.ttk",
        "pandas",
        "openpyxl",
        "openpyxl.styles.stylesheet",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # no terminal window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows icon (ignored on macOS)
    icon=None,
)

# macOS: wrap the exe in a .app bundle
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name=f"{APP_NAME}.app",
        icon=None,
        bundle_identifier="com.jet2.efos-crewlounge-converter",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "1.0.0",
        },
    )
