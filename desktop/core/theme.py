# -*- coding: utf-8 -*-
"""AXIOM · 三主题色板 + Windows 系统主题探测（纯标准库）"""
import ctypes
import tkinter as tk

THEMES = ("light", "dark", "system")
THEME_LABELS = {"light": "浅色", "dark": "深色", "system": "跟随系统"}

# 色板：所有 UI 颜色从这里取，禁止在 ui/ 与 app.py 里硬编码
PALETTES = {
    "light": {
        "bg": "#f6f4ee", "panel": "#ffffff", "panel2": "#eeeae0",
        "fg": "#2a2a32", "dim": "#8c8c99", "border": "#ddd7c8",
        "accent": "#12a150", "accent_soft": "#e3f5ea",
        "orange": "#e8830c", "red": "#e5484d", "blue": "#2f6fdb",
        "pending": "#9a9aa8", "correct": "#12a150", "wrong": "#e5484d",
        "skip": "#e8830c", "brand_bg": "#1f2429", "brand_fg": "#f4f4f6",
        "brand_dim": "#8b949e", "shadow": "#d8d3c6",
        "entry_bg": "#ffffff", "hover": "#f0ede4",
    },
    "dark": {
        "bg": "#14171b", "panel": "#1c2026", "panel2": "#242a31",
        "fg": "#e6e8eb", "dim": "#8b949e", "border": "#303841",
        "accent": "#3ddc84", "accent_soft": "#1b3528",
        "orange": "#e8a33d", "red": "#f0646a", "blue": "#5b9cff",
        "pending": "#6b7480", "correct": "#3ddc84", "wrong": "#f0646a",
        "skip": "#e8a33d", "brand_bg": "#0d1013", "brand_fg": "#f4f4f6",
        "brand_dim": "#6b7480", "shadow": "#0a0c0f",
        "entry_bg": "#111418", "hover": "#262d35",
    },
}

FONT_UI = "Microsoft YaHei"
FONT_MONO = "Consolas"


def system_is_light():
    """读注册表 AppsUseLightTheme：1=浅色 0=深色；失败默认浅色"""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return int(value) == 1
    except Exception:
        return True


def effective_theme(setting):
    if setting == "system":
        return "light" if system_is_light() else "dark"
    return setting if setting in PALETTES else "light"


def get_palette(setting):
    return PALETTES[effective_theme(setting)]


def apply_palette(widget, p):
    """递归给控件树刷色（保守：只设置已知支持的选项）"""
    try:
        widget.configure(bg=p["bg"])
    except Exception:
        pass
    for child in widget.winfo_children():
        _apply_child(child, p)


def _apply_child(w, p):
    kind = w.winfo_class()
    opts = set()
    try:
        opts = set(w.configure().keys())
    except Exception:
        pass
    cfg = {}
    if "background" in opts:
        if kind in ("Entry", "TEntry"):
            cfg["background"] = p["entry_bg"]
        elif kind in ("Button", "TButton"):
            cfg["background"] = p["panel2"]
        else:
            cfg["background"] = p["panel"]
    if "foreground" in opts:
        cfg["foreground"] = p["fg"]
    if "borderwidth" in opts and kind in ("Frame", "LabelFrame"):
        pass
    if cfg:
        try:
            w.configure(**cfg)
        except Exception:
            pass
    if "insertbackground" in opts:
        try:
            w.configure(insertbackground=p["fg"])
        except Exception:
            pass
    for c in w.winfo_children():
        _apply_child(c, p)
