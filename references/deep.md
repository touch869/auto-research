# deep 模式:单点深挖规范

对单个论文 / 开源项目 / 话题做多轮 agentic 深挖( PaperQA2 式 )。SKILL.md 的 deep 流程按此执行。

## 两种入口
- **A. 从 report 下钻**:report 跑完,用户指定"第 N 条深挖" → 复用该条已有材料( url/summary_raw )进入深挖。
- **B. 独立深挖**:用户直接给论文 URL / repo / 话题 → 先小规模检索种子( WebSearch + WebFetch ),再深挖。

## 核心环节

### 1. 种子获取( 按目标类型 )

> 重要:本环境的 WebFetch 对多数外部域名( arxiv/github/substack/nvidia… )被拦。
> **改用脚本 curl 下载 + 本地处理**,不要依赖 WebFetch。

**A. 论文( arXiv )** → 下载 PDF 分析
```bash
python scripts/pdf_extract.py <arxiv_id> --out tmp/papers/<slug>.json
# 输出 pages:[{page,text}] + full_text,带页码便于出处追溯
```
- arXiv PDF 端点通常可下( 即使网页端点被拦 )。
- **降级链( 元研究实测:PDF 常超时 )**:
  1. PDF 超时 → 抓 **arXiv abs HTML 页**( `curl -sL https://arxiv.org/abs/<id>`,提 `<blockquote class=abstract>` 摘要,比 PDF 快很多 )
  2. 摘要不够 → **WebSearch 多角度深挖**( 搜 `<标题> method/results/how it works`,拼出方法/结果 )
  3. 再不够 → 用 report 阶段的 summary_raw
  - 每级降级如实标注阅读程度( "全文" / "摘要" / "摘要+WebSearch深挖" ),影响出处精度。

**B. GitHub repo** → clone 到 tmp → 用 `/project-analyzer` 分析( 比抓 README 深 )
```bash
git clone --depth 1 https://github.com/<owner>/<repo>.git tmp/repos/<repo>
# 然后用 project-analyzer 技能分析( 它会读架构/模块/依赖 )
# 若无该技能 → agent 自己读代码:README + 目录结构 + 关键源码文件
```
- **优先 clone + project-analyzer**:能看懂真实架构,远胜 README。
- 大 repo 用 `--depth 1` 浅克隆省时。
- clone 失败( 网络/私有 )→ 降级 GitHub API 取 README。

**C. 博客/网页/其他材料** → **不预设研究方式,agent 自由发挥**
- 可用 `scripts/web_extract.py` 抓正文,也可 WebSearch、也可别的方式。
- 关键:把信息提取出来、标出处即可,**不限制手段**。
- WebFetch 常被拦,curl 系脚本更稳。

**通用降级链**:clone/PDF 失败 → GitHub API/summary_raw → WebSearch 多角度搜。每级降级如实标注信息源等级。

### 2. 多轮提问-检索-综合( 强模型驱动 )
按以下提问框架逐轮深挖,**每轮不够就主动补检索**( WebFetch 引用论文、对比基线、相关讨论 ),不要硬答:

| 轮 | 问题 | 目的 |
|----|------|------|
| 1 | 它解决什么问题?动机是什么?( 现有方法哪里不行 ) | 定位贡献 |
| 2 | 核心方法/架构是什么?关键创新点? | 理解怎么做 |
| 3 | 和谁对比?实验设置?效果如何?( 数字 ) | 评估有多好 |
| 4 | 局限/假设/开放问题? | 批判性看待 |
| 5 | 对领域的影响?后续方向?可借鉴之处? | 价值判断 |

### 3. 出处追溯( 硬要求 )
- 每个结论必须能追溯到具体来源。读原文时:
  - 论文 → 标**第 N 页 / 第 N 节**( pdf_extract 输出带页码 )
  - repo → 标 **README 某段 / release vX.Y / 某文件**
  - 网页 → 标 **链接 + 小节**
- 报告里关键结论后用 `[来源]` 标注。
- **材料没覆盖的问题,明确写"材料未覆盖",并建议是否补检索** —— 不许编造。

### 4. 综合成深挖报告
用 `scripts/render_deep.py` 渲染。输入结构( agent 构造 ):
```json
{
  "target": "TideRL (arXiv:2608.10402)",
  "target_url": "https://arxiv.org/abs/2608.10402v1",
  "one_liner": "一句话定性",
  "qa": [
    {"q": "解决什么问题?", "a": "...", "sources": ["arXiv §1", "某链接"]},
    {"q": "核心方法?", "a": "...", "sources": [...]}
  ],
  "verdict": "综合判断:值不值得跟 / 适合谁 / 风险",
  "gaps": ["材料未覆盖的问题1", "..."]
}
```
输出 `output/<目标slug>-deep-<日期>.md`。

## 与 report 的区别
| | report | deep |
|---|---|---|
| 粒度 | 多条概览( 广 ) | 单点钻取( 深 ) |
| 检索 | 三源并行拉一批 | 围绕一个目标多轮补料 |
| 产出 | N 篇 + 简评 | 单篇/单项目深度分析 |
| 时长 | 快 | 慢( 多轮 WebFetch ) |

## 何时用 deep
- report 里某条特别重要,想看清细节。
- 技术选型前,要把一个方案吃透。
- 读不懂某论文,要 agent 帮你拆解。
