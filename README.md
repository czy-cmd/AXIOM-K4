# AXIOM · K4 / Alpha 3

> 产品名 **AXIOM**，型号 **K4**，版本 **Alpha 3**。
> 本文件 = 项目总览（所有版本 / 效果 / 代码位置 / 改造方式）；详细方案与使用说明见 `USE.md`；版本变更见 `CHANGELOG.md`。

**在线地址（已部署 · 2026-11-21）**：https://czy-cmd.github.io/AXIOM-K4/
**源码仓库**：https://github.com/czy-cmd/AXIOM-K4
> 旧预览方式（`https://htmlpreview.github.io/?...`）已停用，旧仓库内嵌的 `K4-Alpha3/` 目录已删除；网页文件现位于仓库根目录，线上地址为上述 Pages 地址。

## 简介

AXIOM 是一款极简打字训练系统。它把练习、关卡、人机对战与成绩记录收进同一套冷峻界面：文章可自由选读，逐字着色实时反馈；人机对战提供 minimal 到 xhigh 五档难度，你的进度与对手进度同屏可见。支持浅色、深色、跟随系统三套主题，以及 exe、网页、手机三种打开模式。内置错字本、成绩导出、文章收藏与更新日志；调试模式需口令进入，全程不写存档。少一点花哨，多一点准确——AXIOM 只保留打字本身。

---

## 1. 所有项目（版本谱系）

根目录：`C:\Users\54215\Desktop\czy文件\p\打字游戏\测试版\`

| 版本 | 目录 | 主程序 | 效果 / 定位 | 存档 |
| --- | --- | --- | --- | --- |
| 1.0（初始） | `1.0版本/` | `main.py` | 登录注册 + 5 分钟打字 + 逐字着色 + 成绩管理与 CSV 导出 + `articles.json` 文章池 | SQLite `typing.db` |
| 2.0 | `2.0版本/` | `main2.py` | 新增模式选择页与「联机」模式（模拟 20~50 人房间、结算排名），练习与联机记录分离 | SQLite |
| 3.0 | `3.0版本/` | `main3.py` | 新增游客 / 无痕模式、游客成绩合并、TXT 自定义文本、文章池扩至约 64 KB | SQLite |
| 3.2 | `3.2版本/` | `main3.2.py` + `run.pyw` | 合并版：AI 错字分析、错题训练、字母 / 句子练习、称号、兑换码、主题与快捷键；独立启动器带进度条 | SQLite（自动补列） |
| K4 Beta-01 | `4.0版本/K4 Beta-01/` | 源码在 `1/`（`main.py` + `config/ core/ ui/` + `version.py`），打包成品在 `K4exe/` | 品牌更名 K4 = Keyboard 4；分层重构；50 关 + 95 称号 + 20 赛季 + 每日任务 + 盲打 + 音效；Inno Setup 安装包 | JSON 配置 + 数据库双轨 |
| K4 Alpha | `4.0版本/K4-Alpha/` | `main.py` + `run.pyw` | 分支重写为单文件源码免安装；纯 JSON 存档；5 类 ×4 段主题关卡；米白 / 绿色极简卡片；砍掉赛季 / 成就 / 兑换码等配菜 | `typing_userdata.json` |
| K4 Alpha2 | `4.0版本/K4-Alpha2/` | `main.py` + `run.pyw` | 游客 / 无痕快捷入口、圆环倒计时、箭头自由移动与撤销、机器人列表含玩家自己、拟真加载条 | `typing_userdata.json` |
| **AXIOM（本版）** | `4.0版本/K4-Alpha3/` | **`web/index.html`（HTML 先行）**，exe 端待建 | 全功能网页版 + 人机对战双进度 + 三主题 + 三打开模式 + 协议层 + 调试会话 + 17 篇文章 | `localStorage`（网页）/ `data/user_data.json`（待建 exe） |

每个版本目录内均有 `CHANGELOG.md`，只写相对上一版的变更。Alpha2 的 `typing_userdata.json` 与 `typing.db` 为用户真实数据，全程只读，不打开、不修改、不覆盖。

---

## 2. 效果一览（AXIOM 已实现）

- **登录**：分栏极简布局，左栏 `AX.` logo 靠左；登录 / 注册 + 游客 / 无痕 / 调试三个并列入口；登录后弹出《用户协议与数据说明》，每账号一次。
- **练习**：17 篇内置文章（含 4 篇时政政策常识科普），分类筛选、收藏、字数显示；逐字着色、5 分钟计时、准确率 / 分数实时统计。
- **人机对战**：Codex 五级难度 minimal / low / medium / high / xhigh，连续拖动 + 260ms 缓动吸附；YOU 与 OTHER AGENTS 进度同屏，对手进度靠右；可选 8 / 12 / 16 个 AGENT。
- **关卡**：5 类主题 × 4 段，共 20 关，评级达标解锁；关卡 ID 与 Alpha2 一致，老存档解锁进度可用。
- **纪录**：积分、最高分、平均准确率、错字本（可生成专项练习）、成绩列表与 CSV 导出。
- **设置**：浅色 / 深色 / 跟随系统三主题；exe / html / 手机端三打开模式；标点开关；调试开关；存档导出 / 导入 / 清空；程序内更新日志。
- **调试**：登录页固定口令 `devczy` 进入无存储会话（仅练习 + 人机 + 开发者面板「导出 log」）；设置页开关同口令验证；F9 覆盖层、F10 复制诊断。
- **网页模式**：双击 `web/index.html` 离线可用，也可发布到 GitHub Pages；默认打开远端网址，失败提示「网络故障，尝试打开本地html中……」并回退本地。
- **输入法**：隐藏输入框统一收字，中文候选框跟随光标；中英文按键不再重复或丢失。
- **手机端**：单列布局、底部固定五个实体按钮、390px 视口无横向溢出。

---

## 3. 代码在哪里

```
K4-Alpha3/
├── README.md          # 本文件：总览 / 效果 / 代码位置 / 改造方式
├── USE.md             # 原 README：完整行动方案、数据约束、验收清单、参考来源
├── CHANGELOG.md       # 相对 Alpha2 的更新日志
├── config.json        # 产品/型号/版本 + remote_url（Pages 地址）+ source_url（仓库）+ 断网提示 + 超时
├── deploy/            # GitHub Pages 发布包（根目录结构，含 .nojekyll）
│   ├── index.html / style.css / app.js / articles.js / config.js
│   └── README.md / USE.md / CHANGELOG.md / config.json
├── docs/              # Pages 备用目录（同等网页文件）
└── web/               # 已交付：纯原生 HTML/CSS/JS，无依赖
    ├── index.html     # 单页入口（登录 → 菜单 → 各功能页 → 弹层）
    ├── style.css      # 三主题 CSS 变量 + 三打开模式样式 + 响应式
    ├── app.js         # 全部逻辑：存档、登录、协议、打字、对战、关卡、纪录、设置、调试
    ├── articles.js    # 17 篇文章 + 协议正文 + 更新日志内容 + 分类
    └── config.js      # 难度参数、限时、固定调试口令、存储键
```

后续 exe 端规划目录（尚未创建）：`launcher.pyw`、`app.py`、`core/`（theme / articles / levels / difficulty / storage / debug / changelog）、`ui/`（login_view / menu_view / versus_setup / race_hud / settings_view 等）、`data/user_data.json`、`tests/`。详见 `USE.md` 第 1 节。

---

## 4. 怎么改的（Alpha2 → AXIOM）

| 需求 | 改法 | 落地位置 |
| --- | --- | --- |
| 登录改版 | 左品牌栏 + 右表单分栏，logo 顶部左对齐；游客 / 无痕降为文字链接，新增并列调试模式；注册登录后插入协议层 | `web/index.html`、`style.css`、`app.js`、`articles.js`（`K4_AGREEMENT`） |
| 联机 → 人机对战 | 去掉「联机」字样；五级难度滑块；YOU / 其他进度双区 HUD；机器人 12 名 | `config.js`（`difficulties`）、`app.js`（`renderVersus` / `renderHud` / `renderAgentBars`） |
| 难度文字与进度条对齐 | 按滑块半径修正刻度与浮标坐标：`calc(pct% + (0.5-pct/100)*20px)` | `app.js`（`thumbPos` / `paintSlider`）、`style.css`（`.diff-ticks` / `.diff-marker`） |
| 增加文章 | 5 篇原文一字不改迁移 + 新增 12 篇，其中 4 篇时政政策科普 | `web/articles.js`（`K4_ARTICLES` / `K4_CATEGORIES`） |
| 3 条自拟更新 | 错字本、成绩导出 CSV、文章收藏 | `app.js`（`renderRecords` / `btn-export-records` / `star-btn`） |
| 更新日志 | 对外 `CHANGELOG.md` + 程序内日志页；历史 8 个版本各补一份 | `CHANGELOG.md`、`articles.js`（`K4_CHANGELOG`） |
| 调试模式 | 固定口令 `devczy`，删除改密按钮；无存储调试会话 + 开发者面板 | `config.js`（`debug_password`）、`app.js`（`confirmDebugPwd` / `persist`） |
| 三主题 | CSS 变量 `data-theme=light|dark|system`，`prefers-color-scheme` 跟随系统 | `style.css`、`app.js`（`applyTheme`） |
| 界面简洁 | 6 张主菜单卡片；打字页五个实体按钮；全屏 API 失败降级沉浸式 | `index.html`、`style.css`、`app.js`（`toggleFullscreen`） |
| 网页模式 | 网址优先 + 断网回退；三打开模式决定布局与存档介质；允许网页写存档 | `config.json`、`config.js`、`app.js`（`applyMode` / `persist`） |
| 文件名全英文 + README | 文件名英文；README 拆为总览（本文件）+ 详细方案（`USE.md`） | 目录结构 |
| 输入法修复 | 隐藏输入框统一收 `input` + `compositionend`，全局键盘只处理功能键；输入框贴当前字 | `app.js`（`feedText` / `updateCaret`）、`style.css`（`.ghost-input`） |
| 定名 AXIOM | 产品名 AXIOM，K4 为型号，Alpha 3 为版本；技术标识（存档键 / 全局变量 / 目录名）不动 | 全部文档 + `index.html` / `config.js` / `app.js` |

---

## 5. 安装程序规划（尚未实施）

做 exe 安装包时，界面上必须有 **「下载源码」** 选项：点击后打开 GitHub 源码仓库（或源码压缩包下载地址），使用户在不安装的情况下也能获取源码。该地址随 GitHub 仓库网址一并填入 `config.json` 的 `remote_url` / 新增 `source_url` 字段。

其余规划（网址优先启动、断网回退、安装到 `%LOCALAPPDATA%`、卸载不碰 3.0 数据等）见 `USE.md` 第 R9 节与第 4 节。

---

## 6. 运行与验证

- 网页版：直接双击 `web/index.html` 离线运行，或打开 https://czy-cmd.github.io/AXIOM-K4/ 在线运行（两者功能一致）。
- Pages 源文件在 `deploy/`（与 `web/` 内容一致，多了 `.nojekyll`），仓库根目录结构保证网址不带子路径。
- 回归：Edge 无头 + CDP 已验证登录 / 协议 / 打字 / 实体按钮 / 五档吸附与对齐 / 输入法 / 三主题 / 三模式 / 调试口令与无存储会话 / 存档落盘 / 390px 手机视口。
- 调试口令：`devczy`。含 AI 生成内容，请注意辨别。
