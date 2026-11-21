# -*- coding: utf-8 -*-
"""AXIOM 本地端冒烟测试（系统 Python 3.11）

运行：python tests/smoke_test.py
特性：
- 数据目录重定向到临时目录（AXIOM_DATA_DIR），绝不触碰真实存档与 Alpha2 数据
- stub 掉弹窗，离屏运行，逐页验证无异常
"""
import os
import sys
import tempfile
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp(prefix="axiom_test_")
os.environ["AXIOM_DATA_DIR"] = TMP
sys.path.insert(0, ROOT)

from tkinter import messagebox
messagebox.showinfo = lambda *a, **k: None
messagebox.showerror = lambda *a, **k: None
messagebox.showwarning = lambda *a, **k: None

import app as A

app = A.App()
app.geometry("+3000+3000")

assert A.storage.DATA_FILE and A.storage.DATA_FILE.startswith(TMP), \
    "数据文件必须在临时目录，中止！"
print("DATA FILE (temp):", A.storage.DATA_FILE)

errors = []


def step(name, fn):
    try:
        fn()
        app.update()
        print("  OK", name)
    except Exception as e:
        errors.append((name, repr(e)))
        print("  FAIL", name, repr(e))
        traceback.print_exc(limit=2)


# 登录 / 注册 / 协议
step("show login", lambda: app.show("login"))

def reg():
    app.view.user_var.set("tester")
    app.view.pwd_var.set("1234")
    app.view._register()

step("register", reg)
if app.view_name == "agreement":
    step("accept agreement", lambda: app.view._agree())

# 各页切换
for name in ["menu", "articles", "versus", "levels", "records",
             "changelog", "settings", "debug_menu"]:
    step("show " + name, lambda n=name: app.show(n))

# 打字
def play():
    app.start_typing("abcdefghijklmnopqrstuvwxyz", "冒烟测试", "练习", "menu")

step("start typing", play)
v = app.view
step("type chars", lambda: [v._feed(c) for c in "abcdefg"])
step("backspace", lambda: v._back())
step("finish typing", lambda: v._finish())

# 人机对战
def versus():
    app.show("versus")
    app.view._select(0)
    app.view._start()

step("start versus", versus)
v2 = app.view
step("versus typing", lambda: [v2._feed(c) for c in "abc"])
step("versus hud", lambda: v2._update_hud())
step("versus finish", lambda: v2._finish())

# 三主题
def theme_cycle():
    app.show("settings")
    for t in ["light", "dark", "system"]:
        app.theme_setting = t
        app.data["theme"] = t
        app.rebuild()

step("theme cycle rebuild", theme_cycle)

# JSON 导入
def imp():
    from core import importer
    demo = os.path.join(ROOT, "data", "sample_import.json")
    if os.path.isfile(demo):
        arts = importer.parse_file(demo)
        importer.save_custom(A.storage.DATA_DIR, arts)

step("import sample JSON", imp)

# 存档
step("persist", lambda: app.persist())
data = A.storage.load()
print("  users:", list(data.get("users", {}).keys()))
print("  records:", len(data.get("records", [])))

app.destroy()
print("=== ERRORS:", len(errors))
for n, e in errors:
    print(" -", n, e)
sys.exit(1 if errors else 0)
