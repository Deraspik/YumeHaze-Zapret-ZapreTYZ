# Yume Haze Zapret (ZapreTYZ)

Удобная программа для Windows, которая объединяет в одном окне
[zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube) и
[tg-ws-proxy](https://github.com/Flowseal/tg-ws-proxy) от **Flowseal**.

**[⬇ Скачать установщик (Releases)](https://github.com/Deraspik/YumeHazeZapret---ZapreTYZ/releases/tag/ZapreTYZ)**

## Возможности
- **Zapret** включается одним переключателем, есть выбор стратегии. Работает как служба Windows и сам запускается при старте системы.
- **TG WS Proxy** — локальный прокси, который открывает Telegram без VPN.
- Быстрый тест подключения, подбор стратегии, игровой фильтр, IPSet, hosts.
- Обновление компонентов с GitHub, консоль, работа из трея, AMOLED-темы.

## Сборка из исходников
- **Windows:** установите Python 3.12 и Inno Setup 6, затем запустите `build.bat`. Установщик появится в `release\`.
- **GitHub Actions:** Actions → Build Yume Haze Zapret → артефакт `YumeHazeZapret_Setup`.

## Структура
| Путь | Что внутри |
|---|---|
| `app/main.py` | точка входа (режим `--tgproxy` — встроенный TG WS Proxy) |
| `app/core.py` | служба Zapret, TG-прокси, обновления, автозапуск |
| `app/zapret_tools.py` | диагностика, тесты стратегий |
| `app/ui.py`, `app/themes.py` | интерфейс и темы |
| `packaging/` | PyInstaller spec, Inno Setup, загрузка компонентов |

Настройки хранятся в `%APPDATA%\ZapreTYZ`.

## Лицензия
MIT. Zapret и tg-ws-proxy принадлежат своим авторам и распространяются по своим лицензиям.
