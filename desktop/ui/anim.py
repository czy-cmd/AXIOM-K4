# -*- coding: utf-8 -*-
"""AXIOM · 轻量动画引擎（纯标准库），参照 PCL2 的逐帧缓动思路。

tkinter 没有控件级透明度，这里用两种等效手法：
  1) 位移：grid/pack 的 pady 由大变小，形成"滑入到位"；
  2) 淡入：控件 bg/fg 由背景色渐变到目标色，模拟透明度淡入。
核心曲线 OutCubic = 1-(1-t)^3，与 PCL 主力 AniEaseOutFluent 一致。
所有动画走 after 逐帧，中途控件销毁自动停止。
"""
import time

# 缓动函数家族（t ∈ [0,1]）
EASE = {
    "out3": lambda t: 1 - (1 - t) ** 3,                       # 主力 OutCubic
    "out2": lambda t: 1 - (1 - t) ** 2,
    "out5": lambda t: 1 - (1 - t) ** 5,
    "in3": lambda t: t ** 3,
    "back": lambda t: 1 - (1 - t) ** 1.5 * __import__("math").cos(1.5 * 3.141592653589793 * t),
}

# 全局速度倍率（对应 PCL AniSpeed），设 0 可整体关闭动画（测试用）
SPEED = 1.0
ENABLED = True


def mix(c1, c2, t):
    """两个 #RRGGBB 颜色按 t∈[0,1] 线性混合。"""
    try:
        c1, c2 = c1.lstrip("#"), c2.lstrip("#")
        ch = lambda s, i: int(s[i:i + 2], 16)
        r = round(ch(c1, 0) + (ch(c2, 0) - ch(c1, 0)) * t)
        g = round(ch(c1, 2) + (ch(c2, 2) - ch(c1, 2)) * t)
        b = round(ch(c1, 4) + (ch(c2, 4) - ch(c1, 4)) * t)
        cl = lambda v: max(0, min(255, v))
        return "#%02x%02x%02x" % (cl(r), cl(g), cl(b))
    except Exception:
        return c2


def _alive(w):
    try:
        return bool(w and w.winfo_exists())
    except Exception:
        return False


def grid_slide_in(widget, bg, fg, delay=0, distance=10, duration=300,
                  geometry="grid", ease="out3", base_pady=None, base_fg=None,
                  fade_color=True):
    """控件错峰滑入 + 颜色淡入。

    widget     : 目标控件（Frame / Label / 任意）
    bg, fg     : 该控件最终的背景色与前景色（淡入目标）
    delay      : 错峰延迟 ms
    distance   : 起始下移像素
    duration   : 动画时长 ms
    geometry   : 'grid' 用 grid_configure(pady=...)，'pack' 用 pack_configure
    base_pady  : 保留的原始 pady（grid 用 (top,bottom) 或数字）
    base_fg    : 显式指定最终前景色（默认用 fg）
    """
    if not ENABLED or SPEED <= 0 or not _alive(widget):
        return
    fn = EASE.get(ease, EASE["out3"])
    delay = delay / SPEED
    duration = max(1, duration / SPEED)
    bg, fg = bg, (base_fg or fg)
    if base_pady is None:
        base_pady = (0, 0)
    top, bottom = (base_pady if isinstance(base_pady, tuple) else (0, base_pady))

    def apply(t):
        e = fn(t)
        pad = (round(top + (1 - e) * distance), bottom)
        try:
            if geometry == "grid":
                widget.grid_configure(pady=pad)
            else:
                widget.pack_configure(pady=pad)
            # 颜色淡入：前景由 bg 渐变到 fg（可选，避免覆盖彩色控件）
            if fade_color:
                try:
                    widget.configure(fg=mix(bg, fg, e))
                except Exception:
                    pass
                for c in widget.winfo_children():
                    try:
                        c.configure(fg=mix(bg, fg, e))
                    except Exception:
                        pass
        except Exception:
            pass

    start = [None]

    def step():
        if not _alive(widget):
            return
        if start[0] is None:
            start[0] = time.perf_counter()
        el = (time.perf_counter() - start[0]) * 1000
        if el < delay:
            apply(0)
            widget.after(16, step)
            return
        t = min(1.0, (el - delay) / duration)
        apply(t)
        if t < 1.0:
            widget.after(16, step)
        else:
            # 复位为原始 pady 与最终颜色
            try:
                if geometry == "grid":
                    widget.grid_configure(pady=base_pady)
                else:
                    widget.pack_configure(pady=base_pady)
                if fade_color:
                    widget.configure(fg=fg)
                    for c in widget.winfo_children():
                        try:
                            c.configure(fg=fg)
                        except Exception:
                            pass
            except Exception:
                pass

    widget.after(16, step)


def view_enter(view, bg, fg, duration=220):
    """视图整体入场：底部说明条轻微上滑淡入。供 App.show 调用。"""
    if not ENABLED or SPEED <= 0 or not _alive(view):
        return
    # 找到视图最后一个 pack 的 Label（通常是底部提示），给它一个入场
    kids = [c for c in view.winfo_children() if _alive(c)]
    if not kids:
        return
    last = kids[-1]
    try:
        info = last.pack_info()
    except Exception:
        return
    base = info.get("pady", 0)
    grid_slide_in(last, bg, fg, delay=0, distance=8, duration=duration,
                  geometry="pack", base_pady=base, base_fg=fg, fade_color=False)
