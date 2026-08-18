# AI Health Research Radar

面向 AI for Health 与 AI for Nutrition 的每周研究雷达。项目每周三 09:00（Asia/Shanghai）自动检索 arXiv，生成中文分析、alphaXiv 阅读链接和可直接进入 Obsidian 的 Markdown 周报，同时通过 GitHub Pages 提供网页浏览。

本项目基于 [Futuresxy/paper-daily](https://github.com/Futuresxy/paper-daily) 改造，保留其 arXiv 抓取、去重、相关性评分、LLM 中文分析和静态网页能力。

## 关注方向

- AI for Nutrition、个性化营养、精准营养、膳食推荐
- 健康管理、体检后管理、慢病预防、生活方式干预
- 医疗健康 Agentic AI、多智能体、工具调用、推理验证
- 患者数字孪生、虚拟患者、个体生理与干预模拟
- 健康世界模型、患者状态转移、疾病演化、长期规划
- 功能医学、系统医学、多组学、生物标志物与因果推断
- 可信多模态健康 AI、EHR、时序、可解释性、不确定性与隐私

完整关键词和 alphaXiv 标签见 [`config/interests.json`](config/interests.json)。

## 每周产出

周报写入：

```text
obsidian/AI for Health 周报/YYYY/YYYY-MM-DD_AI健康前沿周报.md
```

每篇论文包含：

- 论文标签、arXiv / alphaXiv / PDF 链接
- 研究问题、核心方法、主要创新点、证据与局限
- 对营养推荐、健康管理、体检后管理、功能医学的分别评价
- 阅读建议，以及面向当前研究方向的后续行动

alphaXiv 用作论文阅读、讨论和趋势跟踪入口；标题、作者、发布日期和摘要等事实信息以 arXiv API 为准。所有论文默认按预印本证据处理，自动分析不构成医疗建议。

## 启用自动运行

1. 在仓库 `Settings -> Pages` 中选择 `GitHub Actions` 作为发布源。
2. 打开 `Actions -> AI Health Weekly Research Radar`，执行一次 `Run workflow` 完成初始化。

默认使用 GitHub Models 的 `openai/gpt-4.1-mini`，通过工作流自带的短期 `GITHUB_TOKEN` 调用，无需额外密钥。需要切换到其他 OpenAI-compatible 服务时，在 `Settings -> Secrets and variables -> Actions` 中配置：

| 类型 | 名称 | 示例 |
| --- | --- | --- |
| Secret | `LLM_API_KEY` | 自定义模型服务 API Key |
| Variable | `LLM_BASE_URL` | `https://api.openai.com/v1` |
| Variable | `LLM_MODEL` | 支持 JSON 输出的模型名 |

三个 `LLM_*` 值应一起配置；未配置时自动回退到 GitHub Models。

常用可选变量：

| 名称 | 默认值 | 说明 |
| --- | --- | --- |
| `LOOKBACK_DAYS` | `8` | 每次回看的时间窗口 |
| `MAX_PER_TOPIC` | `20` | 每个方向最多抓取数量 |
| `MAX_SUMMARIES` | `20` | 每次最多调用 LLM 分析的论文数 |
| `DIGEST_MAX_PAPERS` | `12` | 周报最多收录论文数 |
| `CONTACT_EMAIL` | 空 | 写入 arXiv 请求标识的联系邮箱，建议配置 |

## 放入 Obsidian

最简单的方式是将仓库克隆到 Obsidian Vault 中。GitHub Actions 生成并提交周报后，在本地执行：

```bash
git pull
```

随后 Obsidian 会直接识别 `obsidian/AI for Health 周报/` 下的 Markdown 文件。

## 本地验证

```bash
python3 -m unittest discover -s tests -v
python3 scripts/collect_papers.py --days 8 --max-per-topic 20
python3 scripts/generate_weekly_digest.py --lookback-days 8 --max-papers 12
```

第二条命令会访问 arXiv；未配置模型密钥时使用基础摘要。第三条命令只读取本地 `web/data/papers.json`。

## 目录

```text
config/interests.json                 研究领域、关键词、arXiv 分类与 alphaXiv 标签
scripts/collect_papers.py             检索、去重、评分与中文分析
scripts/generate_weekly_digest.py     Obsidian 周报生成器
obsidian/AI for Health 周报/           自动生成的周报
web/                                  GitHub Pages 页面
tests/                                采集器和周报生成器测试
.github/workflows/ai-health-weekly.yml 每周三自动任务
```
