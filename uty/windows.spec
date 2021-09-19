# -*- mode: python -*-
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None
data = [
    ('doc/*', 'doc'),
    ('../pygal/css/*.css', 'pygal/css')]
data.extend(collect_data_files('tkinterhtml'))
a = Analysis(['ms0000.py'],
        pathex=['.'],
        binaries=[],
        datas=data,
        hiddenimports=['tkinter', 'tarimp', 'pyexcel_io.writers', 'pyexcel_ods', 'pyexcel_ods.odsr', 'pyexcel_ods.odsw'],

        hookspath=[],
        runtime_hooks=[],
        excludes=['PyQt4', 'PyQt5'],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=block_cipher,
        noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='ms0000',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False)
coll = COLLECT(exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name='ms0000')
