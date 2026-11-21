# -*- coding: utf-8 -*-
"""AXIOM · 自定义文本导入（JSON / TXT）

JSON 格式兼容 1.0 版 articles.json：
    [{"id":1, "difficulty":"简单", "paragraphs":["段落一","段落二",...]}]
也兼容：
    {"articles":[...]} / [{"title":..,"text":..}] / ["字符串", ...]
TXT：按空行分段，整篇作为一篇文章。
导入结果保存到 data/custom_articles.json，与内置文章合并显示，不改动内置数据。
"""
import os
import json


def parse_file(path):
    """返回文章列表 [{id,title,category,tags,text}]，失败抛异常"""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        return _parse_json(path)
    if ext == ".txt":
        return _parse_txt(path)
    raise ValueError("仅支持 .json 或 .txt 文件")


def _norm(title, text, idx, difficulty="自定义"):
    return {
        "id": "custom_%d" % idx,
        "title": title or ("自定义文本 %d" % idx),
        "category": "自定义",
        "tags": [difficulty] if difficulty else [],
        "text": text,
    }


def _parse_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("articles") or data.get("data") or [data]
    if not isinstance(data, list):
        raise ValueError("JSON 顶层必须是数组或含 articles 的对象")
    out = []
    for i, item in enumerate(data):
        if isinstance(item, str):
            if item.strip():
                out.append(_norm("自定义文本 %d" % (i + 1), item.strip(), i))
            continue
        if not isinstance(item, dict):
            continue
        paragraphs = item.get("paragraphs") or []
        if isinstance(paragraphs, str):
            paragraphs = [paragraphs]
        text = "\n".join(str(x) for x in paragraphs if str(x).strip())
        if not text:
            text = str(item.get("text") or item.get("content") or "").strip()
        if not text:
            continue
        # 段落直接拼接（打字时换行需可跳过，统一改为连续文本）
        text = text.replace("\n", "")
        title = str(item.get("title") or item.get("name") or
                    "文本 %s" % (item.get("id", i + 1)))
        diff = str(item.get("difficulty") or "")
        out.append(_norm(title, text, i, diff))
    if not out:
        raise ValueError("文件中没有可用文本")
    return out


def _parse_txt(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        raw = f.read()
    blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
    if not blocks:
        raise ValueError("TXT 文件为空")
    text = "".join(blocks).replace("\n", "")
    name = os.path.splitext(os.path.basename(path))[0]
    return [_norm(name, text, 0)]


def load_custom(data_dir):
    path = os.path.join(data_dir, "custom_articles.json")
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            v = json.load(f)
        return v if isinstance(v, list) else []
    except Exception:
        return []


def save_custom(data_dir, articles):
    path = os.path.join(data_dir, "custom_articles.json")
    os.makedirs(data_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    return path
