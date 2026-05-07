# -*- mode: python ; coding: utf-8 -*-

import sys
import os

# Add src to path for Analysis
sys.path.insert(0, os.path.join(SPECPATH, 'src'))

block_cipher = None

# Collect portchecker package files
portchecker_src = os.path.join('src', 'portchecker')
portchecker_files = [(os.path.join(portchecker_src, f), 'portchecker') 
                     for f in os.listdir(portchecker_src) 
                     if f.endswith('.py')]

a = Analysis(
    ['portchecker_build.py'],
    pathex=['src'],
    binaries=[],
    datas=portchecker_files,
    hiddenimports=[
        'portchecker',
        'portchecker.cli',
        'portchecker.models',
        'portchecker.scanner',
        'portchecker.security',
        'portchecker.fingerprint',
        'portchecker.process_control',
        'portchecker.config',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='portchecker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
