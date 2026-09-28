"""ZapreTYZ — интерфейс (PySide6). Стиль: чёрный + синий градиент."""
from __future__ import annotations

import os
import re
import time
import webbrowser

from PySide6.QtCore import (Qt, QPropertyAnimation, QEasingCurve, Property, QRectF, QSize,
                            Signal, QTimer, QPointF)
from PySide6.QtGui import (QColor, QPainter, QLinearGradient, QBrush, QPen, QIcon, QFont,
                           QTextCursor, QAction, QGuiApplication, QPixmap, QRadialGradient)
from PySide6.QtWidgets import (QWidget, QMainWindow, QHBoxLayout, QVBoxLayout, QLabel,
                               QPushButton, QComboBox, QStackedWidget, QFrame, QPlainTextEdit,
                               QLineEdit, QSpinBox, QCheckBox, QButtonGroup, QRadioButton,
                               QSystemTrayIcon, QMenu, QMessageBox, QGridLayout, QSizePolicy,
                               QScrollArea, QApplication, QTextEdit)

import core
from core import LOG, log

import zapret_tools as zt
from themes import T, THEMES, ALIASES, set_theme, build_qss

DISCORD_URL = "https://discord.gg/qHabsmgKVP"
DISCORD_SVG = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 127.14 96.36"><path fill="white" d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,46,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,46,96.12,53,91.08,65.69,84.69,65.69Z"/></svg>'''


NAV_ICONS = {
    "menu": '<path d="M4 7h16M4 12h16M4 17h10"/>',
    "collapse": '<path d="M15 6l-6 6 6 6"/>',
    "home": '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/>',
    "zapret": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
    "tg": '<path d="M21 4L3 11l6 2 2 6 3-4 5 4z"/><path d="M9 13l12-9"/>',
    "updates": '<path d="M20 12a8 8 0 1 1-2.3-5.7"/><path d="M20 4v5h-5"/>',
    "tests": '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3"/><path d="M7.5 15h9"/>',
    "console": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 9l3 3-3 3M12 15h5"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
}


def line_icon(key, color, size=18) -> QIcon:
    from PySide6.QtSvg import QSvgRenderer
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
           f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{NAV_ICONS[key]}</svg>').encode()
    pm = QPixmap(size * 2, size * 2)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    QSvgRenderer(svg).render(p)
    p.end()
    pm.setDevicePixelRatio(2)
    return QIcon(pm)


def discord_icon(size=20) -> QIcon:
    from PySide6.QtSvg import QSvgRenderer
    pm = QPixmap(size, int(size * 0.76) + 1)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    QSvgRenderer(DISCORD_SVG).render(p)
    p.end()
    return QIcon(pm)


# ───────────────────────── Виджеты ─────────────────────────
class Toggle(QWidget):
    """Анимированный переключатель-слайдер."""
    toggled = Signal(bool)

    def __init__(self, w=64, h=34, parent=None):
        super().__init__(parent)
        self.setFixedSize(w, h)
        self.setCursor(Qt.PointingHandCursor)
        self._checked = False
        self._pos = 0.0
        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def getPos(self):
        return self._pos

    def setPos(self, v):
        self._pos = v
        self.update()

    offset = Property(float, getPos, setPos)

    def isChecked(self):
        return self._checked

    def setChecked(self, v: bool, animate=True, emit=False):
        if v == self._checked and not emit:
            return
        self._checked = v
        self._anim.stop()
        if animate:
            self._anim.setStartValue(self._pos)
            self._anim.setEndValue(1.0 if v else 0.0)
            self._anim.start()
        else:
            self.setPos(1.0 if v else 0.0)
        if emit:
            self.toggled.emit(v)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self.isEnabled():
            self.setChecked(not self._checked, emit=True)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(1, 1, self.width() - 2, self.height() - 2)
        rad = r.height() / 2
        off = QColor(T["toggleOff"])
        if self._pos > 0:
            g = QLinearGradient(r.topLeft(), r.topRight())
            a = int(255 * self._pos)
            c1, c2 = QColor(T["a1"]), QColor(T["a2"])
            c1.setAlpha(a); c2.setAlpha(a)
            g.setColorAt(0, c1)
            g.setColorAt(1, c2)
            p.setPen(Qt.NoPen)
            p.setBrush(off)
            p.drawRoundedRect(r, rad, rad)
            p.setBrush(QBrush(g))
            p.drawRoundedRect(r, rad, rad)
        else:
            p.setPen(QPen(QColor(T["inputBorder"]), 1))
            p.setBrush(off)
            p.drawRoundedRect(r, rad, rad)
        d = r.height() - 8
        x = r.left() + 4 + (r.width() - d - 8) * self._pos
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 60))
        p.drawEllipse(QRectF(x, r.top() + 5, d, d))
        p.setBrush(QColor("white") if self.isEnabled() else QColor("#6b7699"))
        p.drawEllipse(QRectF(x, r.top() + 4, d, d))


class Card(QFrame):
    def __init__(self, title: str | None = None, sub: str | None = None):
        super().__init__()
        self.setObjectName("Card")
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(22, 18, 22, 18)
        self.lay.setSpacing(12)
        if title:
            title = re.sub(r"^[^\wА-Яа-яЁё]+", "", title)
            t = QLabel(title)
            t.setObjectName("CardTitle")
            self.lay.addWidget(t)
        if sub:
            s = QLabel(sub)
            s.setObjectName("Muted")
            s.setWordWrap(True)
            self.lay.addWidget(s)


class GlowDot(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(14, 14)
        self.on = False

    def set(self, on):
        self.on = on
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = QColor("#3ddc97") if self.on else QColor("#3a4568")
        g = QRadialGradient(QPointF(7, 7), 7)
        g.setColorAt(0, c)
        c2 = QColor(c)
        c2.setAlpha(0)
        g.setColorAt(1, c2)
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawEllipse(0, 0, 14, 14)
        p.setBrush(c)
        p.drawEllipse(4, 4, 6, 6)


def page_header(title, sub):
    w = QWidget()
    l = QVBoxLayout(w)
    l.setContentsMargins(0, 0, 0, 6)
    l.setSpacing(2)
    t = QLabel(title)
    t.setObjectName("PageTitle")
    s = QLabel(sub)
    s.setObjectName("PageSub")
    l.addWidget(t)
    l.addWidget(s)
    return w


def scroll_page(inner: QWidget) -> QScrollArea:
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    sa.setWidget(inner)
    inner.setObjectName("ScrollInner")
    inner.setStyleSheet("#ScrollInner { background: transparent; }")
    return sa


def muted(text):
    l = QLabel(text)
    l.setObjectName("Muted")
    l.setWordWrap(True)
    return l


class Console(QPlainTextEdit):
    COLORS = {"zapret": "#4d9dff", "tg": "#22d3ee", "app": "#a78bfa"}

    def __init__(self, max_lines=3000):
        super().__init__()
        self.setObjectName("Console")
        self.setReadOnly(True)
        self.setMaximumBlockCount(max_lines)
        self.filter = None

    def append_line(self, src, text):
        if self.filter and src != self.filter:
            return
        ts = time.strftime("%H:%M:%S")
        text = re.sub(r"^\d\d:\d\d:\d\d\s+", "", text)
        color = self.COLORS.get(src, "#8c98bb")
        esc = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        tcolor = "#ff6b8a" if ("✖" in text or "ERROR" in text) else ("#ffd166" if ("⚠" in text or "WARN" in text) else "#b8c4e6")
        tag = {"zapret": "ZAPRET", "tg": "TG", "app": "APP"}.get(src, src.upper())
        self.appendHtml(f'<span style="color:#4b5675">{ts}</span> '
                        f'<span style="color:{color};font-weight:600">[{tag}]</span> '
                        f'<span style="color:{tcolor}">{esc}</span>')
        self.moveCursor(QTextCursor.End)


# ───────────────────────── Страницы ─────────────────────────
class HomePage(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        z, t = win.zapret, win.tg
        lay = QVBoxLayout(self)
        lay.setContentsMargins(34, 28, 34, 28)
        lay.setSpacing(16)
        lay.addWidget(page_header("Главная", "Быстрое управление обходом блокировок"))

        row = QHBoxLayout()
        row.setSpacing(16)

        # --- Zapret card ---
        zc = Card()
        top = QHBoxLayout()
        box = QVBoxLayout()
        box.setSpacing(3)
        tt = QLabel("Zapret")
        tt.setObjectName("CardTitle")
        tt.setStyleSheet("font-size: 20px;")
        box.addWidget(tt)
        sr = QHBoxLayout()
        self.z_dot = GlowDot()
        self.z_status = QLabel("Выключен")
        self.z_status.setObjectName("StatusOff")
        sr.addWidget(self.z_dot)
        sr.addWidget(self.z_status)
        sr.addStretch()
        box.addLayout(sr)
        top.addLayout(box)
        top.addStretch()
        self.z_toggle = Toggle(72, 38)
        self.z_toggle.toggled.connect(self.on_z_toggle)
        top.addWidget(self.z_toggle)
        zc.lay.addLayout(top)
        zc.lay.addWidget(muted("Работает как служба Windows — включается сам вместе с ПК"))
        lab = QLabel("Стратегия (сервис)")
        lab.setObjectName("Hint")
        zc.lay.addWidget(lab)
        self.strategy = QComboBox()
        self.strategy.setMinimumHeight(36)
        self.strategy.currentTextChanged.connect(self.on_strategy)
        zc.lay.addWidget(self.strategy)
        row.addWidget(zc, 1)

        # --- TG card ---
        tc = Card()
        top = QHBoxLayout()
        box = QVBoxLayout()
        box.setSpacing(3)
        tt = QLabel("TG WS Proxy")
        tt.setObjectName("CardTitle")
        tt.setStyleSheet("font-size: 20px;")
        box.addWidget(tt)
        sr = QHBoxLayout()
        self.t_dot = GlowDot()
        self.t_status = QLabel("Выключен")
        self.t_status.setObjectName("StatusOff")
        sr.addWidget(self.t_dot)
        sr.addWidget(self.t_status)
        sr.addStretch()
        box.addLayout(sr)
        top.addLayout(box)
        top.addStretch()
        self.t_toggle = Toggle(72, 38)
        self.t_toggle.toggled.connect(self.on_t_toggle)
        top.addWidget(self.t_toggle)
        tc.lay.addLayout(top)
        tc.lay.addWidget(muted("Локальный MTProto-прокси для Telegram через WebSocket"))
        self.t_addr = QLabel()
        self.t_addr.setObjectName("Hint")
        tc.lay.addWidget(self.t_addr)
        br = QHBoxLayout()
        b1 = QPushButton("Подключить в Telegram")
        b1.setObjectName("Primary")
        b1.setMinimumHeight(36)
        b1.clicked.connect(lambda: self.win.open_tg_link())
        b2 = QPushButton("Копировать ссылку")
        b2.setMinimumHeight(36)
        b2.clicked.connect(lambda: self.win.copy_tg_link())
        br.addWidget(b1)
        br.addWidget(b2)
        tc.lay.addLayout(br)
        row.addWidget(tc, 1)
        lay.addLayout(row)

        # --- тест подключения ---
        qc = Card()
        qh = QHBoxLayout()
        qt = QLabel("Тест подключения")
        qt.setObjectName("CardTitle")
        qh.addWidget(qt)
        self.q_summary = QLabel("")
        self.q_summary.setObjectName("Hint")
        qh.addWidget(self.q_summary)
        qh.addStretch()
        self.q_btn = QPushButton("Проверить")
        self.q_btn.setObjectName("Primary")
        self.q_btn.clicked.connect(self.run_quick)
        qh.addWidget(self.q_btn)
        more = QPushButton("Подбор стратегии →")
        more.clicked.connect(lambda: self.win.go("tests"))
        qh.addWidget(more)
        qc.lay.addLayout(qh)
        chips = QHBoxLayout()
        chips.setSpacing(10)
        self.q_chips = {}
        for g in zt.QUICK_GROUPS:
            w = QFrame()
            w.setObjectName("Chip")
            wl = QHBoxLayout(w)
            wl.setContentsMargins(12, 8, 12, 8)
            dot = GlowDot()
            wl.addWidget(dot)
            lb = QLabel(f"<b>{g}</b><br><span style='color:#7c84a0'>—</span>")
            wl.addWidget(lb, 1)
            chips.addWidget(w, 1)
            self.q_chips[g] = (dot, lb)
        qc.lay.addLayout(chips)
        lay.addWidget(qc)
        self.checker = zt.QuickChecker()
        self.checker.group_done.connect(self.on_group)
        self.checker.finished.connect(self.on_quick_done)

        # --- mini console ---
        cc = Card()
        hdr = QHBoxLayout()
        ct = QLabel("Журнал")
        ct.setObjectName("CardTitle")
        hdr.addWidget(ct)
        hdr.addStretch()
        full = QPushButton("Открыть консоль →")
        full.clicked.connect(lambda: self.win.go("console"))
        hdr.addWidget(full)
        cc.lay.addLayout(hdr)
        self.console = Console(400)
        cc.lay.addWidget(self.console, 1)
        lay.addWidget(cc, 1)

        z.state_changed.connect(self.set_z)
        z.state_changed.connect(lambda on: on and self.win.s.data.get("auto_quick_test", True)
                                and QTimer.singleShot(3500, self.run_quick))
        t.state_changed.connect(self.set_t)
        self.reload_strategies()
        self.refresh_addr()

    def run_quick(self):
        if self.checker.running:
            return
        self.q_btn.setEnabled(False)
        self.q_btn.setText("Проверка…")
        self.q_summary.setText("")
        for dot, lb in self.q_chips.values():
            dot.set(False)
            lb.setText(lb.text().split("<br>")[0] + "<br><span style='color:#7c84a0'>проверка…</span>")
        self.checker.start()

    def on_group(self, g, ok, total, ms):
        dot, lb = self.q_chips[g]
        dot.set(ok == total)
        col = "#3ddc97" if ok == total else ("#ffd166" if ok else "#ff6b8a")
        txt = f"{ok}/{total}" + (f" · {int(ms)} мс" if ok else " · недоступен")
        lb.setText(f"<b>{g}</b><br><span style='color:{col}'>{txt}</span>")
        log("app", f"Тест подключения — {g}: {txt}")

    def on_quick_done(self, ok, total):
        self.q_btn.setEnabled(True)
        self.q_btn.setText("Проверить")
        z = "Zapret вкл" if self.win.zapret.running() else "Zapret выкл"
        self.q_summary.setText(f"   {ok}/{total} доступно · {z} · {self.win.s['strategy'][:-4]}")
        if ok < total:
            self.win.notify("Тест подключения", f"Доступно {ok} из {total}. Попробуйте подбор стратегии во вкладке «Тесты».")

    def reload_strategies(self):
        cur = self.win.s["strategy"]
        self.strategy.blockSignals(True)
        self.strategy.clear()
        items = self.win.zapret.strategies()
        self.strategy.addItems([i[:-4] for i in items])
        if cur in items:
            self.strategy.setCurrentIndex(items.index(cur))
        elif items:
            self.win.s["strategy"] = items[0]
        self.strategy.blockSignals(False)

    def on_strategy(self, name):
        if not name:
            return
        self.win.s["strategy"] = name + ".bat"
        self.win.tray_rebuild()
        if self.win.zapret.running():
            log("app", f"Смена стратегии → {name}, перезапуск…")
            self.win.zapret.restart()

    def on_z_toggle(self, v):
        (self.win.zapret.start if v else self.win.zapret.stop)()

    def on_t_toggle(self, v):
        (self.win.tg.start if v else self.win.tg.stop)()

    def set_z(self, on):
        self.z_toggle.setChecked(on)
        self.z_dot.set(on)
        self.z_status.setText("Работает" if on else "Выключен")
        self.z_status.setObjectName("StatusOn" if on else "StatusOff")
        self.z_status.setStyleSheet("")

    def set_t(self, on):
        self.t_toggle.setChecked(on)
        self.t_dot.set(on)
        self.t_status.setText("Работает" if on else "Выключен")
        self.t_status.setObjectName("StatusOn" if on else "StatusOff")
        self.t_status.setStyleSheet("")

    def refresh_addr(self):
        c = self.win.s["tg"]
        self.t_addr.setText(f"Адрес: {c['host']}:{c['port']}")


class ZapretPage(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        z = win.zapret
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(34, 28, 34, 28)
        lay.setSpacing(16)
        lay.addWidget(page_header("Настройки Zapret", "Game Filter, IPSet, списки доменов и службы"))

        # Game filter
        gc = Card("🎮  Game Filter", "Расширяет обход на игровые порты (TCP/UDP). После изменения Zapret будет перезапущен.")
        gf = z.game_filter()
        rr = QHBoxLayout()
        self.gmode = QButtonGroup(self)
        for i, (k, label) in enumerate([("disabled", "Выключен"), ("all", "TCP + UDP"), ("tcp", "Только TCP"), ("udp", "Только UDP")]):
            rb = QRadioButton(label)
            rb.setProperty("key", k)
            rb.setChecked(gf["mode"] == k)
            self.gmode.addButton(rb, i)
            rr.addWidget(rb)
        rr.addStretch()
        gc.lay.addLayout(rr)
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.addWidget(QLabel("TCP порты"), 0, 0)
        grid.addWidget(QLabel("UDP порты"), 0, 1)
        self.gtcp = QLineEdit(gf["tcp"])
        self.gudp = QLineEdit(gf["udp"])
        self.gtcp.setPlaceholderText("1024-65535")
        self.gudp.setPlaceholderText("1024-65535")
        grid.addWidget(self.gtcp, 1, 0)
        grid.addWidget(self.gudp, 1, 1)
        gc.lay.addLayout(grid)
        gb = QPushButton("Применить Game Filter")
        gb.setObjectName("Primary")
        gb.clicked.connect(self.apply_game)
        gc.lay.addWidget(gb, 0, Qt.AlignLeft)
        lay.addWidget(gc)

        # IPSet
        ic = Card("🌐  IPSet Filter", "loaded — обход по списку IP; none — отключён; any — для всех IP.")
        ir = QHBoxLayout()
        self.imode = QButtonGroup(self)
        cur = z.ipset_mode() if z.installed() else "loaded"
        for i, (k, label) in enumerate([("loaded", "Loaded (список)"), ("none", "None"), ("any", "Any (все IP)")]):
            rb = QRadioButton(label)
            rb.setProperty("key", k)
            rb.setChecked(cur == k)
            self.imode.addButton(rb, i)
            ir.addWidget(rb)
        ir.addStretch()
        ic.lay.addLayout(ir)
        ib = QHBoxLayout()
        b = QPushButton("Применить")
        b.setObjectName("Primary")
        b.clicked.connect(self.apply_ipset)
        ib.addWidget(b)
        b = QPushButton("Обновить IPSet-лист")
        b.clicked.connect(lambda: self.win.bg(z.update_ipset, "Обновление IPSet"))
        ib.addWidget(b)
        b = QPushButton("Обновить hosts")
        b.clicked.connect(lambda: self.win.bg(z.update_hosts, "Обновление hosts"))
        ib.addWidget(b)
        ib.addStretch()
        ic.lay.addLayout(ib)
        lay.addWidget(ic)

        # Lists
        lc = Card("📝  Пользовательские списки", "Добавляйте свои домены и исключения. Файлы сохраняются при обновлении Zapret.")
        lr = QHBoxLayout()
        for fname, label in [("list-general-user.txt", "Мои домены"), ("list-exclude-user.txt", "Исключения доменов"),
                             ("ipset-exclude-user.txt", "Исключения IP")]:
            b = QPushButton(label)
            b.clicked.connect(lambda _=False, f=fname: self.open_list(f))
            lr.addWidget(b)
        b = QPushButton("Папка Zapret")
        b.clicked.connect(lambda: self.win.open_path(core.ZAPRET_DIR))
        lr.addWidget(b)
        lr.addStretch()
        lc.lay.addLayout(lr)
        lay.addWidget(lc)

        # Fakes
        fc = Card("Активные фейки", "Какие .bin-фейки используются для Discord UDP и Game Filter UDP (пункт 7 service.bat).")
        fg = QGridLayout()
        fg.setHorizontalSpacing(12)
        fg.addWidget(QLabel("Discord UDP"), 0, 0)
        fg.addWidget(QLabel("GameFilter UDP"), 0, 1)
        self.fake_d = QComboBox()
        self.fake_g = QComboBox()
        fg.addWidget(self.fake_d, 1, 0)
        fg.addWidget(self.fake_g, 1, 1)
        fc.lay.addLayout(fg)
        b = QPushButton("Применить фейки")
        b.setObjectName("Primary")
        b.clicked.connect(self.apply_fakes)
        fc.lay.addWidget(b, 0, Qt.AlignLeft)
        lay.addWidget(fc)

        # Misc
        mc = Card("Прочее")
        self.auto_upd = QCheckBox("Проверять обновления Zapret автоматически (Auto-Update Check)")
        self.auto_upd.setChecked(zt.check_updates_enabled())
        self.auto_upd.toggled.connect(lambda v: (zt.set_check_updates(v), self.win.s.__setitem__("auto_check_updates", v)))
        mc.lay.addWidget(self.auto_upd)
        mr = QHBoxLayout()
        b = QPushButton("Перезапустить Zapret")
        b.clicked.connect(lambda: z.restart())
        mr.addWidget(b)
        b = QPushButton("Удалить службы zapret / WinDivert")
        b.setObjectName("Danger")
        b.clicked.connect(self.remove_services)
        mr.addWidget(b)
        b = QPushButton("Очистить кэш Discord")
        b.clicked.connect(lambda: self.win.bg(lambda: [log("app", m) for m in zt.clear_discord_cache()], "Кэш Discord"))
        mr.addWidget(b)
        mr.addStretch()
        mc.lay.addLayout(mr)
        lay.addWidget(mc)
        lay.addStretch()

        l = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(scroll_page(inner))

    def apply_game(self):
        mode = self.gmode.checkedButton().property("key")
        tcp = self.gtcp.text().strip() or "1024-65535"
        udp = self.gudp.text().strip() or "1024-65535"
        for v in (tcp, udp):
            if not re.fullmatch(r"\d+(-\d+)?(,\d+(-\d+)?)*", v):
                QMessageBox.warning(self, "Game Filter", f"Неверный формат портов: {v}\nПример: 1024-1934,1936-65535")
                return
        self.win.zapret.set_game_filter(mode, tcp, udp)
        log("app", f"Game Filter: {mode} (TCP {tcp}, UDP {udp})")
        if self.win.zapret.running():
            self.win.zapret.restart()

    def apply_ipset(self):
        mode = self.imode.checkedButton().property("key")
        try:
            self.win.zapret.set_ipset_mode(mode)
            log("app", f"IPSet режим: {mode}")
            if self.win.zapret.running():
                self.win.zapret.restart()
        except Exception as e:
            QMessageBox.warning(self, "IPSet", str(e))

    def open_list(self, fname):
        self.win.zapret.ensure_user_lists()
        self.win.open_path(core.ZAPRET_DIR / "lists" / fname)

    def remove_services(self):
        if QMessageBox.question(self, "Службы", "Остановить и удалить службы zapret и WinDivert?") == QMessageBox.Yes:
            if self.win.zapret.running():
                self.win.zapret.stop()
            self.win.bg(zt.service_remove, "Удаление служб")

    def reload(self):
        z = self.win.zapret
        if z.installed():
            info = zt.fakes_info()
            for cb, key in ((self.fake_d, "discord"), (self.fake_g, "game")):
                cb.clear()
                cb.addItems(info["files"])
                if info[key] in info["files"]:
                    cb.setCurrentText(info[key])

    def apply_fakes(self):
        try:
            if self.fake_d.currentText():
                zt.replace_fake("discord", self.fake_d.currentText())
            if self.fake_g.currentText():
                zt.replace_fake("game", self.fake_g.currentText())
            if self.win.zapret.running():
                self.win.zapret.restart()
        except Exception as e:
            QMessageBox.warning(self, "Фейки", str(e))


class TestsPage(QWidget):
    """Тест стратегий + диагностика (пункты 11 и 12 service.bat)."""
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.tester = zt.StrategyTester(win.zapret)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(34, 28, 34, 28)
        lay.setSpacing(16)
        lay.addWidget(page_header("Тесты и диагностика", "Подбор лучшей стратегии и проверка системы"))

        tc = Card("Тест стратегий", "Каждая стратегия запускается по очереди и проверяется доступ к Discord, YouTube, Google, "
                                    "Cloudflare и др. (utils/targets.txt): TLS 1.2, TLS 1.3 и отправка 16 КБ+.")
        self.list_box = QWidget()
        self.grid = QGridLayout(self.list_box)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(18)
        self.grid.setVerticalSpacing(4)
        self.checks = {}
        tc.lay.addWidget(self.list_box)
        sel = QHBoxLayout()
        for text, val in (("Выбрать все", True), ("Снять все", False)):
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, v=val: [c.setChecked(v) for c in self.checks.values()])
            sel.addWidget(b)
        sel.addStretch()
        self.run_btn = QPushButton("Запустить тест")
        self.run_btn.setObjectName("Primary")
        self.run_btn.clicked.connect(self.run_test)
        sel.addWidget(self.run_btn)
        self.stop_btn = QPushButton("Стоп")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.tester.stop)
        sel.addWidget(self.stop_btn)
        tc.lay.addLayout(sel)
        from PySide6.QtWidgets import QProgressBar
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(6)
        tc.lay.addWidget(self.bar)
        self.state = QLabel("")
        self.state.setObjectName("Hint")
        tc.lay.addWidget(self.state)
        self.results = QPlainTextEdit()
        self.results.setObjectName("Console")
        self.results.setReadOnly(True)
        self.results.setMinimumHeight(220)
        tc.lay.addWidget(self.results)
        br = QHBoxLayout()
        self.best_btn = QPushButton("Применить лучшую стратегию")
        self.best_btn.setObjectName("Primary")
        self.best_btn.setEnabled(False)
        self.best_btn.clicked.connect(self.apply_best)
        br.addWidget(self.best_btn)
        b = QPushButton("Оригинальный тест Flowseal (PowerShell)")
        b.clicked.connect(lambda: self.win.bg(zt.open_original_test, "Тест"))
        br.addWidget(b)
        b = QPushButton("Результаты тестов")
        b.clicked.connect(lambda: self.win.open_path(core.ZAPRET_DIR / "utils" / "test results"))
        br.addWidget(b)
        br.addStretch()
        tc.lay.addLayout(br)
        lay.addWidget(tc)

        dc = Card("Диагностика", "Проверка BFE, прокси, TCP timestamps, конфликтующих программ (Adguard, Killer, Intel, "
                                 "Check Point, SmartByte, VPN, GoodbyeDPI), пути установки, WinDivert, DNS и hosts.")
        drow = QHBoxLayout()
        b = QPushButton("Запустить диагностику")
        b.setObjectName("Primary")
        b.clicked.connect(self.run_diag)
        drow.addWidget(b)
        b = QPushButton("Очистить кэш Discord")
        b.clicked.connect(lambda: self.win.bg(lambda: [log("app", m) for m in zt.clear_discord_cache()], "Кэш Discord"))
        drow.addWidget(b)
        drow.addStretch()
        dc.lay.addLayout(drow)
        self.diag = QLabel("")
        self.diag.setWordWrap(True)
        self.diag.setTextFormat(Qt.RichText)
        dc.lay.addWidget(self.diag)
        lay.addWidget(dc)
        lay.addStretch()
        l = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(scroll_page(inner))

        self.tester.progress.connect(self.on_progress)
        self.tester.strategy_result.connect(self.on_result)
        self.tester.finished.connect(self.on_finished)
        self.best = None
        self.reload()

    def reload(self):
        for c in self.checks.values():
            c.setParent(None)
        self.checks.clear()
        for i, st in enumerate(self.win.zapret.strategies()):
            cb = QCheckBox(st[:-4])
            cb.setChecked(True)
            self.grid.addWidget(cb, i // 3, i % 3)
            self.checks[st] = cb

    def run_test(self):
        sel = [st for st, c in self.checks.items() if c.isChecked()]
        if not sel:
            return
        if not self.win.zapret.installed():
            QMessageBox.warning(self, "Тест", "Zapret не установлен")
            return
        self.results.clear()
        self.best = None
        self.best_btn.setEnabled(False)
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.bar.setRange(0, len(sel))
        self.bar.setValue(0)
        log("app", f"Тест стратегий: {len(sel)} шт.")
        self.tester.start(sel, zt.load_targets())

    def on_progress(self, done, total, text):
        self.bar.setValue(done)
        self.state.setText(f"{text}  ({done}/{total})")

    def on_result(self, st, ok, total, dt, details):
        pct = int(ok * 100 / max(1, total))
        mark = "✔" if pct >= 90 else ("◐" if pct >= 50 else "✖")
        self.results.appendPlainText(f"{mark} {st[:-4]:<34} {ok}/{total}  ({pct}%)  ~{dt:.1f}с")
        for d in details:
            self.results.appendPlainText("     " + d)
        log("zapret", f"Тест {st[:-4]}: {ok}/{total}")

    def on_finished(self, results):
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if not results:
            return
        self.results.appendPlainText("\n══════ РЕЙТИНГ ══════")
        for i, (st, ok, total, dt) in enumerate(results[:10], 1):
            self.results.appendPlainText(f"{i:>2}. {st[:-4]:<34} {ok}/{total}  ~{dt:.1f}с")
        self.best = results[0][0]
        self.best_btn.setEnabled(True)
        self.best_btn.setText(f"Применить лучшую: {self.best[:-4]}")
        self.win.notify("Тест завершён", f"Лучшая стратегия: {self.best[:-4]}")

    def apply_best(self):
        if self.best:
            self.win.home.strategy.setCurrentText(self.best[:-4])
            if not self.win.zapret.running():
                self.win.zapret.start()
            self.win.go("home")

    def run_diag(self):
        self.diag.setText("Проверка…")

        def work():
            res = zt.run_diagnostics()
            col = {"ok": "#3ddc97", "warn": "#ffd166", "err": "#ff6b8a"}
            ico = {"ok": "✔", "warn": "⚠", "err": "✖"}
            html = "<br>".join(f'<span style="color:{col[s]}">{ico[s]}</span>&nbsp; {t}' for s, t in res)
            QTimer.singleShot(0, self, lambda: self.diag.setText(html))
            for s, t in res:
                log("app", f"{ico[s]} {t}")
        self.win.bg(work, "Диагностика")


class TgPage(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        c = win.s["tg"]
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(34, 28, 34, 28)
        lay.setSpacing(16)
        lay.addWidget(page_header("Настройки TG WS Proxy", "Параметры локального MTProto-прокси"))

        nc = Card("🔌  Подключение")
        g = QGridLayout()
        g.setHorizontalSpacing(14)
        g.setVerticalSpacing(8)
        self.host = QLineEdit(c["host"])
        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(int(c["port"]))
        self.secret = QLineEdit(c["secret"])
        self.secret.setMaxLength(32)
        regen = QPushButton("⟳")
        regen.setToolTip("Сгенерировать новый секрет")
        regen.setFixedWidth(42)
        regen.clicked.connect(lambda: self.secret.setText(__import__("secrets").token_hex(16)))
        g.addWidget(QLabel("Хост"), 0, 0)
        g.addWidget(QLabel("Порт"), 0, 1)
        g.addWidget(self.host, 1, 0)
        g.addWidget(self.port, 1, 1)
        g.addWidget(QLabel("Секрет (32 hex)"), 2, 0, 1, 2)
        sr = QHBoxLayout()
        sr.addWidget(self.secret)
        sr.addWidget(regen)
        g.addLayout(sr, 3, 0, 1, 2)
        nc.lay.addLayout(g)
        lay.addWidget(nc)

        dc = Card("🛰  Дата-центры и WebSocket", "DC:IP через запятую. Пусто — использовать значения по умолчанию прокси.")
        self.dcip = QLineEdit(", ".join(c["dc_ip"]))
        self.dcip.setPlaceholderText("2:149.154.167.220, 4:149.154.167.220")
        dc.lay.addWidget(self.dcip)
        g2 = QGridLayout()
        g2.setHorizontalSpacing(14)
        self.pool = QSpinBox()
        self.pool.setRange(0, 32)
        self.pool.setValue(int(c["pool_size"]))
        self.buf = QSpinBox()
        self.buf.setRange(4, 8192)
        self.buf.setSuffix(" KB")
        self.buf.setValue(int(c["buf_kb"]))
        g2.addWidget(QLabel("Пул WS-соединений на DC"), 0, 0)
        g2.addWidget(QLabel("Буфер сокета"), 0, 1)
        g2.addWidget(self.pool, 1, 0)
        g2.addWidget(self.buf, 1, 1)
        dc.lay.addLayout(g2)
        lay.addWidget(dc)

        cf = Card("☁  Cloudflare fallback и маскировка")
        self.cfp = QCheckBox("Использовать Cloudflare-proxy fallback")
        self.cfp.setChecked(bool(c["cfproxy"]))
        self.nosec = QCheckBox("Порт 80 для CF-proxy / CF-worker (без TLS)")
        self.nosec.setChecked(bool(c["no_secure"]))
        self.cfd = QLineEdit(c["cfproxy_domains"])
        self.cfd.setPlaceholderText("Свои CF-домены (через запятую)")
        self.cfw = QLineEdit(c["cfproxy_worker_domains"])
        self.cfw.setPlaceholderText("Домены CF Worker (через запятую)")
        self.ftls = QLineEdit(c["fake_tls_domain"])
        self.ftls.setPlaceholderText("Fake TLS домен (SNI), например example.com — пусто = выкл")
        self.verbose = QCheckBox("Подробный лог (debug)")
        self.verbose.setChecked(bool(c["verbose"]))
        for w in (self.cfp, self.nosec, self.cfd, self.cfw, self.ftls, self.verbose):
            cf.lay.addWidget(w)
        lay.addWidget(cf)

        br = QHBoxLayout()
        sv = QPushButton("Сохранить и применить")
        sv.setObjectName("Primary")
        sv.setMinimumHeight(38)
        sv.clicked.connect(self.save)
        br.addWidget(sv)
        rs = QPushButton("Сбросить по умолчанию")
        rs.setMinimumHeight(38)
        rs.clicked.connect(self.reset)
        br.addWidget(rs)
        br.addStretch()
        lay.addLayout(br)
        lay.addStretch()

        l = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(scroll_page(inner))

    def save(self):
        sec = self.secret.text().strip()
        if not re.fullmatch(r"[0-9a-fA-F]{32}", sec):
            QMessageBox.warning(self, "TG WS Proxy", "Секрет должен состоять из 32 hex-символов.")
            return
        dcs = [d.strip() for d in self.dcip.text().split(",") if d.strip()]
        for d in dcs:
            if not re.fullmatch(r"\d+:[\d.:a-fA-F]+", d):
                QMessageBox.warning(self, "TG WS Proxy", f"Неверный формат DC:IP — {d}")
                return
        c = self.win.s["tg"]
        c.update(host=self.host.text().strip() or "127.0.0.1", port=self.port.value(), secret=sec.lower(),
                 dc_ip=dcs, pool_size=self.pool.value(), buf_kb=self.buf.value(),
                 cfproxy=self.cfp.isChecked(), no_secure=self.nosec.isChecked(),
                 cfproxy_domains=self.cfd.text().strip(), cfproxy_worker_domains=self.cfw.text().strip(),
                 fake_tls_domain=self.ftls.text().strip(), verbose=self.verbose.isChecked())
        self.win.s.save()
        self.win.home.refresh_addr()
        log("app", "Настройки TG WS Proxy сохранены")
        if self.win.tg.running():
            self.win.tg.restart()

    def reset(self):
        d = core.DEFAULTS["tg"]
        self.host.setText(d["host"])
        self.port.setValue(d["port"])
        self.dcip.setText(", ".join(d["dc_ip"]))
        self.pool.setValue(d["pool_size"])
        self.buf.setValue(d["buf_kb"])
        self.cfp.setChecked(True)
        self.nosec.setChecked(False)
        self.cfd.clear()
        self.cfw.clear()
        self.ftls.clear()
        self.verbose.setChecked(False)


class UpdatesPage(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        up = win.updater
        lay = QVBoxLayout(self)
        lay.setContentsMargins(34, 28, 34, 28)
        lay.setSpacing(16)
        lay.addWidget(page_header("Обновления", "Актуальные версии компонентов с GitHub (Flowseal)"))
        self.rows = {}
        for comp, title, repo in [("zapret", "Zapret (zapret-discord-youtube)", core.ZAPRET_REPO),
                                  ("tg", "TG WS Proxy", core.TG_REPO)]:
            c = Card(title)
            info = QHBoxLayout()
            local = QLabel()
            remote = QLabel("Последняя: —")
            remote.setObjectName("Muted")
            info.addWidget(local)
            info.addSpacing(20)
            info.addWidget(remote)
            info.addStretch()
            c.lay.addLayout(info)
            status = muted("")
            c.lay.addWidget(status)
            br = QHBoxLayout()
            chk = QPushButton("Проверить")
            chk.clicked.connect(lambda _=False, k=comp: self.check(k))
            ins = QPushButton("Установить обновление")
            ins.setObjectName("Primary")
            ins.clicked.connect(lambda _=False, k=comp: self.install(k))
            gh = QPushButton("GitHub")
            gh.clicked.connect(lambda _=False, r=repo: webbrowser.open(f"https://github.com/{r}"))
            br.addWidget(chk)
            br.addWidget(ins)
            br.addWidget(gh)
            br.addStretch()
            c.lay.addLayout(br)
            lay.addWidget(c)
            self.rows[comp] = dict(local=local, remote=remote, status=status, chk=chk, ins=ins)
        allb = QPushButton("Проверить всё")
        allb.clicked.connect(lambda: [self.check(k) for k in self.rows])
        lay.addWidget(allb, 0, Qt.AlignLeft)
        lay.addStretch()
        up.checked.connect(self.on_checked)
        up.progress.connect(self.on_progress)
        up.finished.connect(self.on_finished)
        self.refresh_local()

    def refresh_local(self):
        self.rows["zapret"]["local"].setText(f"Установлена: <b>{self.win.zapret.version()}</b>")
        self.rows["tg"]["local"].setText(f"Установлена: <b>{self.win.tg.version()}</b>")

    def check(self, k):
        self.rows[k]["status"].setText("Проверка…")
        self.win.updater.check(k)

    def install(self, k):
        r = self.rows[k]
        r["ins"].setEnabled(False)
        r["chk"].setEnabled(False)
        r["status"].setText("Установка…")
        self.win.updater.install(k)

    def on_checked(self, k, local, remote, has):
        r = self.rows[k]
        if remote:
            r["remote"].setText(f"Последняя: {remote}")
            r["status"].setText("🔔 Доступно обновление!" if has else "✔ Установлена последняя версия")
            if has:
                log("app", f"Доступно обновление {k}: {local} → {remote}")
                self.win.notify("Доступно обновление", f"{'Zapret' if k == 'zapret' else 'TG WS Proxy'} {remote}")

    def on_progress(self, k, msg):
        self.rows[k]["status"].setText(msg)
        log(k, msg)

    def on_finished(self, k, ok, msg):
        r = self.rows[k]
        r["ins"].setEnabled(True)
        r["chk"].setEnabled(True)
        r["status"].setText(("✔ " if ok else "✖ ") + msg)
        log(k, msg)
        self.refresh_local()
        if k == "zapret":
            self.win.home.reload_strategies()
            self.win.pages["zapret"][1].reload()
            self.win.pages["tests"][1].reload()
            self.win.tray_rebuild()


class ConsolePage(QWidget):
    def __init__(self, win):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(34, 28, 34, 28)
        lay.setSpacing(14)
        lay.addWidget(page_header("Консоль", "Вывод winws.exe, TG WS Proxy и приложения"))
        bar = QHBoxLayout()
        self.flt = QComboBox()
        self.flt.addItems(["Все источники", "Zapret", "TG WS Proxy", "Приложение"])
        self.flt.currentIndexChanged.connect(self.set_filter)
        bar.addWidget(self.flt)
        bar.addStretch()
        cp = QPushButton("Копировать")
        cp.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.console.toPlainText()))
        cl = QPushButton("Очистить")
        cl.clicked.connect(lambda: self.console.clear())
        bar.addWidget(cp)
        bar.addWidget(cl)
        lay.addLayout(bar)
        self.console = Console()
        lay.addWidget(self.console, 1)

    def set_filter(self, i):
        self.console.filter = [None, "zapret", "tg", "app"][i]


class ThemeButton(QPushButton):
    """Карточка-превью темы: рисует мини-макет окна в её цветах."""
    def __init__(self, key, th):
        super().__init__()
        self.th = th
        self.setObjectName("ThemeCard")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumWidth(150)
        self.setFixedHeight(110)

    def paintEvent(self, e):
        super().paintEvent(e)
        th = self.th
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(12, 12, self.width() - 24, self.height() - 44)
        rad = max(3, th["radius"] / 3)
        p.setPen(QPen(QColor(th["cardBorder"]), 1))
        p.setBrush(QColor(th["bg"]))
        p.drawRoundedRect(r, rad, rad)
        side = QRectF(r.left(), r.top(), r.width() * 0.28, r.height())
        g = QLinearGradient(side.topLeft(), side.bottomLeft())
        g.setColorAt(0, QColor(th["side1"]))
        g.setColorAt(1, QColor(th["side2"]))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(side, rad, rad)
        ag = QLinearGradient(side.topLeft(), side.topRight())
        ag.setColorAt(0, QColor(th["a1"]))
        ag.setColorAt(1, QColor(th["a2"]))
        p.setBrush(ag)
        p.drawRoundedRect(QRectF(side.left() + 5, side.top() + 10, side.width() - 10, 8), 3, 3)
        p.setBrush(QColor(th["nav"]).darker(250))
        for i in range(3):
            p.drawRoundedRect(QRectF(side.left() + 5, side.top() + 24 + i * 11, side.width() - 14, 5), 2, 2)
        cw = (r.width() - side.width() - 18) / 2
        for i in range(2):
            cr = QRectF(side.right() + 6 + i * (cw + 6), r.top() + 10, cw, r.height() * 0.45)
            p.setPen(QPen(QColor(th["cardBorder"]), 1))
            p.setBrush(QColor(th["card1"]))
            p.drawRoundedRect(cr, rad, rad)
            p.setPen(Qt.NoPen)
            p.setBrush(ag if i == 1 else QColor(th["toggleOff"]))
            p.drawRoundedRect(QRectF(cr.right() - 20, cr.top() + 5, 15, 8), 4, 4)
        p.setBrush(QColor(th["console"]))
        p.setPen(QPen(QColor(th["cardBorder"]), 1))
        p.drawRoundedRect(QRectF(side.right() + 6, r.top() + r.height() * 0.45 + 16, r.width() - side.width() - 12,
                                 r.height() * 0.55 - 22), rad, rad)
        p.setPen(QColor(T["text"]))
        f = p.font()
        f.setPointSize(10)
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(14, self.height() - 30, self.width() - 28, 22), Qt.AlignVCenter | Qt.AlignLeft, th["name"])


class SettingsPage(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        s = win.s
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(34, 28, 34, 28)
        lay.setSpacing(16)
        lay.addWidget(page_header("Настройки приложения", f"{core.DISPLAY_NAME} v{core.APP_VERSION}"))
        c = Card("⚙  Общие")
        self.chk = {}
        for key, label in [("autostart", "Запускать программу вместе с Windows (Zapret стартует сам, без неё)"),
                           ("start_minimized", "Запускать свёрнутым в трей"),
                           ("close_to_tray", "Кнопка «Закрыть» сворачивает в трей"),
                           ("restore_state", "Включать TG WS Proxy при запуске, если он был включён"),
                           ("auto_quick_test", "Проверять подключение после включения Zapret")]:
            cb = QCheckBox(label)
            cb.setChecked(bool(s.data.get(key, True)))
            cb.toggled.connect(lambda v, k=key: self.on_chk(k, v))
            c.lay.addWidget(cb)
            self.chk[key] = cb
        lay.addWidget(c)
        tc = Card("Цвет оформления", "Меняет цвет интерфейса, иконки в трее и ярлыков")
        tg = QGridLayout()
        tg.setSpacing(10)
        self.tgrp = QButtonGroup(self)
        for i, (key, th) in enumerate(THEMES.items()):
            b = ThemeButton(key, th)
            b.setChecked(ALIASES.get(s.data.get("theme", "blue"), s.data.get("theme", "blue")) == key)
            b.clicked.connect(lambda _=False, k=key: win.apply_theme(k))
            self.tgrp.addButton(b)
            tg.addWidget(b, i // 4, i % 4)
        tc.lay.addLayout(tg)
        lay.addWidget(tc)
        a = Card("О программе",
                 "Yume Haze Zapret — графический интерфейс для zapret-discord-youtube и tg-ws-proxy от Flowseal. "
                 "Все права на компоненты принадлежат их авторам.")
        br = QHBoxLayout()
        for text, url in [("zapret-discord-youtube", f"https://github.com/{core.ZAPRET_REPO}"),
                          ("tg-ws-proxy", f"https://github.com/{core.TG_REPO}")]:
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, u=url: webbrowser.open(u))
            br.addWidget(b)
        b = QPushButton("  Discord")
        b.setObjectName("Discord")
        b.setIcon(discord_icon(18))
        b.clicked.connect(lambda: webbrowser.open(DISCORD_URL))
        br.addWidget(b)
        b = QPushButton("Папка данных")
        b.clicked.connect(lambda: win.open_path(core.DATA_DIR))
        br.addWidget(b)
        br.addStretch()
        a.lay.addLayout(br)
        lay.addWidget(a)
        lay.addStretch()
        l = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(scroll_page(inner))

    def on_chk(self, k, v):
        self.win.s[k] = v
        if k == "autostart":
            core.set_autostart(v)


# ───────────────────────── Главное окно ─────────────────────────
class GradientRoot(QWidget):
    """Единый фон на всё окно: тёмно-синий → чёрный."""
    def __init__(self):
        super().__init__()
        self.setObjectName("Root")
        self.setAttribute(Qt.WA_StyledBackground, False)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        g = QLinearGradient(0, 0, w * 0.55, h)
        g.setColorAt(0, QColor(T.get("grad1", T["bg"])))
        g.setColorAt(0.55, QColor(T.get("grad2", T["bg"])))
        g.setColorAt(1, QColor(T.get("grad3", T["bg"])))
        p.fillRect(self.rect(), g)
        r, gg, b, a = T["glow"]
        if a:
            rg = QRadialGradient(QPointF(w * 0.15, 0), max(w, h) * 0.6)
            rg.setColorAt(0, QColor(r, gg, b, a))
            rg.setColorAt(1, QColor(r, gg, b, 0))
            p.fillRect(self.rect(), rg)


class Sidebar(QFrame):
    COLLAPSED, EXPANDED = 64, 200

    def __init__(self):
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(self.COLLAPSED)


def logo_pixmap(size=30) -> QPixmap:
    """Простой логотип: голубая «Z» с градиентом."""
    pm = QPixmap(size * 2, size * 2)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size * 2
    g = QLinearGradient(0, 0, s, s)
    g.setColorAt(0, QColor(T["a1"]))
    g.setColorAt(1, QColor(T["a2"]))
    pen = QPen(QBrush(g), s * 0.14, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    m = s * 0.22
    from PySide6.QtGui import QPainterPath
    path = QPainterPath()
    path.moveTo(m, m)
    path.lineTo(s - m, m)
    path.lineTo(m, s - m)
    path.lineTo(s - m, s - m)
    p.drawPath(path)
    p.end()
    pm.setDevicePixelRatio(2)
    return pm


def app_icon_pixmap(size=256) -> QPixmap:
    """Иконка приложения в цвете темы: «Z» на тёмном скруглённом квадрате."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    tr, tg_, tb = T["tint"]
    g = QLinearGradient(0, 0, size, size)
    g.setColorAt(0, QColor(int(tr * .22), int(tg_ * .22), int(tb * .22)))
    g.setColorAt(1, QColor(2, 2, 6))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    m = size * 0.04
    p.drawRoundedRect(QRectF(m, m, size - 2 * m, size - 2 * m), size * 0.22, size * 0.22)
    zg = QLinearGradient(0, 0, size, size)
    zg.setColorAt(0, QColor(T["a1"]))
    zg.setColorAt(1, QColor(T["a2"]))
    p.setPen(QPen(QBrush(zg), size * 0.12, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    from PySide6.QtGui import QPainterPath
    k = size * 0.29
    path = QPainterPath()
    path.moveTo(k, k)
    path.lineTo(size - k, k)
    path.lineTo(k, size - k)
    path.lineTo(size - k, size - k)
    p.drawPath(path)
    p.end()
    return pm


def themed_icon() -> QIcon:
    ic = QIcon()
    for sz in (16, 24, 32, 48, 64, 128, 256):
        ic.addPixmap(app_icon_pixmap(sz))
    return ic


class MainWindow(QMainWindow):
    def __init__(self, settings, zapret, tg, updater, icon: QIcon):
        super().__init__()
        self.s, self.zapret, self.tg, self.updater = settings, zapret, tg, updater
        self.icon = icon
        self._quitting = False
        self.setWindowTitle(core.DISPLAY_NAME)
        self.setWindowIcon(icon)
        self.resize(1080, 700)
        self.setMinimumSize(860, 580)

        root = GradientRoot()
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        side = Sidebar()
        self.side = side
        sl = QVBoxLayout(side)
        sl.setContentsMargins(10, 18, 10, 14)
        sl.setSpacing(4)

        # логотип: Z + TYZ (текст виден только в раскрытом виде)
        lr = QHBoxLayout()
        lr.setContentsMargins(6, 0, 0, 0)
        lr.setSpacing(10)
        self.logo_icon = QLabel()
        self.logo_icon.setFixedSize(30, 30)
        lr.addWidget(self.logo_icon)
        lt = QVBoxLayout()
        lt.setSpacing(0)
        self.logo = QLabel()
        self.logo.setObjectName("Logo")
        lt.addWidget(self.logo)
        self.logo_sub = QLabel("Yume Haze Zapret")
        self.logo_sub.setObjectName("LogoSub")
        lt.addWidget(self.logo_sub)
        self.logo_text = QWidget()
        self.logo_text.setLayout(lt)
        lt.setContentsMargins(0, 0, 0, 0)
        lr.addWidget(self.logo_text)
        lr.addStretch()
        sl.addLayout(lr)
        self.update_logo()
        sl.addSpacing(14)

        # кнопка раскрытия меню
        self.menu_btn = QPushButton()
        self.menu_btn.setObjectName("Nav")
        self.menu_btn.setIconSize(QSize(18, 18))
        self.menu_btn.setCursor(Qt.PointingHandCursor)
        self.menu_btn.setToolTip("Показать / скрыть названия")
        self.menu_btn.clicked.connect(self.toggle_sidebar)
        sl.addWidget(self.menu_btn)
        sl.addSpacing(6)

        self.stack = QStackedWidget()
        self.home = HomePage(self)
        self.pages = {
            "home": ("Главная", self.home),
            "zapret": ("Zapret", ZapretPage(self)),
            "tg": ("TG WS Proxy", TgPage(self)),
            "tests": ("Тесты", TestsPage(self)),
            "updates": ("Обновления", UpdatesPage(self)),
            "console": ("Консоль", ConsolePage(self)),
            "settings": ("Настройки", SettingsPage(self)),
        }
        self.nav = {}
        grp = QButtonGroup(self)
        for key, (label, page) in self.pages.items():
            if key == "settings":
                sl.addStretch()
            b = QPushButton()
            b.setObjectName("Nav")
            b.setProperty("label", label)
            b.setToolTip(label)
            b.setIconSize(QSize(18, 18))
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, k=key: self.go(k))
            grp.addButton(b)
            sl.addWidget(b)
            self.nav[key] = b
            self.stack.addWidget(page)
        self.dc_btn = QPushButton()
        self.dc_btn.setObjectName("Nav")
        self.dc_btn.setProperty("label", "Наш Discord")
        self.dc_btn.setIcon(discord_icon(20))
        self.dc_btn.setIconSize(QSize(20, 16))
        self.dc_btn.setCursor(Qt.PointingHandCursor)
        self.dc_btn.setToolTip("Discord-сервер")
        self.dc_btn.clicked.connect(lambda: webbrowser.open(DISCORD_URL))
        sl.addWidget(self.dc_btn)
        self.ver = QLabel(f"v{core.APP_VERSION}" + ("" if core.is_admin() or not core.IS_WIN else " ⚠"))
        self.ver.setObjectName("LogoSub")
        self.ver.setAlignment(Qt.AlignCenter)
        self.ver.setContentsMargins(0, 6, 0, 0)
        sl.addWidget(self.ver)

        h.addWidget(side)
        h.addWidget(self.stack, 1)
        self.setCentralWidget(root)

        from PySide6.QtCore import QVariantAnimation
        self._side_anim = QVariantAnimation(self)
        self._side_anim.setDuration(180)
        self._side_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._side_anim.valueChanged.connect(lambda v: side.setFixedWidth(int(v)))
        self.expanded = bool(self.s.data.get("sidebar_expanded", False))
        self.apply_sidebar(animate=False)
        self.go("home")

        LOG.line.connect(self.home.console.append_line)
        LOG.line.connect(self.pages["console"][1].console.append_line)

        self.setup_tray()
        self.apply_icons()
        self.pages["zapret"][1].reload()
        zapret.state_changed.connect(lambda _: self.tray_rebuild())
        tg.state_changed.connect(lambda _: self.tray_rebuild())

    def toggle_sidebar(self):
        self.expanded = not self.expanded
        self.s["sidebar_expanded"] = self.expanded
        self.apply_sidebar()

    def apply_sidebar(self, animate=True):
        e = self.expanded
        for b in list(self.nav.values()) + [self.dc_btn]:
            b.setText(("   " + b.property("label")) if e else "")
            b.setStyleSheet("" if e else "text-align: center; padding-left: 0; padding-right: 0;")
        self.menu_btn.setText("   Свернуть" if e else "")
        self.menu_btn.setStyleSheet("" if e else "text-align: center; padding-left: 0; padding-right: 0;")
        self.menu_btn.setIcon(line_icon("collapse" if e else "menu", T["nav"]))
        self.logo_text.setVisible(e)
        target = Sidebar.EXPANDED if e else Sidebar.COLLAPSED
        if animate:
            self._side_anim.stop()
            self._side_anim.setStartValue(self.side.width())
            self._side_anim.setEndValue(target)
            self._side_anim.start()
        else:
            self.side.setFixedWidth(target)


    def apply_icons(self, update_shortcuts=False):
        self.icon = themed_icon()
        self.setWindowIcon(self.icon)
        QApplication.instance().setWindowIcon(self.icon)
        if hasattr(self, "tray"):
            self.tray.setIcon(self.icon)
        if update_shortcuts:
            try:
                path = core.DATA_DIR / f"icon_{self.s['theme']}.ico"
                app_icon_pixmap(256).save(str(path), "ICO")
                core.update_shortcut_icons(str(path))
            except Exception as e:
                log("app", f"Иконка ярлыков: {e}")

    def update_logo(self):
        self.logo.setText(f'Z <span style="color:{T["logo"]}">TYZ</span>')
        self.logo_icon.setPixmap(logo_pixmap(30))

    def apply_theme(self, key):
        set_theme(key)
        self.s["theme"] = key
        QApplication.instance().setStyleSheet(build_qss())
        self.update_logo()
        self.refresh_nav_icons()
        self.apply_sidebar(animate=False)
        self.apply_icons(update_shortcuts=True)
        for w in self.findChildren(QWidget):
            w.update()
        self.update()

    # --- навигация / helpers ---
    def go(self, key):
        self.nav[key].setChecked(True)
        self.stack.setCurrentWidget(self.pages[key][1])
        self.refresh_nav_icons()

    def refresh_nav_icons(self):
        for k, b in self.nav.items():
            b.setIcon(line_icon(k, T["a2"] if b.isChecked() and T["nav_style"] != "pill" else
                                ("#ffffff" if b.isChecked() else T["nav"])))

    def bg(self, fn, title):
        import threading

        def run():
            try:
                fn()
            except Exception as e:
                log("app", f"✖ {title}: {e}")
        threading.Thread(target=run, daemon=True).start()

    def open_path(self, p):
        try:
            os.startfile(str(p))  # type: ignore[attr-defined]
        except Exception as e:
            log("app", f"Не удалось открыть {p}: {e}")

    def open_tg_link(self):
        if not self.tg.running():
            self.tg.start()
        webbrowser.open(self.tg.link())

    def copy_tg_link(self):
        QGuiApplication.clipboard().setText(self.tg.link())
        log("app", "Ссылка на прокси скопирована в буфер обмена")
        self.notify("TG WS Proxy", "Ссылка скопирована")

    def notify(self, title, msg):
        if self.tray.isVisible():
            self.tray.showMessage(title, msg, self.icon, 3000)

    # --- трей ---
    def setup_tray(self):
        self.tray = QSystemTrayIcon(self.icon, self)
        self.tray.setToolTip(core.DISPLAY_NAME)
        self.tray.activated.connect(self.on_tray)
        self.tray_menu = QMenu()
        self.tray.setContextMenu(self.tray_menu)
        self.tray_rebuild()
        self.tray.show()

    def tray_rebuild(self):
        m = self.tray_menu
        m.clear()
        a = m.addAction(f"Открыть {core.DISPLAY_NAME}")
        a.triggered.connect(self.show_window)
        m.addSeparator()
        zon, ton = self.zapret.running(), self.tg.running()
        a = m.addAction(("✔ " if zon else "   ") + "Zapret")
        a.triggered.connect(lambda: (self.zapret.stop if self.zapret.running() else self.zapret.start)())
        sm = m.addMenu("   Стратегия")
        for st in self.zapret.strategies():
            act = sm.addAction(("● " if st == self.s["strategy"] else "   ") + st[:-4])
            act.triggered.connect(lambda _=False, n=st[:-4]: self.home.strategy.setCurrentText(n))
        a = m.addAction(("✔ " if ton else "   ") + "TG WS Proxy")
        a.triggered.connect(lambda: (self.tg.stop if self.tg.running() else self.tg.start)())
        a = m.addAction("   Тест подключения")
        a.triggered.connect(lambda: (self.show_window(), self.go("home"), self.home.run_quick()))
        a = m.addAction("   Копировать ссылку TG")
        a.triggered.connect(self.copy_tg_link)
        m.addSeparator()
        a = m.addAction(discord_icon(16), "Discord-сервер")
        a.triggered.connect(lambda: webbrowser.open(DISCORD_URL))
        a = m.addAction("Выход")
        a.triggered.connect(self.quit_app)
        self.tray.setToolTip(f"{core.DISPLAY_NAME}\nZapret: {'вкл' if zon else 'выкл'}\nTG Proxy: {'вкл' if ton else 'выкл'}")

    def on_tray(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            if self.isVisible() and not self.isMinimized():
                self.hide()
            else:
                self.show_window()

    def show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, e):
        if self._quitting or not self.s["close_to_tray"]:
            self.quit_app()
            e.accept()
            return
        e.ignore()
        self.hide()
        if not self.s.data.get("_tray_hint"):
            self.notify(core.DISPLAY_NAME, "Приложение продолжает работать в трее")
            self.s["_tray_hint"] = True

    def quit_app(self):
        self._quitting = True
        zon, ton = self.zapret.running(), self.tg.running()
        # Zapret — служба Windows, продолжает работать и после выхода из программы
        if self.tg.running():
            self.tg.stop(remember=False)
        self.s.data["zapret_was_on"], self.s.data["tg_was_on"] = zon, ton
        self.s.save()
        self.tray.hide()
        QApplication.quit()

    def showEvent(self, e):
        super().showEvent(e)
        dark_titlebar(self)


def dark_titlebar(w):
    if not core.IS_WIN:
        return
    try:
        import ctypes
        hwnd = int(w.winId())
        val = ctypes.c_int(1)
        for attr in (20, 19):
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(val), 4) == 0:
                break
        color = ctypes.c_int(0x0F0907)  # COLORREF 0x00BBGGRR -> #07090f
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(color), 4)
    except Exception:
        pass
