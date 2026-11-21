# -*- coding: utf-8 -*-
"""AXIOM · 人机对战难度定义（与 web/config.js 同源）"""
import random

DIFFICULTIES = [
    {"code": "minimal", "label": "热身", "min": 0.9, "max": 1.3, "desc": "只做最少的活"},
    {"code": "low",     "label": "稳速", "min": 1.5, "max": 2.1, "desc": "轻载运行"},
    {"code": "medium",  "label": "基准", "min": 2.3, "max": 3.1, "desc": "默认平衡点"},
    {"code": "high",    "label": "高压", "min": 3.4, "max": 4.4, "desc": "多线并行推进"},
    {"code": "xhigh",   "label": "极限", "min": 4.6, "max": 6.2, "desc": "全力推理，不留余量"},
]
DEFAULT_INDEX = 2
AGENT_COUNT = 12
AGENT_COUNTS = (8, 12, 16)
DEBUG_PASSWORD = "devczy"


def difficulty(index):
    return DIFFICULTIES[max(0, min(len(DIFFICULTIES) - 1, int(index)))]


def agent_speeds(index, count=AGENT_COUNT, seed=None):
    """按难度生成机器人速度（字/0.3s），单调递增；可传 seed 便于调试复现"""
    rng = random.Random(seed)
    d = difficulty(index)
    return [round(rng.uniform(d["min"], d["max"]), 3) for _ in range(count)]
