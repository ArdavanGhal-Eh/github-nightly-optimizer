"""
Core Data Models for GitHub Nightly Autonomous Optimizer.
Provides typed schemas for diagnostics, health scoring, optimizations, and execution reports.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional
import datetime


class IssueSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class AuditIssue:
    category: str
    message: str
    severity: IssueSeverity
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


@dataclass
class CategoryScore:
    category_name: str
    score: float  # 0.0 to 100.0
    weight: float  # 0.0 to 1.0
    issues: List[AuditIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category_name": self.category_name,
            "score": round(self.score, 2),
            "weight": self.weight,
            "issues": [i.to_dict() for i in self.issues],
            "metrics": self.metrics
        }


@dataclass
class GitInfo:
    current_branch: str
    latest_commit_hash: str
    latest_commit_msg: str
    has_uncommitted_changes: bool
    remote_url: str
    default_branch: str = "main"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RepoHealthReport:
    repo_name: str
    local_path: str
    remote_url: str
    timestamp: str
    total_score: float  # 0.0 to 100.0
    category_scores: Dict[str, CategoryScore] = field(default_factory=dict)
    all_issues: List[AuditIssue] = field(default_factory=list)
    git_info: Optional[GitInfo] = None
    primary_language: str = "Unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo_name": self.repo_name,
            "local_path": self.local_path,
            "remote_url": self.remote_url,
            "timestamp": self.timestamp,
            "total_score": round(self.total_score, 2),
            "category_scores": {k: v.to_dict() for k, v in self.category_scores.items()},
            "all_issues": [i.to_dict() for i in self.all_issues],
            "git_info": self.git_info.to_dict() if self.git_info else None,
            "primary_language": self.primary_language
        }


@dataclass
class OptimizationResult:
    repo_name: str
    local_path: str
    branch_name: Optional[str]
    changes_applied: List[str]
    score_before: float
    score_after: float
    tests_passed: bool
    status: str  # 'SUCCESS', 'SKIPPED', 'REVERTED_REGRESSION', 'FAILED'
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NightlyRunSummary:
    run_id: str
    start_time: str
    end_time: str
    total_repos_inspected: int
    repos_optimized: int
    prs_created: int
    average_score_before: float
    average_score_after: float
    reports: List[RepoHealthReport] = field(default_factory=list)
    results: List[OptimizationResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_repos_inspected": self.total_repos_inspected,
            "repos_optimized": self.repos_optimized,
            "prs_created": self.prs_created,
            "average_score_before": round(self.average_score_before, 2),
            "average_score_after": round(self.average_score_after, 2),
            "reports": [r.to_dict() for r in self.reports],
            "results": [res.to_dict() for res in self.results]
        }
