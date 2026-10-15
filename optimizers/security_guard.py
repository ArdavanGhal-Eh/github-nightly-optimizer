"""
Security & Hygiene Guard Optimizer.
Hardens repository boundaries by ensuring comprehensive .gitignore entries.
"""

import os
from typing import List
from .base import BaseOptimizer
from core.models import RepoHealthReport

STANDARD_GITIGNORE_RULES = [
    "# Environment and Secrets",
    ".env",
    ".env.*",
    "*.key",
    "*.pem",
    "",
    "# Python Artifacts & Cache",
    "__pycache__/",
    "*.py[cod]",
    "*$py.class",
    ".pytest_cache/",
    ".coverage",
    "htmlcov/",
    ".mypy_cache/",
    "",
    "# Build Artifacts & Virtual Environments",
    "venv/",
    "env/",
    ".venv/",
    "build/",
    "dist/",
    "target/",
    "",
    "# OS & Editor Artifacts",
    ".DS_Store",
    "Thumbs.db",
    "*.log"
]


class SecurityGuardOptimizer(BaseOptimizer):
    def __init__(self):
        super().__init__(name="Security & Hygiene Guard")

    def optimize(self, repo_path: str, report: RepoHealthReport) -> List[str]:
        changes: List[str] = []
        gitignore_path = os.path.join(repo_path, ".gitignore")

        if not os.path.exists(gitignore_path):
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write("\n".join(STANDARD_GITIGNORE_RULES) + "\n")
            changes.append("Created production-grade .gitignore preventing secret leaks and cache clutter")
        else:
            with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
                existing = f.read()

            missing_entries = []
            for entry in [".env", "__pycache__/", ".pytest_cache/", "*.py[cod]", "*.key"]:
                if entry not in existing:
                    missing_entries.append(entry)

            if missing_entries:
                with open(gitignore_path, "a", encoding="utf-8") as f:
                    f.write("\n# Nightly Hardened Hygiene Rules\n")
                    for rule in missing_entries:
                        f.write(f"{rule}\n")
                changes.append(f"Hardened .gitignore with rules: {', '.join(missing_entries)}")

        return changes
