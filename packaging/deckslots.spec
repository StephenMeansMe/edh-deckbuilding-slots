from PyInstaller.utils.hooks import collect_data_files
import os

datas = collect_data_files("deckslots")  # data/templates/ and data/fonts/

a = Analysis(
    [os.path.join(os.path.dirname(SPECPATH), "bin", "deckslots")],
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
