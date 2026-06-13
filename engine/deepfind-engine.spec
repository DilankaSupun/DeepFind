# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

block_cipher = None

# Hidden imports for dynamic modules and dependencies
hidden_imports = []
hidden_imports += collect_submodules('uvicorn')
hidden_imports += collect_submodules('sentence_transformers')
hidden_imports += collect_submodules('transformers')
hidden_imports += collect_submodules('torch')
hidden_imports += collect_submodules('faiss')
hidden_imports += collect_submodules('pypdf')
hidden_imports += collect_submodules('docx')
hidden_imports += collect_submodules('watchdog')
hidden_imports += collect_submodules('tokenizers')

# Engine modules
hidden_imports += [
    'database',
    'api',
    'indexer',
    'scanner',
    'ai',
    'config',
    'runtime_control'
]

datas = [
    # Include bundled models. We download this via our script.
    ('bundled_models', 'bundled_models'),
    # Include SQL schema
    ('database/schema.sql', 'database'),
]

datas += collect_data_files('sentence_transformers')
datas += collect_data_files('transformers')
datas += collect_data_files('torch')
datas += collect_data_files('tokenizers')

datas += copy_metadata('sentence_transformers')
datas += copy_metadata('transformers')
datas += copy_metadata('torch')
datas += copy_metadata('tqdm')
datas += copy_metadata('regex')
datas += copy_metadata('packaging')
datas += copy_metadata('filelock')
datas += copy_metadata('numpy')
datas += copy_metadata('tokenizers')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tests', 'scripts', 'pytest', 'scipy.spatial.cKDTree'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='deepfind-engine',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, # Must be true to debug easily, or Electron hides it
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='deepfind-engine',
)
