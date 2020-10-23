# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
from kivy.tools.packaging.pyinstaller_hooks import get_deps_minimal, hookspath, runtime_hooks

a = Analysis(['cli.py'],
             pathex=['/Users/krigolsonlab/Downloads/uvicmuse'],
             #binaries=[],
             datas=[ ('docs/Header.png','./') ,


	     ('/Users/krigolsonlab/miniconda3/envs/muse/lib/python3.6/site-packages/pylsl/lib/*','pylsl/lib/')
			     ],
             #hiddenimports=[],
             hookspath=[],
             runtime_hooks=runtime_hooks(),
             #excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
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
          name='uvicmuse-mac',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
app = BUNDLE(exe,
             name='uvicmuse.app',
             icon='docs/uvic.ico',
             bundle_identifier=None)
