# -*- coding: utf-8 -*-
"""AXIOM 卸载程序。

- 默认询问是否保留存档，保留则把 data/ 备份到桌面
- 删除快捷方式与 HKCU 卸载注册项
- 删不掉自己：先删其他文件，再把自己挪到 %TEMP%，最后删空目录
  （运行中的 exe 可移动、不可删除；os.replace 对它有效）
- --silent 静默卸载（--keep-data=1 / --force=1）
"""
import ctypes
import os
import shutil
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import messagebox

APP_NAME = "AXIOM"
APP_DISPLAY = "AXIOM · Model K4"
MAIN_EXE = "AXIOM.exe"
DATA_DIRNAME = "data"

BG = "#f6f4ee"
FG = "#2a2a32"
DIM = "#7c7c88"
ACCENT = "#2f6fdb"
ERR = "#c0392b"
FONT = ("Microsoft YaHei", 10)
FONT_S = ("Microsoft YaHei", 9)
FONT_B = ("Microsoft YaHei", 14, "bold")
FONT_MONO = ("Consolas", 9)

INSTALL_DIR = os.path.dirname(os.path.abspath(
    sys.executable if getattr(sys, "frozen", False) else __file__))
ME = os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__)
DESKTOP_LNK = APP_DISPLAY + ".lnk"
MENU_LNKS = [APP_DISPLAY + ".lnk", "卸载 " + APP_DISPLAY + ".lnk"]


def _arg(key, default=""):
    for a in sys.argv[1:]:
        if a.startswith("--" + key + "="):
            return a.split("=", 1)[1]
    return default


def _flag(key):
    return ("--" + key) in sys.argv[1:]


def _shfolder(csidl):
    try:
        buf = ctypes.create_unicode_buffer(260)
        ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buf)
        return buf.value
    except Exception:
        return ""


def is_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq " + MAIN_EXE, "/NH"],
                             capture_output=True, text=True, timeout=15).stdout or ""
        return MAIN_EXE.lower() in out.lower()
    except Exception:
        return False


def backup_data():
    src = os.path.join(INSTALL_DIR, DATA_DIRNAME)
    if not os.path.isdir(src) or not os.listdir(src):
        return None
    dst = os.path.join(_shfolder(0) or os.path.expanduser("~"), "AXIOM_存档备份")
    try:
        os.makedirs(dst, exist_ok=True)
        for fn in os.listdir(src):
            fp = os.path.join(src, fn)
            if os.path.isfile(fp):
                shutil.copy2(fp, os.path.join(dst, fn))
        return dst
    except Exception:
        return None


def remove_shortcuts():
    desktop = _shfolder(0) or os.path.join(os.path.expanduser("~"), "Desktop")
    progs = _shfolder(2) or os.path.join(
        os.environ.get("APPDATA", os.path.expanduser("~")),
        r"Microsoft\Windows\Start Menu\Programs")
    for p in [os.path.join(desktop, DESKTOP_LNK)] + \
             [os.path.join(progs, APP_NAME, n) for n in MENU_LNKS]:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    try:
        sm = os.path.join(progs, APP_NAME)
        if os.path.isdir(sm) and not os.listdir(sm):
            os.rmdir(sm)
    except Exception:
        pass


def remove_registry():
    try:
        import winreg
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
                         r"Software\Microsoft\Windows\CurrentVersion\Uninstall\%s" % APP_NAME)
    except Exception:
        pass


def wipe_install_dir():
    victims = []
    for name in os.listdir(INSTALL_DIR):
        p = os.path.join(INSTALL_DIR, name)
        if os.path.abspath(p) == ME:
            continue
        victims.append(p)
    errors = 0
    for p in victims:
        try:
            if os.path.isdir(p):
                shutil.rmtree(p)
            else:
                os.remove(p)
        except Exception:
            errors += 1

    moved = None
    try:
        moved = os.path.join(tempfile.gettempdir(), "axiom_uninst_%d.exe" % os.getpid())
        os.replace(ME, moved)
    except Exception:
        moved = None

    removed_dir = False
    try:
        os.rmdir(INSTALL_DIR)
        removed_dir = True
    except Exception:
        pass

    if moved:
        try:
            subprocess.Popen(["cmd", "/c", "timeout", "/t", "3", "/nobreak", ">nul",
                              "&", "del", "/f", "/q", moved],
                             creationflags=0x08000000)
        except Exception:
            pass
    return errors, removed_dir


def do_uninstall(keep_data=True, force=False):
    if is_running() and not force:
        return False, "程序正在运行，请先关闭 AXIOM 再卸载。"
    result = {"backup": None, "errors": 0}
    if keep_data:
        result["backup"] = backup_data()
    remove_shortcuts()
    remove_registry()
    errors, removed = wipe_install_dir()
    result["errors"] = errors
    result["removed_dir"] = removed
    return True, result


class Uninstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("卸载 " + APP_DISPLAY)
        self.configure(bg=BG)
        self.geometry("580x380")
        self.resizable(False, False)
        self.update_idletasks()
        w, h = 580, 380
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2 - 20
        self.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")
        self.keep = tk.BooleanVar(value=True)
        self._build()

    def _build(self):
        top = tk.Frame(self, bg="#2c3e50", height=52)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="卸载 AXIOM", bg="#2c3e50", fg="#ffffff",
                 font=FONT_B).pack(side="left", padx=18)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=22, pady=16)
        tk.Label(body, text="即将从以下目录卸载 AXIOM：", bg=BG, fg=FG,
                 font=FONT).pack(anchor="w")
        tk.Label(body, text=INSTALL_DIR, bg=BG, fg=DIM, font=FONT_MONO,
                 wraplength=520, justify="left").pack(anchor="w", pady=(4, 16))
        tk.Checkbutton(body, text="保留我的存档（备份到桌面 AXIOM_存档备份）",
                       variable=self.keep, bg=BG, fg=FG, selectcolor="#ffffff",
                       activebackground=BG, activeforeground=ACCENT,
                       font=FONT, highlightthickness=0).pack(anchor="w")
        tk.Label(body, text="取消勾选将连同 data 里的存档一起删除，无法恢复。",
                 bg=BG, fg=DIM, font=FONT_S).pack(anchor="w", pady=(2, 20))

        bar = tk.Frame(body, bg=BG)
        bar.pack(anchor="w")
        tk.Button(bar, text="  开始卸载  ", command=self._run, relief="flat", bd=0,
                  bg=ERR, fg="#ffffff", activebackground="#a93226",
                  activeforeground="#ffffff", font=FONT, cursor="hand2",
                  padx=10, pady=5).pack(side="left")
        tk.Button(bar, text="  取消  ", command=self.destroy, relief="flat", bd=0,
                  bg="#e8e4da", fg=FG, activebackground="#dcd7c8", font=FONT,
                  cursor="hand2", padx=10, pady=5).pack(side="left", padx=10)

    def _run(self):
        if is_running():
            messagebox.showwarning("卸载", "AXIOM 正在运行。\n\n请先关闭它，再点一次「开始卸载」。")
            return
        if not self.keep.get():
            if not messagebox.askyesno("确认", "确定要连存档一起删除吗？此操作无法撤销。"):
                return
        ok, res = do_uninstall(keep_data=self.keep.get(), force=True)
        if not ok:
            messagebox.showerror("卸载", res)
            return
        msg = "卸载完成。"
        if res.get("backup"):
            msg += "\n\n存档已备份到：\n%s" % res["backup"]
        if res.get("errors"):
            msg += "\n\n有 %d 个文件未能删除（可能被占用），可手动删除残留目录。" % res["errors"]
        messagebox.showinfo("卸载", msg)
        self.destroy()


def main():
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AXIOM.Uninstaller")
    except Exception:
        pass
    if _flag("silent"):
        keep = _arg("keep-data", "1") not in ("0", "false", "no")
        ok, res = do_uninstall(keep_data=keep, force=_flag("force"))
        if not ok:
            print("uninstall blocked:", res)
            return 1
        print("uninstalled. backup =", res.get("backup"), " errors =", res.get("errors"))
        return 0
    Uninstaller().mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
