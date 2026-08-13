---
name: autoresearch
description: 技术动向监测、自动综述与深度研究 — 三源(arXiv/GitHub/Web)+ 社区源(中英)检索,去重筛选,产出带简评的轻量周报+热点检测;或对一个主题做多 agent 协作的深度综述长文。两种模式:①简单总结(周报+热点)②deepresearch(深度综述)。适用:跟踪技术方向、做调研综述、某主题/论文深挖、技术选型情报。触发词:技术动向、最新进展、周报、综述、调研、深挖、热点、deepresearch、autoresearch、研究 agent。
category: research
---

# autoresearch 技术动向监测与深度研究技能

## 目的
跟踪技术动向、做综述、深挖。多源检索( arXiv + GitHub + Web + 社区中英 )→ 去重筛选 → 按模式产出。默认强模型,可配置。

## 两种模式
| 模式 | 触发 | 做什么 | 产出 |
|------|------|--------|------|
| **① 简单总结**( 默认 ) | 给主题 | 三源+社区浅检索→Top N 简评→**热点检测** | 轻量周报 + 热点 → `output/<主题>-<日期>.md` |
| **② deepresearch** | 给主题,要"深度/吃透/综述长文" | 多 agent(检索/分析/写作)对核心材料读全文深挖,综合 | 分章节深度综述 → `output/<主题>-research-<日期>.md` |

另有 **deep( 单点 )**:对单篇论文/repo 深挖,可作 deepresearch 的子环节,也可独立用 → `output/<目标>-deep-<日期>.md`。

用户没明说默认 ①;说"深度/吃透/综述长文"用 ②;给单篇论文/repo 用 deep。

## 工具

### 检索脚本( `scripts/`,Python 标准库为主 )
- `search_arxiv.py "query" --days N --max 20 --out tmp/arxiv.json`( 论文,--fields ti_abs 降噪 )
- `search_github.py "query" --days N --max 20 --out tmp/github.json`( repo+star )
- `search_community.py "query" --days N --max 15 [--reddit] --out tmp/community.json`( HN/Reddit,带热度 )
- `iter_collect.py --history tmp/history.json --add <jsons> --round N --queries <...>`( **迭代循环累积去重**,跨轮持久化历史;`--stat` 看统计 )
- `dedupe.py a.json b.json ... --out tmp/merged.json`( 一次性跨源去重,非循环用 )
- 中文社区( 无 API ):WebSearch `site:zhihu.com/juejin.cn/...` + `web_extract.py`( 见 references/community.md )

### 渲染脚本
- `render_report.py tmp/briefs.json --topic "..." --days N --out output/xxx.md`( ① 周报,含热点段 )
- `render_deepresearch.py tmp/research.json --out output/xxx-research-xxx.md`( ② 深度综述 )
- `render_deep.py tmp/deep_data.json --out output/xxx-deep-xxx.md`( 单点深挖 )

### 全文获取( WebFetch 被拦时的降级,curl 下载 )
- `pdf_extract.py <arxiv_id> --out tmp/papers/<slug>.json`( 论文 PDF+全文,带页码 )
- GitHub:`git clone --depth 1 <repo> tmp/repos/<name>` → 用 `/project-analyzer` 分析( 优先 );无则 agent 自读代码;clone 失败降级 README
- `web_extract.py "<url>" --out tmp/web/<slug>.json`( 网页/博客正文 )
- GitHub README:`curl -s -H "Accept: application/vnd.github.raw" .../repos/<o>/<r>/readme`

### 参考资料( `references/`,按需读别全读 )
- `iteration.md` **迭代检索循环 + 收敛判据 + 时效性**( 两模式核心机制 )
- `sources.md` arXiv/GitHub/Web 三源 + 统一 schema + 降级
- `community.md` 中英文社区源( HN/Reddit/知乎/掘金 )
- `filtering.md` 去重/筛选规则
- `report-template.md` 简评三段式 + 周报模板( 含 hotspots 字段 )
- `trends.md` 热点检测( ①模式增量 )
- `deep.md` 单点深挖提问框架 + 出处追溯 + 种子获取( PDF/clone/博客自由 )
- `deepresearch.md` ②深度综述模式 + 多 agent 分工

## 核心原则
- **真实优先**:简评/综述基于检索材料 + 全文,不许编造;未覆盖项单列。
- **强模型兜底**:正文提取、相关性、简评、综述、热点判断都用强模型。
- **定时是 harness 的事**:skill 不做 cron/定时,被调用时即跑。
- **降级可用**:WebFetch 被拦用 curl 脚本;某源失败跳过继续。

---

## ① 简单总结模式工作流

### 第 0 步:对齐参数( 启动问或用默认 )
主题( 必填 )、时间窗( 默认 30 天 )、N( 默认 5~10 )、源开关( 默认全开 )、模型、maxRounds( 默认 3 )。

### 第 1 步:主题解析
强模型:主题 → 初始 query 集( 中英 + 同义词 )。

### 第 2 步:迭代检索循环( 见 references/iteration.md,maxRounds 默认 3 )
```
round = 0;  history = [];  queries = 初始 query 集
while round < maxRounds:
    round += 1
    ① 检索:四源用本轮 queries( search_arxiv/search_github/search_community + 中文社区 WebSearch )
    ② 累积去重:`iter_collect.py --history tmp/history.json --add <本轮各源json> --round round --queries <...>`
    ③ 浅分析:相关性/质量打分 + 简评( 三段式 )+ 热点检测( trends.md )
    ④ 收敛判断( agent ):还有无可检索的信息缺口( 漏的子方向/关键词/对比对象 )?
       - 无 → 收敛,break
       - 有 → 生成下轮 query( 针对缺口,不重复 )→ 继续
达 maxRounds 仍未收敛 → 用现有材料出报告,剩余缺口列入"未覆盖"
```
- **简单模式自然收敛快**( 浅分析缺口少 ),通常 2 轮就没了。

### 第 3 步:成报
从 history.json 取累积结果;强模型写 overview/trends;
构造 briefs.json( items+brief+hotspots+overview+trends );
`render_report.py ... --days N --out output/<主题>-<日期>.md`。

---

## ② deepresearch 模式工作流( 详见 references/deepresearch.md + iteration.md )

迭代循环 + 多 agent 串行分工( agent 主循环扮演,不引并行编排 ),maxRounds 默认 5:

### 循环( 每轮 )
1. **检索 agent**:四源用本轮 query 拉,`iter_collect.py` 累积去重。
2. **分析 agent**:对核心材料读全文深挖( 见 deep.md 种子获取 ):
   - 论文 → `pdf_extract.py` 下 PDF
   - GitHub → `git clone --depth 1` 到 tmp/repos → **`/project-analyzer` 技能分析**( 无则 agent 自读代码 )
   - 博客/网页 → **不预设,agent 自由发挥**( web_extract.py / WebSearch 等 )
   - 每个按 deep.md 五轮框架( 解决什么/方法/对比/局限/影响 ),带出处。
3. **收敛判断( agent )**:还有无可检索缺口?( deep 缺口多,可到 maxRounds 5 )
   - 有 → 演化 query( 基于新发现的概念/对比对象 )→ 下轮
   - 无 → 收敛

### 写作 agent( 收敛后 )
把多轮深挖**横向综合**成分章节综述( 背景/方法分类/对比表/趋势/结论 ),不是拼接。
构造 research.json( materials/sections/comparison_table/gaps,可含 rounds 展示检索过程 );
`render_deepresearch.py ... --out output/<主题>-research-<日期>.md`。

**成本提示**:deepresearch 慢且费 token( 多轮 + 读全文 + clone )。建议先 ① 摸清主题,再对重要方向跑 ②。

---

## deep 单点深挖( 详见 references/deep.md )
给单篇论文/repo:种子获取( pdf/web/README )→ 5 轮提问-检索-综合( 出处追溯 )→ `render_deep.py`。
可独立用,也是 deepresearch 分析 agent 的子环节。

## 交付
- ① 周报:`output/<主题>-<日期>.md`
- ② 综述:`output/<主题>-research-<日期>.md`
- deep:`output/<目标>-deep-<日期>.md`
告诉用户路径;按需直接展示内容。

## 渐进路线
- **v0.1**( 已完成 ):report + deep 单点
- **v0.2**( 已完成 ):①简单总结( +热点+社区源 )②deepresearch( 多 agent 深度综述 )
- **v0.3**( 已完成 ):迭代检索循环( 搜索→深挖→发现缺口→再搜索,收敛驱动 )+ GitHub clone+project-analyzer + 博客自由发挥
- **v0.4**( 当前 ):元研究反哺( 用本 skill 研究 deepresearch,把实测教训改进 skill )——query OR 技巧/PDF 降级链/5类停止判据/分类法/检索过程展示
- **后续**:成本预算停止判据、综述质量评估、更多材料类型
