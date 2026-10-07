"""Yume Haze Zapret 2.0 — новые страницы и окна: оформление, настройки, компоненты, мастер, виджет."""
from __future__ import annotations

import time
import webbrowser

from PySide6.QtCore import Qt, QTimer, QPoint, QRectF
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QPixmap, QGuiApplication
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit,
                               QSlider, QGridLayout, QButtonGroup, QFileDialog, QMessageBox, QDialog,
                               QStackedWidget, QCheckBox, QProgressBar, QTableWidget, QTableWidgetItem,
                               QHeaderView, QColorDialog, QFrame, QApplication)

import core
from core import log
import features as F
import zapret_tools as zt
from themes import T, ACCENTS


def _ui():
    import ui
    return ui


def row(*ws, stretch=True):
    h = QHBoxLayout()
    h.setSpacing(10)
    for w in ws:
        if isinstance(w, int):
            h.addSpacing(w)
        elif hasattr(w, "addWidget") and not isinstance(w, QWidget):
            h.addLayout(w)
        else:
            h.addWidget(w)
    if stretch:
        h.addStretch()
    return h


def setting_row(title, sub, widget):
    """Строка «заголовок + описание … переключатель»."""
    ui = _ui()
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 4, 0, 4)
    v = QVBoxLayout()
    v.setSpacing(2)
    t = QLabel(title)
    t.setStyleSheet("font-weight: 600; font-size: 13px;")
    v.addWidget(t)
    if sub:
        v.addWidget(ui.muted(sub))
    h.addLayout(v, 1)
    h.addWidget(widget, 0, Qt.AlignVCenter)
    return w


def toggle(win, key, default=True, on_change=None):
    ui = _ui()
    t = ui.Toggle(48, 26)
    t.setChecked(bool(win.s.data.get(key, default)), animate=False)

    def ch(v):
        win.s[key] = v
        if on_change:
            on_change(v)
    t.toggled.connect(ch)
    return t


def page(title, sub):
    ui = _ui()
    inner = QWidget()
    lay = QVBoxLayout(inner)
    lay.setContentsMargins(34, 28, 34, 28)
    lay.setSpacing(16)
    lay.addWidget(ui.page_header(title, sub))
    return inner, lay


def wrap(self, inner, lay):
    lay.addStretch()
    l = QVBoxLayout(self)
    l.setContentsMargins(0, 0, 0, 0)
    l.addWidget(_ui().scroll_page(inner))


# ───────────────────────── Оформление ─────────────────────────
class Swatch(QPushButton):
    def __init__(self, key, name, a1, a2):
        super().__init__()
        self.key, self.name, self.a1, self.a2 = key, name, a1, a2
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(108, 64)
        self.setToolTip(name)
        self.setStyleSheet("QPushButton{background:transparent;border:1px solid transparent;border-radius:10px;}"
                           "QPushButton:checked{border:2px solid %s;}" % T["a2"])

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), 0)
        g.setColorAt(0, QColor(self.a1))
        g.setColorAt(1, QColor(self.a2))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(QRectF(8, 8, self.width() - 16, 24), 7, 7)
        p.setPen(QColor(T["text"]))
        f = p.font()
        f.setPointSizeF(8.5)
        p.setFont(f)
        from i18n import tr
        p.drawText(QRectF(4, 36, self.width() - 8, 22), Qt.AlignCenter, tr(self.name))


class LookPage(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        s = win.s
        ui = _ui()
        inner, lay = page("Оформление", "Тема, цвет, фон и размеры")

        c = ui.Card("Тема", "Тема + цвет = твоя тема (тёмная + красный = чёрно-красная)")
        self.mode = QButtonGroup(self)
        hb = QHBoxLayout()
        for k, lab in [("dark", "🌙 Тёмная"), ("light", "☀ Светлая"), ("windows", "🪟 Как в Windows"),
                       ("time", "🌗 По времени суток")]:
            b = QPushButton(lab)
            b.setCheckable(True)
            b.setChecked(s.data.get("theme_base", "dark") == k)
            b.clicked.connect(lambda _=False, kk=k: self.set_base(kk))
            self.mode.addButton(b)
            hb.addWidget(b)
        hb.addStretch()
        c.lay.addLayout(hb)
        self.base_hint = ui.muted("")
        c.lay.addWidget(self.base_hint)
        lay.addWidget(c)

        c = ui.Card("Цвет", "Значок в трее и ярлыки в цвет темы")
        g = _ui().RGrid(6, 70, 10)
        self.sw = QButtonGroup(self)
        items = [(k, v[0], v[1], v[2]) for k, v in ACCENTS.items()]
        cc = s.data.get("custom_colors", ["#22d3ee", "#f472b6"])
        items.append(("custom", "Свой градиент", cc[0], cc[1]))
        for i, (k, n, a1, a2) in enumerate(items):
            b = Swatch(k, n, a1, a2)
            b.setChecked(s.data.get("theme", "blue") == k)
            b.clicked.connect(lambda _=False, kk=k: self.set_accent(kk))
            self.sw.addButton(b)
            g.addWidget(b)
            if k == "custom":
                self.custom_sw = b
        c.lay.addWidget(g)
        self.c1 = QPushButton("Цвет 1")
        self.c2 = QPushButton("Цвет 2")
        self.c1.clicked.connect(lambda: self.pick(0))
        self.c2.clicked.connect(lambda: self.pick(1))
        c.lay.addLayout(row(QLabel("Свой градиент:"), self.c1, self.c2, ui.muted("Два цвета, получится своя тема")))
        self.glow = QSlider(Qt.Horizontal)
        self.glow.setRange(0, 100)
        self.glow.setValue(int(s.data.get("glow", 50)))
        self.glow.valueChanged.connect(lambda v: (s.data.__setitem__("glow", v), self.debounce()))
        c.lay.addWidget(setting_row("Яркость свечения", "До 100% фон полностью заливается цветами темы", self.glow))
        self.glow.setFixedWidth(240)
        lay.addWidget(c)

        c = ui.Card("Интерфейс")
        self.rad = QSlider(Qt.Horizontal)
        self.rad.setRange(0, 22)
        self.rad.setFixedWidth(240)
        self.rad.setValue(int(s.data.get("radius", 10)))
        self.rad.valueChanged.connect(lambda v: (s.data.__setitem__("radius", v), self.debounce()))
        c.lay.addWidget(setting_row("🧷 Скругление углов", "От квадратных до круглых", self.rad))
        self.scale = QComboBox()
        self.scale.addItems(["90%", "100%", "110%", "125%", "150%"])
        self.scale.setCurrentText(f"{s.data.get('ui_scale', 100)}%")
        self.scale.currentTextChanged.connect(self.set_scale)
        c.lay.addWidget(setting_row("🔤 Размер интерфейса", "Применится после перезапуска программы", self.scale))
        lay.addWidget(c)

        c = ui.Card("🖼 Свой фон", "Картинка или арт фоном окна, затемняется под тему")
        b1 = QPushButton("Выбрать картинку")
        b1.setObjectName("Primary")
        b1.clicked.connect(self.pick_bg)
        b2 = QPushButton("Убрать")
        b2.clicked.connect(lambda: (s.__setitem__("bg_image", ""), win.root.update()))
        c.lay.addLayout(row(b1, b2))
        self.dim = QSlider(Qt.Horizontal)
        self.dim.setRange(0, 95)
        self.dim.setFixedWidth(240)
        self.dim.setValue(int(s.data.get("bg_dim", 70)))
        self.dim.valueChanged.connect(lambda v: (s.data.__setitem__("bg_dim", v), win.root.update()))
        c.lay.addWidget(setting_row("Затемнение фона", "", self.dim))
        lay.addWidget(c)
        wrap(self, inner, lay)
        self._t = QTimer(self)
        self._t.setSingleShot(True)
        self._t.timeout.connect(lambda: (win.s.save(), win.apply_theme()))
        self.update_hint()

    def debounce(self):
        self._t.start(120)

    def update_hint(self):
        m = self.win.s.data.get("theme_base", "dark")
        cur = "светлая" if F.resolve_base(m) == "light" else "тёмная"
        self.base_hint.setText({"windows": f"Как в настройках Windows. Сейчас: {cur}",
                                "time": f"С 07:00 до 20:00 светлая, ночью тёмная. Сейчас: {cur}"}.get(m, ""))
        self.base_hint.setVisible(m in ("windows", "time"))

    def set_base(self, k):
        self.win.s["theme_base"] = k
        self.update_hint()
        self.win.apply_theme()

    def set_accent(self, k):
        self.win.s["theme"] = k
        self.win.apply_theme()

    def pick(self, i):
        cc = list(self.win.s.data.get("custom_colors", ["#22d3ee", "#f472b6"]))
        c = QColorDialog.getColor(QColor(cc[i]), self)
        if c.isValid():
            cc[i] = c.name()
            self.win.s["custom_colors"] = cc
            self.custom_sw.a1, self.custom_sw.a2 = cc
            self.custom_sw.setChecked(True)
            self.set_accent("custom")

    def set_scale(self, t):
        self.win.s["ui_scale"] = int(t.rstrip("%"))
        self.win.toast("Размер применится после перезапуска")

    def pick_bg(self):
        f, _ = QFileDialog.getOpenFileName(self, "Фон", "", "Картинки (*.png *.jpg *.jpeg *.webp *.bmp *.gif)")
        if f:
            self.win.s["bg_image"] = f
            self.win.root.load_bg()
            self.win.root.update()


# ───────────────────────── Настройки ─────────────────────────
class SettingsPage(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        s = win.s
        ui = _ui()
        inner, lay = page("Настройки", "Запуск, язык, звук, уведомления, резервная копия")

        c = ui.Card("Запуск и трей")
        c.lay.addWidget(setting_row("Запускать вместе с Windows", "Zapret как служба работает и без программы",
                                    toggle(win, "autostart", False, core.set_autostart)))
        c.lay.addWidget(setting_row("Запускать свёрнутым в трей", "", toggle(win, "start_minimized", False)))
        c.lay.addWidget(setting_row("Сворачивать в трей при закрытии", "", toggle(win, "close_to_tray", True)))
        c.lay.addWidget(setting_row("Включать TG WS Proxy при запуске, если он был включён", "",
                                    toggle(win, "restore_state", True)))
        c.lay.addWidget(setting_row("Проверять подключение после включения Zapret", "",
                                    toggle(win, "auto_quick_test", True)))
        lay.addWidget(c)

        c = ui.Card("Язык")
        self.lang = QComboBox()
        self.lang.addItems(["🇷🇺 Русский", "🇬🇧 English"])
        self.lang.setCurrentIndex(1 if s.data.get("lang") == "en" else 0)
        self.lang.currentIndexChanged.connect(lambda i: win.set_lang("en" if i else "ru"))
        self.lang.setProperty("notr", True)
        c.lay.addWidget(setting_row("Язык интерфейса", "", self.lang))
        lay.addWidget(c)

        c = ui.Card("Уведомления")
        c.lay.addWidget(setting_row("Уведомления Windows", "", toggle(win, "notifications", True)))
        lay.addWidget(c)

        c = ui.Card("🧙 Мастер первого запуска", "Появляется сам при первом запуске. Можно пройти заново в любой момент")
        b = QPushButton("Запустить мастер")
        b.clicked.connect(lambda: Wizard(win).exec())
        c.lay.addLayout(row(b))
        lay.addWidget(c)

        c = ui.Card("О программе", "Yume Haze Zapret — графический интерфейс для zapret-discord-youtube и tg-ws-proxy "
                                   "от Flowseal. Все права на компоненты принадлежат их авторам.")
        br = []
        for text, url in [("zapret-discord-youtube", f"https://github.com/{core.ZAPRET_REPO}"),
                          ("tg-ws-proxy", f"https://github.com/{core.TG_REPO}"),
                          ("GitHub", ui.GITHUB_URL), ("Discord", ui.DISCORD_URL)]:
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, u=url: webbrowser.open(u))
            br.append(b)
        b = QPushButton("Папка данных")
        b.clicked.connect(lambda: win.open_path(core.DATA_DIR))
        br.append(b)
        c.lay.addLayout(row(*br))
        lay.addWidget(c)

        c = ui.Card("🧹 Очистка следов", "Полностью убирает всё, что программа поставила в систему: службу zapret, "
                                       "драйвер WinDivert, задачу автозапуска, записи в hosts, DNS-настройки и папку "
                                       "с настройками. Нужно для чистого удаления")
        b = QPushButton("Удалить всё…")
        b.setObjectName("Danger")
        b.clicked.connect(self.clean)
        c.lay.addLayout(row(b))
        lay.addWidget(c)
        wrap(self, inner, lay)

    def export(self):
        f, _ = QFileDialog.getSaveFileName(self, "Экспорт", "YumeHazeZapret.json", "JSON (*.json)")
        if f:
            F.export_cfg(self.win.s, f)
            self.win.toast("Файл настроек сохранён")

    def imp(self):
        f, _ = QFileDialog.getOpenFileName(self, "Импорт", "", "JSON (*.json)")
        if f:
            try:
                F.import_cfg(self.win.s, f)
                self.win.apply_theme()
                self.win.toast("Настройки загружены ✔")
            except Exception as e:
                QMessageBox.warning(self, "Импорт", str(e))

    def clean(self):
        from i18n import tr
        if QMessageBox.question(self, tr("Очистка следов"),
                                tr("Удалить службу zapret, WinDivert, автозапуск, записи hosts, DNS и настройки? "
                                   "Программа закроется.")) != QMessageBox.Yes:
            return
        msgs = F.clean_all(self.win.zapret, self.win.tg)
        for m in msgs:
            log("app", "✔ " + m)
        QMessageBox.information(self, tr("Очистка следов"),
                                "\n".join("✔ " + tr(m) for m in msgs) + "\n\n" +
                                tr("Готово. Теперь программу можно удалить через «Приложения» Windows — "
                                   "в системе ничего не останется."))
        self.win._no_save = True
        self.win.quit_app()


# ───────────────────────── Компоненты (вкладка «Обновления») ─────────────────────────
class CompCard(QWidget):
    def __init__(self, win, k):
        super().__init__()
        self.win, self.k = win, k
        ui = _ui()
        self.card = ui.Card()
        l = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(self.card)
        self.title = QLabel("Zapret (zapret-discord-youtube)" if k == "zapret" else "TG WS Proxy")
        self.title.setObjectName("CardTitle")
        self.info = ui.muted("")
        v = QVBoxLayout()
        v.setSpacing(2)
        v.addWidget(self.title)
        v.addWidget(self.info)
        self.chk = QPushButton("Проверить")
        self.chk.clicked.connect(lambda: (self.info.setText("Проверка…"), win.updater.check(k)))
        self.upd = QPushButton("Обновить")
        self.upd.setObjectName("Primary")
        self.upd.clicked.connect(self.install)
        self.inst = QPushButton("Установить")
        self.inst.setObjectName("Primary")
        self.inst.clicked.connect(self.install)
        self.rm = QPushButton("Удалить")
        self.rm.setObjectName("Danger")
        self.rm.clicked.connect(self.remove)
        h = QHBoxLayout()
        h.addLayout(v, 1)
        for b in (self.chk, self.upd, self.inst, self.rm):
            h.addWidget(b)
        self.card.lay.addLayout(h)
        self.card.lay.addWidget(ui.muted("Zapret: Discord, YouTube и другие сайты без VPN" if k == "zapret"
                                         else "Telegram без VPN: локальный MTProto-прокси через WebSocket"))
        self.bar = QProgressBar()
        self.bar.setFixedHeight(6)
        self.bar.setTextVisible(False)
        self.bar.setRange(0, 0)
        self.bar.hide()
        self.card.lay.addWidget(self.bar)
        self.rb = QComboBox()
        self.rb.setMinimumWidth(150)
        self.rbb = QPushButton("Откатить")
        self.rbb.clicked.connect(self.rollback)
        self.rbw = setting_row("♻ Откат версии", "Если обновление что-то сломало, верни прошлую версию. "
                                                "Хранятся 3 последние", QWidget())
        rl = self.rbw.layout()
        rl.itemAt(rl.count() - 1).widget().deleteLater()
        rl.addWidget(self.rb)
        rl.addWidget(self.rbb)
        self.card.lay.addWidget(self.rbw)
        # выбор любой версии с GitHub
        self.vcb = QComboBox()
        self.vcb.setMinimumWidth(150)
        self.vcb.addItem("Последняя", None)
        self.vbtn = QPushButton("Установить эту версию")
        self.vbtn.clicked.connect(lambda: self.install(self.vcb.currentData()))
        self.vw = setting_row("📌 Версия", "Можно поставить любую версию с GitHub, в том числе более старую", QWidget())
        vl = self.vw.layout()
        vl.itemAt(vl.count() - 1).widget().deleteLater()
        vl.addWidget(self.vcb)
        vl.addWidget(self.vbtn)
        self.card.lay.addWidget(self.vw)
        win.updater.versions.connect(self.on_versions)
        self._vloaded = False
        self.remote = ""
        self.refresh()

    def showEvent(self, e):
        super().showEvent(e)
        if not self._vloaded:
            self._vloaded = True
            self.win.updater.list_versions(self.k)

    def on_versions(self, k, tags):
        if k != self.k:
            return
        cur = self.vcb.currentData()
        self.vcb.clear()
        self.vcb.addItem("Последняя", None)
        for t in tags:
            self.vcb.addItem(t, t)
        self.vcb.setCurrentIndex(max(0, self.vcb.findData(cur)))

    def obj(self):
        return self.win.zapret if self.k == "zapret" else self.win.tg

    def refresh(self, busy=False):
        inst = self.obj().installed()
        ver = self.obj().version()
        if not busy:
            self.bar.hide()
            if inst:
                txt = f"Установлена {ver}" + (f" · Последняя {self.remote}" if self.remote else "")
                self.info.setText(txt)
            else:
                self.info.setText("Не установлен")
        self.inst.setVisible(not inst)
        self.rm.setVisible(inst)
        self.chk.setVisible(inst)
        self.upd.setVisible(inst and bool(self.remote) and core._vtuple(self.remote) > core._vtuple(ver))
        bk = [b for b in F.backups(self.k) if b != ver]
        self.rb.clear()
        self.rb.addItems(bk)
        self.rbw.setVisible(inst and bool(bk))
        for b in (self.inst, self.rm, self.chk, self.upd, self.rbb, self.vbtn):
            b.setEnabled(not busy)

    def install(self, tag=None):
        if self.obj().installed():
            F.backup_component(self.k, self.obj().version())
        self.bar.show()
        self.info.setText("Скачивание…")
        self.refresh(busy=True)
        self.win.updater.install(self.k, tag if isinstance(tag, str) else None)

    def remove(self):
        from i18n import tr
        name = "Zapret" if self.k == "zapret" else "TG WS Proxy"
        if QMessageBox.question(self, tr("Удалить"), tr(f"Удалить {name}? Его можно будет установить заново.")) \
                != QMessageBox.Yes:
            return
        self.refresh(busy=True)
        self.bar.show()

        def work():
            F.remove_component(self.k, self.win.zapret, self.win.tg)
            F.ui(lambda: (self.refresh(), self.win.apply_components(), self.win.toast(f"{name} удалён")))
        F.bg(work)

    def rollback(self):
        v = self.rb.currentText()
        if not v:
            return
        self.refresh(busy=True)
        self.bar.show()

        def work():
            try:
                F.rollback(self.k, v, self.win.zapret, self.win.tg)
            finally:
                F.ui(lambda: (self.refresh(), self.win.after_component_change(self.k)))
        F.bg(work)

    def on_checked(self, local, remote, has):
        if remote:
            self.remote = remote
        self.refresh()

    def on_progress(self, msg):
        self.info.setText(msg)

    def on_finished(self, ok, msg):
        self.refresh()
        if not ok:
            self.info.setText("✖ " + msg)
        self.win.after_component_change(self.k)


class UpdatesPage(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        ui = _ui()
        inner, lay = page("Обновления", "Программа и компоненты")
        c = ui.Card()
        self.app_title = QLabel(f"{core.DISPLAY_NAME}")
        self.app_title.setObjectName("CardTitle")
        self.app_info = ui.muted(f"Установлена {core.APP_VERSION}")
        v = QVBoxLayout()
        v.addWidget(self.app_title)
        v.addWidget(self.app_info)
        self.app_chk = QPushButton("Проверить")
        self.app_chk.clicked.connect(lambda: win.check_app_update(manual=True))
        self.app_upd = QPushButton("Обновить сейчас")
        self.app_upd.setObjectName("Primary")
        self.app_upd.hide()
        self.app_upd.clicked.connect(win.install_app_update)
        h = QHBoxLayout()
        h.addLayout(v, 1)
        h.addWidget(self.app_chk)
        h.addWidget(self.app_upd)
        c.lay.addLayout(h)
        c.lay.addWidget(setting_row("Проверять обновления автоматически",
                                    f"При запуске и раз в день, с github.com/{F.APP_REPO}",
                                    toggle(win, "app_autoupdate_check", True)))
        c.lay.addWidget(setting_row("Устанавливать без вопросов", "Скачает и обновится сам, когда выйдет новая версия",
                                    toggle(win, "app_autoupdate_install", False)))
        lay.addWidget(c)
        t = QLabel("📦 Компоненты: ставь только то, что нужно")
        t.setStyleSheet("font-weight: 700; font-size: 14px; margin-top: 6px;")
        lay.addWidget(t)
        self.cards = {k: CompCard(win, k) for k in ("zapret", "tg")}
        for cc in self.cards.values():
            lay.addWidget(cc)
        allb = QPushButton("Проверить всё")
        allb.clicked.connect(lambda: [win.updater.check(k) for k in self.cards if self.cards[k].obj().installed()])
        lay.addLayout(row(allb))
        wrap(self, inner, lay)
        up = win.updater
        up.checked.connect(lambda k, l, r, h: self.cards[k].on_checked(l, r, h))
        up.progress.connect(lambda k, m: (self.cards[k].on_progress(m), log(k, m)))
        up.finished.connect(lambda k, ok, m: (self.cards[k].on_finished(ok, m), log(k, m)))

    def refresh_local(self):
        for c in self.cards.values():
            c.refresh()


# ───────────────────────── Мастер первого запуска ─────────────────────────
class Wizard(QDialog):
    def __init__(self, win):
        super().__init__(win)
        from i18n import tr
        self.win = win
        self.setWindowTitle(tr("Мастер первого запуска"))
        self.setModal(True)
        self.resize(560, 430)
        self.setStyleSheet(f"QDialog {{ background: {T['bg']}; }}")
        ui = _ui()
        l = QVBoxLayout(self)
        l.setContentsMargins(28, 24, 28, 20)
        self.steps = QStackedWidget()
        l.addWidget(self.steps, 1)
        self.dots = QLabel()
        self.dots.setAlignment(Qt.AlignCenter)
        self.back = QPushButton("← Назад")
        self.skip = QPushButton("Пропустить")
        self.next = QPushButton("Далее →")
        self.next.setObjectName("Primary")
        self.back.clicked.connect(lambda: self.go(-1))
        self.next.clicked.connect(lambda: self.go(1))
        self.skip.clicked.connect(self.finish)
        l.addLayout(row(self.back, self.skip, stretch=False))
        l.itemAt(1).layout().addStretch()
        l.itemAt(1).layout().addWidget(self.dots)
        l.itemAt(1).layout().addStretch()
        l.itemAt(1).layout().addWidget(self.next)

        def step(title, sub):
            w = QWidget()
            v = QVBoxLayout(w)
            v.setSpacing(12)
            t = QLabel(title)
            t.setStyleSheet("font-size: 21px; font-weight: 700;")
            t.setWordWrap(True)
            v.addWidget(t)
            v.addWidget(ui.muted(sub))
            self.steps.addWidget(w)
            return v

        v = step("Добро пожаловать в Yume Haze Zapret", "Настроим всё за минуту. Выбери язык:")
        self.l_ru = QPushButton("🇷🇺 Русский")
        self.l_en = QPushButton("🇬🇧 English")
        for b, code in ((self.l_ru, "ru"), (self.l_en, "en")):
            b.setCheckable(True)
            b.setMinimumHeight(44)
            b.setChecked(win.s.data.get("lang", "ru") == code)
            b.clicked.connect(lambda _=False, c=code: self.set_lang(c))
            v.addWidget(b)
        v.addStretch()

        v = step("Что тебе нужно?", "Ненужное можно не ставить, программа будет легче. "
                                    "Поменять можно потом во вкладке «Обновления»")
        self.c_z = QCheckBox("Zapret — Discord, YouTube и другие сайты без VPN")
        self.c_t = QCheckBox("TG WS Proxy — Telegram без VPN")
        self.c_z.setChecked(win.zapret.installed())
        self.c_t.setChecked(win.tg.installed())
        v.addWidget(self.c_z)
        v.addWidget(self.c_t)
        v.addStretch()

        v = step("Подбираем стратегию", "Проверяем, какая стратегия лучше работает у твоего провайдера. "
                                        "Это займёт несколько минут, можно пропустить")
        self.s_btn = QPushButton("Запустить подбор")
        self.s_btn.setObjectName("Primary")
        self.s_btn.clicked.connect(self.run_pick)
        self.s_bar = QProgressBar()
        self.s_bar.setFixedHeight(6)
        self.s_bar.setTextVisible(False)
        self.s_lab = ui.muted("")
        v.addLayout(row(self.s_btn))
        v.addWidget(self.s_bar)
        v.addWidget(self.s_lab)
        v.addStretch()
        self.tester = None

        v = step("Выбери оформление", "Всё можно поменять во вкладке «Оформление»")
        hb = QHBoxLayout()
        for k, lab in [("dark", "🌙 Тёмная"), ("light", "☀ Светлая")]:
            b = QPushButton(lab)
            b.setMinimumHeight(40)
            b.clicked.connect(lambda _=False, kk=k: (win.s.__setitem__("theme_base", kk), win.apply_theme(),
                                                    self.restyle()))
            hb.addWidget(b)
        v.addLayout(hb)
        g = QGridLayout()
        for i, (k, val) in enumerate(ACCENTS.items()):
            b = Swatch(k, val[0], val[1], val[2])
            b.clicked.connect(lambda _=False, kk=k: (win.s.__setitem__("theme", kk), win.apply_theme(), self.restyle()))
            g.addWidget(b, i // 4, i % 4)
        v.addLayout(g)
        v.addStretch()

        v = step("Готово! 🎉", "")
        self.done_lab = ui.muted("")
        v.addWidget(self.done_lab)
        v.addStretch()
        self.i = 0
        self.render()
        win.translate(self)

    def restyle(self):
        self.setStyleSheet(f"QDialog {{ background: {T['bg']}; }}")

    def set_lang(self, code):
        self.l_ru.setChecked(code == "ru")
        self.l_en.setChecked(code == "en")
        self.win.set_lang(code)
        self.win.translate(self)

    def render(self):
        self.steps.setCurrentIndex(self.i)
        n = self.steps.count()
        self.dots.setText("  ".join("●" if j == self.i else "○" for j in range(n)))
        self.back.setVisible(self.i > 0)
        self.next.setText("Готово" if self.i == n - 1 else "Далее →")
        if self.i == 2 and not self.win.zapret.installed() and not self.c_z.isChecked():
            self.s_lab.setText("Zapret не выбран, подбирать не нужно")
            self.s_btn.hide()
        if self.i == n - 1:
            parts = []
            if self.win.zapret.installed() or self.c_z.isChecked():
                parts.append(f"Zapret: стратегия {self.win.s['strategy'][:-4]}, включается тумблером на главной "
                             "и сам запускается вместе с Windows.")
            if self.win.tg.installed() or self.c_t.isChecked():
                parts.append("TG WS Proxy: нажми «Подключить в Telegram» на главной.")
            parts.append("Программа живёт в трее рядом с часами.")
            self.done_lab.setText("\n\n".join(parts))
        self.win.translate(self)

    def go(self, d):
        if self.i == 1 and d > 0:
            if not self.c_z.isChecked() and not self.c_t.isChecked():
                self.win.toast("Выбери хотя бы что-то одно")
                return
            self.apply_components()
        if self.i + d >= self.steps.count():
            return self.finish()
        self.i = max(0, self.i + d)
        self.render()

    def apply_components(self):
        for k, cb in (("zapret", self.c_z), ("tg", self.c_t)):
            obj = self.win.zapret if k == "zapret" else self.win.tg
            if cb.isChecked() and not obj.installed():
                self.win.updater.install(k)
            elif not cb.isChecked() and obj.installed():
                F.bg(lambda kk=k: (F.remove_component(kk, self.win.zapret, self.win.tg),
                                   F.ui(self.win.apply_components)))

    def run_pick(self):
        if not self.win.zapret.installed():
            self.s_lab.setText("Zapret ещё устанавливается, подожди немного")
            return
        sts = self.win.zapret.strategies()
        self.tester = zt.StrategyTester(self.win.zapret)
        self.s_bar.setRange(0, len(sts))
        self.s_btn.setEnabled(False)
        self.tester.progress.connect(lambda d, t, txt: (self.s_bar.setValue(d), self.s_lab.setText(f"{txt} ({d}/{t})")))
        self.tester.finished.connect(self.picked)
        tg = [t for t in zt.load_targets() if zt.group_of(*t) in ("Discord", "YouTube")][:6] or zt.load_targets()
        self.tester.start(sts, tg)

    def picked(self, results):
        self.s_btn.setEnabled(True)
        if results:
            best = results[0][0]
            self.win.home.strategy.setCurrentText(best[:-4])
            self.s_lab.setText(f"Лучшая: {best[:-4]} ✔")
            F.add_history(self.win.s, "Подбор", best, extra=f"{results[0][1]}/{results[0][2]}")
        self.win.translate(self)

    def finish(self):
        if self.tester:
            self.tester.stop()
        self.win.s["wizard_done"] = True
        self.accept()


# ───────────────────────── Общие элементы «как в предпросмотре» ─────────────────────────
def zi_pixmap(size, dot=None):
    """Квадратик с градиентом темы и белой «Z» (+ точка статуса)."""
    from PySide6.QtGui import QPainterPath, QPen, QFont
    pm = QPixmap(size * 2, size * 2)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size * 2
    g = QLinearGradient(0, 0, s, s)
    g.setColorAt(0, QColor(T["a1"]))
    g.setColorAt(1, QColor(T["a2"]))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawRoundedRect(QRectF(0, 0, s, s), s * 0.26, s * 0.26)
    p.setPen(QPen(QColor("#000" if T.get("name") == "Mono" and not T.get("light") else "#fff"), s * 0.12,
                  Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    k = s * 0.29
    path = QPainterPath()
    path.moveTo(k, k); path.lineTo(s - k, k); path.lineTo(k, s - k); path.lineTo(s - k, s - k)
    p.drawPath(path)
    if dot:
        r = s * 0.34
        p.setPen(QPen(QColor("#15161d"), s * 0.07))
        p.setBrush(QColor(dot))
        p.drawEllipse(QRectF(s - r + s * 0.06, s - r + s * 0.06, r, r))
    p.end()
    pm.setDevicePixelRatio(2)
    return pm


def res_color(ok, tot):
    return "#3ddc97" if ok == tot else ("#ffd166" if ok else "#ff6b8a")


def menu_colors():
    light = T.get("light")
    return dict(bg="#fbfbfd" if light else "#1c1f2a", border="#d8dce6" if light else "#33374a",
                text="#111" if light else "#e5e7eb", muted="#8b93ab",
                chip="rgba(128,128,160,0.12)", sep="rgba(128,128,160,0.25)")


# ───────────────────────── Меню трея ─────────────────────────
class _Row(QFrame):
    def __init__(self, popup, check, text, hint="", arrow=False, icon=None, cb=None):
        super().__init__()
        from i18n import tr
        self.popup, self.cb, self.arrow = popup, cb, arrow
        self.setObjectName("MI")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(32)
        h = QHBoxLayout(self)
        h.setContentsMargins(10, 0, 10, 0)
        h.setSpacing(10)
        ck = QLabel(check or "")
        ck.setFixedWidth(16)
        ck.setAlignment(Qt.AlignCenter)
        ck.setStyleSheet(f"color: {T['a2']}; font-weight: 700; background: transparent;")
        if icon is not None:
            ck.setPixmap(icon.pixmap(16, 16))
        h.addWidget(ck)
        lb = QLabel(tr(text))
        lb.setStyleSheet("background: transparent;")
        h.addWidget(lb, 1)
        if hint or arrow:
            hl = QLabel(tr(hint) if hint else "▸")
            hl.setStyleSheet(f"color: {menu_colors()['muted']}; font-size: 11px; background: transparent;")
            h.addWidget(hl)

    def enterEvent(self, e):
        if self.arrow and self.cb:
            self.cb(self)
        elif self.popup.sub:
            try:
                self.popup.sub.close()
            except RuntimeError:
                pass
            self.popup.sub = None

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self.cb:
            if self.arrow:
                self.cb(self)
            else:
                self.popup.close_all()
                QTimer.singleShot(0, self.cb)


class Popup(QFrame):
    """Своё меню (как в предпросмотре): шапка, пункты с галочками, плашки теста, подменю."""
    def __init__(self, win, parent_popup=None, width=290):
        super().__init__(None, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.win, self.parent_popup, self.sub = win, parent_popup, None
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFixedWidth(width)
        c = menu_colors()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.box = QFrame()
        self.box.setObjectName("Box")
        self.box.setStyleSheet(
            f"#Box {{ background: {c['bg']}; border: 1px solid {c['border']}; border-radius: 10px; }}"
            f"QLabel {{ color: {c['text']}; font-size: 13px; }}"
            f"#MI {{ border-radius: 6px; background: transparent; }}"
            f"#MI:hover {{ background: rgba({','.join(map(str, T['tint']))},0.18); }}"
            f"#Chip2 {{ background: {c['chip']}; border-radius: 6px; }}"
            f"#Sep {{ background: {c['sep']}; }}")
        outer.addWidget(self.box)
        self.lay = QVBoxLayout(self.box)
        self.lay.setContentsMargins(6, 6, 6, 6)
        self.lay.setSpacing(0)

    def header(self, title, sub):
        from i18n import tr
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(10, 8, 10, 10)
        h.setSpacing(10)
        ic = QLabel()
        ic.setPixmap(zi_pixmap(30))
        h.addWidget(ic)
        v = QVBoxLayout()
        v.setSpacing(0)
        t = QLabel(f"<b>{title}</b>")
        s = QLabel(tr(sub))
        s.setStyleSheet(f"color: {menu_colors()['muted']}; font-size: 11px;")
        v.addWidget(t)
        v.addWidget(s)
        h.addLayout(v, 1)
        self.lay.addWidget(w)
        self.sep()

    def sep(self):
        f = QFrame()
        f.setObjectName("Sep")
        f.setFixedHeight(1)
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(6, 4, 6, 4)
        l.addWidget(f)
        self.lay.addWidget(w)

    def item(self, text, cb=None, check=None, hint="", arrow=False, icon=None):
        r = _Row(self, check, text, hint, arrow, icon, cb)
        self.lay.addWidget(r)
        return r

    def chips(self, results):
        from ui import BrandDot
        w = QWidget()
        g = QGridLayout(w)
        g.setContentsMargins(10, 4, 10, 8)
        g.setSpacing(6)
        for i, (name, (ok, tot)) in enumerate(results.items()):
            f = QFrame()
            f.setObjectName("Chip2")
            h = QHBoxLayout(f)
            h.setContentsMargins(8, 5, 8, 5)
            h.setSpacing(6)
            d = BrandDot(name)
            d.set(ok > 0)
            h.addWidget(d)
            lb = QLabel(name)
            lb.setStyleSheet("font-size: 12px;")
            h.addWidget(lb, 1)
            r = QLabel(f"<b style='color:{res_color(ok, tot)}'>{ok}/{tot}</b>")
            r.setStyleSheet("font-size: 12px;")
            h.addWidget(r)
            g.addWidget(f, i // 2, i % 2)
        self.lay.addWidget(w)

    def open_sub(self, row, build):
        if self.sub and self.sub.isVisible():
            return
        self.sub = Popup(self.win, self, 340)
        build(self.sub)
        self.sub.adjustSize()
        gp = row.mapToGlobal(QPoint(0, 0))
        x = self.x() - self.sub.width() - 4
        scr = QGuiApplication.screenAt(gp) or QGuiApplication.primaryScreen()
        ag = scr.availableGeometry()
        if x < ag.left():
            x = self.x() + self.width() + 4
        y = min(gp.y() - 6, ag.bottom() - self.sub.height())
        self.sub.move(x, max(ag.top(), y))
        self.sub.show()

    def close_all(self):
        p = self
        while p.parent_popup:
            p = p.parent_popup
        if p.sub:
            p.sub.close()
        p.close()

    def popup_at(self, pos):
        self.adjustSize()
        scr = QGuiApplication.screenAt(pos) or QGuiApplication.primaryScreen()
        ag = scr.availableGeometry()
        x = min(max(ag.left(), pos.x() - self.width() // 2), ag.right() - self.width())
        y = pos.y() - self.height() - 8
        if y < ag.top():
            y = pos.y() + 8
        self.move(x, min(y, ag.bottom() - self.height()))
        self.show()
        self.activateWindow()


def build_tray_popup(win):
    from i18n import tr
    import ui
    z, t, s = win.zapret, win.tg, win.s
    zi, ti = z.installed(), t.installed()
    zon, ton = zi and z.running(), ti and t.running()
    m = Popup(win)
    parts = []
    if zi:
        parts.append(f"Zapret {'вкл' if zon else 'выкл'}")
    if ti:
        parts.append(f"TG Proxy {'вкл' if ton else 'выкл'}")
    m.header(core.DISPLAY_NAME, " · ".join(parts) or "Компоненты не установлены")
    m.item("Открыть окно", win.show_window, check="⬚")
    m.sep()
    if zi:
        m.item("Zapret", lambda: (z.stop if z.running() else z.start)(), check="✔" if zon else "",
               hint=s["strategy"][:-4] if zon else "")

        def strat_menu(sub):
            fav = s.data.get("fav", [])
            res = s.data.get("strat_results", {})
            sts = z.strategies()
            for st in [x for x in sts if x in fav] + [x for x in sts if x not in fav]:
                r = res.get(st, {})
                hint = "  ".join(f"<span style='color:{ui.BRAND.get(g, '#aaa')}'>●</span>"
                                 f"<span style='color:{res_color(*r[g])}'>{r[g][0]}/{r[g][1]}</span>"
                                 for g in zt.QUICK_GROUPS if g in r) or tr("не проверялась")
                row = sub.item(("★ " if st in fav else "") + st[:-4] + ("  🏆" if st == win.best else ""),
                               lambda n=st[:-4]: win.home.strategy.setCurrentText(n),
                               check="●" if st == s["strategy"] else "")
                hl = QLabel(hint)
                hl.setStyleSheet("font-size: 11px; background: transparent;")
                row.layout().addWidget(hl)
        m.item("Стратегия", lambda row=None: m.open_sub(m._srow, strat_menu), check="⇄", arrow=True)
        m._srow = m.lay.itemAt(m.lay.count() - 1).widget()
        m._srow.cb = lambda row: m.open_sub(row, strat_menu)
    if ti:
        m.item("TG WS Proxy", lambda: (t.stop if t.running() else t.start)(), check="✔" if ton else "")
    if zi:
        m.sep()
        ago = ""
        if win.quick_time:
            mins = int((time.time() - win.quick_time) / 60)
            ago = "только что" if mins < 1 else f"{mins} мин назад"
        m.item("Тест подключения", win.tray_test, check="⚡", hint=ago)
        if win.quick_last:
            m.chips(win.quick_last)
        m.item("Перезапустить Discord", win.fix_discord, check="🔄")
    if ti:
        m.item("Копировать ссылку TG", win.copy_tg_link, check="🔗")
    m.sep()
    m.item("Discord-сервер", lambda: webbrowser.open(ui.DISCORD_URL), icon=ui.discord_icon(16))
    m.item("GitHub", lambda: webbrowser.open(ui.GITHUB_URL), icon=ui.github_icon(16))
    m.item("Выход", win.quit_app, check="⏻")
    return m


# ───────────────────────── Мини-виджет (капсула, как в предпросмотре) ─────────────────────────
class MiniWidget(QWidget):
    def __init__(self, win):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.win = win
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.OpenHandCursor)
        self._drag = None
        h = QHBoxLayout(self)
        h.setContentsMargins(14, 12, 14, 12)
        self.cap = QFrame()
        self.cap.setObjectName("Cap")
        h.addWidget(self.cap)
        l = QHBoxLayout(self.cap)
        l.setContentsMargins(10, 8, 12, 8)
        l.setSpacing(10)
        self.ic = QLabel()
        l.addWidget(self.ic)
        v = QVBoxLayout()
        v.setSpacing(2)
        self.title = QLabel()
        self.line = QLabel()
        v.addWidget(self.title)
        v.addWidget(self.line)
        l.addLayout(v)
        for _w in (self.ic, self.title, self.line):
            _w.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.x_btn = QLabel("✕")
        self.x_btn.setCursor(Qt.PointingHandCursor)
        self.x_btn.mousePressEvent = lambda e: (self.win.s.__setitem__("widget", False), self.win.set_widget(False))
        l.addWidget(self.x_btn, 0, Qt.AlignTop)
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        sh = QGraphicsDropShadowEffect(self.cap)
        sh.setBlurRadius(26)
        sh.setOffset(0, 4)
        sh.setColor(QColor(*T["tint"], 110))
        self.cap.setGraphicsEffect(sh)
        pos = win.s.data.get("widget_pos")
        if pos:
            self.move(*pos)
        else:
            g = QGuiApplication.primaryScreen().availableGeometry()
            self.move(g.right() - 300, g.top() + 40)
        self.refresh()

    def refresh(self):
        from i18n import tr
        import ui
        light = T.get("light")
        tint = ",".join(map(str, T["tint"]))
        txt = "#111" if light else "#fff"
        self.cap.setStyleSheet(
            f"#Cap {{ background: {'rgba(255,255,255,0.88)' if light else 'rgba(12,14,22,0.86)'};"
            f" border: 1px solid rgba({tint},0.45); border-radius: 22px; }}"
            f"QLabel {{ color: {txt}; font-size: 12px; background: transparent; }}")
        self.x_btn.setStyleSheet(f"color: {txt}; opacity: .5; font-size: 11px;")
        z, t, s = self.win.zapret, self.win.tg, self.win.s
        zon = z.installed() and z.running()
        ton = t.installed() and t.running()
        bad = any(ok == 0 for ok, _ in self.win.quick_last.values()) if zon else False
        dot = "#f43f5e" if bad else ("#3ddc97" if (zon or ton) else "#6b7280")
        self.ic.setPixmap(zi_pixmap(22, dot))
        if z.installed():
            title = f"Zapret · {s['strategy'][:-4]}" if zon else tr("Zapret выключен")
        else:
            title = "TG WS Proxy · " + tr("вкл" if ton else "выкл")
        self.title.setText(f"<b>{title}</b>")
        if zon and self.win.quick_last:
            self.line.setText("&nbsp;&nbsp;".join(
                f"<span style='color:{ui.BRAND.get(g, '#aaa')}'>●</span> "
                f"<b style='color:{res_color(ok, tot)}'>{ok}/{tot}</b>"
                for g, (ok, tot) in self.win.quick_last.items()))
        else:
            extra = []
            if z.installed() and t.installed():
                extra.append("TG Proxy " + tr("вкл" if ton else "выкл"))
            self.line.setText(" · ".join(extra) or tr("нажми «Проверить» для теста") if zon else " · ".join(extra))
        self.line.setVisible(bool(self.line.text()))
        self.adjustSize()

    def update(self):
        try:
            self.refresh()
        except RuntimeError:
            pass
        super().update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        if self._drag is not None:
            self.win.s["widget_pos"] = [self.x(), self.y()]
        self._drag = None
        self.setCursor(Qt.OpenHandCursor)

    def mouseDoubleClickEvent(self, e):
        self.win.show_window()


# ───────────────────────── Всплывающие подсказки внутри окна ─────────────────────────
class Toast(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.hide()
        self._t = QTimer(self)
        self._t.setSingleShot(True)
        self._t.timeout.connect(self.hide)

    def show_text(self, text):
        from i18n import tr
        self.setText(tr(text))
        self.setStyleSheet(f"background: {T['input']}; color: {T['text']}; border: 1px solid {T['inputBorder']};"
                           f"border-left: 3px solid {T['a2']}; border-radius: 8px; padding: 9px 14px;")
        self.adjustSize()
        p = self.parentWidget()
        self.move(p.width() - self.width() - 20, p.height() - self.height() - 20)
        self.show()
        self.raise_()
        self._t.start(2600)


# ───────────────────────── Доп. карточки вкладки Zapret ─────────────────────────
class TagList(QWidget):
    """Список доменов-«чипов» с полем добавления (свои сайты / исключения)."""
    def __init__(self, win, kind, placeholder):
        super().__init__()
        self.win, self.kind = win, kind
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        self.inp = QLineEdit()
        self.inp.setPlaceholderText(placeholder)
        self.inp.returnPressed.connect(self.add)
        b = QPushButton("Добавить")
        b.setObjectName("Primary")
        b.clicked.connect(self.add)
        h = QHBoxLayout()
        h.addWidget(self.inp, 1)
        h.addWidget(b)
        v.addLayout(h)
        self.box = QWidget()
        self.flow = QGridLayout(self.box)
        self.flow.setContentsMargins(0, 0, 0, 0)
        self.flow.setSpacing(6)
        v.addWidget(self.box)
        self.render()

    def items(self):
        return F.read_list(self.kind) if core.ZAPRET_DIR.exists() else []

    def add(self, text=None):
        vals = [F.clean_domain(x) for x in re.split(r"[\s,;]+", text or self.inp.text()) if x.strip()]
        if not vals:
            return
        F.write_list(self.kind, self.items() + vals)
        self.inp.clear()
        self.render()
        self.changed()

    def remove(self, d):
        F.write_list(self.kind, [x for x in self.items() if x != d])
        self.render()
        self.changed()

    def changed(self):
        if self.win.zapret.running():
            self.win.zapret.restart()

    def render(self):
        while self.flow.count():
            w = self.flow.takeAt(0).widget()
            if w:
                w.deleteLater()
        for i, d in enumerate(self.items()):
            b = QPushButton(d + "  ✕")
            b.setToolTip("Убрать")
            b.setStyleSheet("padding: 4px 10px; font-size: 12px;")
            b.clicked.connect(lambda _=False, dd=d: self.remove(dd))
            self.flow.addWidget(b, i // 4, i % 4)


import re  # noqa: E402


def zapret_extras(win, lay):
    ui = _ui()
    c = ui.Card("🌐 Свои сайты", "Эти сайты Zapret будет обходить")
    win.sites = TagList(win, "sites", "Например: rutracker.org")
    c.lay.addWidget(win.sites)
    lay.addWidget(c)

    c = ui.Card("🚫 Исключения", "Эти сайты и программы Zapret не трогает. "
                               "Если какой-то сайт сломался, добавь его сюда и он заработает")
    win.excl = TagList(win, "excl", "sberbank.ru")
    c.lay.addWidget(win.excl)
    qb = [QLabel("Быстро добавить:")]
    for k, doms in F.EXCL_PRESETS.items():
        b = QPushButton("+ " + k)
        b.clicked.connect(lambda _=False, d=doms: win.excl.add(" ".join(d)))
        qb.append(b)
    c.lay.addLayout(row(*qb))
    lay.addWidget(c)

    c = ui.Card("🧭 DNS в один клик", "Провайдер может подменять DNS. Защищённый DNS (DoH) это исправляет")
    btns = []
    grp = QButtonGroup(c)
    for k, (name, _, _) in F.DNS.items():
        b = QPushButton(name)
        b.setCheckable(True)
        b.setChecked(win.s.data.get("dns", "isp") == k)
        grp.addButton(b)
        b.clicked.connect(lambda _=False, kk=k: (win.s.__setitem__("dns", kk), F.bg(F.set_dns, kk),
                                                win.toast("DNS: " + F.DNS[kk][0])))
        btns.append(b)
    c.lay.addLayout(row(*btns))
    lay.addWidget(c)

    c = ui.Card("🛑 Блокировка рекламы и трекеров", "Через файл hosts: реклама и слежка не загружаются во всех "
                                                  "браузерах и программах. Список обновляется сам раз в неделю")
    keys = ["off", "basic", "social"]
    agrp = QButtonGroup(c)
    abtns = []
    for i, nm in enumerate(["Выключено", "Базовый (StevenBlack)", "+ соцсети-виджеты"]):
        ab = QPushButton(nm)
        ab.setCheckable(True)
        ab.setChecked(win.s.data.get("adblock", "off") == keys[i])
        agrp.addButton(ab, i)
        abtns.append(ab)
    st = ui.muted(win.s.data.get("adblock_info", ""))

    def setad(i):
        k = keys[i]
        win.s["adblock"] = k
        st.setText("Скачивание…")

        def work():
            n = F.set_adblock(k)
            info = f"Заблокировано {n} доменов · обновлено {time.strftime('%d.%m.%Y')}" if n else ""
            win.s["adblock_info"] = info
            win.s["adblock_time"] = time.time()
            F.ui(lambda: st.setText(info))
        F.bg(work)
    agrp.idClicked.connect(setad)
    c.lay.addLayout(row(*abtns))
    c.lay.addWidget(st)
    lay.addWidget(c)



# ───────────────────────── Доп. карточки вкладки «Тесты» ─────────────────────────
def tests_extras(win, page, lay):
    ui = _ui()
    c = ui.Card("🧪 Проверить любой сайт", "Открывается ли сайт сейчас, с текущей стратегией")
    inp = QLineEdit()
    inp.setPlaceholderText("Например: rutracker.org")
    res = QLabel("")
    res.setWordWrap(True)
    add = QPushButton("Добавить в «Свои сайты» →")
    add.hide()

    def check():
        d = F.clean_domain(inp.text())
        if not d:
            return
        res.setText(f"Проверяю {d}…")
        add.hide()

        def work():
            ok, ms = zt.probe("https://" + d, timeout=8)
            listed = d in (F.read_list("sites") if core.ZAPRET_DIR.exists() else [])

            def done():
                from i18n import tr
                if ok:
                    res.setText(f"<span style='color:#3ddc97'>✔ {tr('открывается')} · {int(ms)} {tr('мс')}</span>")
                else:
                    res.setText(f"<span style='color:#ff6b8a'>✖ {tr('не открывается')}</span>" +
                                ("" if listed else f" — {tr('сайта нет в списках Zapret')}"))
                    add.setVisible(not listed)
                log("app", f"Проверка {d}: " + (f"открывается · {int(ms)} мс" if ok else "не открывается"))
            F.ui(done)
        F.bg(work)
    b = QPushButton("Проверить")
    b.setObjectName("Primary")
    b.clicked.connect(check)
    inp.returnPressed.connect(check)
    add.clicked.connect(lambda: (win.sites.add(inp.text()), add.hide(), win.toast("Добавлено в «Свои сайты»")))
    h = QHBoxLayout()
    h.addWidget(inp, 1)
    h.addWidget(b)
    c.lay.addLayout(h)
    c.lay.addLayout(row(res, add))
    lay.insertWidget(1, c)

    page.fill_history = lambda: None

    c = ui.Card("Консоль", "Вывод winws.exe и тестов в реальном времени")
    page.console = ui.Console(300)
    page.console.setMinimumHeight(200)
    c.lay.addWidget(page.console)
    lay.addWidget(c)
