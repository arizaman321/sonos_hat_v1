# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['RPi.GPIO', 'gpiozero.pins.rpigpio', 'gpiozero.pins.pigpio', 'gpiozero.pins.lgpio']
hiddenimports += collect_submodules('gpiozero')
hiddenimports += collect_submodules('RPi.GPIO')
hiddenimports += collect_submodules('pigpio')
hiddenimports += collect_submodules('lgpio')


a = Analysis(
    ['controller.py'],
    pathex=[],
    binaries=[],
    datas=[('sonos_config.json', '.')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=True,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [('v', None, 'OPTION')],
    name='controller',
    debug=True,
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
