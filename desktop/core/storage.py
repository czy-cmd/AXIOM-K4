# -*- coding: utf-8 -*-
"""AXIOM · 存档读写 + Alpha2 旧档只读导入

硬约束：
- Alpha2 的 typing_userdata.json / typing.db 只读，绝不回写、删除、重命名。
- 新存档独立放在 data/user_data.json；已存在则不重复导入。
- 导入只在用户明确点击「从旧版导入」时发生，绝不自动扫描/覆盖。
"""
import os
import json
import hashlib
import secrets

APP_DIR = None          # 由 app.py 启动时设置为程序目录（打包后为 exe 同级）
DATA_DIR = None
DATA_FILE = None
OLD_DATA_FILE = None    # Alpha2 的 typing_userdata.json（只读）

DEFAULT_DATA = {
    "next_id": 1,
    "users": {},
    "session": {"user": None, "mode": "normal"},   # normal / guest / incognito / debug
    "theme": "system",
    "open_mode": "exe",
    "punct": True,
    "agreement_accepted": [],
    "debug": False,
    "difficulty": 3,
    "agent_count": 12,
    "favorites": [],
    "mistakes": {},
    "records": [],
    "points": 0,
}


def configure(app_dir, data_dir=None):
    """必须在任何读写前调用。测试时传入临时目录，避免碰真实存档。"""
    global APP_DIR, DATA_DIR, DATA_FILE, OLD_DATA_FILE
    APP_DIR = app_dir
    DATA_DIR = data_dir or os.path.join(app_dir, "data")
    DATA_FILE = os.path.join(DATA_DIR, "user_data.json")
    OLD_DATA_FILE = os.path.join(app_dir, "typing_userdata.json")


def hash_password(pwd, salt=None):
    salt = salt or secrets.token_hex(8)
    digest = hashlib.sha256((salt + str(pwd)).encode("utf-8")).hexdigest()
    return salt + ":" + digest


def verify_password(pwd, stored):
    try:
        salt, digest = stored.split(":", 1)
        return hashlib.sha256((salt + str(pwd)).encode("utf-8")).hexdigest() == digest
    except Exception:
        return False


def load():
    """加载存档；缺键用默认字典补齐，兼容老档。"""
    data = json.loads(json.dumps(DEFAULT_DATA))   # deep copy
    if DATA_FILE and os.path.isfile(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                old = json.load(f)
            if isinstance(old, dict):
                for k, v in DEFAULT_DATA.items():
                    if k in old:
                        data[k] = old[k]
                for k in list(data):
                    if k not in DEFAULT_DATA:
                        data.pop(k, None)
                # 清理旧调试密码字段
                for u in data.get("users", {}).values():
                    if isinstance(u, dict):
                        u.pop("debugSalt", None)
                        u.pop("debugHash", None)
        except Exception:
            pass
    return data


def save(data):
    if not DATA_FILE:
        raise RuntimeError("storage.configure() 未调用")
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


def can_import_old():
    """只判断文件是否存在，绝不打开内容。"""
    return bool(OLD_DATA_FILE and os.path.isfile(OLD_DATA_FILE))


def import_old():
    """只读导入 Alpha2 账号数据。返回 (ok, message)。旧档只 open('r')，绝不写入。"""
    if not can_import_old():
        return False, "未找到 Alpha2 旧存档"
    data = load()
    if data.get("users"):
        return False, "当前已有账号，跳过导入"
    try:
        with open(OLD_DATA_FILE, "r", encoding="utf-8") as f:   # 只读
            old = json.load(f)
    except Exception as e:
        return False, "旧档读取失败：%s" % str(e)[:80]

    imported = 0
    # Alpha2 结构可能是 users 字典或顶层用户列表，做保守兼容
    users = old.get("users", {}) if isinstance(old, dict) else {}
    if isinstance(users, list):
        users = {"u%d" % i: u for i, u in enumerate(users)}
    for key, u in users.items():
        if not isinstance(u, dict):
            continue
        name = u.get("username") or u.get("user") or u.get("name")
        if not name:
            continue
        rec = {
            "id": u.get("id", key),
            "username": name,
            "password": u.get("password", ""),
            "points": u.get("points", 0),
            "unlocked": u.get("unlocked", []),
            "records": u.get("records", []),
            "punct": u.get("punct", True),
        }
        # 明文密码转成哈希（若旧档已是 salt:hash 则保留）
        pw = rec["password"]
        if pw and ":" not in pw:
            rec["password"] = hash_password(pw)
        data["users"][name] = rec
        imported += 1

    data["points"] = old.get("points", 0) if isinstance(old, dict) else 0
    save(data)
    return True, "已只读导入 %d 个账号（旧档未修改）" % imported


def data_file_path():
    return DATA_FILE
