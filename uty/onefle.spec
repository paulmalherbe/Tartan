# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None
data = [
    ('doc/*', 'doc'),
    ('../pygal/css/*.css', 'pygal/css')]
if sys.version_info[:2][0] == "2":
    data.append(('c:/windows/system32/api-ms-win-crt-*.dll', '.'))
data.extend(collect_data_files('tkinterhtml'))
a = Analysis(['ms0000.py'],
        pathex=['.'],
        binaries=[],
        datas=data,
        hiddenimports=['tkinter', 'tarimp',
            'babel.dates', 'babel.numbers',
            'pyexcel_ods', 'pyexcel_ods.odsr', 'pyexcel_ods.odsw',
            'pyexcel_xls', 'pyexcel_xls.xlsr', 'pyexcel_xls.xlsw',
            'pyexcel_io.writers', 'pyexcel_io.writers.csvw',
            'pyexcel_io.writers.csvz', 'pyexcel_io.writers.tsv',
            'pyexcel_io.writers.tsvz', 'PIL._tkinter_finder',
            'pywintypes'],
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=['PyQt4', 'PyQt5'],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=block_cipher,
        noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='ms0000',
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
        entitlements_file=None)
