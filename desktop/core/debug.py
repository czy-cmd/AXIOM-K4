# -*- coding: utf-8 -*-
"""AXIOM · 调试状态、诊断信息与 debug.log（口令来自 difficulty.DEBUG_PASSWORD）"""
import os
import sys
import time
import platform
import tkinter as tk

from . import difficulty

LOG_NAME = "debug.log"
_log_path = None
_buffer = []
_enabled = False


def configure(data_dir):
    global _log_path
    _log_path = os.path.join(data_dir, LOG_NAME)


def enabled():
    return _enabled


def set_enabled(value):
    global _enabled
    _enabled = bool(value)
    if _enabled:
        log("debug mode on")
    return _enabled


def verify_password(text):
    return text.strip() == difficulty.DEBUG_PASSWORD


def log(message):
    if not _enabled:
        return
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), message)
    _buffer.append(line)
    if len(_buffer) > 500:
        del _buffer[0]
    if _log_path:
        try:
            with open(_log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass


def diagnostics(extra=None):
    lines = [
        "AXIOM · Model K4 / Alpha 3 — Diagnostics",
        "time       : " + time.strftime("%Y-%m-%d %H:%M:%S"),
        "python     : " + platform.python_version(),
        "platform   : " + platform.platform(),
        "data_file  : " + str((extra or {}).get("data_file", "-")),
        "articles   : " + str((extra or {}).get("articles", "-")),
        "view       : " + str((extra or {}).get("view", "-")),
        "theme      : " + str((extra or {}).get("theme", "-")),
        "open_mode  : " + str((extra or {}).get("open_mode", "-")),
    ]
    try:
        root = tk._default_root
        if root is not None:
            lines.append("screen     : %dx%d @ %s" % (
                root.winfo_screenwidth(), root.winfo_screenheight(),
                root.winfo_pixels("")))
    except Exception:
        pass
    return "\n".join(lines)


def export_log(target_path):
    """把缓冲区写入用户指定的文件（由调用方弹出保存对话框）"""
    if not _enabled:
        return False
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            f.write("AXIOM K4-Alpha3 DEBUG LOG\n")
            f.write("\n".join(_buffer))
        return True
    except Exception:
        return False
