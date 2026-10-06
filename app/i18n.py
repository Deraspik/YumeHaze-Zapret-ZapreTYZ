"""Перевод интерфейса RU → EN. Переводятся все видимые надписи, подсказки, пункты списков,
меню трея, уведомления и строки журнала. Оригиналы запоминаются, поэтому обратно на русский — без потерь."""
from __future__ import annotations

import re

from PySide6.QtWidgets import (QLabel, QAbstractButton, QLineEdit, QComboBox, QWidget, QPlainTextEdit,
                               QTableWidget, QGroupBox, QMenu)

from i18n_dict import EN, RX

LANG = {"cur": "ru"}
_CYR = re.compile(r"[А-Яа-яЁё]")
_PRE = re.compile(r"^([^A-Za-zА-Яа-яЁё0-9«(]*)([\s\S]*?)([\s.…→✔✓!:?]*)$")
_RX = [(re.compile(a), b) for a, b in RX]


def _rx(c):
    o = c
    for r, b in _RX:
        o = r.sub(b, o)
    return None if _CYR.search(o) else o


def _one(core):
    r = EN.get(core)
    if r is not None:
        return r
    m = _PRE.match(core)
    if m and m.group(2) and m.group(2) != core:
        r = EN.get(m.group(2))
        if r is None:
            r = _rx(m.group(2))
        if r is not None:
            return m.group(1) + r + m.group(3)
    r = _rx(core)
    if r is not None:
        return r
    for sep in (" · ", ": ", " — ", ", "):
        if sep in core:
            parts = core.split(sep)
            out = [p if not _CYR.search(p) else _one(p.strip()) for p in parts]
            if all(o is not None for o in out):
                return sep.join(out)
    return None


MISSING = set()


def tr(text: str) -> str:
    if LANG["cur"] != "en" or not text or not _CYR.search(text):
        return text
    if "<" in text and ">" in text:      # rich text: переводим только текст между тегами
        return re.sub(r">([^<]+)<", lambda m: ">" + tr(m.group(1)) + "<", "<x>" + text + "</x>")[3:-4]
    if "\n" in text:
        return "\n".join(tr(x) for x in text.split("\n"))
    m = re.match(r"^(\s*)([\s\S]*?)(\s*)$", text)
    r = _one(m.group(2))
    if r is None:
        MISSING.add(m.group(2))
        return text
    return m.group(1) + r + m.group(3)


def _swap(w, getter, setter, key):
    """Хранит пару (ru, en) в свойстве виджета; новую русскую строку (обновлённую кодом) переводит заново."""
    cur = getter()
    if not cur:
        return
    st = w.property(key)
    ru = st[0] if (st and cur in st) else cur
    en = tr(ru)
    w.setProperty(key, (ru, en))
    want = en if LANG["cur"] == "en" else ru
    if cur != want:
        setter(want)


def translate(root: QWidget):
    ws = [root] + root.findChildren(QWidget)
    for w in ws:
        if w.property("notr"):
            continue
        try:
            if isinstance(w, (QLabel, QAbstractButton)):
                _swap(w, w.text, w.setText, "_t")
            if isinstance(w, QGroupBox):
                _swap(w, w.title, w.setTitle, "_t")
            if isinstance(w, (QLineEdit, QPlainTextEdit)):
                _swap(w, w.placeholderText, w.setPlaceholderText, "_p")
            if w.toolTip():
                _swap(w, w.toolTip, w.setToolTip, "_tt")
            if isinstance(w, QComboBox) and not w.property("notr_items"):
                for i in range(w.count()):
                    t = w.itemText(i)
                    if _CYR.search(t) or w.itemData(i, 0x0101):
                        ru = w.itemData(i, 0x0101) or t
                        w.setItemData(i, ru, 0x0101)
                        w.setItemText(i, tr(ru) if LANG["cur"] == "en" else ru)
            if isinstance(w, QTableWidget):
                for c in range(w.columnCount()):
                    it = w.horizontalHeaderItem(c)
                    if it:
                        ru = it.data(0x0101) or it.text()
                        it.setData(0x0101, ru)
                        it.setText(tr(ru) if LANG["cur"] == "en" else ru)
            if w.windowTitle() and w.isWindow():
                _swap(w, w.windowTitle, w.setWindowTitle, "_wt")
        except RuntimeError:
            pass


def translate_menu(m: QMenu):
    for a in m.actions():
        ru = a.property("_ru") or a.text()
        a.setProperty("_ru", ru)
        a.setText(tr(ru) if LANG["cur"] == "en" else ru)
        if a.menu():
            translate_menu(a.menu())
