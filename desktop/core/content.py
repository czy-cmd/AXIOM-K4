# -*- coding: utf-8 -*-
"""AXIOM · 文章/关卡/协议/更新日志的只读封装"""
from .content_data import ARTICLES, LEVEL_CATEGORIES, CATEGORIES, AGREEMENT, CHANGELOG

# 关卡：5 类 × 4 段 = 20 关，ID 与 Alpha2 保持一致（c01_1 ... c05_4）
LEVELS = []
for ci, cat in enumerate(LEVEL_CATEGORIES, start=1):
    for seg in range(1, 5):
        options = [a for a in ARTICLES if a["category"] == cat]
        text = options[(seg - 1) % len(options)] if options else ARTICLES[0]
        LEVELS.append({
            "id": "c%02d_%d" % (ci, seg),
            "category": cat,
            "segment": seg,
            "title": "%s · 第 %d 段" % (cat, seg),
            "article_id": text["id"],
            "text": text["text"],
        })


def articles(category="全部", keyword="", favorites=None):
    result = list(ARTICLES)
    if category and category != "全部":
        if category == "收藏":
            fav = set(favorites or [])
            result = [a for a in result if a["id"] in fav]
        else:
            result = [a for a in result if a["category"] == category]
    if keyword:
        kw = keyword.strip().lower()
        result = [a for a in result if kw in a["title"].lower() or kw in a["text"].lower()]
    return result


def article_by_id(aid):
    for a in ARTICLES:
        if a["id"] == aid:
            return a
    return ARTICLES[0] if ARTICLES else None


def agreement_text():
    return AGREEMENT["title"], AGREEMENT["paragraphs"]


def changelog_entries():
    return CHANGELOG
