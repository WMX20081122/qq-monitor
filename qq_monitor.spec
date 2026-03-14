# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 - 优化体积
使用方法: pyinstaller qq_monitor.spec
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 收集必要的依赖
datas = []
hiddenimports = [
    'requests',
    'urllib3',
    'charset_normalizer',
    'idna',
    'certifi',
    'yaml',
    'email.mime.text',
    'email.mime.multipart',
    'email.header',
]

# PyQt5 相关 - 只包含必要模块
hiddenimports += [
    'PyQt5.QtCore',
    'PyQt5.QtGui', 
    'PyQt5.QtWidgets',
]

# 排除不需要的模块
excludes = [
    # 不需要的标准库
    'tkinter',
    'unittest',
    'test',
    'tests',
    'pydoc',
    'doctest',
    'distutils',
    'setuptools',
    'pip',
    # 不需要的第三方库
    'numpy',
    'pandas',
    'matplotlib',
    'PIL',
    'cv2',
    'scipy',
    'sympy',
    'IPython',
    'jupyter',
    'notebook',
    # PyQt5 不需要的模块
    'PyQt5.QtBluetooth',
    'PyQt5.QtDBus',
    'PyQt5.QtDesigner',
    'PyQt5.QtHelp',
    'PyQt5.QtMultimedia',
    'PyQt5.QtMultimediaWidgets',
    'PyQt5.QtNetwork',
    'PyQt5.QtNfc',
    'PyQt5.QtOpenGL',
    'PyQt5.QtPositioning',
    'PyQt5.QtPrintSupport',
    'PyQt5.QtQml',
    'PyQt5.QtQuick',
    'PyQt5.QtQuickWidgets',
    'PyQt5.QtRemoteObjects',
    'PyQt5.QtSensors',
    'PyQt5.QtSerialPort',
    'PyQt5.QtSql',
    'PyQt5.QtSvg',
    'PyQt5.QtTest',
    'PyQt5.QtWebChannel',
    'PyQt5.QtWebEngine',
    'PyQt5.QtWebEngineCore',
    'PyQt5.QtWebEngineWidgets',
    'PyQt5.QtWebSockets',
    'PyQt5.QtXml',
    'PyQt5.QtXmlPatterns',
]

a = Analysis(
    ['qq_monitor.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 移除重复的二进制文件
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='QQMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Linux下可以设为True进一步减小体积
    upx=True,  # 使用UPX压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
