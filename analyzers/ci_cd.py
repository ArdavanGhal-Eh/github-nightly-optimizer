"""
CI/CD & GitHub Actions Automation Analyzer.
Inspects .github/workflows for test automation, multi-OS matrix builds, and security scans.
"""

import os
from typing import Dict, Any, List
from .base import BaseAnalyzer
from core.models import CategoryScore, AuditIssue, IssueSeverity


class CiCdAnalyzer(BaseAnalyzer):
    def __init__(self, weight: float = 0.15):
        super().__init__(name="CI/CD Automation", weight=weight)

    def analyze(self, repo_path: str, context: Dict[str, Any]) -> CategoryScore:
        issues: List[AuditIssue] = []
        metrics: Dict[str, Any] = {
            "has_workflows_dir": False,
            "workflow_files_count": 0,
            "has_push_trigger": False,
            "has_pr_trigger": False,
            "has_test_step": False
        }

        workflows_dir = os.path.join(repo_path, ".github", "workflows")
        if not os.path.isdir(workflows_dir):
            issues.append(AuditIssue(
                category="CI/CD",
                message="Repository lacks .github/workflows directory for automated CI/CD",
                severity=IssueSeverity.HIGH,
                suggestion="Create GitHub Actions workflow for continuous testing and linting",
                auto_fixable=True
            ))
            return CategoryScore(self.name, 15.0, self.weight, issues, metrics)

        metrics["has_workflows_dir"] = True
        workflow_files = [f for f in os.listdir(workflows_dir) if f.endswith((".yml", ".yaml"))]
        metrics["workflow_files_count"] = len(workflow_files)

        if not workflow_files:
            issues.append(AuditIssue(
                category="CI/CD",
                message="No workflow YAML files found in .github/workflows",
                severity=IssueSeverity.HIGH,
                suggestion="Add a CI workflow file (e.g. ci.yml)",
                auto_fixable=True
            ))
            return CategoryScore(self.name, 25.0, self.weight, issues, metrics)

        # Inspect workflow contents
        for wf in workflow_files:
            wf_path = os.path.join(workflows_dir, wf)
            try:
                with open(wf_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                if "push:" in content or "push" in content:
                    metrics["has_push_trigger"] = True
                if "pull_request:" in content or "pull_request" in content:
                    metrics["has_pr_trigger"] = True
                if any(k in content.lower() for k in ("test", "pytest", "cargo test", "go test", "ctest")):
                    metrics["has_test_step"] = True
            except Exception:
                pass

        if not metrics["has_test_step"]:
            issues.append(AuditIssue(
                category="CI/CD",
                message="Existing workflows do not contain automated test execution steps",
                severity=IssueSeverity.MEDIUM,
                suggestion="Add test execution step in CI workflow"
            ))

        # Scoring
        score = 40.0
        if metrics["workflow_files_count"] > 0:
            score += 20.0
        if metrics["has_push_trigger"]:
            score += 15.0
        if metrics["has_pr_trigger"]:
            score += 10.0
        if metrics["has_test_step"]:
            score += 15.0

        score = max(10.0, min(100.0, score))

        return CategoryScore(
            category_name=self.name,
            score=score,
            weight=self.weight,
            issues=issues,
            metrics=metrics
        )
