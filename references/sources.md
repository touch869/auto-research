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
- **多词/多系统名用 OR 逻辑,不要塞一个 query 里 AND**:如要找 DeepResearcher/WebThinker/STORM,**分三次搜或用宽泛词**,不能 `python search_arxiv.py "DeepResearcher WebThinker STORM"`( ti_abs 会要求三者同时出现在标题/摘要 → 几乎 0 命中 )。正确:分别搜每个系统名,或用共同上位词( 如 "deep research agent" )。
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
python scripts/search_github.py "<query>" --days <N> --max 20 --out tmp/github.json
```
- 按 `pushed`( 最近推送 )过滤时间窗,保证项目"活着"。
- 输出含 stars / 语言 / topics。
- **降级**:脚本失败 → WebSearch 搜 `<query> site:github.com`,取仓库名。
- 想看某 repo 的近期 release/issue,WebFetch 该 repo 的 releases 页让模型提取。
