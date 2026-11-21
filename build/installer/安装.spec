# -*- mode: python ; coding: utf-8 -*-
import os
HERE = os.getcwd()
PAYLOAD = os.path.join(HERE, "payload")
a = Analysis(
    [os.path.join(HERE, "安装程序.py")],
    pathex=[HERE], binaries=[],
    datas=[(PAYLOAD, "payload")],
    hiddenimports=["_winlnk"], hookspath=[], hooksconfig={},
    runtime_hooks=[], excludes=["tkinter.test"], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="安装程序", debug=False, bootloader_ignore_signals=False, strip=False,
    upx=True, upx_exclude=[], runtime_tmpdir=None, console=False,
    disable_windowed_traceback=False, argv_emulation=False, target_arch=None,
    codesign_identity=None, entitlements_file=None,
    icon=os.path.join(PAYLOAD, "app.ico"),
)
