"""ZapreTYZ — точка входа."""
import os
import sys
from pathlib import Path


def _tgproxy_mode():
    # Дочерний режим: ZapreTYZ.exe --tgproxy <аргументы tg-ws-proxy>
    base = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(base / "components" / "tgproxy"))
    # cryptography не упакован (экономия ~15 МБ): AES берётся из libcrypto-3.dll,
    # который уже есть в Python — подсказываем его путь для proxy/_aes.py
    import ctypes.util
    _orig = ctypes.util.find_library
    internal = Path(getattr(sys, "_MEIPASS", base))
    dll = next(iter(sorted(internal.glob("libcrypto-*.dll"))), None)
    ctypes.util.find_library = lambda n: str(dll) if (n == "crypto" and dll) else _orig(n)
    if "--selftest-aes" in sys.argv:
        from proxy._aes import Cipher, algorithms, modes  # noqa
        enc = Cipher(algorithms.AES(b"k" * 32), modes.CTR(b"i" * 16)).encryptor()
        print("AES OK", enc.update(b"hello").hex())
        return
    if os.name == "nt":   # прокси — обычный приоритет (интерфейс работает с пониженным)
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x20)
    sys.argv = ["tg-ws-proxy"] + sys.argv[2:]
    try:
        from proxy.tg_ws_proxy import main as tg_main  # noqa
    except Exception as e:      # без всплывающего окна PyInstaller — ошибка уйдёт в консоль программы
        print(f"✖ TG WS Proxy не запустился: {type(e).__name__}: {e}", flush=True)
        print("✖ Возможно, новая версия прокси требует библиотеку, которой нет в программе. "
              "Обновите Yume Haze Zapret.", flush=True)
        sys.exit(1)
    tg_main()


if len(sys.argv) > 1 and sys.argv[1] == "--tgproxy":
    _tgproxy_mode()
    sys.exit(0)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtGui import QIcon  # noqa: E402
import socket  # noqa: E402
import threading  # noqa: E402
from PySide6.QtCore import QObject, Signal  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

import core  # noqa: E402
import ui  # noqa: E402

INSTANCE_PORT = 47913


class _Bridge(QObject):
    show = Signal()


def main():
    if core.IS_WIN:
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ZapreTYZ.App")
        except Exception:
            pass

    try:   # размер интерфейса (применяется при запуске)
        import json as _j
        sc = int(_j.loads(core.SETTINGS_FILE.read_text("utf-8")).get("ui_scale", 100))
        if sc != 100:
            os.environ["QT_SCALE_FACTOR"] = str(sc / 100)
    except Exception:
        pass
    app = QApplication(sys.argv)
    app.setApplicationName(core.APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    # единственный экземпляр: второй запуск просто показывает окно первого
    try:
        c = socket.create_connection(("127.0.0.1", INSTANCE_PORT), timeout=0.3)
        c.sendall(b"show")
        c.close()
        return 0
    except OSError:
        pass
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        srv.bind(("127.0.0.1", INSTANCE_PORT))
        srv.listen(2)
    except OSError:
        srv = None
    bridge = _Bridge()

    def _accept():
        while srv:
            try:
                conn, _ = srv.accept()
                conn.close()
                bridge.show.emit()
            except OSError:
                break
    if srv:
        threading.Thread(target=_accept, daemon=True).start()

    icon = QIcon(str(core.ASSETS / "icon.ico"))
    app.setWindowIcon(icon)

    core.set_low_priority()
    s = core.Settings()
    ui.set_theme(s.data.get("theme", "blue"))
    app.setStyleSheet(ui.build_qss())
    zapret = core.Zapret(s)
    tg = core.TgProxy(s)
    updater = core.Updater(zapret, tg)
    win = ui.MainWindow(s, zapret, tg, updater, icon)

    bridge.show.connect(win.show_window)

    core.log("app", f"{core.APP_NAME} v{core.APP_VERSION} запущен. Zapret {zapret.version()}, TG WS Proxy {tg.version()}")
    if core.IS_WIN and not core.is_admin():
        core.log("app", "⚠ Нет прав администратора — Zapret (WinDivert) работать не будет.")

    minimized = "--minimized" in sys.argv or s["start_minimized"]
    if not minimized:
        win.show()

    zapret.sync()

    def autorun():
        if s["restore_state"]:
            if s["tg_was_on"]:
                tg.start()
        updater.check("zapret")
        updater.check("tg")
    QTimer.singleShot(600, autorun)

    rc = app.exec()
    return rc


if __name__ == "__main__":
    sys.exit(main())
