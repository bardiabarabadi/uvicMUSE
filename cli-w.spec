# -*- mode: python ; coding: utf-8 -*-

from kivy.tools.packaging.pyinstaller_hooks import get_deps_minimal, hookspath, runtime_hooks

block_cipher = None


a = Analysis(['cli.py'],
             pathex=['C:\\Users\\bbara\\MUSE\\uvicMUSE'],
             #binaries=[],
             datas=[ ('C:/Users/bbara/.conda/envs/muse-lsl/Lib/site-packages/pylsl/*', 'pylsl/'),
                     ('C:/Users/bbara/.conda/envs/muse-lsl/share/sdl2/bin/*', '.'),
                     ('docs/Header.png', './')
                   ],
             #hiddenimports=[],
             hookspath=[],#hookspath(),
             runtime_hooks=runtime_hooks(),
             #excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             #cipher=block_cipher,
             noarchive=False,
             **get_deps_minimal()
             )
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='uvicmuse',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          icon='docs/uvic.ico'
          )
