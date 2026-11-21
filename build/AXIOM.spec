# -*- mode: python ; coding: utf-8 -*-
"""AXIOM · Model K4 / Alpha 3 主程序单文件打包配置。
入口 = launcher.pyw（启动器），内嵌 app.py + core/ + ui/。
"""
import os

APP_SRC = os.path.join(os.getcwd(), "app_src")

a = Analysis(
    [os.path.join(APP_SRC, "launcher.pyw")],
    pathex=[APP_SRC],
    binaries=[],
    datas=[
        (os.path.join(APP_SRC, "config.json"), "."),
        (os.path.join(APP_SRC, "assets"), "assets"),
        (os.path.join(APP_SRC, "web"), "web"),
        (os.path.join(APP_SRC, "core", "content_data.py"), "core"),
    ],
    hiddenimports=[
        "app", "core.storage", "core.theme", "core.content", "core.difficulty",
        "core.debug", "core.importer", "core.content_data", "ui.widgets", "ui.anim",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "numpy", "PIL", "pandas", "tkinter.test"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AXIOM",
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
    icon=os.path.join(APP_SRC, "assets", "app.ico"),
)
