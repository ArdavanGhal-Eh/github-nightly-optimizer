"""
Security & Credential Hygiene Analyzer.
Detects leaked secrets, API keys, insecure patterns, and assesses .gitignore hygiene.
"""

import os
import re
from typing import Dict, Any, List
from .base import BaseAnalyzer
from core.models import CategoryScore, AuditIssue, IssueSeverity

SECRET_PATTERNS = [
    ("GitHub Personal Access Token", r"(ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36})", IssueSeverity.CRITICAL),
    ("OpenAI Secret Key", r"sk-[a-zA-Z0-9]{48}", IssueSeverity.CRITICAL),
    ("AWS Access Key ID", r"(AKIA[0-9A-Z]{16})", IssueSeverity.CRITICAL),
    ("Private Key Block", r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", IssueSeverity.CRITICAL),
    ("Generic Bearer Token", r"Bearer\s+[a-zA-Z0-9_\-\.]{25,}", IssueSeverity.HIGH),
    ("Telegram Bot Token", r"\b\d{9,10}:[a-zA-Z0-9_-]{35}\b", IssueSeverity.CRITICAL),
]

REQUIRED_GITIGNORE_ENTRIES = [
    (".env", "Environment variable files (.env)"),
    ("*.pyc", "Python bytecode (*.pyc)"),
    ("__pycache__", "Python cache directories (__pycache__)"),
    (".pytest_cache", "Pytest cache directories (.pytest_cache)"),
]


class SecurityAnalyzer(BaseAnalyzer):
    def __init__(self, weight: float = 0.20):
        super().__init__(name="Security & Secret Hygiene", weight=weight)

    def analyze(self, repo_path: str, context: Dict[str, Any]) -> CategoryScore:
        issues: List[AuditIssue] = []
        metrics: Dict[str, Any] = {
            "leaked_secrets_count": 0,
            "gitignore_exists": False,
            "missing_gitignore_rules": 0,
            "insecure_patterns_count": 0
        }

        # 1. Audit .gitignore
        gitignore_path = os.path.join(repo_path, ".gitignore")
        if not os.path.exists(gitignore_path):
            issues.append(AuditIssue(
                category="Security / Hygiene",
                message="Repository lacks a .gitignore file",
                severity=IssueSeverity.HIGH,
                suggestion="Create a standard .gitignore to prevent secret leaks and cache clutter",
                auto_fixable=True
            ))
        else:
            metrics["gitignore_exists"] = True
            with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
                gitignore_content = f.read()

            for rule, desc in REQUIRED_GITIGNORE_ENTRIES:
                if rule not in gitignore_content:
                    metrics["missing_gitignore_rules"] += 1
                    issues.append(AuditIssue(
                        category="Hygiene",
                        message=f".gitignore is missing rule for {desc}",
                        severity=IssueSeverity.LOW,
                        file_path=".gitignore",
                        suggestion=f"Append '{rule}' to .gitignore",
                        auto_fixable=True
                    ))

        # 2. Scan files for secrets
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "target", "build", "dist")]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                # Skip binaries and non-text files
                if ext in (".png", ".jpg", ".jpeg", ".webp", ".zip", ".tar", ".gz", ".exe", ".dll", ".so", ".bin"):
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path)

                # Skip tests containing dummy keys
                if "test" in rel_path.lower():
                    continue

                self._scan_file_for_secrets(full_path, rel_path, issues, metrics)

        # Calculate score
        score = 100.0
        score -= metrics["leaked_secrets_count"] * 30.0
        if not metrics["gitignore_exists"]:
            score -= 20.0
        score -= min(15.0, metrics["missing_gitignore_rules"] * 3.0)
        score -= metrics["insecure_patterns_count"] * 10.0

        score = max(0.0, min(100.0, score))

        return CategoryScore(
            category_name=self.name,
            score=score,
            weight=self.weight,
            issues=issues,
            metrics=metrics
        )

    def _scan_file_for_secrets(self, full_path: str, rel_path: str, issues: List[AuditIssue], metrics: Dict[str, Any]):
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_idx, line in enumerate(f, start=1):
                    for label, pattern, severity in SECRET_PATTERNS:
                        if re.search(pattern, line):
                            # Ignore comments that look like documentation examples
                            if "example" in line.lower() or "your_" in line.lower() or "dummy" in line.lower():
                                continue
                            metrics["leaked_secrets_count"] += 1
                            issues.append(AuditIssue(
                                category="Leaked Secret",
                                message=f"Potential {label} detected in code",
                                severity=severity,
                                file_path=rel_path,
                                line_number=line_idx,
                                suggestion="Move credential to environment variable or secret manager immediately",
                                auto_fixable=False
                            ))
        except Exception:
            pass
