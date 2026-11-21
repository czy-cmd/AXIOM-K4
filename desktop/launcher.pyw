# -*- coding: utf-8 -*-
"""
AXIOM · Model K4 / Alpha 3 · 启动器
作者：CZY
说明：双击本文件即可启动（也可用 pythonw launcher.pyw 运行）
      界面沿用 K4 Alpha2 启动器，仅额外增加「打开网页版」按钮。
"""

import os
import random
import sys
import time
import json
import webbrowser
import tkinter as tk
from tkinter import messagebox

# ============================================================
#  应用信息
# ============================================================
APP_TITLE = "AXIOM · Model K4"
APP_SHORT = "AXIOM"
AUTHOR    = "CZY"
VERSION   = "MODEL K4 · Alpha 3"
# 冻结兼容：资源（配置/网页/图标）从包内读；app.py 在打包后是内嵌模块。
_FROZEN = getattr(sys, "frozen", False)
RES_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.dirname(os.path.abspath(sys.executable)) if _FROZEN else os.path.dirname(os.path.abspath(__file__))

# 配色（沿用 Alpha2）
BG      = "#f6f4ee"
PANEL   = "#ffffff"
PANEL2  = "#eeeae0"
FG      = "#2a2a32"
DIM     = "#9a9aa8"
BORDER  = "#ddd7c8"
BLUE    = "#2f6fdb"
ORANGE  = "#e8830c"
GREEN   = "#12a150"
PURPLE  = "#8b5cf6"

FONT_UI = "Microsoft YaHei"

# 加载提示池（Minecraft 风格：每次随机抽取若干条，随进度切换，文字不做闪动）
# 每条都是稳定显示，直到进度推进到下一条；同一次加载不会重复。
LOADING_TIPS = [
    "正在启动 AXIOM ...",
    "正在加载内置文本 ...",
    "正在初始化关卡数据 ...",
    "正在准备人机对战模块 ...",
    "正在校准评分系统 ...",
    "正在整理个人纪录 ...",
    "即将进入 ...",
    "提示：手腕放松、指尖轻落，速度反而更稳。",
    "提示：按 Esc 可以随时返回上一级。",
    "提示：按 F11 切换全屏，专注当下这一段。",
    "提示：人机对战有五档难度，从 minimal 到 xhigh。",
    "提示：调试模式全程不写入任何存档。",
    "提示：打错的字会变红，别急，退格改掉就好。",
    "提示：自定义 JSON / TXT 文本可以在设置里导入。",
    "提示：支持浅色、深色、跟随系统三套主题。",
    "小知识：正确的指法，往往比一味求快更有效。",
    "小知识：长文练习按正确字数计分，稳住准确率。",
    "小知识：文章收藏能在菜单里一键回到常读的那篇。",
    "小知识：关卡上一关达到 C 级，就能解锁下一关。",
    "小知识：成绩可以导出 CSV，留作自己的成长记录。",
    "提示：中英文输入法都能直接用，不必切换模式。",
    "提示：进度条偶尔停顿一下，是在认真准备。",
    "AXIOM · 少一点花哨，多一点准确。",
    "感谢使用，祝你打字越来越快。",
]

# 简介文本
INTRO_TEXT = f"""【关于本程序】

  {APP_TITLE}（{VERSION}）是一款纯 Python 编写的打字练习软件，
  无需联网，无需安装第三方库，双击即可运行。
  它把练习、关卡、人机对战与成绩记录收进同一套冷峻界面：
  文章可自由选读，逐字着色实时反馈。


【主要功能】

  · 练习模式
      内置多篇中文长文，按正确字数与准确率实时计分。

  · 人机对战（原联机模式）
      5 档 Codex 风格难度：minimal / low / medium / high / xhigh，
      你的进度与对手进度同屏可见，对手速度更加顺滑。

  · 关卡模式
      5 大类小说关卡（仙侠 / 都市 / 悬疑 / 科幻 / 武侠），
      每大类 20 关。上一关达到 C 级即可解锁下一关。

  · 个人纪录
      查看总积分、练习次数、通关进度与历史成绩。

  · 文章 / 设置
      内置 17 篇文章（含 4 篇时政政策常识），支持自定义 JSON / TXT 导入；
      浅色 / 深色 / 跟随系统三套主题，含错字本与成绩导出。


【操作提示】

  · 直接敲键盘即可开始，支持中英文输入法
  · 打对的字变绿，打错的字变红，未打的字为黑色
  · 按 Esc 可随时返回上一级，按 F11 切换全屏
  · 调试模式需口令进入，全程不写存档


【版本信息】

  程序名称：{APP_TITLE}
  版本：    {VERSION}
  作者：    {AUTHOR}
  风险警告：含有AI生成内容，请注意辨别。


  感谢使用，祝你打字越来越快！
"""


# ============================================================
#  打开网页版（在线优先，断网回退本地 HTML）
# ============================================================
def open_web():
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

    import urllib.request
    ok = False
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "AXIOM-K4/1.0"})
        with op.open(req, timeout=timeout) as r:
            ok = getattr(r, "status", 200) < 400
    except Exception:
        ok = False

    if ok:
        webbrowser.open(url)
    else:
        local = os.path.join(RES_DIR, "web", "index.html")
        if os.path.isfile(local):
            messagebox.showinfo("AXIOM", msg)
            webbrowser.open("file:///" + local.replace("\\", "/"))
        else:
            messagebox.showwarning("AXIOM", msg + "\n（未找到本地 web/index.html）")


# ============================================================
#  启动器界面
# ============================================================
class Launcher:
    def __init__(self, root):
        self.root = root
        self.launch = False
        self.loading = False
        self.start_ts = 0.0
        self.total_time = 3.0
        self._last_pct = -1

        # 真实进度模拟用
        self._progress = 0.0
        self._speed = 0.0
        self._speed_target = 0.0
        self._next_change = 0.0
        self._stall_until = 0.0
        self._next_stall = 0.0
        self._hold_98_until = 0.0
        self._held_98 = False
        self._tip = ""           # 本次加载抽取的单条提示（全程固定，每次打开重抽）
        self._fading = False     # 文字淡入进行中

        root.title(f"{APP_TITLE} · 启动")
        root.configure(bg=BG)
        root.resizable(False, False)
        try:
            root.iconbitmap(os.path.join(RES_DIR, "assets", "app.ico"))
        except Exception:
            pass

        W, H = 560, 620
        root.update_idletasks()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = (sw - W) // 2
        y = (sh - H) // 2 - 20
        root.geometry(f"{W}x{H}+{max(0, x)}+{max(0, y)}")

        # ---- 顶部标题区 ----
        head = tk.Frame(root, bg=BG)
        head.pack(fill="x", pady=(48, 0))

        tk.Label(head, text=APP_SHORT, font=(FONT_UI, 56, "bold"),
                 bg=BG, fg=FG).pack()
        tk.Label(head, text="打 字 练 习 器", font=(FONT_UI, 15),
                 bg=BG, fg=DIM).pack(pady=(2, 0))

        badge = tk.Frame(head, bg=BG)
        badge.pack(pady=(14, 0))
        tk.Label(badge, text=f" {VERSION} ", font=(FONT_UI, 10, "bold"),
                 bg=PURPLE, fg="#ffffff", padx=8, pady=3).pack(side="left")
        tk.Label(badge, text=f"  作者：{AUTHOR}  ",
                 font=(FONT_UI, 10), bg=BG, fg=DIM).pack(side="left")

        # ---- 按钮区（默认显示）----
        self.btn_area = tk.Frame(root, bg=BG)
        self.btn_area.pack(pady=(40, 0))

        self._big_button(
            self.btn_area, "开 始 打 字", BLUE,
            "进入登录界面，选择模式开始练习",
            self.on_start,
        ).pack(pady=(0, 14))

        self._big_button(
            self.btn_area, "打 开 网 页 版", ORANGE,
            "在线优先 · 断网自动回退本地 HTML",
            open_web,
        ).pack(pady=(0, 14))

        self._big_button(
            self.btn_area, "简 介", PANEL,
            "功能介绍 · 操作提示 · 版本信息",
            self.on_intro,
            fg=FG,
        ).pack()

        # ---- 进度条区（默认不显示）----
        self.prog_area = tk.Frame(root, bg=BG)

        self.load_lbl = tk.Label(self.prog_area, text="正在启动 ...",
                                 font=(FONT_UI, 12), bg=BG, fg=FG)
        self.load_lbl.pack(pady=(0, 14))

        self.pbar_w = 360
        self.pbar_h = 12
        self.pbar = tk.Canvas(self.prog_area,
                              width=self.pbar_w, height=self.pbar_h,
                              bg=BG, highlightthickness=0)
        self.pbar.pack()
        self.pbar.create_rectangle(
            0, 0, self.pbar_w, self.pbar_h,
            fill=PANEL2, outline=BORDER)
        self.pbar_fill = self.pbar.create_rectangle(
            1, 1, 1, self.pbar_h - 1,
            fill=BLUE, outline="")

        self.pct_lbl = tk.Label(self.prog_area, text="0%",
                                font=(FONT_UI, 10), bg=BG, fg=DIM)
        self.pct_lbl.pack(pady=(8, 0))

        # ---- 底部 ----
        tk.Label(root, text=f"© {AUTHOR}   ·   {VERSION}",
                 font=(FONT_UI, 9), bg=BG,
                 fg=DIM).pack(side="bottom", pady=16)

    # ---------- 大按钮 ----------
    def _big_button(self, parent, text, color, sub, cmd, fg="#ffffff"):
        w, h = 340, 76
        f = tk.Frame(parent, bg=color, width=w, height=h,
                     cursor="hand2", highlightthickness=0)
        f.pack_propagate(False)
        f.grid_propagate(False)

        lab = tk.Label(f, text=text, font=(FONT_UI, 18, "bold"),
                       bg=color, fg=fg)
        lab.pack(pady=(12, 0))
        sub_lab = tk.Label(f, text=sub, font=(FONT_UI, 10),
                           bg=color, fg=fg if color != PANEL else DIM)
        sub_lab.pack()

        hover = self._shade(color, 0.92)

        def enter(_):
            if self.loading:
                return
            f.configure(bg=hover)
            lab.configure(bg=hover)
            sub_lab.configure(bg=hover)

        def leave(_):
            if self.loading:
                return
            f.configure(bg=color)
            lab.configure(bg=color)
            sub_lab.configure(bg=color)

        def click(_):
            if self.loading:
                return
            cmd()

        for wdg in (f, lab, sub_lab):
            wdg.bind("<Enter>", enter)
            wdg.bind("<Leave>", leave)
            wdg.bind("<Button-1>", click)

        return f

    @staticmethod
    def _shade(hex_color, factor):
        try:
            hex_color = hex_color.lstrip("#")
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            r = max(0, min(255, int(r * factor)))
            g = max(0, min(255, int(g * factor)))
            b = max(0, min(255, int(b * factor)))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    @staticmethod
    def _mix(c1, c2, t):
        """两个十六进制颜色按 t∈[0,1] 线性混合。"""
        try:
            c1, c2 = c1.lstrip("#"), c2.lstrip("#")
            ch = lambda s, i: int(s[i:i + 2], 16)
            r = round(ch(c1, 0) + (ch(c2, 0) - ch(c1, 0)) * t)
            g = round(ch(c1, 2) + (ch(c2, 2) - ch(c1, 2)) * t)
            b = round(ch(c1, 4) + (ch(c2, 4) - ch(c1, 4)) * t)
            return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"
        except Exception:
            return c2

    def _animate_progress_in(self):
        """进度区文字淡入（颜色由背景渐变到前景），约 260ms，OutCubic。"""
        total_ms = 260
        start = time.time()
        self._fading = True

        def step():
            elapsed = (time.time() - start) * 1000
            t = min(1.0, elapsed / total_ms)
            eased = 1 - (1 - t) ** 3          # OutCubic
            try:
                self.load_lbl.configure(fg=self._mix(BG, FG, eased))
                self.pct_lbl.configure(fg=self._mix(BG, DIM, eased))
            except Exception:
                self._fading = False
                return
            if t < 1.0:
                self.root.after(20, step)
            else:
                self._fading = False

        self.root.after(30, step)

    # ---------- 简介 ----------
    def on_intro(self):
        win = tk.Toplevel(self.root)
        win.title(f"简介 · {APP_TITLE}")
        win.configure(bg=BG)
        win.transient(self.root)

        W, H = 620, 640
        self.root.update_idletasks()
        px = self.root.winfo_rootx() + (self.root.winfo_width() - W) // 2
        py = self.root.winfo_rooty() + (self.root.winfo_height() - H) // 2
        win.geometry(f"{W}x{H}+{max(0, px)}+{max(0, py)}")
        win.minsize(480, 400)

        head = tk.Frame(win, bg=BG)
        head.pack(fill="x", padx=24, pady=(20, 6))
        tk.Label(head, text="简 介", font=(FONT_UI, 18, "bold"),
                 bg=BG, fg=FG).pack(side="left")
        tk.Label(head, text=f"{VERSION}  ·  {AUTHOR}",
                 font=(FONT_UI, 10), bg=BG, fg=DIM).pack(side="right")

        wrap = tk.Frame(win, bg=PANEL, highlightthickness=1,
                        highlightbackground=BORDER)
        wrap.pack(fill="both", expand=True, padx=24, pady=(6, 12))

        canvas = tk.Canvas(wrap, bg=PANEL, highlightthickness=0)
        sb = tk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=PANEL)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(
                       scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        txt = tk.Text(inner, wrap="word", font=(FONT_UI, 11),
                      bg=PANEL, fg=FG, bd=0, padx=22, pady=18,
                      spacing1=3, spacing3=6, cursor="arrow",
                      highlightthickness=0)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", INTRO_TEXT)

        for kw in ["【关于本程序】", "【主要功能】", "【操作提示】", "【版本信息】"]:
            start = "1.0"
            while True:
                pos = txt.search(kw, start, stopindex="end")
                if not pos:
                    break
                end = f"{pos}+{len(kw)}c"
                txt.tag_add("hl", pos, end)
                start = end
        txt.tag_configure("hl", foreground=BLUE)
        txt.configure(state="disabled")

        def _wheel(e):
            try:
                if not canvas.winfo_exists():
                    return
                canvas.yview_scroll(int(-e.delta / 120), "units")
            except tk.TclError:
                pass
        canvas.bind_all("<MouseWheel>", _wheel)

        def _cleanup(_):
            try:
                canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass
        win.bind("<Destroy>", _cleanup)

        bar = tk.Frame(win, bg=BG)
        bar.pack(fill="x", padx=24, pady=(0, 18))
        tk.Button(bar, text="关 闭", font=(FONT_UI, 12, "bold"),
                  bg=BLUE, fg="#ffffff", bd=0, cursor="hand2",
                  padx=26, pady=9,
                  activebackground="#2459b8", activeforeground="#ffffff",
                  command=win.destroy).pack(side="right")

    # ---------- 开始 ----------
    def on_start(self):
        if self.loading or self.launch:
            return

        # 打包后 app 是内嵌模块，无需检查文件；源码方式才检查。
        if not _FROZEN:
            main_path = os.path.join(APP_DIR, "app.py")
            if not os.path.exists(main_path):
                messagebox.showerror(
                    "找不到主程序",
                    f"未找到 app.py\n\n请把 app.py 放到与 launcher.pyw 同一个文件夹：\n{APP_DIR}",
                )
                return

        self.loading = True
        self.btn_area.pack_forget()
        self.prog_area.pack(pady=(60, 0))
        self._animate_progress_in()

        self.total_time = random.uniform(2.0, 10.0)
        self.start_ts = time.time()
        self._last_pct = -1

        # 每次打开随机抽一条提示，整个加载过程固定不动；下次打开重新抽。
        self._tip = random.choice(LOADING_TIPS)
        try:
            self.load_lbl.configure(text=self._tip, fg=FG)
        except Exception:
            pass

        self._progress = 0.0
        self._speed = 0.0
        self._speed_target = random.uniform(0.8, 1.8)
        self._next_change = self.start_ts + random.uniform(0.25, 0.55)
        self._next_stall = self.start_ts + random.uniform(0.8, 1.8)
        self._stall_until = 0.0
        self._hold_98_until = 0.0
        self._held_98 = False

        self.root.after(30, self._tick_progress)

    # ---------- 真实进度模拟 ----------
    def _simulate_step(self, now):
        """模拟一步真实感进度：忽快忽慢、偶尔卡顿、98% 停留"""
        dt = 0.03

        # 已到 100%
        if self._progress >= 1.0:
            self._progress = 1.0
            return

        # 98% 停留阶段
        if self._held_98:
            if now < self._hold_98_until:
                return
            self._progress = 1.0
            return

        # 卡顿中
        if now < self._stall_until:
            return

        # 到点换速度
        if now >= self._next_change:
            elapsed = now - self.start_ts
            ratio = elapsed / max(0.1, self.total_time)

            if ratio < 0.15:
                self._speed_target = random.uniform(0.4, 0.9)
            elif ratio < 0.55:
                self._speed_target = random.uniform(1.6, 3.2)
            elif ratio < 0.85:
                self._speed_target = random.uniform(0.9, 1.8)
            else:
                self._speed_target = random.uniform(0.3, 0.8)

            self._next_change = now + random.uniform(0.25, 0.65)

        # 随机卡顿（< 94% 才触发）
        if now >= self._next_stall and self._progress < 0.94:
            self._stall_until = now + random.uniform(0.12, 0.45)
            self._next_stall = now + random.uniform(1.0, 2.4)
            return

        # 速度惯性
        self._speed += (self._speed_target - self._speed) * 0.18

        # 推进
        self._progress += self._speed * dt

        # 推进后立刻判断是否到达/越过 98%
        if self._progress >= 0.98 and not self._held_98:
            self._held_98 = True
            self._progress = 0.98
            self._hold_98_until = now + random.uniform(0.9, 1.2)

        if self._progress < 0:
            self._progress = 0

    def _tick_progress(self):
        if not self.loading:
            return

        now = time.time()
        self._simulate_step(now)

        self._draw_progress(self._progress)
        self._update_msg(self._progress)

        if self._progress >= 1.0:
            try:
                self.load_lbl.configure(text="进入中 ...", fg=GREEN)
                self.pct_lbl.configure(text="100%", fg=GREEN)
            except Exception:
                pass
            self.loading = False
            self.launch = True
            self.root.after(160, self.root.destroy)
            return

        self.root.after(30, self._tick_progress)

    def _draw_progress(self, p):
        try:
            if p < 0:
                p = 0
            if p > 1:
                p = 1
            w = max(1, int((self.pbar_w - 2) * p))
            self.pbar.coords(self.pbar_fill, 1, 1, 1 + w,
                             self.pbar_h - 1)

            if p < 0.66:
                color = BLUE
            elif p < 0.95:
                color = ORANGE
            else:
                color = GREEN
            self.pbar.itemconfig(self.pbar_fill, fill=color)

            pct = int(p * 100)
            if pct != self._last_pct:
                self.pct_lbl.configure(text=f"{pct}%")
                self._last_pct = pct
        except Exception:
            pass

    def _update_msg(self, p):
        """提示文字在 on_start 时抽取一次，整个加载过程固定不变（下次打开重抽）。"""
        # 不再随进度切换，避免文字变化过快；这里仅兜底防止被清空。
        try:
            if not self.load_lbl.cget("text"):
                self.load_lbl.configure(text=self._tip, fg=FG)
        except Exception:
            pass


# ============================================================
#  入口
# ============================================================
def main():
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.15)
    except Exception:
        pass

    launcher = Launcher(root)
    root.mainloop()

    if launcher.launch:
        if RES_DIR not in sys.path:
            sys.path.insert(0, RES_DIR)
        try:
            import app as main_mod
            main_mod.main()
        except Exception as e:
            err = tk.Tk()
            err.withdraw()
            messagebox.showerror("启动失败", f"主程序启动出错：\n{e}")
            err.destroy()


if __name__ == "__main__":
    main()
