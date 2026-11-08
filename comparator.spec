# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

hiddenimports = [
    "main_window",
    "pdf_viewer",
    "markdown_editor",
    "custom_text_edit",
    "config_storage",
    "project_manager",
    "file_pattern",
    "highlighter",
    "invisible_chars_highlighter",
    "search_replace_bar",
    "search_replace_dialog",
    "shortcuts_manager",
    "preferences_dialog",
    "highlight_config",
    "offset_config",
    "text_cleaner_panel",
    "orphan_couples_panel",
    "color_utils",
    "fitz",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "torch", "tensorflow", "transformers", "pandas", "scipy", "sklearn",
        "matplotlib", "notebook", "jupyter", "IPython", "pytest", "cv2",
        "onnxruntime", "yt_dlp", "sympy", "audio_separator",
    ],
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
    name="Comparator",
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
)
