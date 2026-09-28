"""Скачивает последние Zapret и TG WS Proxy в components/ перед сборкой установщика."""
import json, sys, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from core import install_zip  # noqa

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ZapreTYZ-build"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()

def latest(repo):
    return json.loads(get(f"https://api.github.com/repos/{repo}/releases/latest"))

z = latest("Flowseal/zapret-discord-youtube")
asset = next(a for a in z["assets"] if a["name"].lower().endswith(".zip"))
print("Zapret", z["tag_name"], asset["name"])
install_zip(get(asset["browser_download_url"]), ROOT / "components" / "zapret")

t = latest("Flowseal/tg-ws-proxy")
print("TG WS Proxy", t["tag_name"])
install_zip(get(t["zipball_url"]), ROOT / "components" / "tgproxy", only=("proxy/", "utils/", "LICENSE"))
print("OK")
