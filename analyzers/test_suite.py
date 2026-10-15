"""
Test Suite Coverage & Execution Analyzer.
Discovers unit/integration tests, runs pytest safely with isolation, and computes test readiness.
"""

import os
import subprocess
from typing import Dict, Any, List
from .base import BaseAnalyzer
from core.models import CategoryScore, AuditIssue, IssueSeverity


class TestSuiteAnalyzer(BaseAnalyzer):
    def __init__(self, weight: float = 0.25):
        super().__init__(name="Test Robustness & Verification", weight=weight)

    def analyze(self, repo_path: str, context: Dict[str, Any]) -> CategoryScore:
        issues: List[AuditIssue] = []
        metrics: Dict[str, Any] = {
            "has_tests_dir": False,
            "test_files_count": 0,
            "source_files_count": 0,
            "tests_collected": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "execution_attempted": False,
            "execution_successful": False
        }

        # Check directories
        tests_dir = os.path.join(repo_path, "tests")
        if os.path.isdir(tests_dir):
            metrics["has_tests_dir"] = True

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "target", "build", "node_modules")]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                name = file.lower()
                if ext in (".py", ".rs", ".go", ".cpp"):
                    if "test" in name:
                        metrics["test_files_count"] += 1
                    else:
                        metrics["source_files_count"] += 1

        primary_lang = context.get("primary_language", "Python")

        if metrics["test_files_count"] == 0:
            issues.append(AuditIssue(
                category="Testing",
                message="No test files discovered in repository",
                severity=IssueSeverity.HIGH,
                suggestion="Synthesize automated unit tests to ensure software reliability",
                auto_fixable=True
            ))

        # Attempt safe execution if Python
        if primary_lang == "Python" and metrics["test_files_count"] > 0:
            self._run_python_tests(repo_path, issues, metrics)

        # Compute Score
        score = 0.0
        if metrics["has_tests_dir"] or metrics["test_files_count"] > 0:
            score += 35.0
            # Test to source ratio
            ratio = metrics["test_files_count"] / max(1, metrics["source_files_count"])
            score += min(35.0, ratio * 70.0)

            if metrics["execution_attempted"]:
                if metrics["execution_successful"] and metrics["tests_failed"] == 0:
                    score += 30.0
                elif metrics["tests_failed"] > 0:
                    score += 10.0
                else:
                    score += 15.0
            else:
                score += 15.0
        else:
            score = 15.0  # Basic baseline

        score = max(5.0, min(100.0, score))

        return CategoryScore(
            category_name=self.name,
            score=score,
            weight=self.weight,
            issues=issues,
            metrics=metrics
        )

    def _run_python_tests(self, repo_path: str, issues: List[AuditIssue], metrics: Dict[str, Any]):
        metrics["execution_attempted"] = True
        try:
            cmd = ["python", "-m", "pytest", "-q", "--disable-warnings", "--maxfail=5"]
            proc = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=25,
                encoding="utf-8",
                errors="replace"
            )

            metrics["test_stdout"] = proc.stdout.strip()[:500]
            if proc.returncode == 0:
                metrics["execution_successful"] = True
                # Parse passed count if possible (e.g., "5 passed in 0.23s")
                for line in proc.stdout.splitlines():
                    if "passed" in line:
                        metrics["tests_passed"] = 1
            else:
                metrics["execution_successful"] = False
                metrics["tests_failed"] = 1
                issues.append(AuditIssue(
                    category="Test Failure",
                    message="Unit test suite encountered failures or import errors during execution",
                    severity=IssueSeverity.HIGH,
                    suggestion="Fix failing tests or ensure required local mock fixtures are configured"
                ))
        except subprocess.TimeoutExpired:
            issues.append(AuditIssue(
                category="Test Timeout",
                message="Test suite execution timed out (>25s)",
                severity=IssueSeverity.MEDIUM,
                suggestion="Optimize slow integration tests or mock heavy external dependencies"
            ))
        except Exception as e:
            issues.append(AuditIssue(
                category="Test Runner",
                message=f"Could not execute pytest runner: {e}",
                severity=IssueSeverity.LOW
            ))
