# -*- coding: utf-8 -*-
"""AXIOM · Model K4 / Alpha 3 — 本地原生主程序（tkinter + 纯标准库）

启动：python app.py（或 pythonw app.py 无控制台）
数据：data/user_data.json；测试时通过环境变量 AXIOM_DATA_DIR 重定向。
约束：Alpha2 的 typing_userdata.json / typing.db 只读，不扫描、不回写。
"""
import os
import sys
import json
import time
import random
import webbrowser
import tkinter as tk
from tkinter import messagebox, filedialog

# 冻结兼容：exe 运行时 __file__ 指向 _MEIPASS 临时目录，不能作为数据目录。
# RES_DIR = 只读资源（配置/网页/图标）；APP_DIR = 可写程序目录（exe 同级）。
_FROZEN = getattr(sys, "frozen", False)
RES_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.dirname(os.path.abspath(sys.executable)) if _FROZEN else os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, RES_DIR)

from core import storage, theme, content, difficulty, debug, importer
from core.content_data import ARTICLES, AGREEMENT, CHANGELOG, CATEGORIES
from ui.widgets import ThemedButton, MenuCard, ProgressBar, Toggle, ScrollPanel, bind_mousewheel
from ui import anim

# 测试 / 低性能环境可用 AXIOM_NO_ANIM=1 关闭动画
if os.environ.get("AXIOM_NO_ANIM") == "1":
    anim.ENABLED = False

APP_TITLE = "AXIOM · Model K4 / Alpha 3"
VERSION = "K4-Alpha3"
FONT_UI = theme.FONT_UI
FONT_MONO = theme.FONT_MONO

TIME_LIMIT = 300


class App(tk.Tk):
    def __init__(self, data_dir=None):
        super().__init__()
        self.app_dir = APP_DIR
        _dir = data_dir or os.environ.get("AXIOM_DATA_DIR")
        storage.configure(APP_DIR, _dir)
        debug.configure(storage.DATA_DIR)
        self.data = storage.load()
        self.theme_setting = self.data.get("theme", "system")
        self.p = theme.get_palette(self.theme_setting)
        self.view = None
        self.view_name = ""
        self.typing_state = None
        self._timer = None
        self._system_theme_check = None

        self.title(APP_TITLE)
        self.geometry("1080x700")
        self.minsize(900, 600)
        self.configure(bg=self.p["bg"])
        try:
            self.iconbitmap(os.path.join(RES_DIR, "assets", "app.ico"))
        except Exception:
            pass

        self.container = tk.Frame(self, bg=self.p["bg"])
        self.container.pack(fill="both", expand=True)
        self.show("login")
        self._poll_system_theme()

    # ---------- 基础设施 ----------
    def persist(self):
        # 无痕/调试会话不落盘
        if self.data.get("session", {}).get("mode") in ("incognito", "debug"):
            return
        storage.save(self.data)

    def show(self, name, **kwargs):
        # 记住当前页与参数，供主题切换 rebuild 使用
        self._view_args = (name, dict(kwargs))
        if self._timer:
            try:
                self.after_cancel(self._timer)
            except Exception:
                pass
            self._timer = None
        if self.view is not None:
            self.view.destroy()
        self.view_name = name
        builders = {
            "login": LoginView, "agreement": AgreementView, "menu": MenuView,
            "articles": ArticlesView, "typing": TypingView, "versus": VersusSetupView,
            "levels": LevelsView, "records": RecordsView, "settings": SettingsView,
            "changelog": ChangelogView, "debug_menu": DebugMenuView,
        }
        cls = builders.get(name, LoginView)
        self.view = cls(self.container, self, **kwargs)
        self.view.pack(fill="both", expand=True)
        debug.log("view=" + name)
        self.update_idletasks()
        # 视图入场动效（PCL 风格轻上滑淡入）
        anim.view_enter(self.view, self.p["bg"], self.p["fg"])

    def rebuild(self):
        """主题切换后重建整个 shell（局部改色不可靠）"""
        self.p = theme.get_palette(self.theme_setting)
        self.configure(bg=self.p["bg"])
        self.container.configure(bg=self.p["bg"])
        name, args = getattr(self, "_view_args", (self.view_name, {}))
        # typing 页重建需要参数；若不在打字页则按记录参数重建
        self.show(name, **args)

    def _poll_system_theme(self):
        if self.theme_setting == "system":
            eff = theme.effective_theme("system")
            if eff != theme.effective_theme(getattr(self, "_last_eff", "system")):
                self._last_eff = eff
                self.rebuild()
        self._system_theme_check = self.after(30000, self._poll_system_theme)

    def toast(self, msg):
        """轻量提示：状态栏式，不用模态弹窗打断"""
        if not hasattr(self, "_toast"):
            self._toast = tk.Label(self, font=(FONT_UI, 9), bd=0)
        self._toast.configure(text=msg, bg=self.p["panel2"], fg=self.p["fg"])
        self._toast.place(relx=0.5, rely=0.94, anchor="center")
        self.after(2200, lambda: self._toast.place_forget())

    # ---------- 协议 ----------
    def need_agreement(self, username):
        return username not in self.data.get("agreement_accepted", [])

    def accept_agreement(self, username):
        acc = self.data.setdefault("agreement_accepted", [])
        if username not in acc:
            acc.append(username)
        self.persist()

    # ---------- 网页模式 ----------
    def open_web(self):
        cfg_path = os.path.join(RES_DIR, "config.json")
        url = "https://czy-cmd.github.io/AXIOM-K4/"
        timeout = 6
        msg = "网络故障，尝试打开本地html中……"
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            url = cfg.get("remote_url") or url
            timeout = cfg.get("net_timeout_seconds", 6)
            msg = cfg.get("network_message") or msg
        except Exception:
            pass

        if self._net_ok(url, timeout):
            webbrowser.open(url)
        else:
            local = os.path.join(RES_DIR, "web", "index.html")
            self.toast(msg)
            if os.path.isfile(local):
                webbrowser.open("file:///" + local.replace("\\", "/"))
            else:
                messagebox.showwarning("AXIOM", msg + "\n（未找到本地 web/index.html）")

    def _net_ok(self, url, timeout):
        import urllib.request
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            req = urllib.request.Request(url, method="HEAD",
                                         headers={"User-Agent": "AXIOM-K4/1.0"})
            with opener.open(req, timeout=timeout) as r:
                return getattr(r, "status", 200) < 400
        except Exception:
            return False

    # ---------- 打字核心（供 TypingView / Versus 复用） ----------
    def start_typing(self, text, title, mode="练习", back="menu",
                     difficulty_index=None, agent_count=None):
        self.show("typing", text=text, title=title, mode=mode, back=back,
                  difficulty_index=difficulty_index, agent_count=agent_count)

    def finish_typing(self, result):
        """记录成绩、错字、积分，然后进入结算"""
        if self.data.get("session", {}).get("mode") in ("incognito", "debug"):
            self.show("result", **result) if False else self._show_result(result)
            return
        self.data.setdefault("records", []).append(result)
        self.data["points"] = self.data.get("points", 0) + int(result.get("score", 0))
        # 错字本
        for ch, cnt in result.get("mistakes", {}).items():
            m = self.data.setdefault("mistakes", {})
            m[ch] = m.get(ch, 0) + cnt
        self.persist()
        self._show_result(result)

    def _show_result(self, result):
        dlg = tk.Toplevel(self)
        dlg.title("结算 · " + result.get("mode", "练习"))
        dlg.configure(bg=self.p["panel"])
        dlg.geometry("460x420")
        dlg.transient(self)
        dlg.grab_set()
        p = self.p
        tk.Label(dlg, text=result.get("grade", "—"), font=(FONT_MONO, 56, "bold"),
                 fg=p["accent"], bg=p["panel"]).pack(pady=(28, 6))
        lines = [
            "模式  " + result.get("mode", "练习"),
            "分数  %d" % result.get("score", 0),
            "正确率  %.1f%%" % result.get("accuracy", 0),
            "速度  %.1f 字/秒" % result.get("speed", 0),
            "用时  %d 秒" % result.get("elapsed", 0),
        ]
        if result.get("rank"):
            lines.append("名次  %s" % result["rank"])
        if result.get("difficulty"):
            lines.append("难度  " + str(result["difficulty"]).upper())
        tk.Label(dlg, text="\n".join(lines), font=(FONT_UI, 12), fg=p["fg"],
                 bg=p["panel"], justify="left").pack(pady=12)
        ThemedButton(dlg, p, "返回主菜单", lambda: (dlg.destroy(), self.show("menu")),
                     variant="primary").pack(pady=(6, 20))


# ============================================================
#  登录页
# ============================================================
class LoginView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=app.p["bg"])
        self.app = app
        p = app.p
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # 左品牌栏
        brand = tk.Frame(self, bg=p["brand_bg"], width=400)
        brand.grid(row=0, column=0, sticky="nsew")
        brand.pack_propagate(False)
        tk.Label(brand, text="AXIOM / TYPING SYSTEM", font=(FONT_MONO, 9),
                 fg=p["brand_dim"], bg=p["brand_bg"]).pack(anchor="w", padx=40, pady=(52, 0))
        tk.Label(brand, text="AX.", font=(FONT_MONO, 64, "bold"),
                 fg=p["brand_fg"], bg=p["brand_bg"]).pack(anchor="w", padx=40, pady=(16, 0))
        tk.Label(brand, text="MODEL K4  ·  ALPHA 3", font=(FONT_MONO, 12),
                 fg=p["brand_dim"], bg=p["brand_bg"]).pack(anchor="w", padx=40, pady=(4, 0))
        tk.Frame(brand, bg=p["brand_dim"], height=1, width=220).place(x=40, y=232)
        tk.Label(brand, text="少一点花哨，多一点准确。", font=(FONT_UI, 13),
                 fg=p["brand_fg"], bg=p["brand_bg"]).place(x=40, y=256)
        tk.Label(brand, text="TYPING TRAINER  ·  BUILD 2026.11", font=(FONT_MONO, 8),
                 fg=p["brand_dim"], bg=p["brand_bg"]).place(x=40, y=292)

        # 右表单区
        right = tk.Frame(self, bg=p["bg"])
        right.grid(row=0, column=1, sticky="nsew")
        card = tk.Frame(right, bg=p["panel"], highlightthickness=1,
                        highlightbackground=p["border"])
        card.place(relx=0.5, rely=0.5, anchor="center", width=400, height=470)
        tk.Label(card, text="欢迎回来", font=(FONT_UI, 22, "bold"),
                 fg=p["fg"], bg=p["panel"]).pack(anchor="w", padx=36, pady=(42, 4))
        tk.Label(card, text="登录或创建一个本机账号", font=(FONT_UI, 10),
                 fg=p["dim"], bg=p["panel"]).pack(anchor="w", padx=36, pady=(0, 22))

        self.user_var = tk.StringVar()
        self.pwd_var = tk.StringVar()
        self.tip = tk.Label(card, text="", font=(FONT_UI, 9), fg=p["red"], bg=p["panel"])
        self.tip.pack(anchor="w", padx=36)

        tk.Label(card, text="用户名", font=(FONT_UI, 9), fg=p["dim"],
                 bg=p["panel"]).pack(anchor="w", padx=36)
        e1 = tk.Entry(card, textvariable=self.user_var, font=(FONT_UI, 11),
                      bg=p["entry_bg"], fg=p["fg"], bd=0,
                      highlightthickness=1, highlightbackground=p["border"])
        e1.pack(fill="x", padx=36, pady=(2, 14), ipady=7)

        tk.Label(card, text="密码", font=(FONT_UI, 9), fg=p["dim"],
                 bg=p["panel"]).pack(anchor="w", padx=36)
        self.pwd_entry = tk.Entry(card, textvariable=self.pwd_var, show="•",
                                  font=(FONT_UI, 11), bg=p["entry_bg"], fg=p["fg"],
                                  bd=0, highlightthickness=1,
                                  highlightbackground=p["border"])
        self.pwd_entry.pack(fill="x", padx=36, pady=(2, 4), ipady=7)

        row = tk.Frame(card, bg=p["panel"])
        row.pack(fill="x", padx=36)
        self.show_pwd = False
        tk.Button(row, text="显示", font=(FONT_UI, 8), bd=0, cursor="hand2",
                  bg=p["panel"], fg=p["dim"], command=self._toggle_pwd).pack(side="right")

        btnrow = tk.Frame(card, bg=p["panel"])
        btnrow.pack(fill="x", padx=36, pady=(18, 0))
        ThemedButton(btnrow, p, "登录", self._login, variant="primary", width=10).pack(side="left")
        ThemedButton(btnrow, p, "注册", self._register, variant="ghost", width=10).pack(side="left", padx=8)

        sep = tk.Frame(card, bg=p["border"], height=1)
        sep.pack(fill="x", padx=36, pady=(22, 12))
        links = tk.Frame(card, bg=p["panel"])
        links.pack(padx=36)
        tk.Button(links, text="游客模式", font=(FONT_UI, 9), bd=0, cursor="hand2",
                  bg=p["panel"], fg=p["dim"], command=lambda: self._quick("guest", "游客")).pack(side="left")
        tk.Label(links, text="·", fg=p["dim"], bg=p["panel"]).pack(side="left", padx=8)
        tk.Button(links, text="无痕模式", font=(FONT_UI, 9), bd=0, cursor="hand2",
                  bg=p["panel"], fg=p["dim"], command=lambda: self._quick("incognito", "无痕")).pack(side="left")
        tk.Label(links, text="·", fg=p["dim"], bg=p["panel"]).pack(side="left", padx=8)
        tk.Button(links, text="调试模式", font=(FONT_UI, 9), bd=0, cursor="hand2",
                  bg=p["panel"], fg=p["dim"], command=self._debug_login).pack(side="left")
        tk.Label(card, text="游客：暂存本机  ·  无痕：不保存  ·  调试：口令进入",
                 font=(FONT_UI, 8), fg=p["dim"], bg=p["panel"]).pack(anchor="w", padx=36, pady=(10, 0))
        tk.Label(card, text="含 AI 生成内容，请注意辨别", font=(FONT_UI, 8),
                 fg=p["dim"], bg=p["panel"]).pack(anchor="w", padx=36, pady=(4, 0))

        e1.focus_set()
        self._tabs = [e1, self.pwd_entry]
        e1.bind("<Return>", lambda e: self.pwd_entry.focus_set())
        self.pwd_entry.bind("<Return>", lambda e: self._login())

    def _toggle_pwd(self):
        self.show_pwd = not self.show_pwd
        self.pwd_entry.configure(show="" if self.show_pwd else "•")

    def _set_tip(self, text):
        self.tip.configure(text=text)

    def _login(self):
        name = self.user_var.get().strip()
        pwd = self.pwd_var.get()
        if not name or not pwd:
            return self._set_tip("请输入用户名和密码")
        users = self.app.data.get("users", {})
        if name not in users:
            return self._set_tip("用户不存在")
        if not storage.verify_password(pwd, users[name].get("password", "")):
            return self._set_tip("密码错误")
        self.app.data["session"] = {"user": name, "mode": "normal"}
        self.app.persist()
        self._enter(name)

    def _register(self):
        name = self.user_var.get().strip()
        pwd = self.pwd_var.get()
        if not name or not pwd:
            return self._set_tip("请输入用户名和密码")
        if len(pwd) < 4:
            return self._set_tip("密码至少 4 位")
        users = self.app.data.setdefault("users", {})
        if name in users:
            return self._set_tip("用户名已存在")
        users[name] = {"id": self.app.data.get("next_id", 1), "username": name,
                       "password": storage.hash_password(pwd), "points": 0,
                       "unlocked": [], "records": []}
        self.app.data["next_id"] = self.app.data.get("next_id", 1) + 1
        self.app.data["session"] = {"user": name, "mode": "normal"}
        self.app.persist()
        self._enter(name)

    def _enter(self, name):
        if self.app.need_agreement(name):
            self.app.show("agreement", user=name, back="login")
        else:
            self.app.show("menu")

    def _quick(self, mode, label):
        self.app.data["session"] = {"user": label, "mode": mode}
        self.app.persist()
        self.app.show("menu")

    def _debug_login(self):
        win = tk.Toplevel(self.app)
        win.title("调试模式")
        win.configure(bg=self.app.p["panel"])
        win.geometry("340x180")
        win.transient(self.app)
        p = self.app.p
        tk.Label(win, text="输入调试口令", font=(FONT_UI, 12),
                 bg=p["panel"], fg=p["fg"]).pack(pady=(24, 8))
        var = tk.StringVar()
        e = tk.Entry(win, textvariable=var, show="•", font=(FONT_UI, 11),
                     bg=p["entry_bg"], fg=p["fg"], bd=0, highlightthickness=1,
                     highlightbackground=p["border"])
        e.pack(ipady=6, padx=30, fill="x")
        tip = tk.Label(win, text="", font=(FONT_UI, 9), fg=p["red"], bg=p["panel"])
        tip.pack(pady=4)
        e.focus_set()

        def ok():
            if debug.verify_password(var.get()):
                self.app.data["session"] = {"user": "开发者", "mode": "debug"}
                debug.set_enabled(True)
                win.destroy()
                self.app.show("debug_menu")
            else:
                tip.configure(text="口令错误")
        ThemedButton(win, p, "进入", ok, variant="primary").pack(pady=(4, 16))
        e.bind("<Return>", lambda ev: ok())


# ============================================================
#  协议页
# ============================================================
class AgreementView(tk.Frame):
    def __init__(self, master, app, user, back):
        super().__init__(master, bg=app.p["bg"])
        self.app, self.user, self.back = app, user, back
        p = app.p
        box = tk.Frame(self, bg=p["panel"], highlightthickness=1, highlightbackground=p["border"])
        box.place(relx=0.5, rely=0.5, anchor="center", width=720, height=560)
        title, paras = content.agreement_text()
        tk.Label(box, text=title, font=(FONT_UI, 18, "bold"),
                 bg=p["panel"], fg=p["fg"]).pack(anchor="w", padx=32, pady=(26, 14))
        sc = ScrollPanel(box, p)
        sc.pack(fill="both", expand=True, padx=32)
        for para in paras:
            tk.Label(sc.inner, text=para, font=(FONT_UI, 11), bg=p["panel"], fg=p["fg"],
                     wraplength=630, justify="left", anchor="w").pack(anchor="w", fill="x", pady=6)
        bind_mousewheel(sc.inner, sc.canvas)
        bar = tk.Frame(box, bg=p["panel"])
        bar.pack(fill="x", padx=32, pady=18)
        ThemedButton(bar, p, "暂不使用", lambda: app.show(back), variant="ghost").pack(side="left")
        ThemedButton(bar, p, "同意并继续", self._agree, variant="primary").pack(side="right")

    def _agree(self):
        self.app.accept_agreement(self.user)
        self.app.show("menu")


# ============================================================
#  主菜单
# ============================================================
class MenuView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=app.p["bg"])
        self.app = app
        p = app.p
        user = app.data.get("session", {}).get("user") or "玩家"
        top = tk.Frame(self, bg=p["panel"], height=66)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="AXIOM", font=(FONT_MONO, 18, "bold"),
                 bg=p["panel"], fg=p["accent"]).pack(side="left", padx=28)
        tk.Label(top, text="MODEL K4 / ALPHA 3", font=(FONT_MONO, 9),
                 bg=p["panel"], fg=p["dim"]).pack(side="left", padx=(0, 20))
        tk.Label(top, text="你好，" + user, font=(FONT_UI, 10),
                 bg=p["panel"], fg=p["fg"]).pack(side="right", padx=20)
        tk.Label(top, text="积分 %d" % app.data.get("points", 0), font=(FONT_MONO, 10),
                 bg=p["panel"], fg=p["dim"]).pack(side="right", padx=10)
        ThemedButton(top, p, "网页版", app.open_web, variant="ghost").pack(side="right", padx=6)
        ThemedButton(top, p, "退出登录", self._logout, variant="ghost").pack(side="right", padx=6)

        body = tk.Frame(self, bg=p["bg"])
        body.pack(fill="both", expand=True, padx=48, pady=32)
        cards = [
            ("01", "练 习", "选文 · 5 分钟限时", lambda: app.show("articles")),
            ("02", "人机对战", "5 档难度 · 双进度", lambda: app.show("versus")),
            ("03", "关 卡", "5 类主题 · 共 20 关", lambda: app.show("levels")),
            ("04", "纪 录", "成绩 · 错字本 · 导出", lambda: app.show("records")),
            ("05", "更新日志", "这版有什么", lambda: app.show("changelog")),
            ("06", "设 置", "主题 · 模式 · 调试", lambda: app.show("settings")),
        ]
        for i, (idx, name, desc, cmd) in enumerate(cards):
            card = MenuCard(body, p, idx, name, desc, cmd)
            card.grid(row=i // 3, column=i % 3, sticky="nsew", padx=10, pady=10)
            # 卡片错峰进场：PCL 右栏 25ms 间隔，轻上滑 + 文字淡入
            anim.grid_slide_in(card, p["bg"], p["fg"], delay=i * 30,
                               distance=12, duration=300, geometry="grid",
                               base_pady=(10, 10), ease="out3", fade_color=False)
        for c in range(3):
            body.grid_columnconfigure(c, weight=1, uniform="card")
        for r in range(2):
            body.grid_rowconfigure(r, weight=1, uniform="card")
        tk.Label(self, text="直接敲键盘开始 · Esc 返回 · F11 全屏",
                 font=(FONT_UI, 9), bg=p["bg"], fg=p["dim"]).pack(pady=(0, 16))
        self.bind_all("<F11>", lambda e: self._fullscreen())

    def _fullscreen(self):
        self.app.attributes("-fullscreen", not self.app.attributes("-fullscreen"))

    def _logout(self):
        self.app.data["session"] = {"user": None, "mode": "normal"}
        self.app.persist()
        self.app.show("login")


# ============================================================
#  文章列表 / 选文
# ============================================================
class ArticlesView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=app.p["bg"])
        self.app = app
        p = app.p
        self.category = "全部"
        head = tk.Frame(self, bg=p["panel"], height=60)
        head.pack(fill="x")
        head.pack_propagate(False)
        ThemedButton(head, p, "← 返回", lambda: app.show("menu"), variant="ghost").pack(side="left", padx=18)
        tk.Label(head, text="选 文", font=(FONT_UI, 15, "bold"),
                 bg=p["panel"], fg=p["fg"]).pack(side="left", padx=12)
        self.count_lbl = tk.Label(head, text="", font=(FONT_MONO, 10), bg=p["panel"], fg=p["dim"])
        self.count_lbl.pack(side="right", padx=10)
        ThemedButton(head, p, "导入 JSON / TXT", self._import_file,
                     variant="primary", font_size=9).pack(side="right", padx=18)

        filt = tk.Frame(self, bg=p["bg"])
        filt.pack(fill="x", padx=24, pady=12)
        self.filter_btns = []
        for c in list(CATEGORIES) + ["自定义"]:
            b = ThemedButton(filt, p, c, lambda cc=c: self._filter(cc),
                             variant="ghost", width=6, font_size=9)
            b.pack(side="left", padx=3)
            self.filter_btns.append((c, b))

        self.sc = ScrollPanel(self, p)
        self.sc.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        bind_mousewheel(self.sc.inner, self.sc.canvas)
        self._render()

    def _filter(self, cat):
        self.category = cat
        self._render()

    def _render(self):
        for w in self.sc.inner.winfo_children():
            w.destroy()
        p = self.app.p
        favs = self.app.data.get("favorites", [])
        custom = importer.load_custom(storage.DATA_DIR) + getattr(self.app, "_memory_custom", [])
        if self.category == "自定义":
            arts = custom
        elif self.category == "全部":
            arts = list(ARTICLES) + custom
        else:
            arts = content.articles(self.category, favorites=favs)
        self.count_lbl.configure(text="%d 篇" % len(arts))
        for a in arts:
            row = tk.Frame(self.sc.inner, bg=p["panel"], highlightthickness=1,
                           highlightbackground=p["border"])
            row.pack(fill="x", pady=4)
            star = "★" if a["id"] in favs else "☆"
            tk.Button(row, text=star, font=(FONT_UI, 15), bd=0, cursor="hand2",
                      bg=p["panel"], fg=p["orange"] if a["id"] in favs else p["dim"],
                      command=lambda aid=a["id"]: self._fav(aid)).pack(side="left", padx=(14, 6))
            info = tk.Frame(row, bg=p["panel"])
            info.pack(side="left", fill="x", expand=True, pady=10)
            tk.Label(info, text=a["title"], font=(FONT_UI, 12, "bold"),
                     bg=p["panel"], fg=p["fg"]).pack(anchor="w")
            tk.Label(info, text="%s · %d 字 · %s" % (a["category"], len(a["text"]),
                     " ".join(a["tags"])), font=(FONT_UI, 9),
                     bg=p["panel"], fg=p["dim"]).pack(anchor="w", pady=(3, 0))
            ThemedButton(row, p, "开始练习", lambda aa=a: self.app.start_typing(
                aa["text"], aa["title"], "练习", "articles"), variant="primary").pack(side="right", padx=14)
            # 列表项错峰进场（最多 14 项，避免长列表动画堆积）
            if anim.ENABLED and len(arts) <= 30:
                ai = arts.index(a)
                if ai < 14:
                    anim.grid_slide_in(row, p["bg"], p["fg"], delay=ai * 18,
                                       distance=8, duration=260, geometry="pack",
                                       base_pady=4, fade_color=False)

    def _fav(self, aid):
        favs = self.app.data.setdefault("favorites", [])
        if aid in favs:
            favs.remove(aid)
        else:
            favs.append(aid)
        self.app.persist()
        self._render()

    def _import_file(self):
        path = filedialog.askopenfilename(
            title="导入练习文本",
            filetypes=[("文本/JSON", "*.json *.txt"), ("JSON", "*.json"), ("TXT", "*.txt")])
        if not path:
            return
        # 无痕/调试会话不落盘：仅本次会话内存可用
        no_store = self.app.data.get("session", {}).get("mode") in ("incognito", "debug")
        try:
            items = importer.parse_file(path)
        except Exception as e:
            messagebox.showerror("导入失败", str(e))
            return
        if no_store:
            self.app.toast("当前会话不落盘：导入 %d 篇（仅本次可用）" % len(items))
        else:
            existing = importer.load_custom(storage.DATA_DIR)
            # 用 文件名+序号 去重，重复导入覆盖
            existing = [x for x in existing if x["id"] not in {i["id"] for i in items}]
            importer.save_custom(storage.DATA_DIR, existing + items)
            self.app.toast("已导入 %d 篇" % len(items))
        self.app._memory_custom = (getattr(self.app, "_memory_custom", []) + items) if no_store else []
        self.category = "自定义"
        self._render()


# ============================================================
#  打字页（核心：逐字着色 + 输入 + 实体按钮 + 对战 HUD）
# ============================================================
class TypingView(tk.Frame):
    def __init__(self, master, app, text, title, mode="练习", back="menu",
                 difficulty_index=None, agent_count=None):
        super().__init__(master, bg=app.p["bg"])
        self.app = app
        self.p = app.p
        self.text = text
        self.mode = mode
        self.back = back
        self.idx = 0
        self.correct = 0
        self.wrong = 0
        self.mistakes = {}
        self.start_time = time.time()
        self.finished = False
        self.is_versus = (mode == "人机对战")
        self.difficulty_index = difficulty_index if difficulty_index is not None else app.data.get("difficulty", 3)
        self.agent_count = agent_count or app.data.get("agent_count", 12)

        # 顶栏
        top = tk.Frame(self, bg=self.p["panel"], height=56)
        top.pack(fill="x")
        top.pack_propagate(False)
        ThemedButton(top, self.p, "← 返回", self._quit, variant="ghost").pack(side="left", padx=16)
        tk.Label(top, text=title, font=(FONT_UI, 13, "bold"),
                 bg=self.p["panel"], fg=self.p["fg"]).pack(side="left", padx=8)
        self.timer_lbl = tk.Label(top, text="05:00", font=(FONT_MONO, 20, "bold"),
                                  bg=self.p["panel"], fg=self.p["accent"])
        self.timer_lbl.pack(side="right", padx=20)
        self.progress_lbl = tk.Label(top, text="0 / %d" % len(text), font=(FONT_MONO, 10),
                                     bg=self.p["panel"], fg=self.p["dim"])
        self.progress_lbl.pack(side="right", padx=10)

        # 主体：文字区 + （对战时）HUD
        body = tk.Frame(self, bg=self.p["bg"])
        body.pack(fill="both", expand=True, padx=24, pady=16)
        left = tk.Frame(body, bg=self.p["bg"])
        left.pack(side="left", fill="both", expand=True)

        self.textbox = tk.Text(left, wrap="word", font=(FONT_UI, 17),
                               bg=self.p["panel"], fg=self.p["pending"],
                               bd=0, highlightthickness=1,
                               highlightbackground=self.p["border"],
                               padx=20, pady=18, spacing1=2, spacing3=2)
        self.textbox.pack(fill="both", expand=True)
        self.textbox.insert("1.0", text)
        self.textbox.configure(state="disabled")
        self._setup_tags()
        self._paint(0)

        # 底部实体按钮
        ctrl = tk.Frame(left, bg=self.p["bg"])
        ctrl.pack(fill="x", pady=(10, 0))
        ThemedButton(ctrl, self.p, "开始输入", self._focus, variant="primary").pack(side="left", padx=3)
        ThemedButton(ctrl, self.p, "← 后退", self._back, variant="ghost").pack(side="left", padx=3)
        ThemedButton(ctrl, self.p, "前进 →", self._forward, variant="ghost").pack(side="left", padx=3)
        ThemedButton(ctrl, self.p, "返回", self._quit, variant="ghost").pack(side="left", padx=3)
        ThemedButton(ctrl, self.p, "全屏", self._fullscreen, variant="ghost").pack(side="left", padx=3)
        tk.Label(ctrl, text="打对变绿 · 打错变红", font=(FONT_UI, 9),
                 bg=self.p["bg"], fg=self.p["dim"]).pack(side="right")

        if self.is_versus:
            self._build_hud(body)

        # 隐藏输入域：唯一收字入口（含中文输入法）
        self.entry = tk.Entry(self, font=(FONT_UI, 10), bd=0, bg=self.p["bg"],
                              fg=self.p["bg"], insertwidth=0, width=1,
                              highlightthickness=0, takefocus=1)
        self.entry.place(x=-100, y=-100)
        self.entry.focus_set()
        self._composing = False
        self._timer = None
        self.wrong_positions = []
        self.entry.bind("<KeyPress>", self._on_key)
        self.entry.bind("<KeyRelease>", self._on_keyrelease)
        self.bind_all("<KeyPress>", self._on_global_key)
        self._tick()

    def _setup_tags(self):
        p = self.p
        self.textbox.tag_configure("done", foreground=p["correct"])
        self.textbox.tag_configure("bad", foreground=p["wrong"],
                                   background=p["panel2"])
        self.textbox.tag_configure("cur", foreground=p["fg"],
                                   background=p["accent_soft"],
                                   underline=True)
        self.textbox.tag_configure("todo", foreground=p["pending"])

    def _paint(self, idx):
        self.textbox.configure(state="normal")
        self.textbox.tag_remove("done", "1.0", "end")
        self.textbox.tag_remove("bad", "1.0", "end")
        self.textbox.tag_remove("cur", "1.0", "end")
        self.textbox.tag_remove("todo", "1.0", "end")
        n = len(self.text)
        if n == 0:
            self.textbox.configure(state="disabled")
            return
        if idx > 0:
            self.textbox.tag_add("done", "1.0", "1.0+%dc" % idx)
        if hasattr(self, "wrong_positions"):
            for pos in self.wrong_positions:
                if pos < idx:
                    self.textbox.tag_add("bad", "1.0+%dc" % pos, "1.0+%dc" % (pos + 1))
        if idx < n:
            self.textbox.tag_add("cur", "1.0+%dc" % idx, "1.0+%dc" % (idx + 1))
        self.textbox.tag_add("todo", "1.0+%dc" % min(idx + 1, n), "end")
        self.textbox.configure(state="disabled")
        try:
            self.textbox.see("1.0+%dc" % idx)
            # 把隐藏输入域贴到当前字处：中文输入法候选框会跟随光标出现
            idx_pos = min(idx, n - 1)
            bbox = self.textbox.bbox("1.0+%dc" % idx_pos)
            if bbox:
                tx, ty = bbox[0], bbox[1]
                rootx = self.textbox.winfo_rootx()
                rooty = self.textbox.winfo_rooty()
                self.entry.place(in_=self, x=rootx - self.winfo_rootx() + tx,
                                 y=rooty - self.winfo_rooty() + ty, width=2)
                self.entry.lift()
        except Exception:
            pass
        self.progress_lbl.configure(text="%d / %d" % (self.idx, n))

    def _on_keyrelease(self, e):
        """输入法提交后，Entry 里会留下真实字符：在这里统一收取，避免重复。"""
        if self.finished:
            return
        value = self.entry.get()
        if value:
            self.entry.delete(0, "end")
            for ch in value:
                if ch in ("\n", "\r"):
                    continue
                self._feed(ch)

    def _on_key(self, e):
        """只处理功能键。可打印字符一律交给 Entry 自然录入，由 KeyRelease 统一收取，
        这样英文直输与中文输入法走同一条路径，不会重复也不会漏字。"""
        if self.finished:
            return "break"
        key = e.keysym
        if key in ("BackSpace", "Left"):
            self._back(); return "break"
        if key == "Right":
            self._forward(); return "break"
        if key == "Escape":
            self._quit(); return "break"
        if key == "F11":
            self._fullscreen(); return "break"
        # 可打印字符（含 IME 组合）不拦截，让文字进入 Entry
        return

    def _on_global_key(self, e):
        # 只处理功能键，可打印字符不拦截（保证输入法可用）
        if e.keysym in ("F9", "F10"):
            if e.keysym == "F9":
                self._toggle_debug_overlay()
            else:
                self.app.clipboard_clear()
                self.app.clipboard_append(debug.diagnostics({
                    "view": "typing", "theme": self.app.theme_setting,
                    "open_mode": self.app.data.get("open_mode")}))
                self.app.toast("诊断信息已复制")
            return "break"

    def _feed(self, ch):
        if self.finished or self.idx >= len(self.text):
            return
        expected = self.text[self.idx]
        if ch == expected:
            self.correct += 1
        else:
            self.wrong += 1
            self.mistakes[ch] = self.mistakes.get(ch, 0) + 1
            if not hasattr(self, "wrong_positions"):
                self.wrong_positions = []
            self.wrong_positions.append(self.idx)
        self.idx += 1
        try:
            self.entry.delete(0, "end")
        except Exception:
            pass
        self._paint(self.idx)
        if self.is_versus:
            self._update_hud()
        if self.idx >= len(self.text):
            self._finish()

    def _back(self):
        if self.idx > 0:
            self.idx -= 1
            self.correct = max(0, self.correct - 1)
            if hasattr(self, "wrong_positions") and self.wrong_positions and self.wrong_positions[-1] == self.idx:
                self.wrong_positions.pop()
            self._paint(self.idx)
            if self.is_versus:
                self._update_hud()

    def _forward(self):
        self._focus()

    def _focus(self):
        self.entry.focus_set()

    def _fullscreen(self):
        self.app.attributes("-fullscreen", not self.app.attributes("-fullscreen"))

    def _toggle_debug_overlay(self):
        if not debug.enabled():
            return
        if not hasattr(self, "_overlay"):
            self._overlay = tk.Label(self, text="", font=(FONT_MONO, 10),
                                     bg=self.p["panel"], fg=self.p["fg"], justify="left")
        self._overlay.place(relx=0.99, rely=0.09, anchor="ne")
        self._overlay.configure(text=debug.diagnostics({
            "view": "typing", "theme": self.app.theme_setting,
            "open_mode": self.app.data.get("open_mode")}))

    def _tick(self):
        if self.finished:
            return
        elapsed = int(time.time() - self.start_time)
        left = max(0, TIME_LIMIT - elapsed)
        self.timer_lbl.configure(text="%02d:%02d" % (left // 60, left % 60),
                                 fg=self.p["red"] if left < 60 else self.p["accent"])
        if self.is_versus:
            self._update_hud()
        if left <= 0:
            self._finish()
        else:
            self._timer = self.after(300, self._tick)

    def _build_hud(self, parent):
        hud = tk.Frame(parent, bg=self.p["panel"], width=280,
                       highlightthickness=1, highlightbackground=self.p["border"])
        hud.pack(side="right", fill="y", padx=(16, 0))
        hud.pack_propagate(False)
        tk.Label(hud, text="实时进度", font=(FONT_UI, 12, "bold"),
                 bg=self.p["panel"], fg=self.p["fg"]).pack(anchor="w", padx=14, pady=(14, 8))
        d = difficulty.difficulty(self.difficulty_index)
        self.bot_speeds = difficulty.agent_speeds(self.difficulty_index, self.agent_count)
        # 自己
        self.hud_self_bar = ProgressBar(hud, self.p, width=250, color=self.p["accent"])
        self.hud_self_lbl = tk.Label(hud, text="YOU  0 字  0%", font=(FONT_MONO, 10),
                                     bg=self.p["panel"], fg=self.p["accent"])
        self.hud_self_lbl.pack(anchor="w", padx=14)
        self.hud_self_bar.pack(anchor="w", padx=14, pady=(3, 12))
        tk.Frame(hud, bg=self.p["border"], height=1).pack(fill="x", padx=14, pady=6)
        tk.Label(hud, text="OTHER AGENTS  →", font=(FONT_MONO, 9),
                 bg=self.p["panel"], fg=self.p["dim"]).pack(anchor="e", padx=14, pady=(8, 6))
        self.agent_bars = []
        for i, sp in enumerate(self.bot_speeds):
            row = tk.Frame(hud, bg=self.p["panel"])
            row.pack(fill="x", padx=14, pady=3)
            lbl = tk.Label(row, text="AGENT-%02d  0%%" % (i + 1), font=(FONT_MONO, 8),
                           bg=self.p["panel"], fg=self.p["dim"])
            lbl.pack(anchor="e")
            bar = ProgressBar(row, self.p, width=250, height=5,
                              color=self.p["orange"], from_right=True)
            bar.pack(anchor="e", pady=2)
            self.agent_bars.append({"speed": sp, "label": lbl, "bar": bar})
        self.hud_scroll = hud

    def _update_hud(self):
        if not self.is_versus or not hasattr(self, "hud_self_bar"):
            return
        elapsed = max(0.001, time.time() - self.start_time)
        n = len(self.text)
        my_ratio = self.idx / n if n else 0
        self.hud_self_bar.set(my_ratio)
        self.hud_self_lbl.configure(text="YOU  %d 字  %d%%" % (self.idx, int(my_ratio * 100)))
        for ag in self.agent_bars:
            # speed 单位：字/0.3s -> 字/秒
            chars = ag["speed"] / 0.3 * elapsed
            ratio = min(1.0, chars / n) if n else 0
            ag["bar"].set(ratio)
            ag["label"].configure(text="AGENT-%02d  %d%%" % (
                self.agent_bars.index(ag) + 1, int(ratio * 100)))

    def _finish(self):
        if self.finished:
            return
        self.finished = True
        if self._timer:
            try:
                self.after_cancel(self._timer)
            except Exception:
                pass
        elapsed = max(1, int(time.time() - self.start_time))
        acc = self.correct / max(1, self.correct + self.wrong) * 100
        score = int(self.correct * (acc / 100) * 10)
        speed = self.correct / elapsed
        result = {"mode": self.mode, "score": score, "accuracy": acc,
                  "speed": speed, "elapsed": elapsed,
                  "mistakes": dict(self.mistakes),
                  "grade": self._grade(acc, speed)}
        if self.is_versus:
            d = difficulty.difficulty(self.difficulty_index)
            result["difficulty"] = d["code"]
            # 名次
            beaten = sum(1 for ag in self.agent_bars if self.idx / max(1, len(self.text)) >
                         min(1.0, ag["speed"] / 0.3 * elapsed / max(1, len(self.text))))
            result["rank"] = "%d / %d（胜过 %d 个 Agent）" % (
                len(self.agent_bars) - beaten + 1, len(self.agent_bars) + 1, beaten)
        self.app.finish_typing(result)

    @staticmethod
    def _grade(acc, speed):
        if acc >= 98 and speed >= 4: return "S"
        if acc >= 95 and speed >= 3: return "A"
        if acc >= 90 and speed >= 2: return "B"
        if acc >= 80: return "C"
        return "D"

    def _quit(self):
        self._finish()

    def destroy(self):
        if getattr(self, "_timer", None):
            try:
                self.after_cancel(self._timer)
            except Exception:
                pass
        try:
            self.unbind_all("<KeyPress>")
        except Exception:
            pass
        super().destroy()


# ============================================================
#  人机对战设置（5 档难度滑块 + 选文）
# ============================================================
class VersusSetupView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=app.p["bg"])
        self.app = app
        p = app.p
        self.diff_index = app.data.get("difficulty", 3)
        self.agent_count = app.data.get("agent_count", 12)
        self.selected = 0

        head = tk.Frame(self, bg=p["panel"], height=60)
        head.pack(fill="x")
        head.pack_propagate(False)
        ThemedButton(head, p, "← 返回", lambda: app.show("menu"), variant="ghost").pack(side="left", padx=18)
        tk.Label(head, text="VERSUS / 人机对战", font=(FONT_MONO, 14, "bold"),
                 bg=p["panel"], fg=p["fg"]).pack(side="left", padx=12)

        body = tk.Frame(self, bg=p["bg"])
        body.pack(fill="both", expand=True, padx=40, pady=24)

        # 左：难度
        left = tk.Frame(body, bg=p["panel"], highlightthickness=1, highlightbackground=p["border"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))
        tk.Label(left, text="推理强度 / REASONING EFFORT", font=(FONT_MONO, 10),
                 bg=p["panel"], fg=p["dim"]).pack(anchor="w", padx=24, pady=(24, 6))
        self.code_lbl = tk.Label(left, text="", font=(FONT_MONO, 30, "bold"),
                                 bg=p["panel"], fg=p["accent"])
        self.code_lbl.pack(anchor="w", padx=24)
        self.desc_lbl = tk.Label(left, text="", font=(FONT_UI, 11),
                                 bg=p["panel"], fg=p["fg"])
        self.desc_lbl.pack(anchor="w", padx=24, pady=(4, 20))

        self.scale = tk.Scale(left, from_=1, to=5, orient="horizontal",
                              command=self._on_scale, bg=p["panel"], fg=p["fg"],
                              troughcolor=p["panel2"], activebackground=p["accent"],
                              highlightthickness=0, length=420, width=12,
                              showvalue=False)
        from tkinter import ttk as _ttk
        self.scale.set(self.diff_index + 1)
        self.scale.pack(padx=24, fill="x")
        ticks = tk.Frame(left, bg=p["panel"])
        ticks.pack(fill="x", padx=24)
        for d in difficulty.DIFFICULTIES:
            tk.Label(ticks, text=d["code"].upper(), font=(FONT_MONO, 8),
                     bg=p["panel"], fg=p["dim"]).pack(side="left", expand=True)

        tk.Label(left, text="对手数量", font=(FONT_UI, 10), bg=p["panel"],
                 fg=p["dim"]).pack(anchor="w", padx=24, pady=(24, 6))
        cntrow = tk.Frame(left, bg=p["panel"])
        cntrow.pack(anchor="w", padx=24)
        self.count_btns = []
        for c in difficulty.AGENT_COUNTS:
            b = ThemedButton(cntrow, p, str(c), lambda cc=c: self._set_count(cc),
                             variant="ghost", width=4)
            b.pack(side="left", padx=3)
            self.count_btns.append((c, b))
        self._set_count(self.agent_count)
        tk.Label(left, text="对手进度在右侧与你同屏；速度随难度单调递增。",
                 font=(FONT_UI, 9), bg=p["panel"], fg=p["dim"]).pack(anchor="w", padx=24, pady=18)

        # 右：选文
        right = tk.Frame(body, bg=p["panel"], highlightthickness=1, highlightbackground=p["border"], width=380)
        right.pack(side="right", fill="both")
        right.pack_propagate(False)
        tk.Label(right, text="选择练习文章", font=(FONT_UI, 11, "bold"),
                 bg=p["panel"], fg=p["fg"]).pack(anchor="w", padx=18, pady=(20, 8))
        sc = ScrollPanel(right, p)
        sc.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        bind_mousewheel(sc.inner, sc.canvas)
        for i, a in enumerate(ARTICLES[:12]):
            row = tk.Frame(sc.inner, bg=p["panel"], highlightthickness=1,
                           highlightbackground=p["border"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=a["title"], font=(FONT_UI, 10), bg=p["panel"],
                     fg=p["fg"]).pack(side="left", padx=12, pady=8)
            tk.Label(row, text="%d 字" % len(a["text"]), font=(FONT_MONO, 8),
                     bg=p["panel"], fg=p["dim"]).pack(side="right", padx=10)
            row.bind("<Button-1>", lambda e, ii=i: self._select(ii))
            for w in row.winfo_children():
                w.bind("<Button-1>", lambda e, ii=i: self._select(ii))
        self._select(0)
        ThemedButton(right, p, "开始对战", self._start, variant="primary").pack(fill="x", padx=18, pady=(0, 18))

    def _on_scale(self, val):
        self.diff_index = int(float(val)) - 1
        d = difficulty.difficulty(self.diff_index)
        self.code_lbl.configure(text="%02d / %s" % (self.diff_index + 1, d["code"].upper()))
        self.desc_lbl.configure(text="%s · %.1f–%.1f 字/秒 · %s" %
                                (d["label"], d["min"], d["max"], d["desc"]))

    def _set_count(self, c):
        self.agent_count = c
        for n, b in self.count_btns:
            bg, fg = (self.app.p["accent"], "#ffffff") if n == c else (self.app.p["panel2"], self.app.p["fg"])
            b.configure(bg=bg, fg=fg)

    def _select(self, i):
        self.selected = i
        sc = self
        for w in self.winfo_children():
            pass

    def _start(self):
        a = ARTICLES[self.selected]
        self.app.data["difficulty"] = self.diff_index
        self.app.data["agent_count"] = self.agent_count
        self.app.persist()
        self.app.start_typing(a["text"], "VERSUS · " + a["title"],
                              "人机对战", "versus",
                              difficulty_index=self.diff_index,
                              agent_count=self.agent_count)


# ============================================================
#  关卡
# ============================================================
class LevelsView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=app.p["bg"])
        self.app = app
        p = app.p
        head = tk.Frame(self, bg=p["panel"], height=60)
        head.pack(fill="x")
        head.pack_propagate(False)
        ThemedButton(head, p, "← 返回", lambda: app.show("menu"), variant="ghost").pack(side="left", padx=18)
        tk.Label(head, text="关 卡", font=(FONT_UI, 15, "bold"), bg=p["panel"],
                 fg=p["fg"]).pack(side="left", padx=12)
        sc = ScrollPanel(self, p)
        sc.pack(fill="both", expand=True, padx=40, pady=20)
        bind_mousewheel(sc.inner, sc.canvas)
        user = app.data.get("session", {}).get("user", "")
        unlocked = set(app.data.get("users", {}).get(user, {}).get("unlocked", []))
        for lv in content.LEVELS:
            row = tk.Frame(sc.inner, bg=p["panel"], highlightthickness=1,
                           highlightbackground=p["border"])
            row.pack(fill="x", pady=4)
            ok = lv["id"] in unlocked or lv["segment"] == 1
            tk.Label(row, text=("✓" if ok else "○") + " " + lv["id"], font=(FONT_MONO, 10),
                     bg=p["panel"], fg=p["accent"] if ok else p["dim"]).pack(side="left", padx=16, pady=12)
            tk.Label(row, text=lv["title"], font=(FONT_UI, 11), bg=p["panel"],
                     fg=p["fg"]).pack(side="left", padx=10)
            if ok:
                ThemedButton(row, p, "进入", lambda l=lv: app.start_typing(
                    l["text"], l["title"], "关卡", "levels"), variant="primary").pack(side="right", padx=16)
            else:
                tk.Label(row, text="上一关达 C 级解锁", font=(FONT_UI, 9),
                         bg=p["panel"], fg=p["dim"]).pack(side="right", padx=16)


# ============================================================
#  纪录 / 错字本 / 导出
# ============================================================
class RecordsView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=app.p["bg"])
        self.app = app
        p = app.p
        head = tk.Frame(self, bg=p["panel"], height=60)
        head.pack(fill="x")
        head.pack_propagate(False)
        ThemedButton(head, p, "← 返回", lambda: app.show("menu"), variant="ghost").pack(side="left", padx=18)
        tk.Label(head, text="纪 录", font=(FONT_UI, 15, "bold"), bg=p["panel"],
                 fg=p["fg"]).pack(side="left", padx=12)
        ThemedButton(head, p, "导出 CSV", self._export, variant="primary").pack(side="right", padx=18)

        sc = ScrollPanel(self, p)
        sc.pack(fill="both", expand=True, padx=40, pady=20)
        bind_mousewheel(sc.inner, sc.canvas)
        recs = list(reversed(app.data.get("records", [])))
        tk.Label(sc.inner, text="历史成绩（%d 条）" % len(recs), font=(FONT_UI, 12, "bold"),
                 bg=p["bg"], fg=p["fg"]).pack(anchor="w", pady=(4, 10))
        for r in recs[:50]:
            line = "%s · %s · %d 分 · 正确率 %.1f%% · %s" % (
                r.get("time", time.strftime("%m-%d")), r.get("mode", "练习"),
                r.get("score", 0), r.get("accuracy", 0), r.get("grade", "—"))
            tk.Label(sc.inner, text=line, font=(FONT_MONO, 10), bg=p["panel"],
                     fg=p["fg"], anchor="w").pack(fill="x", pady=2)

        mistakes = app.data.get("mistakes", {})
        tk.Label(sc.inner, text="错字本（%d 字）" % len(mistakes), font=(FONT_UI, 12, "bold"),
                 bg=p["bg"], fg=p["fg"]).pack(anchor="w", pady=(20, 10))
        if mistakes:
            top = sorted(mistakes.items(), key=lambda x: -x[1])[:30]
            tk.Label(sc.inner, text="  ".join("%s×%d" % (c, n) for c, n in top),
                     font=(FONT_UI, 11), bg=p["panel"], fg=p["fg"],
                     wraplength=760, justify="left").pack(fill="x", pady=4)
        else:
            tk.Label(sc.inner, text="暂无错字记录", font=(FONT_UI, 10),
                     bg=p["bg"], fg=p["dim"]).pack(anchor="w")

    def _export(self):
        path = filedialog.asksaveasfilename(
            title="导出成绩 CSV", defaultextension=".csv",
            filetypes=[("CSV", "*.csv")], initialfile="axiom_scores.csv")
        if not path:
            return
        try:
            import csv
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["日期", "模式", "难度", "分数", "等级", "准确率", "速度"])
                for r in self.app.data.get("records", []):
                    w.writerow([r.get("time", ""), r.get("mode", ""), r.get("difficulty", ""),
                                r.get("score", 0), r.get("grade", ""),
                                "%.1f" % r.get("accuracy", 0), "%.2f" % r.get("speed", 0)])
            self.app.toast("已导出 %d 条成绩" % len(self.app.data.get("records", [])))
        except Exception as e:
            messagebox.showerror("导出失败", str(e))


# ============================================================
#  更新日志
# ============================================================
class ChangelogView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=app.p["bg"])
        p = app.p
        head = tk.Frame(self, bg=p["panel"], height=60)
        head.pack(fill="x")
        head.pack_propagate(False)
        ThemedButton(head, p, "← 返回", lambda: app.show("menu"), variant="ghost").pack(side="left", padx=18)
        tk.Label(head, text="更新日志", font=(FONT_UI, 15, "bold"), bg=p["panel"],
                 fg=p["fg"]).pack(side="left", padx=12)
        sc = ScrollPanel(self, p)
        sc.pack(fill="both", expand=True, padx=48, pady=20)
        bind_mousewheel(sc.inner, sc.canvas)
        for entry in content.CHANGELOG:
            card = tk.Frame(sc.inner, bg=p["panel"], highlightthickness=1,
                            highlightbackground=p["border"])
            card.pack(fill="x", pady=8)
            tk.Label(card, text=entry["version"] + "  ·  " + entry["date"],
                     font=(FONT_MONO, 14, "bold"), bg=p["panel"], fg=p["accent"]).pack(anchor="w", padx=20, pady=(16, 8))
            for kind, label in (("added", "新增"), ("changed", "调整"), ("fixed", "修复")):
                if not entry.get(kind):
                    continue
                tk.Label(card, text=label, font=(FONT_UI, 10, "bold"),
                         bg=p["panel"], fg=p["orange"]).pack(anchor="w", padx=20, pady=(8, 2))
                for item in entry[kind]:
                    tk.Label(card, text="  · " + item, font=(FONT_UI, 10),
                             bg=p["panel"], fg=p["fg"], wraplength=880,
                             justify="left", anchor="w").pack(anchor="w", padx=24, pady=1)
            tk.Frame(card, height=12, bg=p["panel"]).pack()


# ============================================================
#  设置
# ============================================================
class SettingsView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=app.p["bg"])
        self.app = app
        p = app.p
        head = tk.Frame(self, bg=p["panel"], height=60)
        head.pack(fill="x")
        head.pack_propagate(False)
        ThemedButton(head, p, "← 返回", lambda: app.show("menu"), variant="ghost").pack(side="left", padx=18)
        tk.Label(head, text="设 置", font=(FONT_UI, 15, "bold"), bg=p["panel"],
                 fg=p["fg"]).pack(side="left", padx=12)
        sc = ScrollPanel(self, p)
        sc.pack(fill="both", expand=True, padx=48, pady=20)
        bind_mousewheel(sc.inner, sc.canvas)

        # 主题
        sec(sc.inner, p, "外观主题", "浅色 / 深色 / 跟随系统")
        row = tk.Frame(sc.inner, bg=p["bg"])
        row.pack(anchor="w", padx=16)
        self.theme_btns = []
        for key in theme.THEMES:
            b = ThemedButton(row, p, theme.THEME_LABELS[key], lambda k=key: self._theme(k),
                             variant="ghost", width=8)
            b.pack(side="left", padx=4)
            self.theme_btns.append((key, b))
        self._sync_theme_btns()

        # 打开模式
        sec(sc.inner, p, "打开模式", "决定布局与存档介质；三种模式都写入存档")
        row = tk.Frame(sc.inner, bg=p["bg"])
        row.pack(anchor="w", padx=16)
        modes = [("exe", "exe 打开模式"), ("html", "html 打开模式"), ("mobile", "手机端打开模式")]
        self.mode_btns = []
        for key, label in modes:
            b = ThemedButton(row, p, label, lambda k=key: self._mode(k),
                             variant="ghost", width=14)
            b.pack(side="left", padx=4)
            self.mode_btns.append((key, b))
        self._sync_mode_btns()

        # 标点
        sec(sc.inner, p, "标点开关", "练习文本是否包含标点符号")
        Toggle(sc.inner, p, app.data.get("punct", True),
               lambda v: self._set("punct", v)).pack(anchor="w", padx=16)

        # 调试
        sec(sc.inner, p, "调试模式", "固定口令进入；F9 覆盖层 / F10 复制诊断")
        trow = tk.Frame(sc.inner, bg=p["bg"])
        trow.pack(anchor="w", padx=16)
        self.debug_toggle = Toggle(trow, p, debug.enabled(), self._toggle_debug)
        self.debug_toggle.pack(side="left")
        ThemedButton(sc.inner, p, "诊断信息", lambda: messagebox.showinfo(
            "诊断信息", debug.diagnostics({
                "view": "settings", "theme": app.theme_setting,
                "open_mode": app.data.get("open_mode"),
                "data_file": storage.data_file_path(),
                "articles": len(ARTICLES)})), variant="ghost").pack(anchor="w", padx=16, pady=8)

        # 旧档导入
        sec(sc.inner, p, "从 Alpha2 导入", "只读导入旧账号；旧文件不会被修改")
        ThemedButton(sc.inner, p, "检查并导入旧档", self._import_old,
                     variant="ghost").pack(anchor="w", padx=16, pady=8)

        # 网页 / 源码
        sec(sc.inner, p, "网页与源码", "打开在线版 / 源码仓库")
        brow = tk.Frame(sc.inner, bg=p["bg"])
        brow.pack(anchor="w", padx=16)
        ThemedButton(brow, p, "打开网页版", app.open_web, variant="primary").pack(side="left", padx=4)
        ThemedButton(brow, p, "下载源码", self._source, variant="ghost").pack(side="left", padx=4)

        tk.Label(sc.inner, text="AXIOM · Model K4 / Alpha 3   |   含 AI 生成内容，请注意辨别",
                 font=(FONT_UI, 9), bg=p["bg"], fg=p["dim"]).pack(anchor="w", padx=16, pady=(30, 10))

    def _set(self, key, value):
        self.app.data[key] = value
        self.app.persist()

    def _theme(self, key):
        self.app.theme_setting = key
        self.app.data["theme"] = key
        self.app.persist()
        self._sync_theme_btns()
        self.app.rebuild()

    def _sync_theme_btns(self):
        p = self.app.p
        for k, b in self.theme_btns:
            active = k == self.app.theme_setting
            b.configure(bg=p["accent"] if active else p["panel2"],
                        fg="#ffffff" if active else p["fg"])

    def _mode(self, key):
        self.app.data["open_mode"] = key
        self.app.persist()
        self._sync_mode_btns()
        self.app.toast("已切换为" + key + " 打开模式")

    def _sync_mode_btns(self):
        p = self.app.p
        cur = self.app.data.get("open_mode", "exe")
        for k, b in self.mode_btns:
            active = k == cur
            b.configure(bg=p["accent"] if active else p["panel2"],
                        fg="#ffffff" if active else p["fg"])

    def _toggle_debug(self, value):
        if value:
            if not self._ask_password():
                self.debug_toggle.set(False, silent=True)
                return
            debug.set_enabled(True)
        else:
            debug.set_enabled(False)
        self._set("debug", debug.enabled())

    def _ask_password(self):
        win = tk.Toplevel(self.app)
        win.title("验证调试口令")
        win.configure(bg=self.app.p["panel"])
        win.geometry("320x160")
        win.transient(self.app)
        p = self.app.p
        tk.Label(win, text="输入调试口令", font=(FONT_UI, 11),
                 bg=p["panel"], fg=p["fg"]).pack(pady=(22, 8))
        var = tk.StringVar()
        e = tk.Entry(win, textvariable=var, show="•", font=(FONT_UI, 11),
                     bg=p["entry_bg"], fg=p["fg"], bd=0, highlightthickness=1,
                     highlightbackground=p["border"])
        e.pack(ipady=6, padx=28, fill="x")
        e.focus_set()
        result = {"ok": False}

        def ok():
            if debug.verify_password(var.get()):
                result["ok"] = True
                win.destroy()
            else:
                messagebox.showerror("AXIOM", "口令错误", parent=win)
        ThemedButton(win, p, "确定", ok, variant="primary").pack(pady=12)
        e.bind("<Return>", lambda ev: ok())
        self.app.wait_window(win)
        return result["ok"]

    def _import_old(self):
        ok, msg = storage.import_old()
        messagebox.showinfo("导入旧档", msg)
        if ok:
            self.app.data = storage.load()

    def _source(self):
        import webbrowser
        cfg = {}
        try:
            with open(os.path.join(RES_DIR, "config.json"), "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            pass
        webbrowser.open(cfg.get("source_url", "https://github.com/czy-cmd/AXIOM-K4"))


def sec(parent, p, title, desc):
    tk.Label(parent, text=title, font=(FONT_UI, 12, "bold"),
             bg=p["bg"], fg=p["fg"]).pack(anchor="w", pady=(18, 2))
    tk.Label(parent, text=desc, font=(FONT_UI, 9),
             bg=p["bg"], fg=p["dim"]).pack(anchor="w", pady=(0, 8))


# ============================================================
#  调试会话菜单（无存储）
# ============================================================
class DebugMenuView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=app.p["bg"])
        self.app = app
        p = app.p
        top = tk.Frame(self, bg=p["brand_bg"], height=64)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="AXIOM / DEBUG SESSION", font=(FONT_MONO, 14, "bold"),
                 bg=p["brand_bg"], fg=p["brand_fg"]).pack(side="left", padx=24)
        tk.Label(top, text="无存储 · 仅练习与人机对战", font=(FONT_UI, 10),
                 bg=p["brand_bg"], fg=p["brand_dim"]).pack(side="right", padx=24)

        body = tk.Frame(self, bg=p["bg"])
        body.pack(fill="both", expand=True, padx=48, pady=32)
        cards = [
            ("01", "练 习", "选文 · 5 分钟限时", lambda: app.show("articles")),
            ("02", "人机对战", "5 档难度 · 双进度", lambda: app.show("versus")),
        ]
        for i, (idx, name, desc, cmd) in enumerate(cards):
            MenuCard(body, p, idx, name, desc, cmd).grid(row=0, column=i, sticky="nsew", padx=10, pady=10)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        panel = tk.Frame(self, bg=p["panel"], highlightthickness=1, highlightbackground=p["border"])
        panel.pack(fill="x", padx=48, pady=(0, 32))
        tk.Label(panel, text="DEVELOPER PANEL", font=(FONT_MONO, 11, "bold"),
                 bg=p["panel"], fg=p["accent"]).pack(anchor="w", padx=20, pady=(16, 6))
        tk.Label(panel, text=debug.diagnostics({"view": "debug_menu", "theme": app.theme_setting}),
                 font=(FONT_MONO, 9), bg=p["panel"], fg=p["dim"],
                 justify="left", anchor="w").pack(anchor="w", padx=20)
        ThemedButton(panel, p, "导出 log", self._export_log, variant="primary").pack(anchor="w", padx=20, pady=(10, 18))

    def _export_log(self):
        path = filedialog.asksaveasfilename(title="导出调试日志", defaultextension=".log",
                                            filetypes=[("LOG", "*.log")], initialfile="k4_debug.log")
        if path:
            debug.export_log(path)
            self.app.toast("日志已导出")


# ============================================================
#  入口
# ============================================================
def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
