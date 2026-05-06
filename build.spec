# -*- mode: python ; coding: utf-8 -*-
"""
Spec do PyInstaller para empacotar PDF-to-Markdown em modo --onedir.
Build: pyinstaller --noconfirm --clean build.spec
Saída: dist/PDF-to-Markdown/PDF-to-Markdown.exe
"""
import os
from PyInstaller.utils.hooks import collect_all, collect_data_files

# Coleta arquivos auxiliares de pacotes que dependem de recursos não-Python
datas = []
binaries = []
hiddenimports = []

# CustomTkinter inclui temas JSON e assets
datas += collect_data_files("customtkinter")

# tkinterdnd2 carrega DLLs nativas (TkDnD) — precisa coletar tudo
_d, _b, _h = collect_all("tkinterdnd2")
datas += _d
binaries += _b
hiddenimports += _h

# Ícone opcional. Se assets/icon.ico não existir, PyInstaller ignora e usa default.
ICON_PATH = os.path.join("assets", "icon.ico")
icon_arg = ICON_PATH if os.path.isfile(ICON_PATH) else None


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PDF-to-Markdown",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                 # UPX pode acionar antivírus
    console=False,             # --windowed: sem terminal preto
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_arg,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="PDF-to-Markdown",
)
