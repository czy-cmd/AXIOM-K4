# -*- coding: utf-8 -*-
"""AXIOM · Model K4 / Alpha 3 安装程序（tkinter 向导，免管理员权限）。

页面：语言 → 欢迎 → 位置 → 选项 → 确认 → 进度 → 完成
开局选择语言（中文 / English），安装向导全双语；主程序本身仅中文。
可选：创建快捷方式、安装后立即运行、下载源码 .zip（联网，失败不阻断）。
支持 --silent 静默安装（脚本验证 / 批量部署）。
"""
import ctypes
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

import tkinter as tk
from tkinter import messagebox, filedialog, ttk

APP_NAME = "AXIOM"
APP_DISPLAY = "AXIOM · Model K4"
APP_VERSION = "Alpha 3"
PUBLISHER = "CZY"
MAIN_EXE = "AXIOM.exe"
UNINST_EXE = "卸载.exe"
ICON_FILE = "app.ico"
DATA_DIRNAME = "data"
SOURCE_ZIP = "AXIOM-K4-Alpha3-source.zip"
SOURCE_URL = "https://github.com/czy-cmd/AXIOM-K4/archive/refs/tags/AXIOM-K4-Alpha3.zip"

# ---------------------------------------------------------------- 双语文本
ZH = {
    "lang": "选择语言 / Select Language",
    "lang_tip": "安装向导支持中文与英文。\n主程序（AXIOM）界面仅提供中文。",
    "welcome": "欢迎安装 AXIOM",
    "welcome_body": (
        "AXIOM · Model K4 / Alpha 3 —— 极简打字训练系统。\n\n"
        "· 练习 / 关卡 / 人机对战 / 个人纪录\n"
        "· 17 篇内置文章，支持自定义 JSON / TXT 导入\n"
        "· 浅色 / 深色 / 跟随系统三套主题\n\n"
        "纯绿色安装：不写系统目录，免管理员权限，\n"
        "所有文件装在当前用户目录下，可随时干净卸载。"
    ),
    "location": "选择安装位置",
    "location_tip": "程序将完整安装到以下文件夹（约 30 MB）：",
    "browse": "浏览…",
    "loc_warn": "默认路径无需管理员权限。若已装过旧版，不会覆盖你的存档与 data 目录。",
    "options": "安装选项",
    "desktop": "在桌面创建快捷方式",
    "menu": "在开始菜单创建快捷方式（含卸载入口）",
    "launch": "安装完成后立即启动 AXIOM",
    "source": "同时下载源码 .zip 到安装目录",
    "source_note": "联网从 GitHub 下载完整源码压缩包；网络不通时会跳过，不影响安装。",
    "opt_note": "卸载入口也可在「设置 → 应用 → 已安装的应用」中找到。",
    "confirm": "即将开始安装",
    "install_to": "安装到",
    "desktop_c": "桌面快捷方式",
    "menu_c": "开始菜单",
    "launch_c": "安装后启动",
    "source_c": "下载源码",
    "yes": "是",
    "no": "否",
    "next_step": "点击「下一步」开始复制文件。",
    "installing": "正在安装…",
    "prepare": "准备中…",
    "done": "安装完成",
    "done_body": "AXIOM 已安装完成。\n\n可从桌面快捷方式启动，或直接运行：",
    "data_note": "\n存档在安装目录的 data\\ 文件夹里，\n整个安装目录可整体拷走，换台电脑照样能用。",
    "next": "下一步",
    "back": "上一步",
    "cancel": "取消",
    "finish": "完成",
    "install_now": "安装中…",
    "path_empty": "安装路径不能为空。",
    "path_bad": "请不要装到系统目录里，换一个普通文件夹。",
    "path_fail": "无法创建目录",
    "install_fail": "安装过程中出错",
    "dl_ok": "源码已下载到安装目录。",
    "dl_fail": "源码下载失败（网络原因），已跳过。",
    "title": "安装 AXIOM",
}
EN = {
    "lang": "Select Language / 选择语言",
    "lang_tip": "The setup wizard supports English and Chinese.\nThe AXIOM application itself is Chinese-only.",
    "welcome": "Welcome to AXIOM Setup",
    "welcome_body": (
        "AXIOM · Model K4 / Alpha 3 — a minimal typing trainer.\n\n"
        "· Practice / Levels / Versus / Records\n"
        "· 17 built-in articles, custom JSON / TXT import\n"
        "· Light / Dark / System themes\n\n"
        "Portable install: no system-directory writes, no admin rights.\n"
        "Everything goes under your user profile and uninstalls cleanly."
    ),
    "location": "Choose Install Location",
    "location_tip": "AXIOM will be installed to this folder (~30 MB):",
    "browse": "Browse…",
    "loc_warn": "The default path needs no admin rights. Existing saves and the data folder are never overwritten.",
    "options": "Installation Options",
    "desktop": "Create a desktop shortcut",
    "menu": "Create Start Menu shortcuts (incl. uninstaller)",
    "launch": "Launch AXIOM after installation",
    "source": "Also download the source .zip into the install folder",
    "source_note": "Downloads the full source archive from GitHub; skipped safely if offline.",
    "opt_note": "You can also uninstall via Settings → Apps → Installed apps.",
    "confirm": "Ready to Install",
    "install_to": "Install to",
    "desktop_c": "Desktop shortcut",
    "menu_c": "Start Menu",
    "launch_c": "Launch after install",
    "source_c": "Download source",
    "yes": "Yes",
    "no": "No",
    "next_step": "Click Next to start copying files.",
    "installing": "Installing…",
    "prepare": "Preparing…",
    "done": "Installation Complete",
    "done_body": "AXIOM is installed.\n\nLaunch it from the desktop shortcut, or run:",
    "data_note": "\nSaves live in the data\\ folder inside the install dir.\nYou can copy the whole folder to another PC and keep using it.",
    "next": "Next",
    "back": "Back",
    "cancel": "Cancel",
    "finish": "Finish",
    "install_now": "Installing…",
    "path_empty": "Install path cannot be empty.",
    "path_bad": "Please choose a normal folder, not a system directory.",
    "path_fail": "Cannot create directory",
    "install_fail": "Error during installation",
    "dl_ok": "Source archive downloaded to the install folder.",
    "dl_fail": "Source download failed (network), skipped.",
    "title": "AXIOM Setup",
}

BG = "#f6f4ee"
CARD = "#ffffff"
FG = "#2a2a32"
DIM = "#7c7c88"
ACCENT = "#2f6fdb"
PURPLE = "#8b5cf6"
FONT = ("Microsoft YaHei", 10)
FONT_S = ("Microsoft YaHei", 9)
FONT_B = ("Microsoft YaHei", 15, "bold")
FONT_MONO = ("Consolas", 9)

HERE = os.path.dirname(os.path.abspath(__file__))
PAYLOAD = os.path.join(HERE, "payload")


# ---------------------------------------------------------------- 路径工具
def _shfolder(csidl):
    try:
        buf = ctypes.create_unicode_buffer(260)
        ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buf)
        return buf.value
    except Exception:
        return ""


def default_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "Programs", APP_NAME)


def desktop_dir():
    d = _shfolder(0)
    return d or os.path.join(os.path.expanduser("~"), "Desktop")


def startmenu_dir():
    d = _shfolder(2)
    if not d:
        d = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                         r"Microsoft\Windows\Start Menu\Programs")
    return os.path.join(d, APP_NAME)


def _arg(key, default=""):
    for a in sys.argv[1:]:
        if a.startswith("--" + key + "="):
            return a.split("=", 1)[1]
    return default


def _flag(key):
    return ("--" + key) in sys.argv[1:]


def _bundle_dir():
    if getattr(sys, "frozen", False):
        return os.path.join(getattr(sys, "_MEIPASS", ""), "payload")
    return PAYLOAD


# ---------------------------------------------------------------- 安装逻辑
def _download_source(target):
    """把源码 .zip 放到安装目录，返回 (ok, msg)。
    优先用安装包自带的副本（离线可用），找不到再联网下载；失败不抛异常。
    """
    dst = os.path.join(target, SOURCE_ZIP)
    bundled = os.path.join(_bundle_dir(), SOURCE_ZIP)
    if os.path.isfile(bundled):
        try:
            shutil.copy2(bundled, dst)
            return True, dst
        except Exception as e:
            return False, str(e)[:120]
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "AXIOM-Setup/1.0"})
        with op.open(req, timeout=20) as r, open(dst, "wb") as f:
            shutil.copyfileobj(r, f)
        return True, dst
    except Exception as e:
        try:
            if os.path.exists(dst):
                os.remove(dst)
        except Exception:
            pass
        return False, str(e)[:120]


def do_install(target, make_desktop=True, make_startmenu=True,
               launch_after=False, with_src=False, progress=None):
    bundle = _bundle_dir()
    total = 12
    done = [0]

    def tick(text):
        done[0] += 1
        if progress:
            progress(done[0], total, text)

    os.makedirs(target, exist_ok=True)
    tick("create dir")

    # 释放 payload 文件（已存在的一律不覆盖，保护存档与用户改动）
    for root, _dirs, files in os.walk(bundle):
        for fn in files:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, bundle)
            dst = os.path.join(target, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(dst):
                tick("skip " + rel)
                continue
            shutil.copy2(full, dst)
            tick(rel)

    os.makedirs(os.path.join(target, DATA_DIRNAME), exist_ok=True)
    tick("data dir")

    # 快捷方式
    exe = os.path.join(target, MAIN_EXE)
    icon = os.path.join(target, ICON_FILE)
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from _winlnk import create_shortcut
        if make_desktop:
            create_shortcut(os.path.join(desktop_dir(), APP_DISPLAY + ".lnk"),
                            exe, workdir=target, icon=icon,
                            desc="%s %s" % (APP_DISPLAY, APP_VERSION))
        if make_startmenu:
            sm = startmenu_dir()
            os.makedirs(sm, exist_ok=True)
            create_shortcut(os.path.join(sm, APP_DISPLAY + ".lnk"),
                            exe, workdir=target, icon=icon,
                            desc="%s %s" % (APP_DISPLAY, APP_VERSION))
            create_shortcut(os.path.join(sm, "卸载 " + APP_DISPLAY + ".lnk"),
                            os.path.join(target, UNINST_EXE),
                            workdir=target, icon=icon, desc="卸载 " + APP_DISPLAY)
        tick("shortcuts")
    except Exception:
        tick("shortcuts skipped")

    # 卸载注册项（HKCU，免 UAC）
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\%s" % APP_NAME
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        vals = [
            ("DisplayName", APP_DISPLAY + " " + APP_VERSION),
            ("DisplayVersion", APP_VERSION),
            ("Publisher", PUBLISHER),
            ("InstallLocation", target),
            ("DisplayIcon", exe),
            ("UninstallString", '"%s"' % os.path.join(target, UNINST_EXE)),
            ("QuietUninstallString", '"%s" --silent --keep-data=1' % os.path.join(target, UNINST_EXE)),
            ("NoModify", 1),
            ("NoRepair", 1),
        ]
        for n, v in vals:
            if isinstance(v, int):
                winreg.SetValueEx(k, n, 0, winreg.REG_DWORD, v)
            else:
                winreg.SetValueEx(k, n, 0, winreg.REG_SZ, str(v))
        winreg.CloseKey(k)
        tick("registry")
    except Exception:
        tick("registry skipped")

    # 可选下载源码
    dl = None
    if with_src:
        ok, msg = _download_source(target)
        dl = (ok, msg)
        tick("source zip")

    tick("done")
    if launch_after:
        try:
            subprocess.Popen([exe], cwd=target)
        except Exception:
            pass
    return True, dl


# ---------------------------------------------------------------- GUI 向导
class Installer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lang = "zh"
        self.title(ZH["title"])
        self.configure(bg=BG)
        self.geometry("640x500")
        self.resizable(False, False)
        self._center()
        self.target = tk.StringVar(value=default_dir())
        self.opt_desktop = tk.BooleanVar(value=True)
        self.opt_menu = tk.BooleanVar(value=True)
        self.opt_launch = tk.BooleanVar(value=True)
        self.opt_src = tk.BooleanVar(value=False)
        self.page = 0
        self._build()
        self._show(0)

    def _center(self):
        self.update_idletasks()
        w, h = 640, 500
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2 - 20
        self.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")

    def t(self, key):
        return (ZH if self.lang == "zh" else EN)[key]

    def _build(self):
        bar = tk.Frame(self, bg="#2c3e50", height=58)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        self.lbl_brand = tk.Label(bar, text="AXIOM", bg="#2c3e50", fg="#ffffff",
                                  font=("Microsoft YaHei", 16, "bold"))
        self.lbl_brand.pack(side="left", padx=20)
        self.lbl_ver = tk.Label(bar, text="Model K4 · Alpha 3", bg="#2c3e50",
                                fg="#b8c2cc", font=FONT_S)
        self.lbl_ver.pack(side="left")

        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True, padx=24, pady=16)

        self.foot = tk.Frame(self, bg=CARD, height=60)
        self.foot.pack(fill="x", side="bottom")
        self.foot.pack_propagate(False)
        self.btn_next = tk.Button(self.foot, command=self._next, relief="flat", bd=0,
                                  bg=ACCENT, fg="#ffffff", activebackground="#2459b8",
                                  activeforeground="#ffffff", font=FONT, cursor="hand2",
                                  padx=18, pady=5)
        self.btn_next.pack(side="right", padx=(6, 20), pady=12)
        self.btn_back = tk.Button(self.foot, command=self._back, relief="flat", bd=0,
                                  bg="#e8e4da", fg=FG, activebackground="#dcd7c8",
                                  font=FONT, cursor="hand2", padx=14, pady=5)
        self.btn_back.pack(side="right", padx=6, pady=12)
        self.btn_cancel = tk.Button(self.foot, text="  " + ZH["cancel"] + "  ",
                                    command=self.destroy, relief="flat", bd=0,
                                    bg=CARD, fg=DIM, activebackground="#eeeae0",
                                    font=FONT, cursor="hand2", padx=12, pady=5)
        self.btn_cancel.pack(side="left", padx=20, pady=12)

    def _clear(self):
        for w in self.body.winfo_children():
            w.destroy()

    def _show(self, idx):
        self.page = idx
        self._clear()
        [self.p0, self.p1, self.p2, self.p3, self.p4, self.p5, self.p6][idx]()
        self.title(self.t("title"))
        self.btn_cancel.configure(text="  " + self.t("cancel") + "  ")
        self.btn_back.configure(text="  " + self.t("back") + "  ",
                                state="normal" if 0 < idx < 5 else "disabled")
        if idx == 6:
            self.btn_next.configure(text="  " + self.t("finish") + "  ")
        elif idx == 5:
            self.btn_next.configure(text="  " + self.t("install_now") + "  ", state="disabled")
        else:
            self.btn_next.configure(text="  " + self.t("next") + "  ", state="normal")

    # ---- 各页 ----
    def p0(self):
        tk.Label(self.body, text=self.t("lang"), bg=BG, fg=FG,
                 font=("Microsoft YaHei", 16, "bold")).pack(anchor="w", pady=(10, 18))
        box = tk.Frame(self.body, bg=BG)
        box.pack(anchor="w")
        tk.Button(box, text="中文  (简体)", command=lambda: self._set_lang("zh"),
                  width=18, relief="flat", bd=0,
                  bg=PURPLE if self.lang == "zh" else CARD,
                  fg="#ffffff" if self.lang == "zh" else FG,
                  activebackground="#7c4fe0", font=("Microsoft YaHei", 12, "bold"),
                  cursor="hand2", pady=14).pack(side="left", padx=(0, 12))
        tk.Button(box, text="English", command=lambda: self._set_lang("en"),
                  width=18, relief="flat", bd=0,
                  bg=PURPLE if self.lang == "en" else CARD,
                  fg="#ffffff" if self.lang == "en" else FG,
                  activebackground="#7c4fe0", font=("Microsoft YaHei", 12, "bold"),
                  cursor="hand2", pady=14).pack(side="left")
        tk.Label(self.body, text=self.t("lang_tip"), bg=BG, fg=DIM,
                 font=FONT, justify="left").pack(anchor="w", pady=(28, 0))

    def _set_lang(self, lang):
        self.lang = lang
        self._show(0)

    def p1(self):
        tk.Label(self.body, text=self.t("welcome"), bg=BG, fg=ACCENT,
                 font=("Microsoft YaHei", 14, "bold")).pack(anchor="w", pady=(6, 12))
        tk.Label(self.body, text=self.t("welcome_body"), bg=BG, fg=FG, font=FONT,
                 justify="left", anchor="w").pack(anchor="w")

    def p2(self):
        tk.Label(self.body, text=self.t("location"), bg=BG, fg=ACCENT,
                 font=("Microsoft YaHei", 13, "bold")).pack(anchor="w", pady=(6, 10))
        tk.Label(self.body, text=self.t("location_tip"), bg=BG, fg=FG,
                 font=FONT).pack(anchor="w")
        row = tk.Frame(self.body, bg=BG)
        row.pack(fill="x", pady=10)
        tk.Entry(row, textvariable=self.target, bg=CARD, fg=FG,
                 insertbackground=FG, relief="solid", bd=1,
                 font=FONT_MONO).pack(side="left", fill="x", expand=True, ipady=5)
        tk.Button(row, text=" " + self.t("browse") + " ", command=self._pick,
                  relief="flat", bd=0, bg="#e8e4da", fg=FG, font=FONT,
                  cursor="hand2", padx=10, pady=5).pack(side="left", padx=6)
        tk.Label(self.body, text=self.t("loc_warn"), bg=BG, fg=DIM,
                 font=FONT_S, justify="left").pack(anchor="w")

    def _pick(self):
        d = filedialog.askdirectory(initialdir=self.target.get() or default_dir())
        if d:
            self.target.set(os.path.normpath(d))

    def p3(self):
        tk.Label(self.body, text=self.t("options"), bg=BG, fg=ACCENT,
                 font=("Microsoft YaHei", 13, "bold")).pack(anchor="w", pady=(6, 12))
        for var, key in ((self.opt_desktop, "desktop"), (self.opt_menu, "menu"),
                         (self.opt_launch, "launch"), (self.opt_src, "source")):
            tk.Checkbutton(self.body, text=self.t(key), variable=var, bg=BG, fg=FG,
                           selectcolor=CARD, activebackground=BG, activeforeground=ACCENT,
                           font=FONT, highlightthickness=0).pack(anchor="w", pady=5)
        tk.Label(self.body, text=self.t("source_note"), bg=BG, fg=PURPLE,
                 font=FONT_S, justify="left", wraplength=580).pack(anchor="w", pady=(4, 0))
        tk.Label(self.body, text="\n" + self.t("opt_note"), bg=BG, fg=DIM,
                 font=FONT_S).pack(anchor="w", pady=(10, 0))

    def p4(self):
        tk.Label(self.body, text=self.t("confirm"), bg=BG, fg=ACCENT,
                 font=("Microsoft YaHei", 13, "bold")).pack(anchor="w", pady=(6, 12))
        box = tk.Frame(self.body, bg=CARD)
        box.pack(fill="x")
        rows = [
            (self.t("install_to"), self.target.get()),
            (self.t("desktop_c"), self.t("yes") if self.opt_desktop.get() else self.t("no")),
            (self.t("menu_c"), self.t("yes") if self.opt_menu.get() else self.t("no")),
            (self.t("launch_c"), self.t("yes") if self.opt_launch.get() else self.t("no")),
            (self.t("source_c"), self.t("yes") if self.opt_src.get() else self.t("no")),
        ]
        for k, v in rows:
            r = tk.Frame(box, bg=CARD)
            r.pack(fill="x", padx=12, pady=4)
            tk.Label(r, text=k, bg=CARD, fg=DIM, font=FONT_S,
                     width=16, anchor="w").pack(side="left")
            tk.Label(r, text=v, bg=CARD,
                     fg=PURPLE if k == self.t("source_c") and self.opt_src.get() else FG,
                     font=FONT_S, anchor="w", justify="left").pack(side="left")
        tk.Label(self.body, text="\n" + self.t("next_step"), bg=BG, fg=DIM,
                 font=FONT_S).pack(anchor="w", pady=(12, 0))

    def p5(self):
        tk.Label(self.body, text=self.t("installing"), bg=BG, fg=ACCENT,
                 font=("Microsoft YaHei", 13, "bold")).pack(anchor="w", pady=(6, 16))
        self.pb = ttk.Progressbar(self.body, orient="horizontal", length=580,
                                  mode="determinate")
        self.pb.pack(anchor="w")
        self.pline = tk.Label(self.body, text=self.t("prepare"), bg=BG, fg=DIM,
                              font=FONT_S)
        self.pline.pack(anchor="w", pady=12)

    def p6(self):
        tk.Label(self.body, text=self.t("done"), bg=BG, fg="#12a150",
                 font=("Microsoft YaHei", 14, "bold")).pack(anchor="w", pady=(6, 12))
        src_msg = ""
        if getattr(self, "_dl", None):
            ok, _ = self._dl
            src_msg = "\n\n" + (self.t("dl_ok") if ok else self.t("dl_fail"))
        tk.Label(self.body,
                 text=self.t("done_body") + "\n" +
                      os.path.join(self.target.get(), MAIN_EXE) + src_msg + self.t("data_note"),
                 bg=BG, fg=FG, font=FONT, justify="left", anchor="w").pack(anchor="w")

    # ---- 导航 ----
    def _back(self):
        if 0 < self.page < 5:
            self._show(self.page - 1)

    def _next(self):
        if self.page == 4:
            tgt = self.target.get().strip()
            if not tgt:
                messagebox.showerror(self.t("title"), self.t("path_empty"))
                return
            low = tgt.lower()
            for bad in (os.environ.get("WINDIR", "c:\\windows").lower(), "\\program files"):
                if low.startswith(bad):
                    messagebox.showerror(self.t("title"), self.t("path_bad"))
                    return
            self._show(5)
            self.update_idletasks()
            self.after(120, self._run)
            return
        if self.page == 6:
            self.destroy()
            return
        self._show(self.page + 1)

    def _run(self):
        def prog(done, total, text):
            try:
                self.pb.configure(maximum=total, value=done)
                self.pline.configure(text="[%d/%d] %s" % (done, total, text))
                self.update_idletasks()
            except Exception:
                pass
        try:
            ok, dl = do_install(self.target.get().strip(),
                                make_desktop=self.opt_desktop.get(),
                                make_startmenu=self.opt_menu.get(),
                                launch_after=self.opt_launch.get(),
                                with_src=self.opt_src.get(),
                                progress=prog)
            self._dl = dl
        except Exception as e:
            messagebox.showerror(self.t("install_fail"), str(e))
            self._show(4)
            return
        self._show(6)


def main():
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AXIOM.Installer")
    except Exception:
        pass
    if _flag("silent"):
        target = _arg("dir", default_dir())
        ok, dl = do_install(target,
                            make_desktop=not _flag("no-desktop"),
                            make_startmenu=not _flag("no-menu"),
                            launch_after=False,
                            with_src=_flag("with-src"))
        print("installed ->", target, "source:", dl)
        return 0
    Installer().mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
