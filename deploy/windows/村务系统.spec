# -*- mode: python -*-
a = Analysis(
    ['../../backend/run.py'],
    pathex=['../../backend'],
    datas=[('../../backend/web', 'web')],
    hiddenimports=['uvicorn.logging', 'uvicorn.loops', 'uvicorn.protocols',
                   'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
                   'uvicorn.protocols.websockets', 'uvicorn.lifespan'],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas,
          name='村务系统', console=False, upx=True)
