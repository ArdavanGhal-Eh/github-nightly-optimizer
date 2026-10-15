"""
Markdown Morning Briefing Generator.
Produces high-signal CLI and markdown summaries of nightly optimization cycles.
"""

from typing import List
from core.models import NightlyRunSummary


class MarkdownReportGenerator:
    @staticmethod
    def generate(summary: NightlyRunSummary) -> str:
        score_delta = summary.average_score_after - summary.average_score_before
        sign = "+" if score_delta >= 0 else ""

        lines = [
            "# 🌙 GitHub Nightly Optimization: Morning Briefing",
            "",
            f"- **Execution Run ID:** `{summary.run_id}`",
            f"- **Start Time:** `{summary.start_time}`",
            f"- **End Time:** `{summary.end_time}`",
            f"- **Repositories Inspected:** `{summary.total_repos_inspected}`",
            f"- **Successfully Optimized:** `{summary.repos_optimized}`",
            f"- **Pull Requests Opened:** `{summary.prs_created}`",
            f"- **Portfolio Health Index:** `{summary.average_score_before:.1f}` ➔ `{summary.average_score_after:.1f}` (**{sign}{score_delta:.1f}**)",
            "",
            "---",
            "",
            "## 📋 Repository Status Matrix",
            "",
            "| Repository | Lang | Status | Score Before | Score After | Δ | PR Link |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |"
        ]

        # Map results by repo name
        results_map = {r.repo_name: r for r in summary.results}

        for report in summary.reports:
            res = results_map.get(report.repo_name)
            status = res.status if res else "AUDITED"
            b_score = res.score_before if res else report.total_score
            a_score = res.score_after if res else report.total_score
            delta = a_score - b_score
            d_sign = "+" if delta >= 0 else ""
            pr_link = f"[{res.pr_number}]({res.pr_url})" if (res and res.pr_url) else "-"

            status_badge = {
                "SUCCESS": "🟢 SUCCESS",
                "SKIPPED": "⚪ OPTIMAL",
                "REVERTED_REGRESSION": "🔴 REVERTED",
                "FAILED": "❌ FAILED",
                "AUDITED": "🔍 AUDITED"
            }.get(status, status)

            lines.append(
                f"| **{report.repo_name}** | `{report.primary_language}` | {status_badge} | "
                f"`{b_score:.1f}` | `{a_score:.1f}` | `{d_sign}{delta:.1f}` | {pr_link} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 🛠️ Key Improvements Applied",
            ""
        ])

        has_any_change = False
        for res in summary.results:
            if res.changes_applied:
                has_any_change = True
                lines.append(f"### 📦 `{res.repo_name}`")
                for c in res.changes_applied:
                    lines.append(f"- {c}")
                lines.append("")

        if not has_any_change:
            lines.append("*All inspected repositories already satisfied baseline quality standards.*")
            lines.append("")

        lines.append("> *Detailed interactive dashboard available in `reports/` directory.*")

        return "\n".join(lines)
