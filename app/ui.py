"""ZapreTYZ — интерфейс (PySide6). Стиль: чёрный + синий градиент."""
from __future__ import annotations

import os
import re
import time
import webbrowser

from PySide6.QtCore import (Qt, QPropertyAnimation, QEasingCurve, Property, QRectF, QSize,
                            Signal, QTimer, QPointF, QEvent)
from PySide6.QtGui import (QColor, QPainter, QLinearGradient, QBrush, QPen, QIcon,
                           QTextCursor, QGuiApplication, QPixmap, QRadialGradient)
from PySide6.QtWidgets import (QWidget, QMainWindow, QHBoxLayout, QVBoxLayout, QLabel,
                               QPushButton, QComboBox, QSizePolicy, QStackedWidget, QFrame, QPlainTextEdit,
                               QLineEdit, QSpinBox, QCheckBox, QButtonGroup, QRadioButton,
                               QSystemTrayIcon, QMenu, QMessageBox, QGridLayout,
                               QScrollArea, QApplication)

import core
from core import LOG, log

import zapret_tools as zt
from themes import T, THEMES, ALIASES, set_theme, build_qss, make_theme
import features as F
import ui2
import i18n
from i18n import tr

DISCORD_URL = "https://discord.gg/qHabsmgKVP"
GITHUB_URL = "https://github.com/Deraspik/YumeHaze-Zapret-ZapreTYZ/releases/latest"
GITHUB_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path fill="white" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>'
DISCORD_SVG = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 127.14 96.36"><path fill="white" d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,46,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,46,96.12,53,91.08,65.69,84.69,65.69Z"/></svg>'''

YT_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect x="0.5" y="4" width="23" height="16" rx="5" fill="#FF0033"/><path d="M9.5 8.3v7.4l6.4-3.7z" fill="white"/></svg>'
CF_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="#F38020" d="M16.6 17.5H4.2a3.2 3.2 0 0 1-.4-6.4 4.6 4.6 0 0 1 6.9-3.3A5.7 5.7 0 0 1 20.9 11a3.3 3.3 0 0 1-.2 6.5z"/><path fill="#FBAD41" d="M20.7 17.5h-3.2l.6-2.2c.3-1-.3-1.9-1.3-1.9l-.1-.4h.4a3 3 0 0 1 3.9 1.6 2.5 2.5 0 0 1-.3 2.9z"/></svg>'


NAV_ICONS = {
    "menu": '<path d="M4 7h16M4 12h16M4 17h10"/>',
    "collapse": '<path d="M15 6l-6 6 6 6"/>',
    "home": '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/>',
    "zapret": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
    "tg": '<path d="M21 4L3 11l6 2 2 6 3-4 5 4z"/><path d="M9 13l12-9"/>',
    "updates": '<path d="M20 12a8 8 0 1 1-2.3-5.7"/><path d="M20 4v5h-5"/>',
    "tests": '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3"/><path d="M7.5 15h9"/>',
    "console": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 9l3 3-3 3M12 15h5"/>',
    "look": '<rect x="3" y="3" width="15" height="6" rx="2"/><path d="M18 6h2.5v5.5H11V15"/><rect x="9" y="15" width="4" height="6" rx="1"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    "star": '<path d="M12 3.5l2.6 5.3 5.9.9-4.25 4.1 1 5.8L12 16.9l-5.25 2.7 1-5.8L3.5 9.7l5.9-.9z"/>',
}


def line_icon(key, color, size=18, fill="none") -> QIcon:
    from PySide6.QtSvg import QSvgRenderer
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{fill}" stroke="{color}" '
           f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{NAV_ICONS[key]}</svg>').encode()
    pm = QPixmap(size * 2, size * 2)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    QSvgRenderer(svg).render(p)
    p.end()
    pm.setDevicePixelRatio(2)
    return QIcon(pm)


def github_icon(size=18) -> QIcon:
    from PySide6.QtSvg import QSvgRenderer
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    QSvgRenderer(GITHUB_SVG.replace(b'white', T['text'].encode())).render(p)
    p.end()
    return QIcon(pm)


def discord_icon(size=20) -> QIcon:
    from PySide6.QtSvg import QSvgRenderer
    pm = QPixmap(size, int(size * 0.76) + 1)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    QSvgRenderer(DISCORD_SVG.replace(b'fill="white"', b'fill="' + T['text'].encode() + b'"')).render(p)
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


BRAND = {"Discord": "#8b5cf6", "YouTube": "#ff3333", "Google": "#4285F4", "Cloudflare": "#f6821f"}
GOOGLE_G_SVG = (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">'
                b'<path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>'
                b'<path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>'
                b'<path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>'
                b'<path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>')


def paint_brand(p: QPainter, g: str, rect: QRectF, alpha=255):
    """Значок сервиса: цветной кружок (Google — разноцветная «G»)."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    p.setOpacity(alpha / 255)
    from PySide6.QtSvg import QSvgRenderer
    svg = {"Google": GOOGLE_G_SVG, "Discord": DISCORD_SVG.replace(b'fill="white"', b'fill="#5865F2"'),
           "YouTube": YT_SVG, "Cloudflare": CF_SVG}.get(g)
    if svg:
        QSvgRenderer(svg).render(p, rect)
    else:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(BRAND.get(g, "#3ddc97")))
        p.drawEllipse(rect.adjusted(3, 3, -3, -3))
    p.restore()


class BrandDot(QWidget):
    def __init__(self, group):
        super().__init__()
        self.g = group
        self.setFixedSize(16, 16)
        self.on = None          # None — не проверялось, True/False — результат

    def set(self, on):
        self.on = on
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        paint_brand(p, self.g, QRectF(1, 1, 14, 14), 255 if self.on is not False else 90)


from PySide6.QtWidgets import QStyledItemDelegate, QStyle  # noqa: E402


class StrategyDelegate(QStyledItemDelegate):
    """Строка выбора стратегии: имя + цветные значки сервисов с результатами ok/всего."""
    def __init__(self, win, parent=None):
        super().__init__(parent)
        self.win = win

    def sizeHint(self, opt, idx):
        sz = super().sizeHint(opt, idx)
        sz.setHeight(max(sz.height(), 30))
        return sz

    def paint(self, p, opt, idx):
        p.save()
        r = opt.rect
        if opt.state & QStyle.State_Selected or opt.state & QStyle.State_MouseOver:
            c = QColor(T["a1"])
            c.setAlpha(70)
            p.fillRect(r, c)
        name = idx.data()
        res = self.win.s.data.get("strat_results", {}).get(name + ".bat", {})
        x = r.right() - 8
        f = p.font()
        f.setPointSizeF(max(7.5, f.pointSizeF() - 1))
        p.setFont(f)
        fm = p.fontMetrics()
        for g in reversed(list(zt.QUICK_GROUPS)):
            if g not in res:
                continue
            ok, tot = res[g]
            txt = f"{ok}/{tot}"
            w = fm.horizontalAdvance(txt)
            x -= w
            p.setPen(QColor("#3ddc97" if ok == tot else ("#ffd166" if ok else "#ff6b8a")))
            p.drawText(QRectF(x, r.top(), w, r.height()), Qt.AlignVCenter, txt)
            x -= 16
            paint_brand(p, g, QRectF(x, r.center().y() - 6, 12, 12), 255 if ok else 110)
            x -= 10
        if name + ".bat" == getattr(self.win, "best", None):
            bt = tr("ЛУЧШАЯ")
            bw = fm.horizontalAdvance(bt) + 12
            x -= bw + 4
            br = QRectF(x, r.center().y() - 8, bw, 16)
            p.setPen(Qt.NoPen)
            bc = QColor(T["a2"]); bc.setAlpha(60)
            p.setBrush(bc)
            p.drawRoundedRect(br, 5, 5)
            p.setPen(QColor(T["a2"]))
            p.drawText(br, Qt.AlignCenter, bt)
        p.setFont(opt.font)
        p.setPen(QColor(T["text"]))
        star = "★ " if name + ".bat" in self.win.s.data.get("fav", []) else ""
        p.drawText(QRectF(r.left() + 10, r.top(), x - r.left() - 10, r.height()), Qt.AlignVCenter,
                   p.fontMetrics().elidedText(star + name, Qt.ElideRight, int(x - r.left() - 10)))
        p.restore()


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


class RGrid(QWidget):
    """Адаптивная сетка: число колонок зависит от ширины, скрытые элементы пропускаются."""
    def __init__(self, cols=2, min_col=380, spacing=16):
        super().__init__()
        self.cols, self.min_col, self.items = cols, min_col, []
        self.g = QGridLayout(self)
        self.g.setContentsMargins(0, 0, 0, 0)
        self.g.setSpacing(spacing)
        self._n = None

    def addWidget(self, w, *a):
        self.items.append(w)
        w.setParent(self)
        w.installEventFilter(self)
        self.relayout(force=True)

    def eventFilter(self, o, e):
        if e.type() in (QEvent.Show, QEvent.Hide, QEvent.ShowToParent, QEvent.HideToParent):
            self.relayout(force=True)
        return False

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.relayout()

    def relayout(self, force=False):
        vis = [w for w in self.items if not (w.isHidden() and w.testAttribute(Qt.WA_WState_ExplicitShowHide))]
        sp = self.g.spacing()
        n = max(1, min(self.cols, (self.width() + sp) // (self.min_col + sp))) if self.width() > 50 else self.cols
        if n == 3 and len(vis) == 4:
            n = 2
        if not force and n == self._n:
            return
        self._n = n
        for w in self.items:
            self.g.removeWidget(w)
        for c in range(self.cols):
            self.g.setColumnStretch(c, 1 if c < n else 0)
        for i, w in enumerate(vis):
            self.g.addWidget(w, i // n, i % n)

    def minimumSizeHint(self):
        return QSize(120, super().minimumSizeHint().height())


class FlowRow(QWidget):
    """Шапка карточки: заголовок слева, кнопки справа; при нехватке места кнопки уходят вниз."""
    def __init__(self, left: list, right: list, brk=720):
        super().__init__()
        self.brk = brk
        self.v = QVBoxLayout(self)
        self.v.setContentsMargins(0, 0, 0, 0)
        self.v.setSpacing(10)
        self.l1 = QHBoxLayout()
        self.l2 = QHBoxLayout()
        self.lw = QWidget(); self.lw.setLayout(self.l1)
        self.rw = QWidget(); self.rw.setLayout(self.l2)
        self.l1.setContentsMargins(0, 0, 0, 0); self.l2.setContentsMargins(0, 0, 0, 0)
        for w in left:
            self.l1.addWidget(w)
        self.l1.addStretch()
        for w in right:
            self.l2.addWidget(w)
        self.h = QHBoxLayout()
        self.h.setContentsMargins(0, 0, 0, 0)
        self.v.addLayout(self.h)
        self._wide = None
        self.apply(True)

    def apply(self, wide):
        if wide == self._wide:
            return
        self._wide = wide
        for w in (self.lw, self.rw):
            self.h.removeWidget(w); self.v.removeWidget(w)
        if wide:
            self.h.addWidget(self.lw, 1); self.h.addWidget(self.rw)
        else:
            self.v.addWidget(self.lw); self.v.addWidget(self.rw)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.apply(self.width() >= self.brk)

    def minimumSizeHint(self):
        return QSize(120, super().minimumSizeHint().height())


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
        text = tr(text)
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
        inner = QWidget()
        lay = QVBoxLayout(inner)
        self._lay = lay
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll_page(inner))
        lay.setContentsMargins(34, 28, 34, 28)
        lay.setSpacing(16)
        lay.addWidget(page_header("Главная", "Быстрое управление обходом блокировок"))

        row = RGrid(2, 380)
        self._grid = row

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
        self.strategy.setItemDelegate(StrategyDelegate(win, self.strategy))
        self.strategy.view().setMinimumWidth(460)
        self.strategy.setToolTip("Цифры рядом со стратегией — результаты прошлых проверок\n"
                                 "(быстрый тест на главной и подбор во вкладке «Тесты»)")
        srow = QHBoxLayout()
        srow.addWidget(self.strategy, 1)
        self.fav_btn = QPushButton()
        self.fav_btn.setIconSize(QSize(18, 18))
        self.fav_btn.setFixedWidth(40)
        self.fav_btn.setToolTip("Избранная стратегия: всегда сверху списка и в трее")
        self.fav_btn.clicked.connect(self.toggle_fav)
        srow.addWidget(self.fav_btn)
        self.best_btn = QPushButton("Поставить лучшую")
        self.best_btn.setToolTip("Стратегия с лучшими результатами проверок")
        self.best_btn.clicked.connect(self.set_best)
        self.best_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.strategy.setMinimumWidth(120)
        srow.addWidget(self.best_btn)
        zc.lay.addLayout(srow)
        self.zcard = zc
        row.addWidget(zc)

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
        self.tcard = tc
        row.addWidget(tc)
        lay.addWidget(row)

        # --- тест подключения ---
        qc = Card()
        qt = QLabel("Тест подключения")
        qt.setObjectName("CardTitle")
        self.q_summary = QLabel("")
        self.q_summary.setObjectName("Hint")
        self.q_btn = QPushButton("Проверить")
        self.q_btn.setObjectName("Primary")
        self.q_btn.clicked.connect(self.run_quick)
        rd = QPushButton("Перезапустить Discord")
        rd.setToolTip("Закрывает Discord, чистит кэш и запускает заново — помогает, когда Discord завис на подключении")
        rd.clicked.connect(lambda: self.win.fix_discord())
        more = QPushButton("Подбор стратегии →")
        more.clicked.connect(lambda: self.win.go("tests"))
        qc.lay.addWidget(FlowRow([qt, self.q_summary], [self.q_btn, rd, more], 760))
        chips = RGrid(4, 190, 10)
        self.q_chips = {}
        for g in zt.QUICK_GROUPS:
            w = QFrame()
            w.setObjectName("Chip")
            wl = QHBoxLayout(w)
            wl.setContentsMargins(12, 8, 12, 8)
            dot = BrandDot(g)
            wl.addWidget(dot)
            lb = QLabel(f"<b style='color:{BRAND[g]}'>{g}</b><br><span style='color:#7c84a0'>—</span>")
            wl.addWidget(lb, 1)
            chips.addWidget(w)
            self.q_chips[g] = (dot, lb)
        qc.lay.addWidget(chips)
        lay.addWidget(qc)
        self.qcard = qc

        # --- игровой режим и авто-восстановление ---
        gr = RGrid(2, 380)
        gc = Card("🎮 Игровой режим", "Пока запущена игра, программа замирает: никаких фоновых проверок, "
                                    "анимаций и уведомлений")
        self.game_lab = muted("Сейчас: игра не запущена")
        gc.lay.addWidget(ui2.setting_row("Автоматически", "", ui2.toggle(win, "game_mode", True)))
        gc.lay.addWidget(self.game_lab)
        gr.addWidget(gc)
        ac = Card("🛡 Авто-восстановление", "Раз в 10 минут проверяет Discord и YouTube. Если сервис отвалился, "
                                          "переключает на следующую лучшую стратегию")
        self.heal_lab = muted("Ещё не проверялось")
        ac.lay.addWidget(ui2.setting_row("Включено", "", ui2.toggle(win, "auto_heal", True)))
        ac.lay.addWidget(self.heal_lab)
        self.heal_card = ac
        gr.addWidget(ac)
        lay.addWidget(gr)
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
        self.console.setMinimumHeight(170)
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
        self._groups = {}
        for dot, lb in self.q_chips.values():
            dot.set(None)
            lb.setText(lb.text().split("<br>")[0] + "<br><span style='color:#7c84a0'>проверка…</span>")
        self.checker.start()

    def on_group(self, g, ok, total, ms):
        self._groups[g] = [ok, total]
        dot, lb = self.q_chips[g]
        dot.set(ok > 0)
        col = "#3ddc97" if ok == total else ("#ffd166" if ok else "#ff6b8a")
        txt = f"{ok}/{total}" + (f" · {int(ms)} мс" if ok else " · недоступен")
        lb.setText(f"<b style='color:{BRAND[g]}'>{g}</b><br><span style='color:{col}'>{tr(txt)}</span>")
        if self.win.zapret.running():
            zt.save_group_results(self.win.s, self.win.s["strategy"], {g: [ok, total]})
            self.strategy.update()
        log("app", f"Тест подключения — {g}: {txt}")

    def toggle_fav(self):
        st = self.win.s["strategy"]
        fav = self.win.s.data.setdefault("fav", [])
        if st in fav:
            fav.remove(st)
        else:
            fav.append(st)
        self.win.s.save()
        self.reload_strategies()
        self.win.tray_rebuild()

    def set_best(self):
        b = F.best_strategy(self.win.s, self.win.zapret.strategies())
        if not b:
            self.win.toast("Сначала запусти тест подключения или подбор стратегии")
            return
        self.strategy.setCurrentText(b[:-4])
        self.win.toast(f"Стратегия: {b[:-4]}")

    def update_fav_btn(self):
        on = self.win.s["strategy"] in self.win.s.data.get("fav", [])
        ac = T["a1"]
        self.fav_btn.setIcon(line_icon("star", ac if on else "#8a90a8", 18, ac if on else "none"))

    def on_quick_done(self, ok, total):
        self.win.best = F.best_strategy(self.win.s, self.win.zapret.strategies())
        self.win.quick_last = dict(self._groups)
        self.win.quick_time = time.time()
        if self.win.zapret.running():
            F.add_history(self.win.s, "Быстрый", self.win.s["strategy"], dict(self._groups))
            self.win.pages["tests"][1].fill_history()
        self.win.tray_rebuild()
        self.q_btn.setEnabled(True)
        self.q_btn.setText("Проверить")
        z = "Zapret вкл" if self.win.zapret.running() else "Zapret выкл"
        self.q_summary.setText(tr(f"   {ok}/{total} доступно · {z} · {self.win.s['strategy'][:-4]}"))
        if ok < total:
            self.win.notify("Тест подключения", f"Доступно {ok} из {total}. Попробуйте подбор стратегии во вкладке «Тесты».")

    def reload_strategies(self):
        cur = self.win.s["strategy"]
        self.strategy.blockSignals(True)
        self.strategy.clear()
        fav = self.win.s.data.get("fav", [])
        items = self.win.zapret.strategies()
        items = [i for i in items if i in fav] + [i for i in items if i not in fav]
        self.strategy.addItems([i[:-4] for i in items])
        if cur in items:
            self.strategy.setCurrentIndex(items.index(cur))
        elif items:
            self.win.s["strategy"] = items[0]
        self.strategy.blockSignals(False)
        self.update_fav_btn()

    def on_strategy(self, name):
        if not name:
            return
        self.win.s["strategy"] = name + ".bat"
        self.update_fav_btn()
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
        self.z_status.setText(tr("Работает" if on else "Выключен"))
        self.z_status.setObjectName("StatusOn" if on else "StatusOff")
        self.z_status.setStyleSheet("")

    def set_t(self, on):
        self.t_toggle.setChecked(on)
        self.t_dot.set(on)
        self.t_status.setText(tr("Работает" if on else "Выключен"))
        self.t_status.setObjectName("StatusOn" if on else "StatusOff")
        self.t_status.setStyleSheet("")

    def refresh_addr(self):
        c = self.win.s["tg"]
        self.t_addr.setText(tr(f"Адрес: {c['host']}:{c['port']}"))


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
        self.skip_valve = QCheckBox("Не пропускать через Zapret CS2 / Dota 2 / Steam (порты 27000–27200) — меньше пинг и фризы")
        self.skip_valve.setChecked(bool(win.s.data.get("skip_valve", True)))
        gc.lay.addWidget(self.skip_valve)
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
        ui2.zapret_extras(win, lay)
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
        self.win.s["skip_valve"] = self.skip_valve.isChecked()
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
        b = QPushButton("Импорт своей стратегии (.bat)")
        b.clicked.connect(self.import_strategy)
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
        ui2.tests_extras(win, self, lay)
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

    def import_strategy(self):
        from PySide6.QtWidgets import QFileDialog
        f, _ = QFileDialog.getOpenFileName(self, tr("Импорт стратегии"), "", "Batch (*.bat)")
        if not f:
            return
        try:
            name = F.import_strategy(f)
            self.win.after_component_change("zapret")
            self.win.toast(f"Стратегия добавлена: {name[:-4]}")
        except Exception as e:
            QMessageBox.warning(self, "Импорт", str(e))

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
            log("zapret", "   " + d)
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
        F.add_history(self.win.s, "Подбор", self.best, extra=f"{results[0][1]}/{results[0][2]}")
        self.fill_history()
        self.win.best = F.best_strategy(self.win.s, self.win.zapret.strategies())
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
            vr = QHBoxLayout()
            vl = QLabel("Версия:")
            vcb = QComboBox()
            vcb.addItem("Последняя", None)
            vcb.setMinimumWidth(200)
            vcb.setToolTip("Можно поставить любую версию с GitHub, в том числе более старую")
            vr.addWidget(vl)
            vr.addWidget(vcb)
            vr.addStretch()
            c.lay.addLayout(vr)
            br = QHBoxLayout()
            chk = QPushButton("Проверить")
            chk.clicked.connect(lambda _=False, k=comp: self.check(k))
            ins = QPushButton("Установить")
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
            self.rows[comp] = dict(local=local, remote=remote, status=status, chk=chk, ins=ins, vcb=vcb)
        ac = Card(f"{core.DISPLAY_NAME} v{core.APP_VERSION}", "Новые версии самой программы выходят на нашем GitHub.")
        ab = QPushButton("Открыть GitHub")
        ab.setObjectName("Primary")
        ab.setIcon(github_icon(16))
        ab.clicked.connect(lambda: webbrowser.open(GITHUB_URL))
        ac.lay.addWidget(ab, 0, Qt.AlignLeft)
        lay.addWidget(ac)
        allb = QPushButton("Проверить всё")
        allb.clicked.connect(lambda: [self.check(k) for k in self.rows])
        lay.addWidget(allb, 0, Qt.AlignLeft)
        lay.addStretch()
        up.checked.connect(self.on_checked)
        up.progress.connect(self.on_progress)
        up.finished.connect(self.on_finished)
        up.versions.connect(self.on_versions)
        self.refresh_local()
        self._vloaded = False

    def refresh_local(self):
        self.rows["zapret"]["local"].setText(f"Установлена: <b>{self.win.zapret.version()}</b>")
        self.rows["tg"]["local"].setText(f"Установлена: <b>{self.win.tg.version()}</b>")

    def showEvent(self, e):
        super().showEvent(e)
        if not self._vloaded:
            self._vloaded = True
            for k in self.rows:
                self.win.updater.list_versions(k)

    def on_versions(self, k, tags):
        cb = self.rows[k]["vcb"]
        cur = cb.currentData()
        cb.clear()
        cb.addItem("Последняя", None)
        for t in tags:
            cb.addItem(t, t)
        i = cb.findData(cur)
        cb.setCurrentIndex(max(0, i))

    def check(self, k):
        self.rows[k]["status"].setText("Проверка…")
        self.win.updater.check(k)
        self.win.updater.list_versions(k)

    def install(self, k):
        r = self.rows[k]
        r["ins"].setEnabled(False)
        r["chk"].setEnabled(False)
        r["status"].setText("Установка…")
        self.win.updater.install(k, r["vcb"].currentData())

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
        self.s = None
        self.bg = None
        self._bg_path = None

    def load_bg(self):
        path = (self.s.data.get("bg_image") if self.s else "") or ""
        if path != self._bg_path:
            self._bg_path = path
            pm = QPixmap(path) if path else QPixmap()
            self.bg = pm if not pm.isNull() else None

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        self.load_bg()
        if self.bg is not None:
            sc = self.bg.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            p.drawPixmap((w - sc.width()) // 2, (h - sc.height()) // 2, sc)
            c = QColor(T["bg"])
            c.setAlpha(int(255 * self.s.data.get("bg_dim", 70) / 100))
            p.fillRect(self.rect(), c)
            return
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
        self.setMinimumSize(640, 520)

        root = GradientRoot()
        root.s = settings
        self.root = root
        self.best = None
        self.quick_last = {}
        self.quick_time = 0
        self.game = None
        self.rpc = None
        self.widget = None
        self.app_update = None
        self._no_save = False
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
            "updates": ("Обновления", ui2.UpdatesPage(self)),
            "console": ("Консоль", ConsolePage(self)),
            "look": ("Оформление", ui2.LookPage(self)),
            "settings": ("Настройки", ui2.SettingsPage(self)),
        }
        self.nav = {}
        grp = QButtonGroup(self)
        for key, (label, page) in self.pages.items():
            if key == "look":
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
        self.gh_btn = QPushButton()
        self.gh_btn.setObjectName("Nav")
        self.gh_btn.setProperty("label", "Наш GitHub")
        self.gh_btn.setIcon(github_icon(18))
        self.gh_btn.setIconSize(QSize(18, 18))
        self.gh_btn.setCursor(Qt.PointingHandCursor)
        self.gh_btn.setToolTip("GitHub — новые версии программы")
        self.gh_btn.clicked.connect(lambda: webbrowser.open(GITHUB_URL))
        sl.addWidget(self.gh_btn)
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
        LOG.line.connect(self.pages["tests"][1].console.append_line)
        self.toaster = ui2.Toast(self.stack)

        self.setup_tray()
        self.apply_icons()
        self.pages["zapret"][1].reload()
        zapret.state_changed.connect(lambda _: self.tray_rebuild())
        tg.state_changed.connect(lambda _: self.tray_rebuild())
        self._init_v2()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if not hasattr(self, "expanded"):
            return
        want = self.s.data.get("sidebar_expanded", True) and self.width() >= 940
        if want != self.expanded:
            self.expanded = want
            try:
                self.apply_sidebar()
            except Exception:
                pass

    def toggle_sidebar(self):
        self.expanded = not self.expanded
        self.s["sidebar_expanded"] = self.expanded
        self.apply_sidebar()

    def apply_sidebar(self, animate=True):
        e = self.expanded
        for b in list(self.nav.values()) + [self.dc_btn, self.gh_btn]:
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

    def apply_theme(self, key=None):
        if key:
            self.s["theme"] = key
        s = self.s.data
        T.clear()
        T.update(make_theme(F.resolve_base(s.get("theme_base", "dark")), s.get("theme", "blue"),
                            s.get("custom_colors"), s.get("glow", 50) / 100, s.get("radius", 10)))
        QApplication.instance().setStyleSheet(build_qss())
        self.toaster.hide()
        self.dc_btn.setIcon(discord_icon(20))
        self.gh_btn.setIcon(github_icon(18))
        dark_titlebar(self)
        self.update_logo()
        self.refresh_nav_icons()
        self.apply_sidebar(animate=False)
        sig = (T["a1"], T["a2"])
        self.apply_icons(update_shortcuts=getattr(self, "_icon_sig", None) not in (None, sig))
        self._icon_sig = sig
        for w in self.findChildren(QWidget):
            QWidget.update(w)
        self.update()

    # --- навигация / helpers ---
    def go(self, key):
        if not self.nav[key].isVisible() and key != "home" and hasattr(self, "toaster"):
            key = "updates"
        self.nav[key].setChecked(True)
        w = self.pages[key][1]
        self.stack.setCurrentWidget(w)
        self.refresh_nav_icons()
        if not self.game and self.isVisible():
            from PySide6.QtWidgets import QGraphicsOpacityEffect
            eff = QGraphicsOpacityEffect(w)
            w.setGraphicsEffect(eff)
            a = QPropertyAnimation(eff, b"opacity", w)
            a.setDuration(170)
            a.setStartValue(0.0)
            a.setEndValue(1.0)
            a.setEasingCurve(QEasingCurve.OutCubic)
            a.finished.connect(lambda: w.setGraphicsEffect(None))
            a.start()
        self.retranslate()

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
        if self.game or not self.s.data.get("notifications", True):
            return
        if self.tray.isVisible():
            self.tray.showMessage(tr(title), tr(msg), self.icon, 3000)

    # --- трей ---
    def setup_tray(self):
        self.tray = QSystemTrayIcon(self.icon, self)
        self.tray.setToolTip(core.DISPLAY_NAME)
        self.tray.activated.connect(self.on_tray)
        self.tray_menu = QMenu()
        self.tray_rebuild()
        self.tray.show()

    def tray_rebuild(self):
        m = self.tray_menu
        m.clear()
        zi, ti = self.zapret.installed(), self.tg.installed()
        zon, ton = zi and self.zapret.running(), ti and self.tg.running()
        a = m.addAction("Открыть окно")
        a.triggered.connect(self.show_window)
        m.addSeparator()
        if zi:
            a = m.addAction(("✔ " if zon else "   ") + "Zapret")
            a.triggered.connect(lambda: (self.zapret.stop if self.zapret.running() else self.zapret.start)())
            sm = m.addMenu("   Стратегия")
            fav = self.s.data.get("fav", [])
            sts = self.zapret.strategies()
            for st in [x for x in sts if x in fav] + [x for x in sts if x not in fav]:
                mark = "● " if st == self.s["strategy"] else ("★ " if st in fav else "   ")
                act = sm.addAction(mark + st[:-4] + ("   🏆" if st == self.best else ""))
                act.setProperty("_ru", act.text())
                act.triggered.connect(lambda _=False, n=st[:-4]: self.home.strategy.setCurrentText(n))
        if ti:
            a = m.addAction(("✔ " if ton else "   ") + "TG WS Proxy")
            a.triggered.connect(lambda: (self.tg.stop if self.tg.running() else self.tg.start)())
        if zi:
            m.addSeparator()
            ago = ""
            if self.quick_time:
                mins = int((time.time() - self.quick_time) / 60)
                ago = "   (только что)" if mins < 1 else f"   ({mins} мин назад)"
            a = m.addAction("⚡ Тест подключения" + ago)
            a.triggered.connect(self.tray_test)
            for g, (ok, tot) in self.quick_last.items():
                a = m.addAction(f"      {'✔' if ok == tot else ('◐' if ok else '✖')}  {g}  {ok}/{tot}")
                a.setEnabled(False)
            a = m.addAction("   Починить Discord")
            a.triggered.connect(self.fix_discord)
            a = m.addAction(("✔ " if self.s.data.get("game_mode", True) else "   ") + "Игровой режим (авто)")
            a.triggered.connect(lambda: self.s.__setitem__("game_mode", not self.s.data.get("game_mode", True)) or self.tray_rebuild())
        a = m.addAction(("✔ " if self.s.data.get("widget") else "   ") + "Мини-виджет")
        a.triggered.connect(lambda: (self.s.__setitem__("widget", not self.s.data.get("widget")), self.set_widget(self.s["widget"])))
        if ti:
            a = m.addAction("   Копировать ссылку TG")
            a.triggered.connect(self.copy_tg_link)
        m.addSeparator()
        a = m.addAction(discord_icon(16), "Discord-сервер")
        a.triggered.connect(lambda: webbrowser.open(DISCORD_URL))
        a = m.addAction(github_icon(16), "GitHub")
        a.triggered.connect(lambda: webbrowser.open(GITHUB_URL))
        a = m.addAction("Выход")
        a.triggered.connect(self.quit_app)
        i18n.translate_menu(m)
        tip = [core.DISPLAY_NAME]
        if zi:
            tip.append(f"Zapret: {'вкл · ' + self.s['strategy'][:-4] if zon else 'выкл'}")
        if ti:
            tip.append(f"TG Proxy: {'вкл' if ton else 'выкл'}")
        self.tray.setToolTip(tr("\n".join(tip)))
        if self.widget:
            self.widget.update()

    def tray_test(self):
        self.home.run_quick()
        self.notify("Тест подключения", "Проверка запущена, результат появится в меню трея")

    def on_tray(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.Context):
            self.show_tray_popup()
        elif reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def show_tray_popup(self):
        from PySide6.QtGui import QCursor
        if getattr(self, "_popup", None):
            try:
                self._popup.close_all()
            except RuntimeError:
                pass
        self._popup = ui2.build_tray_popup(self)
        self._popup.popup_at(QCursor.pos())

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
            self.notify(core.DISPLAY_NAME, "Приложение работает в трее")
            self.s["_tray_hint"] = True

    def quit_app(self):
        self._quitting = True
        zon, ton = self.zapret.running(), self.tg.running()
        # Zapret — служба Windows, продолжает работать и после выхода из программы
        if self.tg.running():
            self.tg.stop(remember=False)
        if self.rpc:
            self.rpc.close()
        if self.widget:
            self.widget.close()
        if not self._no_save:
            self.s.data["zapret_was_on"], self.s.data["tg_was_on"] = zon, ton
            self.s.save()
        self.tray.hide()
        QApplication.quit()

    def showEvent(self, e):
        super().showEvent(e)
        dark_titlebar(self)
        self.retranslate()

    # ───────── 2.0 ─────────
    def _init_v2(self):
        z, t = self.zapret, self.tg
        self.best = F.best_strategy(self.s, z.strategies()) if z.installed() else None
        z.state_changed.connect(lambda _: self.update_rpc(self.s.data.get("discord_rpc", False)))
        self._rt = QTimer(self)
        self._rt.setSingleShot(True)
        self._rt.timeout.connect(self._do_translate)
        LOG.line.connect(lambda *_: self.retranslate())
        z.state_changed.connect(lambda _: self.retranslate())
        t.state_changed.connect(lambda _: self.retranslate())
        # игровой режим: раз в 5 с список процессов через WinAPI (дёшево)
        self._gt = QTimer(self)
        self._gt.timeout.connect(self.check_game)
        self._gt.start(5000)
        # авто-восстановление
        self._ht = QTimer(self)
        self._ht.timeout.connect(self.auto_heal)
        self._ht.start(10 * 60 * 1000)
        # тема по времени / Windows
        self._tt = QTimer(self)
        self._tt.timeout.connect(self._theme_tick)
        self._tt.start(5 * 60 * 1000)
        self._base_now = F.resolve_base(self.s.data.get("theme_base", "dark"))
        # автообновление программы и списка рекламы
        self._ut = QTimer(self)
        self._ut.timeout.connect(self.daily)
        self._ut.start(24 * 3600 * 1000)
        QTimer.singleShot(8000, self.daily)
        i18n.LANG["cur"] = self.s.data.get("lang", "ru")
        self.apply_theme()
        self.apply_components()
        if self.s.data.get("widget"):
            self.set_widget(True)
        # статус Discord: подключается сам, даже если Discord запустили позже программы
        self._rpc_t = QTimer(self)
        self._rpc_t.timeout.connect(lambda: self.s.data.get("discord_rpc") and not self.rpc and not self.game
                                    and self.update_rpc(True))
        self._rpc_t.start(30000)
        z.state_changed.connect(lambda _: None)
        self.home.strategy.currentTextChanged.connect(lambda _: self.update_rpc(self.s.data.get("discord_rpc", False)))
        if self.s.data.get("discord_rpc"):
            QTimer.singleShot(3000, lambda: self.update_rpc(True))
        if not self.s.data.get("wizard_done"):
            QTimer.singleShot(700, lambda: (self.show_window(), ui2.Wizard(self).exec()))

    def _theme_tick(self):
        b = F.resolve_base(self.s.data.get("theme_base", "dark"))
        if b != self._base_now:
            self._base_now = b
            self.apply_theme()

    def daily(self):
        if self.game:
            return
        if self.s.data.get("app_autoupdate_check", True):
            self.check_app_update()
        ad = self.s.data.get("adblock", "off")
        if ad != "off" and time.time() - self.s.data.get("adblock_time", 0) > 7 * 86400:
            F.bg(lambda: (F.set_adblock(ad), self.s.__setitem__("adblock_time", time.time())))

    # --- язык ---
    def set_lang(self, code):
        self.s["lang"] = code
        i18n.LANG["cur"] = code
        self._do_translate()
        self.toast("Язык: русский" if code == "ru" else "Language: English")

    def retranslate(self):
        if hasattr(self, "_rt"):
            self._rt.start(120)

    def translate(self, w):
        i18n.translate(w)

    def _do_translate(self):
        i18n.translate(self)
        self.tray_rebuild()
        if self.widget:
            self.widget.update()
        for k, (label, _) in self.pages.items():
            b = self.nav[k]
            b.setProperty("label", tr(label))
            b.setToolTip(tr(label))
        self.dc_btn.setProperty("label", tr("Наш Discord"))
        self.gh_btn.setProperty("label", tr("Наш GitHub"))
        self.apply_sidebar(animate=False)

    def toast(self, text):
        self.toaster.show_text(text)

    # --- компоненты ---
    def apply_components(self):
        zi, ti = self.zapret.installed(), self.tg.installed()
        for k in ("zapret", "tests"):
            self.nav[k].setVisible(zi)
        self.nav["tg"].setVisible(ti)
        self.home.zcard.setVisible(zi)
        self.home.qcard.setVisible(zi)
        self.home.heal_card.parentWidget() and self.home.heal_card.setVisible(zi)
        self.home.tcard.setVisible(ti)
        if not hasattr(self, "_nocomp"):
            from PySide6.QtWidgets import QPushButton as _B
            c = Card("Компоненты не установлены", "Установите Zapret и/или TG WS Proxy во вкладке «Обновления»")
            b = _B("Перейти к компонентам")
            b.setObjectName("Primary")
            b.clicked.connect(lambda: self.go("updates"))
            c.lay.addWidget(b, 0, Qt.AlignLeft)
            self.home._lay.insertWidget(1, c)
            self._nocomp = c
        self._nocomp.setVisible(not zi and not ti)
        cur = self.stack.currentWidget()
        for k, (_, w) in self.pages.items():
            if w is cur and not self.nav[k].isVisible():
                self.go("home")
        self.tray_rebuild()
        self.retranslate()

    def after_component_change(self, k):
        self.pages["updates"][1].refresh_local()
        if k == "zapret":
            self.home.reload_strategies()
            if self.zapret.installed():
                self.pages["zapret"][1].reload()
                self.sites.render()
                self.excl.render()
            self.pages["tests"][1].reload()
        self.home.refresh_addr()
        self.apply_components()

    # --- мини-виджет / Discord ---
    def set_widget(self, on):
        if on and not self.widget:
            self.widget = ui2.MiniWidget(self)
            self.widget.show()
        elif not on and self.widget:
            self.widget.close()
            self.widget = None
        self.tray_rebuild()

    def update_rpc(self, on):
        app_id = self.s.data.get("discord_app_id", "").strip() or F.DiscordRPC.CLIENT_ID
        if not on:
            if self.rpc:
                self.rpc.close()
                self.rpc = None
            return

        def work():
            if not self.rpc:
                r = F.DiscordRPC()
                if not r.connect(app_id):
                    return
                self.rpc = r
            st = f"Стратегия: {self.s['strategy'][:-4]}" if self.zapret.running() else "Zapret выключен"
            if not self.rpc.update("Discord и YouTube без VPN", st):
                self.rpc = None
        F.bg(work)

    def fix_discord(self):
        log("app", "Починить Discord: закрываю Discord и чищу кэш…")
        F.bg(lambda: [log("app", "✔ " + m) for m in F.fix_discord()])
        self.toast("Discord перезапускается")

    # --- игровой режим ---
    def check_game(self):
        if not self.s.data.get("game_mode", True):
            if self.game:
                self.game = None
            return
        g = F.running_game()
        if g == self.game:
            return
        self.game = g
        if g:
            log("app", f"🎮 Игровой режим: обнаружен {g}, фоновые проверки на паузе")
            self._gt.setInterval(15000)
            self.home.game_lab.setText(f"● {g}: программа на паузе")
        else:
            log("app", "🎮 Игра закрыта, всё работает как обычно")
            self._gt.setInterval(5000)
            self.home.game_lab.setText("Сейчас: игра не запущена")
        self.retranslate()

    # --- авто-восстановление ---
    def auto_heal(self):
        if self.game or not self.s.data.get("auto_heal", True) or not self.zapret.installed() \
                or not self.zapret.running():
            return

        def work():
            res = {}
            for g in ("Discord", "YouTube"):
                ok = sum(zt.probe(u, 6)[0] for u in zt.QUICK_GROUPS[g])
                res[g] = (ok, len(zt.QUICK_GROUPS[g]))
            bad = [g for g, (ok, _) in res.items() if ok == 0]
            stamp = time.strftime("%H:%M")
            if not bad:
                F.ui(lambda: self.home.heal_lab.setText(f"Последняя проверка: {stamp} ✔"))
                return
            if not zt.probe("https://ya.ru", 6)[0]:
                F.ui(lambda: self.home.heal_lab.setText(f"{stamp}: нет интернета, ничего не трогаю"))
                return
            log("app", f"🛡 {', '.join(bad)} недоступен — переключаю стратегию")
            cur = self.s["strategy"]
            order = [x for x in F.ranked_strategies(self.s, self.zapret.strategies()) if x != cur]
            if order:
                nxt = order[0]

                def apply():
                    self.home.strategy.setCurrentText(nxt[:-4])
                    self.home.heal_lab.setText(f"{stamp}: переключил на {nxt[:-4]}")
                    self.notify("Авто-восстановление", f"Переключил стратегию на {nxt[:-4]}")
                    self.retranslate()
                F.ui(apply)
        F.bg(work)

    # --- автообновление программы ---
    def check_app_update(self, manual=False):
        up = self.pages["updates"][1]

        def work():
            try:
                ver, url = F.check_app_update()
            except Exception as e:
                F.ui(lambda: manual and up.app_info.setText(f"Ошибка проверки: {type(e).__name__}"))
                return

            def done():
                self.app_update = (ver, url) if ver and url else None
                if self.app_update:
                    up.app_info.setText(f"Установлена {core.APP_VERSION} · На GitHub вышла {ver}")
                    up.app_upd.show()
                    if self.s.data.get("app_autoupdate_install") and not manual:
                        self.install_app_update()
                    else:
                        self.notify("Доступно обновление", f"{core.DISPLAY_NAME} {ver}")
                else:
                    up.app_info.setText(f"Установлена {core.APP_VERSION} · последняя версия ✔")
                self.retranslate()
            F.ui(done)
        F.bg(work)

    def install_app_update(self):
        if not self.app_update:
            return
        up = self.pages["updates"][1]
        up.app_info.setText("Скачивание…")
        up.app_upd.setEnabled(False)

        def work():
            try:
                F.download_and_run_update(self.app_update[1])
                F.ui(self.quit_app)
            except Exception as e:
                F.ui(lambda: (up.app_info.setText(f"✖ {e}"), up.app_upd.setEnabled(True)))
        F.bg(work)


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
