# 深度综述 · Agentic RL 训练系统与规模化

> **主题**:Agentic RL 训练系统与规模化  
> **材料数**:4 篇/项  
> **检索源**:arXiv · GitHub · Web · 社区( 中英 )  
> **生成方式**:autoresearch skill · deepresearch 模式( 多 agent )  
> **生成日期**:2026-08-12

---

## 0. 概览

本综述深度分析 4 个核心工作,回答「agentic RL 怎么训」。核心结论:2026 年 agentic RL 的瓶颈已从算法转向训练系统与规模化,业界共识「瓶颈在推理/系统而非算法」。两条并行技术路线——训练调度优化( readiness-aware/异步 )与规模化环境( 数十万环境 )——在不同层面解决问题;开源框架( ART/prime-rl )将工业级能力平民化。

## 1. 背景:agentic RL 为什么需要新系统

传统 RL for LLM( 如单轮 RLVR/GRPO )用同步训练即可:rollout 完一批→训练→重复。但 agentic RL 是**多轮**的:agent 的 rollout 会反复因外部工具/环境调用暂停、上下文不断增长、不同 trajectory 完成时间高度不均。这打破了同步训练的前提——同步 barrier 下 GPU 大量空等慢 rollout( stall ),goodput( 有效吞吐 )暴跌;纯异步虽快但权重不一致致 task 性能下降。业界已形成共识(HN 热议↑11):**agentic RL 的瓶颈在推理/训练系统,而非 RL 算法本身**。

**出处**:`TideRL 原文第 1-2 页` · `HN: RL Is Bottlenecked by Inference`

---

## 2. 核心方法:两条并行技术路线

**路线 A — 训练调度优化( 让 stall 不再浪费 )**

- *TideRL( 学术,readiness-aware )*:用「数据是否就绪」作统一调度信号。CTB 保留 rollout 中间状态( 不丢已生成轨迹 )、RA2P 在 decoupled streaming 与 colocated aggregation 间动态选模式、ERS 用就绪信号在 rollout/train 间弹性移 GPU rank。在 stall 与异步不一致间找平衡,32×H100 上 goodput 5.6× 且不掉 task 性能。
- *prime-rl( 工业,全异步 )*:走**完全异步**路线 + 顶配系统优化( FSDP2 训练 + vLLM 推理 + FP8 + PD 分离 + EP/CP 并行 ),把异步的不一致用工程手段( 高吞吐 + 大规模 )摊薄,可训 1T+ MoE on 1000+ GPU。

**路线 B — 规模化环境( 不优化调度,堆环境数量 )**

- *Scaling Agentic RL*:用 36.5 万并发环境( SWE/Terminal/Search ),靠海量环境并发弥补单环境交互低效。和 Agent World Model( 合成 1000 环境 )同理:环境本身就是 scaling 对象。

两条路线**不互斥**:TideRL 优化「怎么调度 rollout」,Scaling 优化「有多少 rollout 可调」,理论上可叠加。

**出处**:`TideRL 原文` · `prime-rl README` · `HN: Scaling Agentic RL` · `ART README`

---

## 3. 工程底座:开源框架将能力平民化

- *ART( ⭐10.5k )* — 上手门槛最低,基于 Unsloth GRPOTrainer,W&B Serverless RL 托管( 降本 40%/提速 28% ),适合个人/小团队快速跑通 agent RL。
- *prime-rl( ⭐1895 )* — 工业级,原生支持 SWE/agentic 环境 + 端到端 SFT+RL+eval + Slurm/K8s 多节点,适合要在千卡规模训前沿模型的团队。
- 两者定位互补:ART 是「易用」,prime-rl 是「可扩展」。配合 RLinf 等,2026 开源生态已能覆盖从入门到前沿全谱系。

**出处**:`ART README` · `prime-rl README`

---

## 4. 趋势与开放问题

**趋势**:①瓶颈从算法→系统( HN 共识 )②调度优化与规模化环境两线并行③开源框架平民化( 千卡能力开源可得 )④合成环境( Agent World Model )成新供给。**开放问题**:①TideRL 三机制 ablation( 各自贡献 )未明;②两路线叠加的实证缺失( 纯推测 );③超大规模( 64/128+ 卡 )可扩展性曲线未公开;④多模态 agentic 负载的系统开销缺数据;⑤环境规模化 vs 调度优化的成本效益边界在哪。

**出处**:`综合判断` · `TideRL 原文`

---

## 横向对比

| 工作 | 路线 | 核心机制 | 规模/效果 | 定位/局限 |
|---|---|---|---|---|
| TideRL | 调度优化 | CTB/RA2P/ERS readiness-aware | 5.6× goodput( 32×H100 ) | 学术系统,ablation 未明 |
| prime-rl | 调度优化( 全异步 ) | FSDP2+vLLM+FP8+PD分离 | 1000+ GPU,1T+ MoE | 工业级,需大集群 |
| Scaling Agentic RL | 规模化环境 | 36.5 万并发环境 | SWE/Terminal/Search | 资源成本极高 |
| ART | 工程底座 | GRPOTrainer 封装 | ⭐10.5k,Serverless | 易用,非系统研究 |

---

## 开放问题 / 未覆盖

- TideRL 三机制( CTB/RA2P/ERS )ablation 未从全文完整提取
- Scheduling Mixed Rollouts( 2608.11152 )仅读摘要,未读全文
- 两路线叠加( 调度优化 + 规模化环境 )的可行性为推测,无实证
- prime-rl 的异步不一致如何靠工程摊薄,README 未详述训练稳定性数据
- 多模态 agentic 负载的系统开销缺量化数据

## 附录:材料清单

| # | 材料 | 来源 | 阅读程度 | 链接 |
|---|---|---|---|---|
| 1 | TIDERL: Readiness-Aware Scheduling | arXiv | 全文( PDF 19 页 ) | https://arxiv.org/abs/2608.10402v1 |
| 2 | prime-rl: Async RL Training at Scale | GitHub | README 全文 | https://github.com/PrimeIntellect-ai/prime-rl |
| 3 | Scaling Agentic RL: 365k Environments | 社区(HN) | 标题+热度 | https://news.ycombinator.com/item?id=49094897 |
| 4 | OpenPipe/ART | GitHub | README | https://github.com/OpenPipe/ART |

---
*由 autoresearch skill(deepresearch 模式)生成。结论标注出处;未覆盖项单独列出,不编造。*