# PyInstaller spec — onedir, с правами администратора (нужно для WinDivert)
import os
from PyInstaller.utils.hooks import collect_submodules
ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
a = Analysis(
    [os.path.join(ROOT, "app", "main.py")],
    pathex=[os.path.join(ROOT, "app")],
    datas=[(os.path.join(ROOT, "assets"), "assets")],
    # зависимости tg-ws-proxy (его исходники лежат снаружи в components/tgproxy и обновляются)
    hiddenimports=["PySide6.QtSvg", "certifi", "ctypes.util",
                   "asyncio", "ssl", "http.client", "logging.handlers", "hashlib", "hmac",
                   "secrets", "base64", "ipaddress", "dataclasses", "struct", "urllib.request", "urllib.parse",
                   "string", "random", "argparse", "collections", "concurrent.futures", "zlib", "gzip"]
                  + [m for p in ("httpx", "httpcore", "h11", "h2", "hpack", "hyperframe", "anyio", "sniffio", "idna")
                     for m in collect_submodules(p) if ".tests" not in m and "trio" not in m],
    excludes=["tkinter", "customtkinter", "pystray", "unittest", "pydoc", "test", "lib2to3", "cryptography", "psutil", "PIL", "PySide6.QtNetwork"],
)
# ── уменьшение размера: выкидываем ненужные части Qt ──
DROP = ("qt6network", "qtnetwork", "opengl32sw", "d3dcompiler", "qt6pdf", "qt6quick", "qt6qml", "qt6opengl", "qt6virtualkeyboard",
        "translations", "qtvirtualkeyboard", "qwebp", "qtiff", "qgif", "qjpeg", "qicns", "qtga", "qwbmp", "qpdf",
        "qnetworklistmanager", "qtuiotouchplugin", "libcrypto-3-x64.dll.not", "qminimal", "qoffscreen", "qdirect2d")
def keep(entry):
    n = entry[0].replace("\\", "/").lower()
    return not any(d in n for d in DROP)
a.binaries = [b for b in a.binaries if keep(b)]
a.datas = [d for d in a.datas if keep(d)]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="ZapreTYZ",
          icon=os.path.join(ROOT, "assets", "icon.ico"), console=False, uac_admin=True,
          version=None)
coll = COLLECT(exe, a.binaries, a.datas, name="ZapreTYZ")
