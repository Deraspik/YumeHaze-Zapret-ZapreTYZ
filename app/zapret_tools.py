"""Полный функционал service.bat от Flowseal: служба, диагностика, фейки, тесты стратегий."""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PySide6.QtCore import QObject, Signal

import core
from core import IS_WIN, CREATE_NO_WINDOW, ZAPRET_DIR, run_quiet, log

SERVICE = "zapret"


# ───────────────────────── Служба Windows ─────────────────────────
def service_status() -> dict:
    res = {"zapret": "не установлена", "windivert": "не установлена", "strategy": ""}
    if not IS_WIN:
        return res
    for name, key in ((SERVICE, "zapret"), ("WinDivert", "windivert")):
        out = run_quiet(["sc", "query", name]).stdout
        if "RUNNING" in out:
            res[key] = "работает"
        elif "STOPPED" in out or "STOP_PENDING" in out:
            res[key] = "остановлена"
    out = run_quiet(["reg", "query", r"HKLM\System\CurrentControlSet\Services\zapret",
                     "/v", "zapret-discord-youtube"]).stdout
    m = re.search(r"REG_SZ\s+(.+)", out)
    if m:
        res["strategy"] = m.group(1).strip()
    return res


def service_install(zapret, strategy: str):
    """Аналог пункта 1 service.bat — установка Zapret как службы Windows (автозапуск без программы)."""
    zapret.ensure_user_lists()
    args = zapret.build_args(strategy)
    exe = zapret.bin_dir / "winws.exe"
    if zapret.running():
        zapret.stop()
    run_quiet(["net", "stop", SERVICE])
    run_quiet(["sc", "delete", SERVICE])
    time.sleep(0.5)
    bin_path = f'"{exe}" {args}'
    r = run_quiet(f'sc create {SERVICE} binPath= "{bin_path.replace(chr(34), chr(92) + chr(34))}" '
                  f'DisplayName= "zapret" start= auto')
    log("zapret", (r.stdout + r.stderr).strip() or "sc create выполнен")
    run_quiet(["sc", "description", SERVICE, "Zapret DPI bypass software"])
    r = run_quiet(["sc", "start", SERVICE])
    run_quiet(["reg", "add", r"HKLM\System\CurrentControlSet\Services\zapret", "/v", "zapret-discord-youtube",
               "/t", "REG_SZ", "/d", strategy[:-4], "/f"])
    log("zapret", f"Служба zapret установлена со стратегией {strategy[:-4]}")


def service_remove():
    for svc in (SERVICE, "WinDivert", "WinDivert14"):
        run_quiet(["net", "stop", svc])
        run_quiet(["sc", "delete", svc])
    run_quiet(["taskkill", "/F", "/IM", "winws.exe"])
    log("zapret", "Службы zapret / WinDivert удалены")


# ───────────────────────── Автопроверка обновлений ─────────────────────────
def check_updates_enabled() -> bool:
    return (ZAPRET_DIR / "utils" / "check_updates.enabled").exists()


def set_check_updates(on: bool):
    f = ZAPRET_DIR / "utils" / "check_updates.enabled"
    f.parent.mkdir(parents=True, exist_ok=True)
    if on:
        f.write_text("ENABLED", "utf-8")
    elif f.exists():
        f.unlink()


# ───────────────────────── Активные фейки ─────────────────────────
def _sha(p: Path) -> str:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except Exception:
        return ""


def fakes_info() -> dict:
    """Список .bin-фейков и какие сейчас активны (как пункт 7 service.bat)."""
    bdir = ZAPRET_DIR / "bin"
    files = sorted(p for p in bdir.glob("*.bin") if not p.stem.upper().startswith("ACTIVE_"))
    hashes = {p.stem: _sha(p) for p in files}
    res = {"files": [p.stem for p in files], "discord": "", "game": ""}
    for key, name in (("discord", "ACTIVE_DISCORD_UDP.bin"), ("game", "ACTIVE_GAME_UDP.bin")):
        h = _sha(bdir / name)
        res[key] = next((n for n, hh in hashes.items() if hh and hh == h), "(свой / не найден)")
    return res


def replace_fake(kind: str, source_stem: str):
    bdir = ZAPRET_DIR / "bin"
    target = bdir / ("ACTIVE_DISCORD_UDP.bin" if kind == "discord" else "ACTIVE_GAME_UDP.bin")
    shutil.copyfile(bdir / f"{source_stem}.bin", target)
    log("zapret", f"Активный фейк {'Discord UDP' if kind == 'discord' else 'GameFilter UDP'} → {source_stem}")


# ───────────────────────── Диагностика ─────────────────────────
OK, WARN, ERR = "ok", "warn", "err"


def run_diagnostics() -> list[tuple[str, str]]:
    """Аналог пункта 11 service.bat. Возвращает список (статус, текст)."""
    out: list[tuple[str, str]] = []
    add = out.append
    if not IS_WIN:
        return [(WARN, "Диагностика доступна только в Windows")]

    add((OK, f"Zapret установлен в: {ZAPRET_DIR}"))
    add((OK, "Base Filtering Engine работает") if "RUNNING" in run_quiet(["sc", "query", "BFE"]).stdout
        else (ERR, "Служба Base Filtering Engine (BFE) не запущена — она нужна для работы zapret"))

    r = run_quiet(["reg", "query", r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings", "/v", "ProxyEnable"]).stdout
    if re.search(r"ProxyEnable\s+REG_DWORD\s+0x1", r):
        srv = run_quiet(["reg", "query", r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings", "/v", "ProxyServer"]).stdout
        m = re.search(r"REG_SZ\s+(.+)", srv)
        add((WARN, f"Включён системный прокси: {m.group(1).strip() if m else '?'} — отключите, если не используете"))
    else:
        add((OK, "Системный прокси не используется"))

    ts = run_quiet(["netsh", "interface", "tcp", "show", "global"]).stdout
    if re.search(r"(?i)timestamps.*enabled", ts):
        add((OK, "TCP timestamps включены"))
    else:
        rr = run_quiet(["netsh", "interface", "tcp", "set", "global", "timestamps=enabled"])
        add((WARN, "TCP timestamps были выключены — включены автоматически") if rr.returncode == 0
            else (ERR, "Не удалось включить TCP timestamps"))

    tasks = run_quiet(["tasklist"]).stdout.lower()
    add((ERR, "Найден Adguard — может мешать Discord (issue #417)") if "adguardsvc.exe" in tasks
        else (OK, "Adguard не найден"))

    svcs = run_quiet(["sc", "query", "type=", "service", "state=", "all"]).stdout
    low = svcs.lower()
    checks = [
        ("killer", "Службы Killer конфликтуют с zapret"),
        ("smartbyte", "SmartByte конфликтует с zapret — отключите в services.msc"),
        ("tracsrvwrapper", "Check Point конфликтует с zapret — удалите Check Point"),
        ("epwd", "Check Point конфликтует с zapret — удалите Check Point"),
    ]
    for key, msg in checks:
        if key in low:
            add((ERR, msg))
    if re.search(r"intel.*connectivity.*network", low):
        add((ERR, "Intel Connectivity Network Service конфликтует с zapret"))
    vpn = sorted(set(re.findall(r"SERVICE_NAME:\s*(\S*vpn\S*)", svcs, re.I)))
    add((WARN, f"Найдены VPN-службы: {', '.join(vpn)} — отключите VPN при проблемах") if vpn
        else (OK, "VPN-службы не найдены"))

    if re.search(r"[А-Яа-яЁё]", str(ZAPRET_DIR)):
        add((WARN, "В пути к Zapret есть кириллица — при проблемах переустановите в путь на латинице"))
    od = os.environ.get("OneDrive")
    if od and str(ZAPRET_DIR).lower().startswith(od.lower()):
        add((ERR, "Zapret находится в папке OneDrive — перенесите его"))
    add((OK, "WinDivert64.sys на месте") if (ZAPRET_DIR / "bin" / "WinDivert64.sys").exists()
        else (ERR, "Файл WinDivert64.sys не найден — переустановите Zapret"))

    # конфликтующие обходчики
    for proc in ("goodbyedpi.exe", "winws.exe"):
        if proc in tasks and proc == "goodbyedpi.exe":
            add((ERR, "Запущен GoodbyeDPI — он конфликтует с zapret"))
    st = service_status()
    add((OK, f"Служба zapret: {st['zapret']}" + (f", стратегия {st['strategy']}" if st['strategy'] else "")))

    # DNS / secure DNS
    dns = run_quiet(["powershell", "-NoProfile", "-Command",
                     "(Get-DnsClientDohServerAddress -ErrorAction SilentlyContinue | Measure-Object).Count"]).stdout.strip()
    add((OK, "DNS-over-HTTPS настроен в системе") if dns and dns != "0"
        else (WARN, "Secure DNS (DoH) не настроен — рекомендуется включить в браузере или Windows"))

    hosts = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/drivers/etc/hosts"
    try:
        txt = hosts.read_text("utf-8", "replace").lower()
        if "youtube" in txt or "discord" in txt:
            add((WARN, "В файле hosts есть записи youtube/discord — они могут мешать"))
    except Exception:
        pass
    return out


def clear_discord_cache() -> list[str]:
    msgs = []
    appdata = Path(os.environ.get("APPDATA", ""))
    for proc, name, folder in (("Discord.exe", "Discord", "discord"),
                               ("DiscordPTB.exe", "Discord PTB", "discordptb"),
                               ("DiscordCanary.exe", "Discord Canary", "discordcanary")):
        run_quiet(["taskkill", "/F", "/IM", proc])
        base = appdata / folder
        for sub in ("Cache", "Code Cache", "GPUCache"):
            d = base / sub
            if d.exists():
                shutil.rmtree(d, ignore_errors=True)
                msgs.append(f"{name}: очищено {sub}")
    return msgs or ["Кэш Discord не найден"]


# ───────────────────────── Тест стратегий ─────────────────────────
def load_targets() -> list[tuple[str, str]]:
    f = ZAPRET_DIR / "utils" / "targets.txt"
    res = []
    try:
        for line in f.read_text("utf-8", "replace").splitlines():
            m = re.match(r'\s*(\w+)\s*=\s*"([^"]+)"', line)
            if m:
                res.append((m.group(1), m.group(2)))
    except Exception:
        pass
    return res or [("DiscordMain", "https://discord.com"), ("YouTubeWeb", "https://www.youtube.com"),
                   ("GoogleMain", "https://www.google.com")]


def _curl() -> str:
    exe = shutil.which("curl.exe") or shutil.which("curl")
    return exe or "curl"


def check_url(url: str, timeout=5) -> tuple[bool, str]:
    """HTTPS с TLS 1.2 и TLS 1.3 + отправка 64 КБ (ловит «заморозку» DPI после 16 КБ)."""
    if url.upper().startswith("PING:"):
        host = url.split(":", 1)[1].strip()
        r = run_quiet(["ping", "-n", "2", "-w", "1500", host] if IS_WIN else ["ping", "-c", "2", host])
        ok = r.returncode == 0
        return ok, "ping ok" if ok else "ping fail"
    results = []
    payload = core.DATA_DIR / "test_payload.bin"
    if not payload.exists():
        payload.write_bytes(os.urandom(64 * 1024))
    tests = [("TLS1.2", ["--tlsv1.2", "--tls-max", "1.2"]), ("TLS1.3", ["--tlsv1.3"]),
             ("16KB+", ["-X", "POST", "--data-binary", f"@{payload}"])]
    passed = 0
    for name, extra in tests:
        cmd = [_curl(), "-s", "-o", os.devnull, "-m", str(timeout), "--connect-timeout", "3",
               "-w", "%{http_code}", *extra, url]
        try:
            r = run_quiet(cmd, timeout=timeout + 3)
            code = r.stdout.strip()[-3:]
            ok = r.returncode == 0 and code.isdigit() and code != "000"
            if r.returncode == 35 and name == "TLS1.3":
                results.append(f"{name}:unsup")
                passed += 1
                continue
        except Exception:
            ok = False
        passed += ok
        results.append(f"{name}:{'ok' if ok else 'fail'}")
    return passed == len(tests), " ".join(results)


class StrategyTester(QObject):
    progress = Signal(int, int, str)         # done, total, text
    strategy_result = Signal(str, int, int, float, list)  # strategy, ok, total, avg_time, details
    finished = Signal(list)                  # sorted results

    def __init__(self, zapret):
        super().__init__()
        self.z = zapret
        self._stop = False
        self.running = False

    def stop(self):
        self._stop = True

    def start(self, strategies: list[str], targets: list[tuple[str, str]]):
        if self.running:
            return
        self._stop = False
        self.running = True
        threading.Thread(target=self._run, args=(strategies, targets), daemon=True).start()

    def _run(self, strategies, targets):
        was_running = self.z.running()
        prev_strategy = self.z.s["strategy"]
        if was_running:
            self.z.stop(remember=False, sync=True)
            log("zapret", "Zapret временно остановлен на время теста")
        svc = {"zapret": ""}
        results = []
        total = len(strategies)
        for i, st in enumerate(strategies):
            if self._stop:
                break
            self.progress.emit(i, total, f"Тест: {st[:-4]}")
            proc = None
            try:
                self.z.ensure_user_lists()
                args = self.z.build_args(st)
                exe = self.z.bin_dir / "winws.exe"
                run_quiet(["taskkill", "/F", "/IM", "winws.exe"])
                proc = subprocess.Popen(f'"{exe}" {args}' if IS_WIN else [str(exe)], cwd=str(self.z.bin_dir),
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                        creationflags=CREATE_NO_WINDOW)
                time.sleep(2.0)
                if proc.poll() is not None:
                    raise RuntimeError("winws.exe не запустился")
                t0 = time.time()
                with ThreadPoolExecutor(max_workers=8) as ex:
                    res = list(ex.map(lambda t: (t[0], *check_url(t[1])), targets))
                dt = (time.time() - t0) / max(1, len(targets))
                ok = sum(1 for r in res if r[1])
                details = [f"{'✔' if r[1] else '✖'} {r[0]}: {r[2]}" for r in res]
                results.append((st, ok, len(targets), dt))
                self.strategy_result.emit(st, ok, len(targets), dt, details)
            except Exception as e:
                results.append((st, 0, len(targets), 99.0))
                self.strategy_result.emit(st, 0, len(targets), 99.0, [f"✖ Ошибка: {e}"])
            finally:
                if proc:
                    try:
                        proc.terminate()
                        proc.wait(3)
                    except Exception:
                        pass
                run_quiet(["taskkill", "/F", "/IM", "winws.exe"])
        results.sort(key=lambda r: (-r[1], r[3]))
        self.progress.emit(total, total, "Тест завершён" if not self._stop else "Тест остановлен")
        self.running = False
        self.z.s["strategy"] = prev_strategy
        if was_running:
            self.z.start(sync=True)
        self.finished.emit(results)


def open_original_test():
    """Оригинальный интерактивный тест Flowseal (utils/test zapret.ps1) в окне PowerShell."""
    script = ZAPRET_DIR / "utils" / "test zapret.ps1"
    subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
                     creationflags=0x00000010)  # CREATE_NEW_CONSOLE


# ───────────────────────── Быстрый тест подключения ─────────────────────────
QUICK_GROUPS = {
    "Discord": ["https://discord.com", "https://gateway.discord.gg", "https://cdn.discordapp.com", "https://updates.discord.com"],
    "YouTube": ["https://www.youtube.com", "https://i.ytimg.com", "https://redirector.googlevideo.com"],
    "Google": ["https://www.google.com", "https://www.gstatic.com"],
    "Cloudflare": ["https://www.cloudflare.com", "https://cdnjs.cloudflare.com"],
}


def probe(url: str, timeout=6) -> tuple[bool, float]:
    """Один HTTPS-запрос через curl (как в тесте Flowseal): (успех, время в мс)."""
    cmd = [_curl(), "-s", "-o", os.devnull, "-m", str(timeout), "--connect-timeout", "4",
           "-w", "%{http_code} %{time_total}", url]
    try:
        r = run_quiet(cmd, timeout=timeout + 3)
        m = re.search(r"(\d{3})\s+([\d.,]+)", r.stdout)
        if r.returncode == 0 and m and m.group(1) != "000":
            return True, float(m.group(2).replace(",", ".")) * 1000
    except Exception:
        pass
    return False, 0.0


class QuickChecker(QObject):
    group_done = Signal(str, int, int, float)   # группа, ок, всего, среднее мс
    finished = Signal(int, int)                 # всего ок, всего проверок

    def __init__(self):
        super().__init__()
        self.running = False

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        tot_ok = tot = 0
        with ThreadPoolExecutor(max_workers=10) as ex:
            futs = {g: [ex.submit(probe, u) for u in urls] for g, urls in QUICK_GROUPS.items()}
            for g, fl in futs.items():
                res = [f.result() for f in fl]
                ok = [t for s, t in res if s]
                tot_ok += len(ok)
                tot += len(res)
                self.group_done.emit(g, len(ok), len(res), sum(ok) / len(ok) if ok else 0.0)
        self.running = False
        self.finished.emit(tot_ok, tot)
