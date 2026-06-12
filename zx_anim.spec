from pathlib import Path


root = Path(SPECPATH)

a = Analysis(
    ["zx_anim.py"],
    pathex=[str(root)],
    binaries=[],
    datas=[
        ("characters", "characters"),
        ("lock.wav", "."),
        ("unlock.wav", "."),
        ("icon.ico", "."),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ZX Anim",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon="icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ZX Anim",
)
