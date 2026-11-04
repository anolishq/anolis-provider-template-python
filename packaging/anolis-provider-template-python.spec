# PyInstaller spec: one self-contained executable, bin/anolis-provider-template-python
# in the release tarball. Build with `just freeze`; the result is
# dist/anolis-provider-template-python.
# -*- mode: python -*-

from PyInstaller.utils.hooks import copy_metadata

datas = (
    # importlib.metadata lookups: the provider and the SDK report their versions from these.
    copy_metadata("anolis-provider-template-python")
    + copy_metadata("anolis-provider-sdk")
)

a = Analysis(
    ["entry.py"],
    datas=datas,
    excludes=["tkinter"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="anolis-provider-template-python",
    console=True,
    strip=False,
    upx=False,
)
