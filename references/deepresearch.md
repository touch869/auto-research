# deepresearch 模式( ② ):主题级深度综述

对一个**主题**( 非单点 )做多材料、多角色协作的深度长文综述。
= 深挖( deep ) × 多目标 + 深度综述( A ) + 多 agent 分工( C )。
产出:分章节深度技术综述( 带出处 ),**不是学术论文**( 无八股 )。

## 与其他模式区别
| 模式 | 输入 | 范围 | 产出 |
|------|------|------|------|
| ① 简单总结 | 主题 | 浅、广 | 轻量周报 + 热点 |
| deep( 单点 ) | 一篇论文/repo | 单目标深 | 5 轮深挖报告 |
| **② deepresearch** | **主题** | **多目标深 + 综合** | **分章节深度综述长文** |

## 业界范式定位( 元研究自 2506.18096 统一分类框架 )
deep research agent 业界分两条路线,按工作流**静态 vs 动态** + **planning/retrieval/reasoning** 三模块划分:
- **训练范式( 动态自适应 )**:RL 让模型学会循环。如 DeepResearcher( GRPO+真实web )、WebThinker( tool use 嵌入推理链 )。强但需训练。
- **工程范式( 静态/半静态编排 )**:规则编排循环。如 GPT Researcher( Plan-Search-Read-Write )、Open Deep Research。无需训练,靠 prompt+架构。
- **本 skill = 工程范式**:对标 GPT Researcher,但收敛判据用 agent 自判( 软判据 )+ maxRounds( 硬上限 ),介于纯静态与动态之间。

## 迭代循环 + 多 agent 分工( C 的落地 )
**核心:每轮 = 检索 → 立即深挖 → 发现缺口 → 演化 query**( 见 iteration.md,不是"搜完再深挖" ):
每轮( round 1..maxRounds,默认 5 ):
1. **检索 agent** — 四源( arXiv/GitHub/Web/社区 )用本轮 query,`iter_collect.py` 累积去重。
2. **分析 agent** — **立即深挖本轮核心材料**( 读全文,非看摘要 ):
   - 论文:`pdf_extract.py`( 降级见 deep.md )
   - GitHub:`git clone --depth 1` + `/project-analyzer`( 无则自读代码 )
   - 网页/博客:不预设,agent 自由发挥( web_extract.py 等 )
   - 按深挖结果( 非摘要 )发现缺口。
3. **收敛判断**:有可检索缺口 → 演化 query 下轮;无 → 收敛。
**收敛后**:
4. **写作 agent** — 把多轮深挖**横向综合**成综述( 背景/方法分类/对比表/趋势/结论 ),不是拼接。

## 综述结构( 写作 agent 产出,render_deepresearch.py 渲染 )
```
# 深度综述 · <主题>
> 元信息( 主题/材料数/检索源/日期 )

## 0. 概览( 这份综述讲什么、覆盖哪些工作 )
## 1. 背景:问题与动机
## 2. 核心方法分类( 按技术路线分组,每组讲代表工作 )
   2.1 <路线A>( 代表:TideRL/... )
   2.2 <路线B>( 代表:... )
## 3. 横向对比( 表格:各工作的目标/方法/效果/局限 )
## 4. 趋势与开放问题
## 5. 结论与建议( 值得跟什么、适合谁 )
## 附录:材料清单( 带链接,每个读了什么 )
```
每节结论带出处( 论文第 N 页 / README / 链接 );未覆盖项列入 §4,**不编造**。

## 输入数据结构( agent 构造,喂 render_deepresearch.py )
```json
{
  "topic": "...",
  "materials": [{"title","url","source","deep": {解决什么/方法/对比/局限/影响}, "read":"全文/摘要"}],
  "sections": [
    {"title":"背景:问题与动机","body":"...","sources":[...]},
    {"title":"核心方法分类","body":"...","sources":[...]}
  ],
  "comparison_table": [["工作","目标","方法","效果","局限"], [...]],
  "gaps": ["未覆盖项"]
}
```

## 何时用 deepresearch
- 要把一个方向**吃透**( 技术选型、写分享、做调研报告 )。
- ① 简单总结觉得太浅,想从"知道有什么"到"理解怎么回事"。
- 单点 deep 只看一个不够,要看清一个**主题全景**。

## 成本提示
deepresearch 要读多篇全文 + 多轮综合,**慢且费 token**。建议:先 ① 简单总结摸清主题,再对真正重要的方向跑 deepresearch。
