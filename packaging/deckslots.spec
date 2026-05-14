from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("deckslots")  # data/templates/ and data/fonts/

a = Analysis(
    ["bin/deckslots"],
    pathex=[],
    datas=datas,
    hiddenimports=["deckslots.gui"],  # lazy import in cli/parser.py
)
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="deckslots",
    console=False,
)
