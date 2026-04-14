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

if sys.platform == "darwin":
    # macOS: onedir mode — binaries live inside the .app bundle permanently,
    # no temp-directory extraction on launch → instant startup, no dock flicker.
    exe = EXE(
        pyz,
        a.scripts,
        exclude_binaries=True,      # binaries go into COLLECT, not the exe
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        target_arch="universal2",   # fat binary: Intel + Apple Silicon in one
        codesign_identity=None,
        entitlements_file=None,
        icon=None,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_NAME,
    )

    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=None,
        bundle_identifier="com.jet2.efos-crewlounge-converter",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "1.0.0",
        },
    )

else:
    # Windows: onefile mode — single self-contained .exe
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
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,
    )
