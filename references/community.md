# 社区源检索( 中英文 )

社区源补 arXiv/GitHub/开放 Web 之外的"业界讨论动态",也是热点检测( references/trends.md )的热度信号来源。

## 英文社区( 有 API,脚本化 )

**HackerNews / Reddit** → `scripts/search_community.py`
```bash
python scripts/search_community.py "<英文query>" --days 30 --max 15 [--reddit] --out tmp/community.json
```
- **HN( Algolia API,主力 )**:稳定,带 `points`/`comments` 热度信号。
- **Reddit**( `--reddit` 开启 ):r/MachineLearning 等,JSON API 不稳,失败自动降级跳过。
- 输出统一 schema,`source=community`,`type=discussion`,`meta` 含 `points/comments/platform`。
- **检索技巧**:HN 用语口语化,query 用核心词( 如 `agentic RL` 而非完整术语 );可多次不同 query 扩召回。

## 中文社区( 无统一 API,WebSearch + 提正文 )

中文源( 知乎/掘金/CSDN/公众号/BAAI 智源 )没有统一 API,**用 WebSearch site: 检索 + web_extract.py 提正文**:

### 第 1 步:WebSearch 定位
```
WebSearch: "<中文关键词>" site:zhihu.com OR site:juejin.cn OR site:csdn.net
# 也试: site:hub.baai.ac.cn ( 智源社区,高质量 ) / 公众号用搜狗微信
```
- 中文关键词( 如 "强化学习 agent"、"智能体 RL" ),中英混合搜。
- 取结果链接列表。

### 第 2 步:web_extract.py 提正文
```bash
# 对搜到的链接批量抓正文
echo "<url1>" > tmp/cn_urls.txt
echo "<url2>" >> tmp/cn_urls.txt
python scripts/web_extract.py --out tmp/cn.json < tmp/cn_urls.txt
```
- 归一成统一 schema:`source=community`,`type=discussion/blog`,`meta.platform=zhihu/juejin/...`。
- 中文源正文提取质量参差( 公众号反爬强 ),失败就退回 WebSearch 摘要片段,标注降级。

### 第 3 步:并入主流程
和英文社区结果一起进 `dedupe.py`,参与去重筛选。

## 注意
- 中文社区时效性弱于 arXiv,多见综述/解读/转载,**原创前沿少**——适合补充观点和热度,不适合当一手进展来源。
- 热点检测时,中文源的"讨论量"信号弱( 无公开 points ),主要靠 arXiv 引用 + HN/Reddit 热度。
