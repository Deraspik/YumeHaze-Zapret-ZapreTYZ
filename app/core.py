"""
ZapreTYZ — ядро: пути, настройки, управление Zapret (winws.exe) и TG WS Proxy,
обновления компонентов.
"""
from __future__ import annotations

import io
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
import zipfile
from pathlib import Path

from PySide6.QtCore import QObject, Signal

APP_NAME = "ZapreTYZ"          # внутреннее имя (папки, задачи)
DISPLAY_NAME = "Yume Haze Zapret"
APP_VERSION = "1.0.2"

IS_WIN = os.name == "nt"
CREATE_NO_WINDOW = 0x08000000 if IS_WIN else 0

ZAPRET_REPO = "Flowseal/zapret-discord-youtube"
TG_REPO = "Flowseal/tg-ws-proxy"
ZAPRET_VERSION_URL = f"https://raw.githubusercontent.com/{ZAPRET_REPO}/main/.service/version.txt"
IPSET_URL = f"https://raw.githubusercontent.com/{ZAPRET_REPO}/refs/heads/main/.service/ipset-service.txt"
HOSTS_URL = f"https://raw.githubusercontent.com/{ZAPRET_REPO}/refs/heads/main/.service/hosts"
TG_VERSION_URL = f"https://raw.githubusercontent.com/{TG_REPO}/main/proxy/__init__.py"


# ───────────────────────────── Пути ─────────────────────────────
def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE = base_dir()
COMPONENTS = BASE / "components"
ZAPRET_DIR = COMPONENTS / "zapret"
TG_DIR = COMPONENTS / "tgproxy"
ASSETS = (Path(getattr(sys, "_MEIPASS", BASE)) / "assets")
if not ASSETS.exists():
    ASSETS = BASE / "assets"

DATA_DIR = Path(os.environ.get("APPDATA", Path.home() / ".config")) / APP_NAME
DATA_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = DATA_DIR / "settings.json"


# ─────────────────────────── Настройки ───────────────────────────
DEFAULTS = {
    "strategy": "general.bat",
    "theme": "blue",
    "autostart": False,
    "start_minimized": False,
    "close_to_tray": True,
    "zapret_on_launch": False,
    "tg_on_launch": False,
    "zapret_was_on": False,
    "tg_was_on": False,
    "restore_state": True,
    "auto_quick_test": True,
    "skip_valve": True,
    "tg": {
        "host": "127.0.0.1",
        "port": 1443,
        "secret": "",
        "dc_ip": ["2:149.154.167.220", "4:149.154.167.220"],
        "pool_size": 4,
        "buf_kb": 256,
        "fake_tls_domain": "",
        "cfproxy": True,
        "cfproxy_domains": "",
        "cfproxy_worker_domains": "",
        "no_secure": False,
        "verbose": False,
    },
}


class Settings:
    def __init__(self):
        self.data = json.loads(json.dumps(DEFAULTS))
        try:
            loaded = json.loads(SETTINGS_FILE.read_text("utf-8"))
            tg = loaded.pop("tg", {})
            self.data.update(loaded)
            self.data["tg"].update(tg)
        except Exception:
            pass
        if not re.fullmatch(r"[0-9a-fA-F]{32}", self.data["tg"].get("secret") or ""):
            self.data["tg"]["secret"] = secrets.token_hex(16)
        self.save()

    def __getitem__(self, k):
        return self.data[k]

    def __setitem__(self, k, v):
        self.data[k] = v
        self.save()

    def save(self):
        try:
            SETTINGS_FILE.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), "utf-8")
        except Exception:
            pass


# ─────────────────────────── Утилиты ───────────────────────────
def run_quiet(cmd, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                          creationflags=CREATE_NO_WINDOW, **kw)


GH_MIRRORS = ["https://ghfast.top/", "https://gh-proxy.com/", "https://ghproxy.net/"]


def http_get(url: str, timeout=15) -> bytes:
    """GET; для github.com / raw.githubusercontent.com при ошибке пробует зеркала."""
    urls = [url]
    if url.startswith(("https://github.com/", "https://raw.githubusercontent.com/")):
        urls += [m + url for m in GH_MIRRORS]
    err = None
    for u in urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}",
                                                     "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            err = e
    raise err


def gh_latest_release(repo: str) -> dict:
    return json.loads(http_get(f"https://api.github.com/repos/{repo}/releases/latest"))


def win_service_state(name: str) -> int:
    """0 — службы нет, иначе dwCurrentState (1 STOPPED … 4 RUNNING)."""
    import ctypes
    from ctypes import wintypes
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    adv.OpenSCManagerW.restype = wintypes.HANDLE
    adv.OpenServiceW.restype = wintypes.HANDLE
    adv.OpenServiceW.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR, wintypes.DWORD]
    adv.QueryServiceStatus.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    adv.CloseServiceHandle.argtypes = [wintypes.HANDLE]
    scm = adv.OpenSCManagerW(None, None, 0x0001)          # SC_MANAGER_CONNECT
    if not scm:
        return 0
    try:
        h = adv.OpenServiceW(scm, name, 0x0004)            # SERVICE_QUERY_STATUS
        if not h:
            return 0
        try:
            buf = (wintypes.DWORD * 7)()
            if not adv.QueryServiceStatus(h, ctypes.byref(buf)):
                return 0
            return int(buf[1])
        finally:
            adv.CloseServiceHandle(h)
    finally:
        adv.CloseServiceHandle(scm)


def set_low_priority():
    """Интерфейс — с пониженным приоритетом, чтобы не мешать играм."""
    if not IS_WIN:
        return
    try:
        import ctypes
        k = ctypes.windll.kernel32
        k.SetPriorityClass(k.GetCurrentProcess(), 0x00004000)   # BELOW_NORMAL_PRIORITY_CLASS
    except Exception:
        pass


# Порты Steam / Valve (CS2, Dota 2, SDR-релеи) — их Zapret не трогает
VALVE_PORTS = (27000, 27200)


def exclude_ports(spec: str, lo: int, hi: int) -> str:
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        a, _, b = part.partition("-")
        a, b = int(a), int(b or a)
        if b < lo or a > hi:
            out.append((a, b))
            continue
        if a < lo:
            out.append((a, lo - 1))
        if b > hi:
            out.append((hi + 1, b))
    return ",".join(f"{a}-{b}" if a != b else str(a) for a, b in out) or "12"


def is_admin() -> bool:
    if not IS_WIN:
        return os.geteuid() == 0 if hasattr(os, "geteuid") else False
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


class LogBus(QObject):
    line = Signal(str, str)  # source, text


LOG = LogBus()


def log(src: str, text: str):
    LOG.line.emit(src, text)


# ───────────────────────────── ZAPRET ─────────────────────────────
class Zapret(QObject):
    state_changed = Signal(bool)

    def __init__(self, settings: Settings):
        super().__init__()
        self.s = settings
        self.proc = None
        self._on = False
        self._busy = False

    # --- информация ---
    @property
    def bin_dir(self) -> Path:
        return ZAPRET_DIR / "bin"

    @property
    def lists_dir(self) -> Path:
        return ZAPRET_DIR / "lists"

    @property
    def utils_dir(self) -> Path:
        return ZAPRET_DIR / "utils"

    def installed(self) -> bool:
        return (self.bin_dir / "winws.exe").exists()

    def version(self) -> str:
        try:
            m = re.search(r'LOCAL_VERSION=([\w.\-]+)', (ZAPRET_DIR / "service.bat").read_text("utf-8", "replace"))
            return m.group(1) if m else "?"
        except Exception:
            return "не установлен"

    def strategies(self) -> list[str]:
        if not ZAPRET_DIR.exists():
            return []
        items = [p.name for p in ZAPRET_DIR.glob("*.bat") if p.name.lower() != "service.bat"]

        def key(n):
            nums = re.findall(r"\d+", n)
            return (0 if n.lower() == "general.bat" else 1, n.split("(")[0], int(nums[0]) if nums else 0, n)
        return sorted(items, key=key)

    def running(self) -> bool:
        return self._on

    # --- Game filter ---
    @property
    def game_file(self) -> Path:
        return self.utils_dir / "game_filter.enabled"

    def game_filter(self) -> dict:
        res = {"mode": "disabled", "tcp": "1024-65535", "udp": "1024-65535"}
        if not self.game_file.exists():
            return res
        for line in self.game_file.read_text("utf-8", "replace").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                k, v = k.strip().lower(), v.strip()
                if k == "mode" and v:
                    res["mode"] = v.lower()
                elif k in ("tcp", "udp") and v and re.fullmatch(r"[\d,\-]+", v):
                    res[k] = v
            elif line.strip().lower() in ("all", "tcp", "udp"):
                res["mode"] = line.strip().lower()
        return res

    def set_game_filter(self, mode: str, tcp: str, udp: str):
        self.utils_dir.mkdir(parents=True, exist_ok=True)
        if mode == "disabled":
            if self.game_file.exists():
                self.game_file.unlink()
            return
        self.game_file.write_text(f"mode={mode}\ntcp={tcp}\nudp={udp}\n", "utf-8")

    # --- IPSet ---
    @property
    def ipset_file(self) -> Path:
        return self.lists_dir / "ipset-all.txt"

    def ipset_mode(self) -> str:
        try:
            txt = self.ipset_file.read_text("utf-8", "replace")
        except Exception:
            return "any"
        if not txt.strip():
            return "any"
        if "203.0.113.113/32" in txt:
            return "none"
        return "loaded"

    def set_ipset_mode(self, mode: str):
        cur = self.ipset_mode()
        if mode == cur:
            return
        backup = self.lists_dir / "ipset-all.txt.backup"
        if cur == "loaded":
            shutil.copyfile(self.ipset_file, backup)
        if mode == "none":
            self.ipset_file.write_text("203.0.113.113/32\n", "utf-8")
        elif mode == "any":
            self.ipset_file.write_text("", "utf-8")
        elif mode == "loaded":
            if backup.exists():
                shutil.copyfile(backup, self.ipset_file)
            else:
                raise RuntimeError("Нет резервной копии списка. Обновите IPSet-лист.")

    def update_ipset(self):
        data = http_get(IPSET_URL)
        self.ipset_file.write_bytes(data)
        log("zapret", f"IPSet-лист обновлён ({len(data.splitlines())} строк)")

    def update_hosts(self):
        data = http_get(HOSTS_URL).decode("utf-8", "replace")
        hosts = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/drivers/etc/hosts"
        cur = hosts.read_text("utf-8", "replace") if hosts.exists() else ""
        start, end = "# ZapreTYZ-BEGIN", "# ZapreTYZ-END"
        cur = re.sub(rf"{start}.*?{end}\n?", "", cur, flags=re.S)
        cur = cur.rstrip() + f"\n\n{start}\n{data.strip()}\n{end}\n"
        hosts.write_text(cur, "utf-8")
        log("zapret", "Файл hosts обновлён")

    # --- Пользовательские списки ---
    def ensure_user_lists(self):
        self.lists_dir.mkdir(parents=True, exist_ok=True)
        defaults = {
            "ipset-exclude-user.txt": "203.0.113.113/32\n",
            "list-general-user.txt": "# Never leave this file empty\ndomain.example.abc\n",
            "list-exclude-user.txt": "domain.example.abc\n",
        }
        for name, content in defaults.items():
            p = self.lists_dir / name
            if not p.exists():
                p.write_text(content, "utf-8")

    # --- Разбор .bat стратегии ---
    def build_args(self, strategy: str) -> str:
        text = (ZAPRET_DIR / strategy).read_text("utf-8", "replace")
        lines = text.splitlines()
        cmd = None
        for i, ln in enumerate(lines):
            if "winws.exe" in ln.lower() and ln.strip().lower().startswith("start"):
                parts = []
                j = i
                while j < len(lines):
                    cur = lines[j].rstrip()
                    if cur.endswith("^"):
                        parts.append(cur[:-1].strip())
                        j += 1
                    else:
                        parts.append(cur.strip())
                        break
                cmd = " ".join(parts)
                break
        if not cmd:
            raise RuntimeError(f"Не удалось найти команду winws.exe в {strategy}")
        m = re.search(r'winws\.exe"?\s*(.*)$', cmd, re.I)
        args = m.group(1)

        gf = self.game_filter()
        mode = gf["mode"]
        gtcp = gf["tcp"] if mode in ("all", "tcp") else "12"
        gudp = gf["udp"] if mode in ("all", "udp") else "12"
        gany = gf["tcp"] if mode in ("all", "tcp") else (gf["udp"] if mode == "udp" else "12")
        if self.s.data.get("skip_valve", True):
            gtcp, gudp, gany = (exclude_ports(x, *VALVE_PORTS) if x != "12" else x for x in (gtcp, gudp, gany))
        repl = {
            "%BIN%": str(self.bin_dir) + "\\",
            "%LISTS%": str(self.lists_dir) + "\\",
            "%~dp0": str(ZAPRET_DIR) + "\\",
            "%GameFilterTCP%": gtcp,
            "%GameFilterUDP%": gudp,
            "%GameFilter%": gany,
        }
        for k, v in repl.items():
            args = re.sub(re.escape(k), lambda _m, v=v: v, args, flags=re.I)
        left = re.findall(r"%[A-Za-z_~0-9]+%", args)
        if left:
            log("zapret", f"⚠ Неизвестные переменные в стратегии: {', '.join(set(left))}")
        return args

    # --- Запуск/остановка: через службу Windows «zapret» (как service.bat) ---
    # Включение слайдера = установка и запуск службы → Zapret работает сразу при
    # включении ПК, даже без запуска программы. Выключение = удаление службы.
    SERVICE = "zapret"

    def kill_all(self):
        if IS_WIN:
            run_quiet(["taskkill", "/F", "/IM", "winws.exe"])

    def service_state(self) -> str:
        """Через WinAPI — без запуска sc.exe (запуск процессов раз в N секунд давал фризы в играх)."""
        if not IS_WIN:
            return "none"
        st = win_service_state(self.SERVICE)
        if st in (2, 4):          # START_PENDING, RUNNING
            return "running"
        if st in (1, 3):          # STOPPED, STOP_PENDING
            return "stopped"
        return "none"

    def service_strategy(self) -> str:
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                rf"System\CurrentControlSet\Services\{self.SERVICE}") as k:
                v = winreg.QueryValueEx(k, "zapret-discord-youtube")[0]
            return (str(v).strip() + ".bat") if v else ""
        except OSError:
            return ""

    def _set_on(self, on: bool):
        if on != self._on:
            self._on = on
            self.state_changed.emit(on)

    def _poll(self):
        import time as _t
        while True:
            _t.sleep(5)
            if self._busy:
                continue
            try:
                self._set_on(self.service_state() == "running")
            except Exception:
                pass

    def sync(self):
        """Прочитать состояние службы при запуске программы."""
        st = self.service_state()
        if st != "none":
            cur = self.service_strategy()
            if cur and cur in self.strategies() and cur != self.s["strategy"]:
                self.s["strategy"] = cur
        self._set_on(st == "running")
        if not getattr(self, "_poller", None):
            self._poller = threading.Thread(target=self._poll, daemon=True)
            self._poller.start()

    def _bg(self, fn, sync):
        if sync:
            fn()
        else:
            threading.Thread(target=fn, daemon=True).start()

    def start(self, strategy: str | None = None, sync=False):
        self._bg(lambda: self._start(strategy), sync)

    def _start(self, strategy=None):
        strategy = strategy or self.s["strategy"]
        if not self.installed():
            log("zapret", "✖ Zapret не установлен. Откройте вкладку «Обновления».")
            self.state_changed.emit(False)
            return
        self._busy = True
        try:
            self.ensure_user_lists()
            args = self.build_args(strategy)
            exe = self.bin_dir / "winws.exe"
            log("zapret", f"▶ Запуск {strategy[:-4]} (служба Windows, автозапуск с системой)")
            run_quiet(["net", "stop", self.SERVICE])
            run_quiet(["sc", "delete", self.SERVICE])
            self.kill_all()
            bin_path = f'"{exe}" {args}'.replace('"', '\\"')
            r = run_quiet(f'sc create {self.SERVICE} binPath= "{bin_path}" DisplayName= "zapret" start= auto')
            if r.returncode != 0:
                raise RuntimeError((r.stdout + r.stderr).strip() or "sc create failed")
            run_quiet(["sc", "description", self.SERVICE, "Zapret DPI bypass (Yume Haze Zapret)"])
            run_quiet(["sc", "failure", self.SERVICE, "reset=", "0", "actions=", "restart/5000"])
            run_quiet(["reg", "add", rf"HKLM\System\CurrentControlSet\Services\{self.SERVICE}", "/v",
                       "zapret-discord-youtube", "/t", "REG_SZ", "/d", strategy[:-4], "/f"])
            run_quiet(["sc", "start", self.SERVICE])
            import time as _t
            for _ in range(20):
                if self.service_state() == "running":
                    break
                _t.sleep(0.3)
            on = self.service_state() == "running"
            log("zapret", "✔ Zapret работает" if on else "✖ Служба не запустилась — запустите «Диагностику» во вкладке «Тесты»")
            self.s["zapret_was_on"] = on
            self._busy = False
            self._on = not on
            self._set_on(on)
        except Exception as e:
            log("zapret", f"✖ Ошибка запуска: {e}")
            self._busy = False
            self._on = True
            self._set_on(False)

    def stop(self, remember=True, sync=False):
        self._bg(lambda: self._stop(remember), sync)

    def _stop(self, remember=True):
        self._busy = True
        run_quiet(["net", "stop", self.SERVICE])
        run_quiet(["sc", "delete", self.SERVICE])
        self.kill_all()
        if remember:
            self.s["zapret_was_on"] = False
        log("zapret", "■ Zapret остановлен (служба удалена из автозапуска)")
        self._busy = False
        self._on = True
        self._set_on(False)

    def restart(self, sync=False):
        self._bg(lambda: (self._start()), sync)

    def remove_services(self):
        for svc in ("zapret", "WinDivert", "WinDivert14"):
            run_quiet(["net", "stop", svc])
            run_quiet(["sc", "delete", svc])
        log("zapret", "Службы zapret / WinDivert удалены")


# ─────────────────────────── TG WS PROXY ───────────────────────────
class TgProxy(QObject):
    state_changed = Signal(bool)

    def __init__(self, settings: Settings):
        super().__init__()
        self.s = settings
        self.proc: subprocess.Popen | None = None
        self._stopping = False

    def installed(self) -> bool:
        return (TG_DIR / "proxy" / "tg_ws_proxy.py").exists()

    def version(self) -> str:
        try:
            m = re.search(r'__version__\s*=\s*["\']([^"\']+)', (TG_DIR / "proxy/__init__.py").read_text("utf-8"))
            return m.group(1) if m else "?"
        except Exception:
            return "не установлен"

    def running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def link(self) -> str:
        c = self.s["tg"]
        host = c["host"] if c["host"] not in ("0.0.0.0", "::") else "127.0.0.1"
        sec = c["secret"]
        if c.get("fake_tls_domain"):
            dom = c["fake_tls_domain"].encode().hex()
            return f"tg://proxy?server={host}&port={c['port']}&secret=ee{sec}{dom}"
        return f"tg://proxy?server={host}&port={c['port']}&secret=dd{sec}"

    def build_cmd(self) -> list[str]:
        c = self.s["tg"]
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--tgproxy"]
        else:
            cmd = [sys.executable, str(Path(__file__).resolve().parent / "main.py"), "--tgproxy"]
        cmd += ["--host", str(c["host"]), "--port", str(c["port"]), "--secret", c["secret"],
                "--pool-size", str(c["pool_size"]), "--buf-kb", str(c["buf_kb"])]
        dcs = [d.strip() for d in c["dc_ip"] if d.strip()]
        if dcs:
            for d in dcs:
                cmd += ["--dc-ip", d]
        else:
            cmd += ["--dc-ip"]
        if c.get("fake_tls_domain"):
            cmd += ["--fake-tls-domain", c["fake_tls_domain"]]
        if not c.get("cfproxy", True):
            cmd += ["--no-cfproxy"]
        for d in re.split(r"[\s,;]+", c.get("cfproxy_domains", "")):
            if d:
                cmd += ["--cfproxy-domain", d]
        for d in re.split(r"[\s,;]+", c.get("cfproxy_worker_domains", "")):
            if d:
                cmd += ["--cfproxy-worker-domain", d]
        if c.get("no_secure"):
            cmd += ["--no-secure"]
        if c.get("verbose"):
            cmd += ["-v"]
        return cmd

    def start(self):
        if self.running():
            return
        if not self.installed():
            log("tg", "✖ TG WS Proxy не установлен. Откройте вкладку «Обновления».")
            self.state_changed.emit(False)
            return
        try:
            env = dict(os.environ, PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
            log("tg", f"▶ Запуск TG WS Proxy на {self.s['tg']['host']}:{self.s['tg']['port']}")
            self.proc = subprocess.Popen(self.build_cmd(), cwd=str(TG_DIR), env=env,
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         stdin=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
            self._stopping = False
            threading.Thread(target=self._reader, daemon=True).start()
            self.s["tg_was_on"] = True
            self.state_changed.emit(True)
        except Exception as e:
            log("tg", f"✖ Ошибка запуска: {e}")
            self.proc = None
            self.state_changed.emit(False)

    def _reader(self):
        p = self.proc
        for raw in iter(p.stdout.readline, b""):
            txt = raw.decode("utf-8", "replace").rstrip()
            if txt:
                log("tg", txt)
        code = p.wait()
        if p is self.proc:
            if not self._stopping:
                log("tg", f"✖ TG WS Proxy завершился (код {code})")
            self.proc = None
            self.state_changed.emit(False)

    def stop(self, remember=True):
        self._stopping = True
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(3)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            self.proc = None
        if remember:
            self.s["tg_was_on"] = False
        log("tg", "■ TG WS Proxy остановлен")
        self.state_changed.emit(False)

    def restart(self):
        if self.running():
            self.stop(remember=False)
        self.start()


def run_tgproxy_embedded(argv: list[str]):
    """Режим дочернего процесса: запускает proxy.tg_ws_proxy из components/tgproxy."""
    sys.path.insert(0, str(TG_DIR))
    sys.argv = ["tg-ws-proxy"] + argv
    from proxy.tg_ws_proxy import main as tg_main  # type: ignore
    tg_main()


# ─────────────────────────── ОБНОВЛЕНИЯ ───────────────────────────
def _vtuple(v: str):
    return tuple(int(x) for x in re.findall(r"\d+", v or "0")) or (0,)


class Updater(QObject):
    progress = Signal(str, str)           # component, message
    checked = Signal(str, str, str, bool)  # component, local, remote, has_update
    finished = Signal(str, bool, str)      # component, ok, message

    def __init__(self, zapret: Zapret, tg: TgProxy):
        super().__init__()
        self.z, self.t = zapret, tg

    def _bg(self, fn, *a):
        threading.Thread(target=fn, args=a, daemon=True).start()

    # --- проверка ---
    def check(self, comp: str):
        self._bg(self._check, comp)

    def _check(self, comp):
        try:
            if comp == "zapret":
                remote = http_get(ZAPRET_VERSION_URL).decode().strip()
                local = self.z.version()
            else:
                txt = http_get(TG_VERSION_URL).decode()
                remote = re.search(r'__version__\s*=\s*["\']([^"\']+)', txt).group(1)
                local = self.t.version()
            has = local in ("не установлен", "?") or _vtuple(remote) > _vtuple(local)
            self.checked.emit(comp, local, remote, has)
        except Exception as e:
            self.checked.emit(comp, "", "", False)
            self.progress.emit(comp, f"Ошибка проверки: {e}")

    # --- установка ---
    def install(self, comp: str):
        self._bg(self._install, comp)

    def _install(self, comp):
        try:
            if comp == "zapret":
                self._install_zapret()
            else:
                self._install_tg()
            self.finished.emit(comp, True, "Обновление установлено")
        except Exception as e:
            self.finished.emit(comp, False, f"Ошибка: {e}")

    def _install_zapret(self):
        rel = gh_latest_release(ZAPRET_REPO)
        asset = next(a for a in rel["assets"] if a["name"].lower().endswith(".zip"))
        self.progress.emit("zapret", f"Скачивание {asset['name']}…")
        data = http_get(asset["browser_download_url"], timeout=120)
        was = self.z.running()
        if was:
            self.z.stop(remember=False, sync=True)
        self.progress.emit("zapret", "Распаковка…")
        keep = {}
        for rel_path in ["lists/list-general-user.txt", "lists/list-exclude-user.txt",
                         "lists/ipset-exclude-user.txt", "utils/game_filter.enabled"]:
            p = ZAPRET_DIR / rel_path
            if p.exists():
                keep[rel_path] = p.read_bytes()
        install_zip(data, ZAPRET_DIR)
        for rel_path, b in keep.items():
            p = ZAPRET_DIR / rel_path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b)
        self.progress.emit("zapret", f"Установлена версия {self.z.version()}")
        if was:
            self.z.start(sync=True)

    def _install_tg(self):
        rel = gh_latest_release(TG_REPO)
        self.progress.emit("tg", f"Скачивание исходников {rel['tag_name']}…")
        data = http_get(rel["zipball_url"], timeout=120)
        was = self.t.running()
        if was:
            self.t.stop(remember=False)
        install_zip(data, TG_DIR, only=("proxy/", "utils/", "LICENSE"))
        self.progress.emit("tg", f"Установлена версия {self.t.version()}")
        if was:
            self.t.start()


def install_zip(data: bytes, dest: Path, only: tuple | None = None):
    """Распаковывает zip в dest (снимая общий корневой каталог, если он есть)."""
    zf = zipfile.ZipFile(io.BytesIO(data))
    names = [n for n in zf.namelist() if not n.endswith("/")]
    roots = {n.split("/", 1)[0] for n in zf.namelist()}
    strip = len(roots) == 1 and all("/" in n for n in names)
    tmp = Path(tempfile.mkdtemp(prefix="zapretyz_"))
    try:
        for n in names:
            rel = n.split("/", 1)[1] if strip else n
            if not rel or (only and not rel.startswith(only)):
                continue
            out = tmp / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(zf.read(n))
        dest.mkdir(parents=True, exist_ok=True)
        if only:
            for pref in only:
                t = dest / pref.rstrip("/")
                if t.is_dir():
                    shutil.rmtree(t, ignore_errors=True)
        else:
            for child in dest.iterdir():
                if child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    try:
                        child.unlink()
                    except Exception:
                        pass
        for item in tmp.iterdir():
            target = dest / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ─────────────────────────── АВТОЗАПУСК ───────────────────────────
TASK_NAME = "ZapreTYZ Autostart"


def set_autostart(enabled: bool):
    """Через Планировщик задач — чтобы запускаться с правами администратора без UAC."""
    if not IS_WIN:
        return
    if enabled:
        exe = sys.executable if getattr(sys, "frozen", False) else f'{sys.executable}" "{Path(__file__).parent / "main.py"}'
        run_quiet(["schtasks", "/Create", "/F", "/TN", TASK_NAME, "/SC", "ONLOGON",
                   "/RL", "HIGHEST", "/DELAY", "0000:10", "/TR", f'"{exe}" --minimized'])
    else:
        run_quiet(["schtasks", "/Delete", "/F", "/TN", TASK_NAME])


def update_shortcut_icons(ico_path: str):
    """Меняет иконку ярлыков в «Пуске» и на рабочем столе под выбранный цвет."""
    if not IS_WIN:
        return
    ps = (
        "$sh=New-Object -ComObject WScript.Shell;"
        "$dirs=@([Environment]::GetFolderPath('CommonStartMenu'),[Environment]::GetFolderPath('StartMenu'),"
        "[Environment]::GetFolderPath('CommonDesktopDirectory'),[Environment]::GetFolderPath('Desktop'));"
        "foreach($d in $dirs){Get-ChildItem -Path $d -Filter *.lnk -Recurse -ErrorAction SilentlyContinue|"
        "ForEach-Object{$l=$sh.CreateShortcut($_.FullName);"
        "if($l.TargetPath -like '*\\ZapreTYZ.exe'){$l.IconLocation='" + ico_path.replace("'", "''") + ",0';$l.Save()}}}"
    )
    try:
        subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                         creationflags=CREATE_NO_WINDOW)
    except Exception:
        pass
