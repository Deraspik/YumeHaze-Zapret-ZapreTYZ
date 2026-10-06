"""Yume Haze Zapret 2.0 — новые функции: компоненты, откат, реклама, DNS, игровой режим,
авто-восстановление, Discord, звук, мини-виджет, экспорт, очистка, автообновление программы."""
from __future__ import annotations

import ctypes
import io
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import wave
import zipfile
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Qt

import core
from core import log
import zapret_tools as zt

IS_WIN = core.IS_WIN
APP_REPO = "Deraspik/YumeHaze-Zapret-ZapreTYZ"
HOSTS = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/drivers/etc/hosts"
BACKUPS = core.DATA_DIR / "backups"


class Invoker(QObject):
    """Выполнить функцию в главном потоке Qt (из фонового потока)."""
    call = Signal(object)

    def __init__(self):
        super().__init__()
        self.call.connect(lambda f: f(), Qt.QueuedConnection)


INV = Invoker()


def ui(fn):
    INV.call.emit(fn)


def bg(fn, *a):
    def run():
        try:
            fn(*a)
        except Exception as e:
            log("app", f"✖ {e}")
    threading.Thread(target=run, daemon=True).start()


# ───────────────────────── Компоненты: удаление / откат ─────────────────────────
def comp_dir(k):
    return core.ZAPRET_DIR if k == "zapret" else core.TG_DIR


def backup_component(k, version):
    d = comp_dir(k)
    if not d.exists() or version in ("", "?", "не установлен"):
        return
    out = BACKUPS / k
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"{version}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for p in d.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(d).as_posix())
    olds = sorted(out.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in olds[3:]:
        p.unlink(missing_ok=True)


def backups(k):
    d = BACKUPS / k
    if not d.exists():
        return []
    return [p.stem for p in sorted(d.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)]


def rollback(k, version, zapret, tg):
    data = (BACKUPS / k / f"{version}.zip").read_bytes()
    obj = zapret if k == "zapret" else tg
    was = obj.running()
    if was:
        obj.stop(remember=False, sync=True) if k == "zapret" else obj.stop(remember=False)
    cur = obj.version()
    if cur != version:
        backup_component(k, cur)
    core.install_zip(data, comp_dir(k))
    log(k, f"Откат на версию {version} выполнен")
    if was:
        obj.start(sync=True) if k == "zapret" else obj.start()


def remove_component(k, zapret, tg):
    if k == "zapret":
        if zapret.running():
            zapret.stop(remember=False, sync=True)
        try:
            zt.service_remove()
        except Exception:
            pass
        zapret.kill_all()
        time.sleep(1)
    else:
        if tg.running():
            tg.stop(remember=False)
    shutil.rmtree(comp_dir(k), ignore_errors=True)
    log("app", ("Zapret" if k == "zapret" else "TG WS Proxy") + " удалён")


# ───────────────────────── hosts: реклама ─────────────────────────
ADS_SRC = {
    "basic": "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
    "social": "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/social/hosts",
}
ADS_B, ADS_E = "# ZapreTYZ-ADS-BEGIN", "# ZapreTYZ-ADS-END"


def _hosts_block(start, end, body):
    cur = HOSTS.read_text("utf-8", "replace") if HOSTS.exists() else ""
    cur = re.sub(rf"{re.escape(start)}.*?{re.escape(end)}\n?", "", cur, flags=re.S).rstrip() + "\n"
    if body:
        cur += f"\n{start}\n{body.strip()}\n{end}\n"
    HOSTS.write_text(cur, "utf-8")
    if IS_WIN:
        core.run_quiet(["ipconfig", "/flushdns"])


def set_adblock(mode):
    """mode: off / basic / social. Возвращает число доменов."""
    if mode == "off":
        _hosts_block(ADS_B, ADS_E, "")
        log("app", "Блокировка рекламы выключена")
        return 0
    raw = core.http_get(ADS_SRC[mode], timeout=60).decode("utf-8", "replace")
    lines = []
    for ln in raw.splitlines():
        ln = ln.split("#", 1)[0].strip()
        if ln.startswith("0.0.0.0 ") and not ln.endswith(" 0.0.0.0"):
            lines.append(ln)
    # Windows быстрее работает, когда в строке несколько доменов (до 9)
    doms = [ln.split()[1] for ln in lines]
    body = "\n".join("0.0.0.0 " + " ".join(doms[i:i + 9]) for i in range(0, len(doms), 9))
    _hosts_block(ADS_B, ADS_E, body)
    log("app", f"Блокировка рекламы: {len(doms)} доменов")
    return len(doms)


# ───────────────────────── DNS ─────────────────────────
DNS = {
    "isp": ("Провайдера", None, None),
    "cloudflare": ("Cloudflare", ("1.1.1.1", "1.0.0.1"), "https://cloudflare-dns.com/dns-query"),
    "google": ("Google", ("8.8.8.8", "8.8.4.4"), "https://dns.google/dns-query"),
    "adguard": ("AdGuard (без рекламы)", ("94.140.14.14", "94.140.15.15"), "https://dns.adguard-dns.com/dns-query"),
}


def set_dns(key):
    name, ips, doh = DNS[key]
    up = "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'}"
    if ips:
        ps = (f"{up} | ForEach-Object {{ Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ServerAddresses "
              f"('{ips[0]}','{ips[1]}') }};")
        for ip in ips:
            ps += (f"try {{ Add-DnsClientDohServerAddress -ServerAddress '{ip}' -DohTemplate '{doh}' "
                   f"-AllowFallbackToUdp $True -AutoUpgrade $True -ErrorAction Stop }} catch {{}};")
    else:
        ps = f"{up} | ForEach-Object {{ Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ResetServerAddresses }};"
    ps += "Clear-DnsClientCache"
    r = core.run_quiet(["powershell", "-NoProfile", "-Command", ps], timeout=60)
    log("app", f"DNS: {name}" + ("" if r.returncode == 0 else f" (ошибка: {r.stderr.strip()[:120]})"))


# ───────────────────────── Списки сайтов ─────────────────────────
EXCL_PRESETS = {
    "банки": ["sberbank.ru", "online.sberbank.ru", "tinkoff.ru", "tbank.ru", "vtb.ru", "alfabank.ru", "gazprombank.ru",
              "raiffeisen.ru", "pochtabank.ru", "nalog.gov.ru"],
    "госсайты": ["gosuslugi.ru", "esia.gosuslugi.ru", "mos.ru", "nalog.ru", "pfr.gov.ru", "kremlin.ru"],
    "античиты": ["faceit.com", "easy.ac", "battleye.com", "vanguard.riotgames.com", "esportal.com"],
}
FILES = {"sites": "list-general-user.txt", "excl": "list-exclude-user.txt"}


def read_list(kind):
    p = core.ZAPRET_DIR / "lists" / FILES[kind]
    try:
        return [l.strip() for l in p.read_text("utf-8", "replace").splitlines()
                if l.strip() and not l.startswith("#") and l.strip() != "domain.example.abc"]
    except Exception:
        return []


def write_list(kind, items):
    p = core.ZAPRET_DIR / "lists" / FILES[kind]
    p.parent.mkdir(parents=True, exist_ok=True)
    items = list(dict.fromkeys(i.strip().lower() for i in items if i.strip()))
    head = "# Never leave this file empty\n" if kind == "sites" else ""
    p.write_text(head + "\n".join(items or ["domain.example.abc"]) + "\n", "utf-8")


def clean_domain(t):
    t = t.strip().lower()
    t = re.sub(r"^\w+://", "", t).split("/")[0].split(":")[0]
    return t


# ───────────────────────── Процессы / игровой режим ─────────────────────────
GAMES = {"cs2.exe", "dota2.exe", "valorant-win64-shipping.exe", "r5apex.exe", "r5apex_dx12.exe",
         "fortniteclient-win64-shipping.exe", "gta5.exe", "gta5_enhanced.exe", "rustclient.exe", "pubg.exe",
         "tslgame.exe", "overwatch.exe", "leagueoflegends.exe", "league of legends.exe", "eldenring.exe",
         "cod.exe", "deadlock.exe", "marvel-win64-shipping.exe", "minecraft.exe", "robloxplayerbeta.exe",
         "warthunder.exe", "aces.exe", "tarkov.exe", "escapefromtarkov.exe", "worldoftanks.exe", "dbd.exe"}


def process_names() -> set[str]:
    """Имена процессов через WinAPI (без запуска tasklist — не роняет FPS)."""
    if not IS_WIN:
        return set()
    names = set()
    try:
        from ctypes import wintypes
        k32 = ctypes.windll.kernel32

        class PE(ctypes.Structure):
            _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                        ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD),
                        ("cntThreads", wintypes.DWORD), ("th32ParentProcessID", wintypes.DWORD),
                        ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD),
                        ("szExeFile", ctypes.c_wchar * 260)]
        k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        snap = k32.CreateToolhelp32Snapshot(2, 0)
        e = PE()
        e.dwSize = ctypes.sizeof(PE)
        ok = k32.Process32FirstW(snap, ctypes.byref(e))
        while ok:
            names.add(e.szExeFile.lower())
            ok = k32.Process32NextW(snap, ctypes.byref(e))
        k32.CloseHandle(snap)
    except Exception:
        pass
    return names


def running_game() -> str | None:
    n = process_names() & GAMES
    return sorted(n)[0] if n else None


# ───────────────────────── Discord ─────────────────────────
def fix_discord() -> list[str]:
    msgs = zt.clear_discord_cache()
    la = Path(os.environ.get("LOCALAPPDATA", ""))
    upd = la / "Discord" / "Update.exe"
    if upd.exists():
        subprocess.Popen([str(upd), "--processStart", "Discord.exe"], creationflags=core.CREATE_NO_WINDOW)
        msgs.append("Discord запущен заново")
    return msgs


class DiscordRPC:
    """Статус «Играет в Yume Haze Zapret» через локальный IPC Discord (\\\\.\\pipe\\discord-ipc-N)."""
    CLIENT_ID = "1556964236150968390"  # приложение «Yume Haze Zapret» на discord.com/developers

    def __init__(self):
        self.f = None
        self.started = int(time.time())

    def _send(self, op, data):
        b = json.dumps(data).encode()
        self.f.write(struct.pack("<II", op, len(b)) + b)
        self.f.flush()
        hdr = self.f.read(8)
        if len(hdr) == 8:
            _, ln = struct.unpack("<II", hdr)
            self.f.read(ln)

    def connect(self, client_id):
        if not IS_WIN:
            return False
        for i in range(10):
            try:
                self.f = open(rf"\\.\pipe\discord-ipc-{i}", "r+b", buffering=0)
                self._send(0, {"v": 1, "client_id": str(client_id)})
                return True
            except Exception:
                self.f = None
        return False

    def update(self, details, state):
        if not self.f:
            return False
        try:
            self._send(1, {"cmd": "SET_ACTIVITY", "nonce": str(time.time()), "args": {
                "pid": os.getpid(), "activity": {"details": details, "state": state,
                                                 "timestamps": {"start": self.started},
                                                 "assets": {"large_image": "logo", "large_text": "Yume Haze Zapret"},
                                                 "buttons": [{"label": "Скачать", "url": "https://github.com/Deraspik/YumeHaze-Zapret-ZapreTYZ/releases/latest"},
                                                             {"label": "Discord-сервер", "url": "https://discord.gg/qHabsmgKVP"}]}}})
            return True
        except Exception:
            self.close()
            return False

    def close(self):
        try:
            if self.f:
                self.f.close()
        except Exception:
            pass
        self.f = None


# ───────────────────────── Звук ─────────────────────────
def _tone(path, freqs, dur=0.09):
    sr = 22050
    frames = bytearray()
    for f in freqs:
        n = int(sr * dur)
        for i in range(n):
            env = min(1, i / 300) * min(1, (n - i) / 600)
            frames += struct.pack("<h", int(9000 * env * math.sin(2 * math.pi * f * i / sr)))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(bytes(frames))


def play_sound(on: bool):
    if not IS_WIN:
        return
    try:
        import winsound
        p = core.DATA_DIR / ("snd_on.wav" if on else "snd_off.wav")
        if not p.exists():
            _tone(p, (660, 990) if on else (880, 520))
        winsound.PlaySound(str(p), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except Exception:
        pass


# ───────────────────────── Тест скорости YouTube ─────────────────────────
def youtube_speed() -> tuple[float, str]:
    import urllib.request
    ua = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130 Safari/537.36"}
    html = urllib.request.urlopen(urllib.request.Request("https://www.youtube.com/", headers=ua), timeout=10).read().decode("utf-8", "replace")
    m = re.search(r'"(/s/player/[^"]+?/base\.js)"', html) or re.search(r'"(/s/desktop/[^"]+?\.js)"', html)
    url = "https://www.youtube.com" + m.group(1) if m else "https://www.youtube.com/s/desktop/"
    total, t0 = 0, time.time()
    for _ in range(3):
        with urllib.request.urlopen(urllib.request.Request(url, headers=ua), timeout=15) as r:
            while True:
                b = r.read(65536)
                if not b:
                    break
                total += len(b)
        if time.time() - t0 > 6:
            break
    mbit = total * 8 / max(0.001, time.time() - t0) / 1e6
    q = "4K" if mbit > 25 else "1440p" if mbit > 12 else "1080p" if mbit > 6 else "720p" if mbit > 3 else "480p"
    return mbit, q


# ───────────────────────── Экспорт / импорт ─────────────────────────
def export_cfg(settings, path):
    data = {"app": "YumeHazeZapret", "version": core.APP_VERSION,
            "settings": {k: v for k, v in settings.data.items() if not k.startswith("_")},
            "sites": read_list("sites"), "excl": read_list("excl")}
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")


def import_cfg(settings, path):
    data = json.loads(Path(path).read_text("utf-8"))
    st = data.get("settings", {})
    tg = st.pop("tg", None)
    settings.data.update(st)
    if tg:
        settings.data["tg"].update(tg)
    settings.save()
    if core.ZAPRET_DIR.exists():
        write_list("sites", data.get("sites", []))
        write_list("excl", data.get("excl", []))


# ───────────────────────── Очистка следов ─────────────────────────
def clean_all(zapret, tg) -> list[str]:
    out = []
    try:
        if tg.running():
            tg.stop(remember=False)
        if zapret.running():
            zapret.stop(remember=False, sync=True)
        zt.service_remove()
        zapret.kill_all()
        out.append("Служба zapret удалена")
        core.run_quiet(["sc", "stop", "WinDivert"])
        core.run_quiet(["sc", "delete", "WinDivert"])
        out.append("Драйвер WinDivert выгружен и удалён")
    except Exception as e:
        out.append(f"zapret: {e}")
    core.set_autostart(False)
    out.append("Задача автозапуска удалена")
    try:
        _hosts_block(ADS_B, ADS_E, "")
        _hosts_block("# ZapreTYZ-BEGIN", "# ZapreTYZ-END", "")
        out.append("Записи в hosts убраны")
    except Exception as e:
        out.append(f"hosts: {e}")
    try:
        set_dns("isp")
        out.append("DNS возвращён на «от провайдера»")
    except Exception:
        pass
    shutil.rmtree(core.DATA_DIR, ignore_errors=True)
    out.append("Папка настроек удалена")
    return out


# ───────────────────────── Автообновление программы ─────────────────────────
def check_app_update():
    """→ (версия, url_установщика) или (None, None)."""
    rel = core.gh_latest_release(APP_REPO)
    ver = rel.get("tag_name", "").lstrip("vV")
    if core._vtuple(ver) <= core._vtuple(core.APP_VERSION):
        return None, None
    a = next((a for a in rel.get("assets", []) if a["name"].lower().endswith(".exe")), None)
    if not a:
        for a2 in rel.get("assets", []):
            if a2["name"].lower().endswith(".zip"):
                a = a2
                break
    return ver, (a["browser_download_url"] if a else None)


def download_and_run_update(url):
    data = core.http_get(url, timeout=300)
    tmp = Path(tempfile.gettempdir())
    if url.lower().endswith(".zip"):
        z = zipfile.ZipFile(io.BytesIO(data))
        name = next(n for n in z.namelist() if n.lower().endswith(".exe") and "setup" in n.lower())
        exe = tmp / Path(name).name
        exe.write_bytes(z.read(name))
    else:
        exe = tmp / "YumeHazeZapret_Update.exe"
        exe.write_bytes(data)
    subprocess.Popen([str(exe), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
                     creationflags=0x00000008)  # DETACHED_PROCESS
    return True


# ───────────────────────── Тема по системе / времени ─────────────────────────
def windows_light() -> bool:
    if not IS_WIN:
        return False
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        return bool(winreg.QueryValueEx(k, "AppsUseLightTheme")[0])
    except Exception:
        return False


def resolve_base(mode) -> str:
    if mode == "windows":
        return "light" if windows_light() else "dark"
    if mode == "time":
        h = time.localtime().tm_hour
        return "light" if 7 <= h < 20 else "dark"
    return mode if mode in ("dark", "light") else "dark"


# ───────────────────────── Импорт стратегии / история ─────────────────────────
def import_strategy(path) -> str:
    src = Path(path)
    name = src.name if src.suffix.lower() == ".bat" else src.stem + ".bat"
    if not name.lower().startswith("general"):
        name = "general (" + Path(name).stem + ").bat"
    dst = core.ZAPRET_DIR / name
    shutil.copy2(src, dst)
    log("zapret", f"Импортирована стратегия: {dst.stem}")
    return name


def add_history(settings, kind, strategy, groups=None, extra=""):
    h = settings.data.setdefault("test_history", [])
    h.insert(0, {"t": time.strftime("%d.%m %H:%M"), "kind": kind, "strategy": strategy[:-4] if strategy.endswith(".bat") else strategy,
                 "groups": groups or {}, "extra": extra})
    del h[60:]
    settings.save()


def best_strategy(settings, available) -> str | None:
    res = settings.data.get("strat_results", {})
    best, score = None, -1.0
    for st in available:
        r = res.get(st)
        if not r:
            continue
        ok = sum(v[0] for v in r.values())
        tot = sum(v[1] for v in r.values()) or 1
        sc = ok / tot + ok * 0.001
        if sc > score:
            best, score = st, sc
    return best


def ranked_strategies(settings, available):
    res = settings.data.get("strat_results", {})

    def sc(st):
        r = res.get(st)
        if not r:
            return -1
        return sum(v[0] for v in r.values()) / (sum(v[1] for v in r.values()) or 1)
    return sorted(available, key=sc, reverse=True)
