# pyinstaller/bsp2stk-cli.spec
from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ['../src/bsp2stk/__main__.py'],
    pathex=[],
    binaries=[],
    datas=collect_data_files('spiceypy') + collect_data_files('jplephem'),
    hiddenimports=[
        'spiceypy',
        'numpy',
        'scipy',
        'jplephem',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='bsp2stk-cli.exe',
    icon=None,
    debug=False,
    console=True,
)