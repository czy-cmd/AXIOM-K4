# -*- coding: utf-8 -*-
"""AXIOM · 通用控件：主题按钮、菜单卡片、进度轨、开关、滚动面板"""
import tkinter as tk
from tkinter import ttk

from core.theme import FONT_UI, FONT_MONO


class ThemedButton(tk.Button):
    """统一按钮：primary / ghost / danger 三种样式，颜色取自 palette"""
    def __init__(self, master, p, text="", command=None, variant="ghost",
                 width=None, height=None, font_size=10, **kw):
        self.variant = variant
        self.p = p
        self._base = {
            "primary": (p["accent"], "#ffffff" if p is not None else "#fff"),
            "ghost": (p["panel2"], p["fg"]),
            "danger": (p["red"], "#ffffff"),
        }.get(variant, (p["panel2"], p["fg"]))
        super().__init__(
            master, text=text, command=command,
            font=(FONT_UI, font_size), bd=0, relief="flat",
            bg=self._base[0], fg=self._base[1],
            activebackground=p["hover"], activeforeground=p["fg"],
            cursor="hand2", padx=14, pady=7,
            width=width, height=height, **kw)
        # PCL 风格按下反馈：按下快、松开渐变回弹
        self.bind("<ButtonPress-1>", self._anim_press, add="+")

    def recolor(self, p):
        self.p = p
        bg, fg = {
            "primary": (p["accent"], "#ffffff"),
            "ghost": (p["panel2"], p["fg"]),
            "danger": (p["red"], "#ffffff"),
        }.get(self.variant, (p["panel2"], p["fg"]))
        self._base = (bg, fg)
        self.configure(bg=bg, fg=fg, activebackground=p["hover"], activeforeground=p["fg"])

    def _anim_press(self, _=None):
        """按下快(80ms)：颜色瞬时加深；松开慢回弹(300ms)：渐变回原色。"""
        try:
            from ui import anim
            if not anim.ENABLED:
                return
            bg, fg = self._base
            # 加深：同时改 bg 与 activebackground（后者防止 tk.Button 内建 active 态覆盖）
            deep = anim.mix(bg, "#000000", 0.18)
            self._press_bg = deep
            self.configure(bg=deep, activebackground=deep)
            self.after(90, lambda: self._anim_release() if self.winfo_exists() else None)
        except Exception:
            pass

    def _anim_release(self):
        try:
            from ui import anim
            from core import theme
            bg, fg = self._base
            hover = self.p["hover"]
            deep = getattr(self, "_press_bg", anim.mix(bg, "#000000", 0.18))
            total = 260
            import time as _t
            start = _t.perf_counter()

            def step():
                if not self.winfo_exists():
                    return
                t = min(1.0, (_t.perf_counter() - start) * 1000 / total)
                e = 1 - (1 - t) ** 3
                cur = anim.mix(deep, bg, e)
                self.configure(bg=cur, activebackground=anim.mix(deep, hover, e))
                if t < 1.0:
                    self.after(16, step)
                else:
                    self.configure(bg=bg, activebackground=hover)
            self.after(16, step)
        except Exception:
            pass


class MenuCard(tk.Frame):
    """主菜单卡片：序号 + 名称 + 描述"""
    def __init__(self, master, p, index, name, desc, command=None):
        super().__init__(master, bg=p["panel"], highlightthickness=1,
                         highlightbackground=p["border"], cursor="hand2")
        self.p = p
        tk.Label(self, text=index, font=(FONT_MONO, 11), fg=p["dim"],
                 bg=p["panel"]).grid(row=0, column=0, sticky="nw", padx=18, pady=(16, 0))
        tk.Label(self, text=name, font=(FONT_UI, 16, "bold"), fg=p["fg"],
                 bg=p["panel"]).grid(row=0, column=0, sticky="w", padx=18, pady=(34, 0))
        tk.Label(self, text=desc, font=(FONT_UI, 9), fg=p["dim"],
                 bg=p["panel"]).grid(row=0, column=0, sticky="sw", padx=18, pady=(0, 16))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        if command:
            for w in (self, *self.winfo_children()):
                w.bind("<Button-1>", lambda e: command())
        self.bind("<Enter>", lambda e: self.configure(bg=p["hover"]))
        self.bind("<Leave>", lambda e: self.configure(bg=p["panel"]))

    def recolor(self, p):
        self.configure(bg=p["panel"], highlightbackground=p["border"])
        for c in self.winfo_children():
            if isinstance(c, tk.Label):
                c.configure(bg=p["panel"])


class ProgressBar(tk.Canvas):
    """进度轨：from_right=True 时从右向左生长（对手用）"""
    def __init__(self, master, p, width=280, height=8, color=None, from_right=False, **kw):
        super().__init__(master, width=width, height=height, bg=p["panel2"],
                         highlightthickness=0, bd=0, **kw)
        self.p = p
        self.color = color or p["accent"]
        self.from_right = from_right
        self._ratio = 0.0
        self._bar = self.create_rectangle(0, 0, 0, height, fill=self.color, outline="")

    def set(self, ratio):
        self._ratio = max(0.0, min(1.0, float(ratio)))
        w = float(self.winfo_width() or self["width"])
        h = float(self.winfo_height() or self["height"])
        span = self._ratio * w
        if self.from_right:
            self.coords(self._bar, w - span, 0, w, h)
        else:
            self.coords(self._bar, 0, 0, span, h)

    def recolor(self, p, color=None):
        self.p = p
        self.configure(bg=p["panel2"])
        self.color = color or p["accent"]
        self.itemconfigure(self._bar, fill=self.color)
        self.set(self._ratio)


class Toggle(tk.Frame):
    """开关：[ 关 | 开 ] 两段式，点击切换"""
    def __init__(self, master, p, value=False, command=None, labels=("关", "开")):
        super().__init__(master, bg=p["panel"])
        self.p = p
        self.value = bool(value)
        self.command = command
        self.labels = labels
        self.buttons = []
        for i, lab in enumerate(labels):
            b = tk.Label(self, text=lab, font=(FONT_UI, 9), padx=12, pady=4, cursor="hand2")
            b.grid(row=0, column=i, padx=1)
            b.bind("<Button-1>", lambda e, idx=i: self.set(idx == 1))
            self.buttons.append(b)
        self.set(self.value, silent=True)

    def set(self, value, silent=False):
        self.value = bool(value)
        for i, b in enumerate(self.buttons):
            active = (i == 1) == self.value
            b.configure(bg=self.p["accent"] if active else self.p["panel2"],
                        fg="#ffffff" if active else self.p["fg"])
        if not silent and self.command:
            self.command(self.value)

    def recolor(self, p):
        self.p = p
        self.set(self.value, silent=True)


class ScrollPanel(tk.Frame):
    """Canvas + Scrollbar 的可滚动内容面板，内含 self.inner"""
    def __init__(self, master, p, **kw):
        super().__init__(master, bg=p["bg"], **kw)
        self.p = p
        self.canvas = tk.Canvas(self, bg=p["bg"], highlightthickness=0, bd=0)
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=p["bg"])
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")
        self.inner.bind("<Configure>", self._on_inner)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.bind_all_mousewheel = False

    def _on_inner(self, e):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, e):
        self.canvas.itemconfigure(self._win, width=e.width)

    def recolor(self, p):
        self.p = p
        self.configure(bg=p["bg"])
        self.canvas.configure(bg=p["bg"])
        self.inner.configure(bg=p["bg"])


def bind_mousewheel(widget, canvas):
    def _wheel(e):
        try:
            canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")
        except Exception:
            pass
    widget.bind_all("<MouseWheel>", _wheel, add="+")
