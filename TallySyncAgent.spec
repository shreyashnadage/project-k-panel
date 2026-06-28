# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for Tally Sync Agent
#
# Produces two executables:
#   dist/TallySyncAgent.exe           — the background service / sync agent
#   dist/registration_wizard.exe      — the onboarding GUI (first-run only)
#
# Build:
#   pyinstaller TallySyncAgent.spec

# ---------------------------------------------------------------------------
# Shared settings
# ---------------------------------------------------------------------------
common_datas = [
    ('agent/extractor/tdml_templates', 'agent/extractor/tdml_templates'),
]
common_hidden = [
    'win32api',
    'win32con',
    'win32security',
    'keyring.backends.Windows',
    'keyring.backends._win_crypto',
    'pywintypes',
    'packaging',
    'packaging.version',
]

# ---------------------------------------------------------------------------
# BUILD 1 — background agent (no console window)
# ---------------------------------------------------------------------------
agent_a = Analysis(
    ['agent/main.py'],
    pathex=['.'],
    binaries=[],
    datas=common_datas,
    hiddenimports=common_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib'],
    noarchive=False,
    optimize=1,
)

agent_pyz = PYZ(agent_a.pure)

agent_exe = EXE(
    agent_pyz,
    agent_a.scripts,
    agent_a.binaries,
    agent_a.datas,
    [],
    name='TallySyncAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# ---------------------------------------------------------------------------
# BUILD 2 — registration wizard (GUI, shown once during install)
# ---------------------------------------------------------------------------
wizard_a = Analysis(
    ['installer/wizard/registration_wizard.py'],
    pathex=['.'],
    binaries=[],
    datas=common_datas,
    hiddenimports=common_hidden + ['tkinter', 'tkinter.ttk', 'tkinter.font'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)

wizard_pyz = PYZ(wizard_a.pure)

wizard_exe = EXE(
    wizard_pyz,
    wizard_a.scripts,
    wizard_a.binaries,
    wizard_a.datas,
    [],
    name='registration_wizard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
