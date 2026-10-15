"""
Unified Health Scoring Engine.
Orchestrates all analyzers and calculates weighted repository health scores.
"""

import datetime
from typing import Dict, Any, List
from core.models import RepoHealthReport, CategoryScore, AuditIssue
from core.git_service import GitService
from .base import BaseAnalyzer
from .code_quality import CodeQualityAnalyzer
from .security import SecurityAnalyzer
from .test_suite import TestSuiteAnalyzer
from .documentation import DocumentationAnalyzer
from .ci_cd import CiCdAnalyzer


class HealthScoringEngine:
    def __init__(self, enabled_analyzers: List[str]):
        self.analyzers: List[BaseAnalyzer] = []
        if "code_quality" in enabled_analyzers:
            self.analyzers.append(CodeQualityAnalyzer(weight=0.25))
        if "test_suite" in enabled_analyzers:
            self.analyzers.append(TestSuiteAnalyzer(weight=0.25))
        if "security" in enabled_analyzers:
            self.analyzers.append(SecurityAnalyzer(weight=0.20))
        if "documentation" in enabled_analyzers:
            self.analyzers.append(DocumentationAnalyzer(weight=0.15))
        if "ci_cd" in enabled_analyzers:
            self.analyzers.append(CiCdAnalyzer(weight=0.15))

    def evaluate_repository(self, repo_name: str, repo_path: str) -> RepoHealthReport:
        """Runs all analyzers on repo and produces a structured health report."""
        context: Dict[str, Any] = {}
        category_scores: Dict[str, CategoryScore] = {}
        all_issues: List[AuditIssue] = []

        total_weight = sum(a.weight for a in self.analyzers) or 1.0
        weighted_sum = 0.0

        for analyzer in self.analyzers:
            cat_score = analyzer.analyze(repo_path, context)
            category_scores[analyzer.name] = cat_score
            all_issues.extend(cat_score.issues)
            weighted_sum += (cat_score.score * cat_score.weight)

        total_score = round(weighted_sum / total_weight, 2)

        # Retrieve git info
        git_service = GitService(repo_path)
        git_info = git_service.get_git_info()
        remote_url = git_info.remote_url if git_info else ""

        return RepoHealthReport(
            repo_name=repo_name,
            local_path=repo_path,
            remote_url=remote_url,
            timestamp=datetime.datetime.now().isoformat(),
            total_score=total_score,
            category_scores=category_scores,
            all_issues=all_issues,
            git_info=git_info,
            primary_language=context.get("primary_language", "Unknown")
        )
