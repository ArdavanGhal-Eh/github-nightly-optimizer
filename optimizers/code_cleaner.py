"""
Code Cleaner & Normalization Optimizer.
Eliminates trailing whitespace, enforces UTF-8, and normalizes EOF newlines.
"""

import os
from typing import List
from .base import BaseOptimizer
from core.models import RepoHealthReport

TARGET_EXTENSIONS = {".py", ".rs", ".go", ".cpp", ".hpp", ".c", ".h", ".js", ".ts", ".json", ".md", ".yml", ".yaml"}


class CodeCleanerOptimizer(BaseOptimizer):
    def __init__(self):
        super().__init__(name="Code Cleaner & Normalizer")

    def optimize(self, repo_path: str, report: RepoHealthReport) -> List[str]:
        changes: List[str] = []
        cleaned_files_count = 0

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "target", "build", "venv")]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in TARGET_EXTENSIONS:
                    continue

                full_path = os.path.join(root, file)
                if self._clean_file(full_path):
                    cleaned_files_count += 1

        if cleaned_files_count > 0:
            changes.append(f"Normalized line endings and removed trailing whitespaces in {cleaned_files_count} source files")

        return changes

    def _clean_file(self, full_path: str) -> bool:
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.splitlines()
            cleaned_lines = [line.rstrip() for line in lines]
            cleaned_content = "\n".join(cleaned_lines) + "\n"

            if cleaned_content != content:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(cleaned_content)
                return True
            return False
        except Exception:
            return False
