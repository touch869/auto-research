# 检索源操作参考

三源 adapter 的用法、字段、降级方案。SKILL.md 的 report 流程按此调用。

## 统一条目 schema( 所有源归一成这个 )

```json
{
  "source": "arxiv | web | github",
  "title": "",
  "url": "",
  "authors_or_owner": "",
  "date": "YYYY-MM-DD",
  "summary_raw": "原始摘要/描述/README 片段",
  "type": "paper | blog | repo | release | discussion | report",
  "meta": { "stars": 0, "citations": 0, "arxiv_id": "", "topics": [] }
}
```

---

## arXiv( 学术论文 )
**脚本**:`scripts/search_arxiv.py`( 零依赖,标准库 urllib + xml )
```bash
python scripts/search_arxiv.py "<query>" --days <N> --max 20 --out tmp/arxiv.json
# --fields ti_abs( 默认,标题+摘要精确,降噪 )| all( 全文模糊,召回广噪声大 )
```
- 默认 `--fields ti_abs`:标题+摘要精确匹配,降噪( 避免 all 全文的物理/医学噪声 )。
- 按提交时间倒序,`--days` 过滤时间窗。输出含 arxiv_id / 作者 / 摘要 / 分类。
- **降级**:脚本失败( 网络/超时/被限 )→ 改用 WebSearch 搜 `<query> site:arxiv.org`,取摘要。

**⚠ 检索技巧( 元研究实测教训 )**:
- 用英文 query。
- **多词/多系统名用 OR 逻辑,不要塞一个 query 里 AND**:如要找 DeepResearcher/WebThinker/STORM,**分三次搜或用宽泛词**,不能 `python scripts/search_arxiv.py "DeepResearcher WebThinker STORM"`( ti_abs 会要求三者同时出现在标题/摘要 → 几乎 0 命中 )。正确:分别搜每个系统名,或用共同上位词( 如 "deep research agent" )。
- 领域可加 `cat:cs.AI` 限定( 需改 --fields all 配合 )。
- 单轮召回少 → 别死磕 query,进下一轮用演化 query( 见 iteration.md )。

## 开放 Web( 博客/HN/Reddit/媒体 )
**方式**:不写脚本,直接用 agent 工具( WebSearch + WebFetch )。
- WebSearch:`"<query>" site:news.ycombinator.com` / `site:reddit.com/r/MachineLearning` / 技术博客。
- 对每条结果用 WebFetch 抓正文;**正文提取交给强模型**( 把网页 Markdown 扔给模型,让它抽出"做了啥+关键点" ),不写解析规则。
- 归一成 schema 时 `source=web`,`type` 按内容判( blog/discussion/report )。
- **降级**:WebFetch 被反爬/超时 → 退回用 WebSearch 的摘要片段当 `summary_raw`,标记质量降级。

## GitHub( 开源项目/release )
**脚本**:`scripts/search_github.py`( 标准库,建议设 `GITHUB_TOKEN` 提高配额 )
```bash
python scripts/search_github.py "<query>" --days <N> --max 20 --sort best --out tmp/github.json
# 语义宽 query 可加 --min-stars 20 压噪声;精确名 query 别加( 见下 )
```
- 按 `pushed`( 最近推送 )过滤时间窗,保证项目"活着"。输出含 stars / 语言 / topics。
- **排序三档**( `--sort` ):
  - `best`( 默认,GitHub 相关性 )——语义 query 用这个。
  - `stars`——找某方向头部项目。
  - `updated`( 最近推送 )——**只用于窄域/精确名查活跃度**。⚠ 实测教训( 2026-11-17 ):
    宽泛语义 query 配 `updated` + `--max 15` = top15 全是当天 push 的 0-3★ 垃圾仓库,
    把 91★ 的目标项目( TokenRhythm/InfraRSI )完全挤出结果集。
- **`--min-stars N`**:客户端过滤低星噪声。语义宽 query 建议 10-20;
  **精确名/组织名 query 不要加**( 会把新出的重要项目滤掉,新项目往往 <10★ )。
- **精确名 query 单独跑**:已知系统名( 如 `InfraRSI`、`Hyperloom` )时,除语义 query 外
  一定补一轮 `python scripts/search_github.py "InfraRSI" --days 180` ——精确名匹配总数少,
  一发命中且不受排序噪声影响。
- **工件链接收割**:读到的 Code repo/dataset 链接直接并入材料清单,不拿去当 query 搜
  ( 见 iteration.md「工件收割」 );复用旧分析时链接随结论一起搬运。
- **降级**:脚本失败 → WebSearch 搜 `<query> site:github.com`,取仓库名。
- 想看某 repo 的近期 release/issue,WebFetch 该 repo 的 releases 页让模型提取。
