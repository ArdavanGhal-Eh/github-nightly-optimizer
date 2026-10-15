"""
Documentation & Bilingual Standards Compliance Analyzer.
Audits README.md depth, badges, LaTeX math, diagrams, and Persian documentation consolidation (RULE-004).
"""

import os
import re
from typing import Dict, Any, List
from .base import BaseAnalyzer
from core.models import CategoryScore, AuditIssue, IssueSeverity


class DocumentationAnalyzer(BaseAnalyzer):
    def __init__(self, weight: float = 0.15):
        super().__init__(name="Documentation & Standards", weight=weight)

    def analyze(self, repo_path: str, context: Dict[str, Any]) -> CategoryScore:
        issues: List[AuditIssue] = []
        metrics: Dict[str, Any] = {
            "has_readme": False,
            "readme_bytes": 0,
            "has_license": False,
            "has_badges": False,
            "has_architecture_section": False,
            "has_math_formulation": False,
            "has_persian_section": False,
            "has_forbidden_separate_readme_fa": False
        }

        # Check LICENSE
        license_path = os.path.join(repo_path, "LICENSE")
        if os.path.exists(license_path):
            metrics["has_license"] = True
        else:
            issues.append(AuditIssue(
                category="Compliance",
                message="Missing LICENSE file in repository root",
                severity=IssueSeverity.MEDIUM,
                suggestion="Add an open-source license (e.g. MIT, Apache-2.0)",
                auto_fixable=True
            ))

        # Check for forbidden separate README_FA.md (RULE-004)
        readme_fa_path = os.path.join(repo_path, "README_FA.md")
        if os.path.exists(readme_fa_path):
            metrics["has_forbidden_separate_readme_fa"] = True
            issues.append(AuditIssue(
                category="Standard Violation (RULE-004)",
                message="Found forbidden separate README_FA.md file. Standard mandates single consolidated README.md",
                severity=IssueSeverity.HIGH,
                suggestion="Consolidate Persian content into canonical README.md and remove README_FA.md",
                auto_fixable=True
            ))

        # Check README.md
        readme_path = os.path.join(repo_path, "README.md")
        if not os.path.exists(readme_path):
            issues.append(AuditIssue(
                category="Documentation",
                message="Repository lacks a README.md file",
                severity=IssueSeverity.CRITICAL,
                suggestion="Create a comprehensive README.md following repository standards",
                auto_fixable=True
            ))
            return CategoryScore(self.name, 10.0, self.weight, issues, metrics)

        metrics["has_readme"] = True
        with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        metrics["readme_bytes"] = len(content.encode("utf-8"))

        # Badges check
        if "img.shields.io" in content or "![" in content:
            metrics["has_badges"] = True
        else:
            issues.append(AuditIssue(
                category="Documentation Style",
                message="README.md lacks Shields.io project badges",
                severity=IssueSeverity.LOW,
                suggestion="Add build status, license, and language badges at header",
                auto_fixable=True
            ))

        # Architecture diagram check
        if "```mermaid" in content or "Architecture" in content or "معماری" in content:
            metrics["has_architecture_section"] = True
        else:
            issues.append(AuditIssue(
                category="Architecture",
                message="README.md lacks an explicit architecture or system workflow section",
                severity=IssueSeverity.LOW,
                suggestion="Add an architecture diagram or workflow overview"
            ))

        # Math / LaTeX formulas check
        if "$" in content or "\\frac" in content or "formula" in content.lower():
            metrics["has_math_formulation"] = True

        # Bilingual Persian section check (RULE-004)
        if re.search(r"[\u0600-\u06FF]", content):
            metrics["has_persian_section"] = True
        else:
            issues.append(AuditIssue(
                category="Localization Standard",
                message="README.md lacks consolidated Persian technical documentation section",
                severity=IssueSeverity.LOW,
                suggestion="Append Persian technical overview directly into README.md with internal anchor jumps"
            ))

        # Scoring
        score = 30.0  # Base for having a readme
        if metrics["readme_bytes"] > 2000:
            score += 20.0
        elif metrics["readme_bytes"] > 800:
            score += 10.0

        if metrics["has_license"]:
            score += 15.0
        if metrics["has_badges"]:
            score += 10.0
        if metrics["has_architecture_section"]:
            score += 10.0
        if metrics["has_persian_section"]:
            score += 15.0

        if metrics["has_forbidden_separate_readme_fa"]:
            score -= 15.0

        score = max(10.0, min(100.0, score))

        return CategoryScore(
            category_name=self.name,
            score=score,
            weight=self.weight,
            issues=issues,
            metrics=metrics
        )
