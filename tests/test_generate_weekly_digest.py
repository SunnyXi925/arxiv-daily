import datetime as dt
import tempfile
import unittest
from pathlib import Path

from scripts.generate_weekly_digest import (
    alpha_xiv_url,
    canonical_arxiv_id,
    generate_weekly_digest,
    select_weekly_papers,
    write_weekly_digest,
)


def sample_paper(paper_id: str, first_seen: str, score: float, topic_id: str = "ai_for_nutrition") -> dict:
    return {
        "id": f"{paper_id}v1",
        "title": "A Personalized Nutrition Agent for Longitudinal Health Management",
        "authors": ["Ada Example", "Lin Researcher"],
        "summary": "We present and evaluate a personalized nutrition agent using longitudinal health records.",
        "published": first_seen,
        "first_seen_at": first_seen,
        "paper_url": f"https://arxiv.org/abs/{paper_id}v1",
        "pdf_url": f"https://arxiv.org/pdf/{paper_id}v1",
        "categories": ["cs.AI", "cs.LG"],
        "best_match": {
            "topic_id": topic_id,
            "topic_name": "AI for Nutrition 与个性化营养",
            "score": score,
            "level": "high" if score >= 0.72 else "medium",
            "keyword_hits": ["personalized nutrition", "health management"],
        },
        "chinese_summary": {
            "problem": "解决纵向健康管理中的个体化营养推荐问题。",
            "method": "使用健康记录和工具调用智能体生成建议。",
            "innovation": "联合营养推荐与持续随访。",
            "evidence": "摘要报告了离线实验。",
            "limitations": "需要前瞻性临床验证。",
            "why_relevant": "直接匹配营养推荐与健康管理。",
            "paper_tags": ["个性化营养", "Agentic AI"],
            "value_precision_nutrition": "高：可用于个体化膳食推荐。",
            "value_health_screening": "中：可承接体检后的干预计划。",
            "value_long_term_health": "高：支持长期随访。",
        },
    }


class WeeklyDigestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.now = dt.datetime(2026, 8, 19, 1, tzinfo=dt.timezone.utc)

    def test_canonical_arxiv_id_removes_version(self) -> None:
        paper = sample_paper("2608.12345", "2026-08-18T00:00:00+00:00", 0.9)
        self.assertEqual(canonical_arxiv_id(paper), "2608.12345")
        self.assertEqual(alpha_xiv_url(paper), "https://alphaxiv.org/abs/2608.12345")

    def test_select_weekly_papers_filters_and_sorts(self) -> None:
        recent_high = sample_paper("2608.10001", "2026-08-18T00:00:00+00:00", 0.9)
        recent_medium = sample_paper("2608.10002", "2026-08-17T00:00:00+00:00", 0.5)
        old = sample_paper("2607.10003", "2026-07-01T00:00:00+00:00", 0.99)

        selected = select_weekly_papers([recent_medium, old, recent_high], self.now, 8, 12)

        self.assertEqual([paper["id"] for paper in selected], ["2608.10001v1", "2608.10002v1"])

    def test_digest_contains_required_research_fields(self) -> None:
        payload = {"papers": [sample_paper("2608.12345", "2026-08-18T00:00:00+00:00", 0.9)]}

        digest = generate_weekly_digest(payload, self.now)

        self.assertIn("paper_count: 1", digest)
        self.assertIn("https://alphaxiv.org/abs/2608.12345", digest)
        self.assertIn("**主要创新点**", digest)
        self.assertIn("精准营养与代谢干预：高", digest)
        self.assertIn("健康筛查与高端健管：中", digest)
        self.assertIn("长期健康管理与慢病预防：高", digest)

    def test_write_digest_uses_obsidian_friendly_path(self) -> None:
        payload = {"papers": [sample_paper("2608.12345", "2026-08-18T00:00:00+00:00", 0.9)]}
        with tempfile.TemporaryDirectory() as tmp:
            path = write_weekly_digest(payload, Path(tmp), self.now, 8, 12)

            self.assertEqual(path.name, "2026-08-19_AI健康前沿周报.md")
            self.assertEqual(path.parent.name, "2026")
            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
