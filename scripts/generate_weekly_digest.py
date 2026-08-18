#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("web/data/papers.json")
DEFAULT_OUTPUT_DIR = Path("obsidian/AI for Health 周报")
VALUE_FIELDS = (
    ("营养推荐", "value_nutrition"),
    ("健康管理", "value_health_management"),
    ("体检后管理", "value_post_exam"),
    ("功能医学", "value_functional_medicine"),
)


def parse_datetime(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def canonical_arxiv_id(paper: dict[str, Any]) -> str:
    candidates = [str(paper.get("id") or ""), str(paper.get("paper_url") or "")]
    for value in candidates:
        match = re.search(r"(?:abs/|arxiv:)?(\d{4}\.\d{4,5})(?:v\d+)?", value, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def alpha_xiv_url(paper: dict[str, Any]) -> str:
    arxiv_id = canonical_arxiv_id(paper)
    return f"https://alphaxiv.org/abs/{arxiv_id}" if arxiv_id else ""


def paper_seen_at(paper: dict[str, Any]) -> dt.datetime:
    for key in ("first_seen_at", "published", "updated", "last_seen_at"):
        parsed = parse_datetime(str(paper.get(key) or ""))
        if parsed:
            return parsed
    return dt.datetime.min.replace(tzinfo=dt.timezone.utc)


def select_weekly_papers(
    papers: list[dict[str, Any]],
    now: dt.datetime,
    lookback_days: int,
    max_papers: int,
) -> list[dict[str, Any]]:
    now_utc = now.astimezone(dt.timezone.utc)
    cutoff = now_utc - dt.timedelta(days=max(1, lookback_days))
    candidates = [paper for paper in papers if cutoff <= paper_seen_at(paper) <= now_utc]
    candidates.sort(
        key=lambda paper: (
            float((paper.get("best_match") or {}).get("score") or 0.0),
            paper_seen_at(paper),
        ),
        reverse=True,
    )
    return candidates[: max(1, max_papers)]


def clean_text(value: Any, fallback: str = "未提供") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def paper_tags(paper: dict[str, Any]) -> list[str]:
    summary = paper.get("chinese_summary") or {}
    tags = summary.get("paper_tags") or []
    if not isinstance(tags, list):
        tags = []
    if not tags:
        tags = (paper.get("best_match") or {}).get("keyword_hits") or []
    if not tags:
        tags = paper.get("categories") or []
    return [clean_text(tag) for tag in tags[:6]]


def research_value_lines(paper: dict[str, Any]) -> list[str]:
    summary = paper.get("chinese_summary") or {}
    return [f"  - {label}：{clean_text(summary.get(field), '未评估')}" for label, field in VALUE_FIELDS]


def topic_trends(papers: list[dict[str, Any]]) -> list[tuple[str, int]]:
    counts = collections.Counter(
        clean_text((paper.get("best_match") or {}).get("topic_name"), "未分类") for paper in papers
    )
    return counts.most_common()


def render_paper(index: int, paper: dict[str, Any]) -> str:
    match = paper.get("best_match") or {}
    summary = paper.get("chinese_summary") or {}
    arxiv_id = canonical_arxiv_id(paper)
    alpha_url = alpha_xiv_url(paper)
    tags = " ".join(f"#{tag.replace(' ', '-')}" for tag in paper_tags(paper)) or "#待标注"
    alpha_tags = "、".join(str(tag) for tag in (match.get("alphaxiv_tags") or [])) or "未标注"
    authors = ", ".join(str(author) for author in (paper.get("authors") or [])[:8]) or "未提供"
    score = float(match.get("score") or 0.0)
    links = [f"[arXiv]({paper.get('paper_url')})"] if paper.get("paper_url") else []
    if alpha_url:
        links.append(f"[alphaXiv]({alpha_url})")
    if paper.get("pdf_url"):
        links.append(f"[PDF]({paper.get('pdf_url')})")

    lines = [
        f"### {index}. {clean_text(paper.get('title'))}",
        "",
        f"- **论文标识**：{arxiv_id or clean_text(paper.get('id'))}",
        f"- **作者**：{authors}",
        f"- **发布日期**：{clean_text(paper.get('published'))[:10]}",
        f"- **方向 / 匹配度**：{clean_text(match.get('topic_name'))} / {score:.2f} ({clean_text(match.get('level'))})",
        f"- **论文标签**：{tags}",
        f"- **alphaXiv 主题**：{alpha_tags}",
        f"- **链接**：{' · '.join(links) if links else '未提供'}",
        f"- **研究问题**：{clean_text(summary.get('problem'))}",
        f"- **核心方法**：{clean_text(summary.get('method'))}",
        f"- **主要创新点**：{clean_text(summary.get('innovation'))}",
        f"- **证据**：{clean_text(summary.get('evidence'))}",
        "- **对我的研究方向的价值**：",
        *research_value_lines(paper),
        f"- **局限与风险**：{clean_text(summary.get('limitations'))}",
        f"- **阅读建议**：{clean_text(summary.get('why_relevant'))}",
        "",
    ]
    return "\n".join(lines)


def render_opportunities(papers: list[dict[str, Any]]) -> list[str]:
    topic_ids = {str((paper.get("best_match") or {}).get("topic_id") or "") for paper in papers}
    opportunities = []
    if {"ai_for_nutrition", "health_agents"} <= topic_ids:
        opportunities.append("把营养推荐器拆成评估、推荐、风险审查和随访四类 Agent，并比较单智能体与多智能体的可靠性和成本。")
    if {"digital_health_twins", "health_world_models"} & topic_ids:
        opportunities.append("将体检纵向指标建模为可更新的个体状态，比较数字孪生、世界模型与传统时序预测在干预模拟上的差异。")
    if "health_management" in topic_ids:
        opportunities.append("围绕体检后 30/90/180 天管理路径，评估风险分层、干预依从性和健康指标改善，而不只看离线预测精度。")
    if "functional_precision_health" in topic_ids:
        opportunities.append("探索多组学、生物标志物与生活方式数据的因果链路，并区分可解释关联与可执行干预建议。")
    if not opportunities:
        opportunities.append("本周信号较分散，建议优先精读最高匹配论文并更新关键词，而不是据此形成强结论。")
    return opportunities


def generate_weekly_digest(
    payload: dict[str, Any],
    now: dt.datetime,
    lookback_days: int = 8,
    max_papers: int = 12,
) -> str:
    selected = select_weekly_papers(payload.get("papers") or [], now, lookback_days, max_papers)
    end_date = now.date()
    start_date = end_date - dt.timedelta(days=max(1, lookback_days))
    trends = topic_trends(selected)
    generated = now.isoformat()

    lines = [
        "---",
        f'title: "AI for Health & Nutrition 前沿周报 {end_date.isoformat()}"',
        "type: literature-digest",
        f"period_start: {start_date.isoformat()}",
        f"period_end: {end_date.isoformat()}",
        f"generated_at: {generated}",
        f"paper_count: {len(selected)}",
        "sources: [arXiv, alphaXiv]",
        "tags: [AI-for-Health, AI-for-Nutrition, 健康管理, 营养推荐, Agentic-AI, 数字孪生, 世界模型]",
        "---",
        "",
        f"# AI for Health & Nutrition 前沿周报｜{end_date.isoformat()}",
        "",
        f"> 覆盖窗口：{start_date.isoformat()} 至 {end_date.isoformat()}。alphaXiv 用于阅读、讨论和趋势跟踪，论文元数据以 arXiv 为准。以下内容基于标题与摘要自动生成，均按预印本证据看待，不构成医疗建议。",
        "",
        "## 本周雷达",
        "",
        f"- 入选论文：**{len(selected)}** 篇",
        f"- 高匹配论文：**{sum(1 for paper in selected if (paper.get('best_match') or {}).get('level') == 'high')}** 篇",
    ]
    if trends:
        lines.append("- 热点方向：" + "；".join(f"{name}（{count}）" for name, count in trends))
    else:
        lines.append("- 热点方向：本周未检索到满足时间窗口的论文")

    lines.extend(["", "## 重点论文", ""])
    if selected:
        for index, paper in enumerate(selected, start=1):
            lines.append(render_paper(index, paper))
    else:
        lines.append("本周没有满足时间窗口与相关性条件的论文。建议检查工作流日志和关键词配置。\n")

    lines.extend(["## 对研究方向的启发", ""])
    for opportunity in render_opportunities(selected):
        lines.append(f"- {opportunity}")

    lines.extend(
        [
            "",
            "## 下周行动",
            "",
            "- [ ] 精读最高匹配的 1-3 篇论文，并核验方法、数据集和结论边界",
            "- [ ] 将可复用的方法或评价指标补充到研究设计库",
            "- [ ] 记录新出现的术语，必要时更新 `config/interests.json`",
            "- [ ] 对涉及临床效果或营养干预的结论查找同行评审证据",
            "",
            "## 检索与质量说明",
            "",
            "- 发现来源：arXiv API；每篇 arXiv 论文附 alphaXiv 阅读链接。",
            "- 排序依据：关键词、arXiv 分类、主题文本重合度及可选 LLM 复核。",
            "- 证据边界：自动摘要不等于全文评审；临床、营养与功能医学结论必须二次核验。",
            "- 去重规则：使用规范化 arXiv ID；同一论文版本只保留一条。",
            "",
        ]
    )
    return "\n".join(lines)


def write_weekly_digest(
    payload: dict[str, Any],
    output_dir: Path,
    now: dt.datetime,
    lookback_days: int,
    max_papers: int,
) -> Path:
    year_dir = output_dir / str(now.year)
    year_dir.mkdir(parents=True, exist_ok=True)
    output_path = year_dir / f"{now.date().isoformat()}_AI健康前沿周报.md"
    output_path.write_text(
        generate_weekly_digest(payload, now, lookback_days=lookback_days, max_papers=max_papers),
        encoding="utf-8",
    )
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an Obsidian weekly digest from collected paper data.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--lookback-days", type=int, default=8)
    parser.add_argument("--max-papers", type=int, default=12)
    parser.add_argument("--date", help="Override generation date as YYYY-MM-DD for reproducible tests.")
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if args.date:
        now = dt.datetime.fromisoformat(args.date).replace(tzinfo=dt.timezone.utc)
    else:
        now = dt.datetime.now().astimezone()
    output_path = write_weekly_digest(payload, args.output_dir, now, args.lookback_days, args.max_papers)
    print(output_path)


if __name__ == "__main__":
    main()
