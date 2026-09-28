"""Темы оформления ZapreTYZ. Все в гамме «чёрный + синий градиент»."""
from string import Template

def _hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c))) for c in rgb)


def _mix(rgb, k):
    return tuple(c * k for c in rgb)


def amoled(name, a1, a2, tint):
    """AMOLED-тема: чёрный фон + градиент выбранного цвета."""
    return dict(
        name=name, bg="#000000", side1=_hex(_mix(tint, .06)), side2="#000000", sideBorder=_hex(_mix(tint, .16)),
        card1=_hex(_mix(tint, .05)), card2="#000000", cardBorder=_hex(_mix(tint, .2)), text="#f3f5ff",
        muted=_hex((95 + tint[0] * .1, 100 + tint[1] * .1, 120 + tint[2] * .1)), nav="#7c84a0",
        navHover=_hex(_mix(tint, .06)), a1=a1, a2=a2, logo=a2,
        input="#01030a", inputBorder=_hex(_mix(tint, .25)), btn=_hex(_mix(tint, .05)), btnBorder=_hex(_mix(tint, .25)),
        btnHover=_hex(_mix(tint, .1)), console="#000000", toggleOff=_hex(_mix(tint, .09)),
        glow=(*tint, 45), radius=8, nav_style="minimal", flat=True, tint=tint,
        grad1=_hex(_mix(tint, .17)), grad2=_hex(_mix(tint, .045)), grad3="#000000")


THEMES = {
    "blue":    amoled("Синий",      "#1d4ed8", "#38bdf8", (60, 110, 255)),
    "cyan":    amoled("Бирюзовый",  "#0e7490", "#2dd4bf", (20, 200, 210)),
    "purple":  amoled("Фиолетовый", "#6d28d9", "#a78bfa", (140, 80, 255)),
    "pink":    amoled("Розовый",    "#be185d", "#f472b6", (240, 70, 160)),
    "red":     amoled("Красный",    "#b91c1c", "#fb7185", (240, 60, 70)),
    "orange":  amoled("Оранжевый",  "#c2410c", "#fbbf24", (250, 130, 40)),
    "green":   amoled("Зелёный",    "#15803d", "#4ade80", (40, 210, 110)),
    "mono":    amoled("Монохром",   "#52525b", "#e4e4e7", (170, 170, 190)),
}
ALIASES = {"amoled": "blue", "neon": "blue", "glass": "blue", "ocean": "cyan", "aurora": "purple"}

T = dict(THEMES["blue"])  # активная тема (читается виджетами при отрисовке)


def set_theme(key: str):
    T.clear()
    T.update(THEMES.get(ALIASES.get(key, key), THEMES["blue"]))


_QSS = Template("""
* { font-family: 'Segoe UI Variable Display', 'Segoe UI', 'Inter', sans-serif; color: $text; }
QMainWindow, #Root { background: $bg; }
#Sidebar { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 $side1, stop:1 $side2);
           border-right: 1px solid $sideBorder; }
#Logo { font-size: 20px; font-weight: 800; letter-spacing: 1px; }
#LogoSub { color: $muted; font-size: 11px; }
QPushButton#Nav { text-align: left; padding: 11px 16px; border: none; border-radius: ${r2}px;
                  font-size: 14px; color: $nav; background: transparent; $navBase }
QPushButton#Nav:hover { background: $navHover; color: $text; }
QPushButton#Nav:checked { $navChecked }
QPushButton#Discord { $discordBase background: #5865F2; border: none; border-radius: ${r2}px; padding: 9px 14px;
                      color: white; font-weight: 600; text-align: left; }
QPushButton#Discord:hover { background: #6d78f5; $discordHover }
#PageTitle { font-size: 26px; font-weight: 700; }
#PageSub { color: $muted; font-size: 13px; }
#Card { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 $card1, stop:1 $card2);
        border: 1px solid $cardBorder; border-radius: ${r}px; }
#CardTitle { font-size: 17px; font-weight: 700; }
#Muted { color: $muted; font-size: 12px; }
#Hint { color: $nav; font-size: 12px; }
#StatusOn { color: #3ddc97; font-weight: 600; }
#StatusOff { color: $muted; font-weight: 600; }
QPushButton { background: $btn; border: 1px solid $btnBorder; border-radius: ${r3}px;
              padding: 8px 16px; font-size: 13px; }
QPushButton:hover { background: $btnHover; border-color: $a1; }
QPushButton:pressed { background: $input; }
QPushButton:disabled { color: $muted; background: $input; }
QPushButton#Primary { border: none; font-weight: 600; color: white;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 $a1, stop:1 $a2); }
QPushButton#Primary:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 $a2, stop:1 $a1); }
QPushButton#Danger { background: #2a1020; border-color: #4a1a33; color: #ff8fb0; }
QPushButton#ThemeCard { text-align: left; padding: 12px; border-radius: ${r3}px; }
QPushButton#ThemeCard:checked { border: 2px solid $a2; }
QComboBox, QLineEdit, QSpinBox { background: $input; border: 1px solid $inputBorder; border-radius: ${r3}px;
    padding: 7px 10px; font-size: 13px; selection-background-color: $a1; }
QComboBox:hover, QLineEdit:hover, QSpinBox:hover { border-color: $a1; }
QComboBox:focus, QLineEdit:focus, QSpinBox:focus { border-color: $a2; }
QComboBox::drop-down { border: none; width: 26px; }
QComboBox QAbstractItemView { background: $input; border: 1px solid $inputBorder; outline: none;
    selection-background-color: $a1; padding: 4px; }
QSpinBox::up-button, QSpinBox::down-button { width: 0; border: none; }
QPlainTextEdit#Console { background: $console; border: 1px solid $cardBorder; border-radius: ${r3}px;
    font-family: 'Cascadia Mono', 'Consolas', monospace; font-size: 12px; padding: 8px; color: #b8c4e6; }
QCheckBox, QRadioButton { font-size: 13px; spacing: 9px; }
QCheckBox::indicator, QRadioButton::indicator { width: 18px; height: 18px; }
QCheckBox::indicator { border-radius: 5px; border: 1px solid $inputBorder; background: $input; }
QCheckBox::indicator:checked { background: $a2; border-color: $a2; }
QRadioButton::indicator { border-radius: 9px; border: 1px solid $inputBorder; background: $input; }
QRadioButton::indicator:checked { background: qradialgradient(cx:.5,cy:.5,radius:.5,fx:.5,fy:.5,
    stop:0 white, stop:.35 white, stop:.45 $a2, stop:1 $a2); border-color: $a2; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: $btnBorder; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: $a1; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QMenu { background: $input; border: 1px solid $inputBorder; border-radius: 8px; padding: 6px; }
QMenu::item { padding: 7px 22px; border-radius: 6px; }
QMenu::item:selected { background: $a1; }
QMenu::separator { height: 1px; background: $inputBorder; margin: 5px 8px; }
QProgressBar { background: $toggleOff; border: none; border-radius: 3px; }
QProgressBar::chunk { border-radius: 3px; background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 $a1, stop:1 $a2); }
#Chip { background: rgba(255,255,255,0.03); border: 1px solid $cardBorder; border-radius: ${r3}px; }
QToolTip { background: $input; color: $text; border: 1px solid $inputBorder; padding: 5px; }
""")


def build_qss() -> str:
    t = dict(T)
    r = t["radius"]
    t.update(r=r, r2=max(4, int(r * 0.62)), r3=max(4, int(r * 0.56)))
    t["discordBase"] = t["discordHover"] = ""
    if t["nav_style"] == "minimal":
        t["discordHover"] = "color: white; border-color: #5865F2;"
        t["navBase"] = ("padding: 9px 14px; font-size: 13px; border-radius: 0; "
                        "border-left: 2px solid transparent; margin-left: 2px;")
        t["navChecked"] = f"color: {t['text']}; font-weight: 600; background: transparent; border-left: 2px solid {t['a2']};"
        t["discordBase"] = ""
    elif t["nav_style"] == "bar":
        t["navBase"] = "border-left: 3px solid transparent; border-top-left-radius: 0; border-bottom-left-radius: 0;"
        t["navChecked"] = (f"color: white; font-weight: 600; border-left: 3px solid {t['a2']}; "
                           f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {t['navHover']}, stop:1 transparent);")
    else:
        t["navBase"] = ""
        t["navChecked"] = (f"color: white; font-weight: 600; "
                           f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {t['a1']}, stop:1 {t['a2']});")
    for k in ("grad1", "grad2", "grad3"):
        t.setdefault(k, t["bg"])
    q = _QSS.substitute(t)
    if t.get("flat"):
        tr, tg_, tb = t["tint"]
        c = f"{tr},{tg_},{tb}"
        q += f"""
QMainWindow {{ background: #000; }}
#Sidebar {{ background: rgba(0,0,0,0.25); border-right: 1px solid rgba({c},0.10); }}
QStackedWidget, QScrollArea, #ScrollInner {{ background: transparent; }}
#Card {{ background: transparent; border: none; border-radius: 0;
         border-top: 1px solid rgba({c},0.10); }}
QPlainTextEdit#Console {{ background: rgba(0,0,0,0.35); border: 1px solid rgba({c},0.12); }}
QComboBox, QLineEdit, QSpinBox {{ background: rgba(0,0,0,0.35); border: 1px solid rgba({c},0.18); }}
QPushButton {{ background: rgba({c},0.07); border: 1px solid rgba({c},0.18); }}
QPushButton:hover {{ background: rgba({c},0.16); border-color: {t['a1']}; }}
QPushButton#Nav {{ border-radius: 8px; border: none; margin: 0; padding: 10px 12px; background: transparent; }}
QPushButton#Nav:hover {{ background: rgba({c},0.10); }}
QPushButton#Nav:checked {{ background: rgba({c},0.16); color: white; border: none; }}
QPushButton#Discord {{ background: transparent; }}
"""
    if t["nav_style"] == "minimal":
        q += ("QPushButton#Discord { background: transparent; border: 1px solid %s; color: #aab4ff; font-weight: 500; }"
              "QPushButton#Discord:hover { background: #0b0f2a; border-color: #5865F2; color: white; }" % t["btnBorder"])
    return q
