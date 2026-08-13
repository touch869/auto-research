# 深度综述 · Deep Research Agent( 自主深度研究智能体 )

> **主题**:Deep Research Agent( 自主深度研究智能体 )  
> **材料数**:5 篇/项  
> **检索源**:arXiv · GitHub · Web · 社区( 中英 )  
> **生成方式**:autoresearch skill · deepresearch 模式( 迭代循环 + 多 agent )  
> **生成日期**:2026-08-12

---

## 0. 概览

本综述用 autoresearch skill 的 deepresearch 模式( 3 轮迭代检索 + 每轮深挖 )研究 deepresearch 主题本身。回答「业界怎么做迭代式深度研究」。核心结论:deep research agent 的本质是「搜索-推理-综合」的迭代循环,业界有训练范式( RL 学会循环 )与工程范式( 规则编排循环 )两条路线;停止判据是最大工程难题,有 5 类( 预算/覆盖/置信/收敛/成本 );统一分类按工作流静态 vs 动态、模块 planning/retrieval/reasoning 划分。

<details><summary>📋 检索过程( 迭代循环,4 轮 / 累计 78 条 )</summary>

- **第1轮**(+58):`deep research agent`、`iterative retrieval reasoning`
- **第2轮**(+2):`DeepResearcher WebThinker STORM`、`when to stop retrieval marginal value`、`gpt-researcher`
- **第2轮**(+6):`DeepResearcher`、`WebThinker`、`STORM`、`adaptive search stopping`
- **第3轮**(+12):`deep research survey taxonomy`、`when to stop reflection`

</details>

## 1. 本元研究的检索过程( 迭代循环实证 )

本研究本身用 3 轮迭代检索跑通,印证了「搜索→深挖→发现缺口→再搜」范式:
- **第1轮**( 初始 query:deep research agent / iterative retrieval ):58 条,发现 DeepResearcher/WebThinker 线索,但经典系统未充分覆盖。
- **第2轮**( query 演化:针对经典系统名 + 停止机制 ):发现多系统名 AND 检索失败( 真实坑 ),改 OR 后补齐 DeepResearcher/WebThinker;深挖两者机制( GRPO/推理链 ),发现「停止判据」缺口。
- **第3轮**( query 演化:综述/taxonomy/when to stop ):找到 2506.18096 统一分类框架 + 5 类停止判据。
- **收敛**:无新可检索缺口,停止。

**实证教训**:①深挖必须在每轮内做( 读摘要发现不了深层缺口 );②多词 query 用 OR 不用 AND;③网络不稳时 abs HTML + WebSearch 深挖是 PDF 降级方案。

**出处**:`本研究检索历史 tmp/meta/history.json` · `iteration.md 设计`

---

## 2. 核心范式:两条路线 + 一个分类法

**路线 A — 训练范式( RL 让模型学会循环 )**
- *DeepResearcher*:GRPO + 真实 web,把研究建模成 MDP( reason/act/observe/synthesize ),靠答案正确性奖励让模型自主涌现检索技能。关键洞察:必须在真实 web 训练,静态语料会 distribution gap。
- *WebThinker*:更进一步,把 tool use( 搜索/导航/起草 )直接嵌入推理链,不分阶段,连续 Think-Search-Draft。

**路线 B — 工程范式( 规则编排循环 )**
- *GPT Researcher*:Plan→Search→Read→Write,Planner 生成研究问题( query 演化的工程版 ),Execution 并行检索,Writer 综合。不训练模型,靠 prompt + 架构编排循环。

**统一分类( 2506.18096 )**:按工作流静态 vs 动态、模块 planning/retrieval/reasoning 划分。训练范式偏动态自适应,工程范式偏静态编排,但边界在模糊( 如 Open Deep Research 融合两者 )。

**我们 skill 的定位**:工程范式( 规则编排 + 强模型判断收敛 ),对标 GPT Researcher,但收敛判据用 agent 自判( A )而非纯规则。

**出处**:`DeepResearcher arXiv:2504.03160` · `WebThinker arXiv:2504.21776` · `GPT Researcher README` · `2506.18096`

---

## 3. 最大工程难题:何时停止检索( 收敛判据 )

业界共识( tianpan.co ):无显式停止条件的 agent 会无限循环,这是 deep research 最大的工程决策。5 类判据:
1. **迭代预算**:硬上限( LangChain 文档示例:5 次 tool call 找不到就停 )。
2. **覆盖度**:子话题都探索过( Firecrawl )。
3. **置信度**:能自信回答就停( LangChain:"Stop when you can answer confidently" )。
4. **收敛**:新搜索收益递减/大量重复( tianpan.co )。
5. **成本预算**:token/$ 耗尽( Temporal/Medium )。

**业界最佳实践 = 组合**:硬预算兜底 + 软判据( 覆盖/置信/收敛 )主停。这正是我们 iteration.md 的设计( agent 自判 A + maxRounds 兜底 ),与业界一致。

**本元研究的实证**:第3轮后判定「无新可检索缺口」即收敛判据④;若硬撑会浪费——印证简单/快收敛场景④生效快。

**出处**:`tianpan.co` · `LangChain docs` · `Firecrawl` · `Temporal`

---

## 4. 材料处理:业界对 GitHub/PDF/博客怎么做

**GitHub**:业界主流是 clone + 读代码/用 analyzer( 如 GPT Researcher 用 scraper 读 README,但深度分析需 clone )。我们 skill 的 `git clone + /project-analyzer` 方案与业界深度分析实践一致,优于纯 README。

**论文/PDF**:业界标准是下 PDF 全文解析( 我们 pdf_extract.py );DeepResearcher 等训练时也需读全文。本环境 PDF 下载慢的降级:arXiv abs HTML + WebSearch 多角度深挖,虽不如全文但可工作。

**博客/网页**:业界用 scraper/reader( GPT Researcher 的 Scraper )提正文。我们 web_extract.py( curl+bs4 )等价。关键:不预设方式、agent 自由发挥,与业界「reader 模块可替换」理念一致。

**出处追溯**:PaperQA2 式硬要求( 每结论可溯源 ),业界共识,我们已落实。

**出处**:`GPT Researcher 架构` · `PaperQA2` · `deep.md`

---

## 横向对比

| 范式/系统 | 路线 | 循环如何驱动 | 停止判据 | 我们可借鉴 |
|---|---|---|---|---|
| DeepResearcher | 训练(RL) | GRPO 学会 reason/act/observe | RL 隐式学习 | 真实环境训练的必要性 |
| WebThinker | 训练(RL) | tool use 嵌入推理链 | RL 隐式 | 推理与检索融合 |
| GPT Researcher | 工程 | Plan-Search-Read-Write 规则 | 提纲完成/预算 | Planner=query演化,架构标杆 |
| Open Deep Research | 工程 | 模块化+MCP | 可配置 | 模块可替换理念 |
| 我们 skill | 工程 | 迭代循环+agent自判 | 自判A+maxRounds兜底 | — |

---

## 开放问题 / 未覆盖

- DeepResearcher/WebThinker 的 PDF 全文未读到( 网络超时 ),训练超参/奖励细节基于二手
- GPT Researcher 未实际 clone 用 project-analyzer 分析( 超时 ),架构基于 README+文档
- 停止判据的量化对比( 各判据在不同任务上的效果 )缺实证数据
- 训练范式 vs 工程范式在相同 benchmark 上的效果对比未深挖

## 附录:材料清单

| # | 材料 | 来源 | 阅读程度 | 链接 |
|---|---|---|---|---|
| 1 | DeepResearcher: Scaling Deep Research via RL( arXiv 2504.03160 ) | arXiv | 摘要+WebSearch深挖 | https://arxiv.org/abs/2504.03160 |
| 2 | WebThinker( arXiv 2504.21776 ) | arXiv | 摘要+WebSearch深挖 | https://arxiv.org/abs/2504.21776 |
| 3 | GPT Researcher( ⭐28.8k ) | GitHub | README+架构文档 | https://github.com/assafelovic/gpt-researcher |
| 4 | Deep Research Agents: Systematic Examination & Roadmap( arXiv 2506.18096 ) | arXiv | WebSearch深挖 | https://arxiv.org/abs/2506.18096 |
| 5 | 业界停止判据实践( 多源博客/文档 ) | Web | WebSearch综合 | https://tianpan.co/2026-04-12 |

---
*由 autoresearch skill(deepresearch 模式)生成。结论标注出处;未覆盖项单独列出,不编造。*