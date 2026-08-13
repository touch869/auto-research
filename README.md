# autoresearch — 技术动向监测与深度研究 Skill

一个 Claude Code skill:跟踪技术动向、自动综述、深度研究。多源检索( arXiv + GitHub + Web + 社区中英 )→ 迭代检索收敛 → 按模式产出。

## 两种模式

| 模式 | 触发 | 做什么 | 产出 |
|------|------|--------|------|
| **① 简单总结** | 给主题 | 迭代检索( 浅分析 )→ Top N 简评 + 热点检测 | 轻量周报 + 热点 |
| **② deepresearch** | 给主题,要"深度/吃透/综述" | 迭代检索 + 每轮深挖( 读全文 )+ 多 agent 综合 | 分章节深度综述长文 |
| **deep( 单点 )** | 给单篇论文/repo | 对单个目标多轮深挖 | 单目标深挖报告 |

**核心机制:迭代检索循环**——搜索 → 分析/深挖 → 发现信息缺口 → 演化 query 再搜,直到 agent 判定收敛或达最大轮数( 对标 DeepResearcher / GPT Researcher )。

## 安装

```bash
# 1. 克隆到 Claude 的 skills 目录
git clone git@github.com:touch869/auto-research.git ~/.claude/skills/autoresearch

# 2. 装依赖( 全是轻量库,标准库脚本无需安装 )
pip install PyMuPDF beautifulsoup4
# PyMuPDF 用于 pdf_extract.py( 论文全文提取 )
# beautifulsoup4 用于 web_extract.py( 网页正文提取 )

# 3.( 可选 )设 GitHub token 提高 search_github.py 配额
export GITHUB_TOKEN=ghp_xxx
```

装好后,Claude 会自动发现这个 skill。直接在对话里说需求即可触发。

## 用法示例

```
# ① 简单总结:跟踪某方向最近进展
"用 autoresearch 跟踪一下 test-time scaling 最近 30 天的进展"

# ② deepresearch:把一个方向吃透
"用 autoresearch 深度研究 agentic RL 训练系统,出一份综述"

# deep 单点:深挖某篇论文
"用 autoresearch 深挖一下 arXiv:2504.03160 这篇"
```

产物落在 skill 工作目录的 `output/`:
- `output/<主题>-<日期>.md` — 简单总结周报
- `output/<主题>-research-<日期>.md` — 深度综述
- `output/<目标>-deep-<日期>.md` — 单点深挖

## 目录结构

```
autoresearch/
├── SKILL.md                  # 核心:两模式编排 + 迭代循环流程
├── references/               # 各环节规范( progressive disclosure )
│   ├── iteration.md          # 迭代循环 + 收敛判据 + 时效性( 核心机制 )
│   ├── sources.md            # arXiv/GitHub/Web 三源 + 检索技巧
│   ├── community.md          # 中英文社区源( HN/Reddit/知乎/掘金 )
│   ├── filtering.md          # 去重/筛选规则
│   ├── report-template.md    # 简评三段式 + 周报模板
│   ├── trends.md             # 热点检测
│   ├── deep.md               # 单点深挖 + 种子获取( PDF/clone/博客 )
│   └── deepresearch.md       # 深度综述 + 多 agent + 业界范式定位
├── scripts/                  # Python 脚本( 标准库为主,零依赖优先 )
│   ├── search_arxiv.py       # arXiv 检索( ti_abs 降噪 )
│   ├── search_github.py      # GitHub 检索( +star )
│   ├── search_community.py   # HN/Reddit( +热度信号 )
│   ├── iter_collect.py       # 迭代累积去重( 跨轮持久化 )
│   ├── dedupe.py             # 一次性跨源去重
│   ├── pdf_extract.py        # arXiv PDF 下载+全文( 带页码 )
│   ├── web_extract.py        # 网页正文( curl+bs4 )
│   ├── render_report.py      # 周报渲染( 含热点 )
│   ├── render_deep.py        # 单点深挖渲染
│   └── render_deepresearch.py# 深度综述渲染( 含检索过程展示 )
└── output/                   # 产物样例( 实际运行也写这 )
```

## 设计要点

- **skill 不做定时**:何时跑、跑多频繁是 harness( Claude Code / cron )的事,skill 被调用即跑。
- **真实优先**:简评/综述基于检索材料 + 全文,不编造;未覆盖项单列。
- **强模型 + 规则分工**:正文提取/相关性/简评/综述/收敛判断用强模型;检索/去重用确定性脚本。
- **出处追溯**:每个结论可溯源( 论文第 N 页 / README / 链接 ),对标 PaperQA2。
- **降级可用**:WebFetch 被拦 → curl 脚本;PDF 超时 → abs HTML + WebSearch;某源失败跳过继续。

## 业界对标

| 我们的模块 | 借鉴 |
|-----------|------|
| 迭代检索循环 | DeepResearcher( RL 学会循环 )、GPT Researcher( 工程编排循环 ) |
| 收敛判据( agent 自判 + maxRounds ) | 业界 5 类停止判据最佳实践( 硬预算兜底 + 软判据主停 ) |
| 简单总结综述 | AutoSurvey / STORM |
| 单点深挖 | PaperQA2( agentic RAG ) |
| skill 形态 | Claude Code skill 规范 |

本 skill 属**工程范式**( 规则编排 + 强模型判断 ),无需训练。

## 开发笔记

本 skill 经历了"用自身研究自身"的元研究迭代:用 deepresearch 模式研究 deepresearch 主题,把实测暴露的问题( query 多词 AND 踩坑、PDF 超时、流程跑偏 )反哺改进。详见版本历史:

- v0.1 — report + deep 单点
- v0.2 — 双模式( 简单总结 / deepresearch )+ 社区源 + 热点检测
- v0.3 — 迭代检索循环( 收敛驱动 )+ GitHub clone + 博客自由发挥
- v0.4 — 元研究反哺( query 技巧 / PDF 降级 / 停止判据 / 分类法 / 检索过程展示 )
