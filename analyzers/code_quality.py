"""
Code Quality & Architectural Diagnostic Analyzer.
Analyzes code syntax, modularity, AST structures, docstring coverage, and manifests.
"""

import os
import ast
from typing import Dict, Any, List
from .base import BaseAnalyzer
from core.models import CategoryScore, AuditIssue, IssueSeverity


class CodeQualityAnalyzer(BaseAnalyzer):
    def __init__(self, weight: float = 0.25):
        super().__init__(name="Code Quality & Architecture", weight=weight)

    def analyze(self, repo_path: str, context: Dict[str, Any]) -> CategoryScore:
        issues: List[AuditIssue] = []
        metrics: Dict[str, Any] = {
            "total_files": 0,
            "py_files": 0,
            "rs_files": 0,
            "cpp_files": 0,
            "go_files": 0,
            "syntax_errors": 0,
            "missing_docstrings": 0,
            "wildcard_imports": 0,
            "trailing_whitespace_lines": 0
        }

        # Scan files
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden and cache dirs
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "target", "build", "venv", "node_modules")]

            for file in files:
                metrics["total_files"] += 1
                ext = os.path.splitext(file)[1].lower()
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path)

                if ext == ".py":
                    metrics["py_files"] += 1
                    self._audit_python_file(full_path, rel_path, issues, metrics)
                elif ext == ".rs":
                    metrics["rs_files"] += 1
                elif ext in (".cpp", ".hpp", ".cc", ".c", ".h"):
                    metrics["cpp_files"] += 1
                elif ext == ".go":
                    metrics["go_files"] += 1

                # Basic whitespace check on source files
                if ext in (".py", ".rs", ".go", ".cpp", ".hpp", ".c", ".h", ".js", ".ts", ".md"):
                    self._check_whitespace(full_path, rel_path, metrics)

        # Detect primary language
        lang_counts = {
            "Python": metrics["py_files"],
            "Rust": metrics["rs_files"],
            "C++": metrics["cpp_files"],
            "Go": metrics["go_files"]
        }
        primary_lang = max(lang_counts, key=lang_counts.get) if any(lang_counts.values()) else "Other"
        context["primary_language"] = primary_lang
        metrics["primary_language"] = primary_lang

        # Check manifests
        if primary_lang == "Rust" and not os.path.exists(os.path.join(repo_path, "Cargo.toml")):
            issues.append(AuditIssue(
                category="Manifest",
                message="Missing Cargo.toml in Rust project root",
                severity=IssueSeverity.HIGH,
                suggestion="Create a standard Cargo.toml package manifest"
            ))
        elif primary_lang == "Go" and not os.path.exists(os.path.join(repo_path, "go.mod")):
            issues.append(AuditIssue(
                category="Manifest",
                message="Missing go.mod in Go project root",
                severity=IssueSeverity.HIGH,
                suggestion="Initialize go module with 'go mod init <module_path>'"
            ))

        # Calculate Score
        score = 100.0
        score -= min(35.0, metrics["syntax_errors"] * 25.0)
        score -= min(20.0, metrics["wildcard_imports"] * 5.0)
        score -= min(15.0, metrics["missing_docstrings"] * 2.0)
        if metrics["trailing_whitespace_lines"] > 20:
            score -= 5.0

        if issues:
            for issue in issues:
                if issue.severity == IssueSeverity.CRITICAL:
                    score -= 20.0
                elif issue.severity == IssueSeverity.HIGH:
                    score -= 10.0

        score = max(10.0, min(100.0, score))

        return CategoryScore(
            category_name=self.name,
            score=score,
            weight=self.weight,
            issues=issues,
            metrics=metrics
        )

    def _audit_python_file(self, full_path: str, rel_path: str, issues: List[AuditIssue], metrics: Dict[str, Any]):
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=rel_path)

            for node in ast.walk(tree):
                # Wildcard imports check
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name == "*":
                            metrics["wildcard_imports"] += 1
                            issues.append(AuditIssue(
                                category="Code Quality",
                                message=f"Wildcard import 'from {node.module} import *' detected",
                                severity=IssueSeverity.MEDIUM,
                                file_path=rel_path,
                                line_number=node.lineno,
                                suggestion="Replace wildcard import with explicit symbol imports",
                                auto_fixable=False
                            ))

                # Function docstrings check
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if not node.name.startswith("_") and not ast.get_docstring(node):
                        metrics["missing_docstrings"] += 1
                        if metrics["missing_docstrings"] <= 5:  # Limit issue flood
                            issues.append(AuditIssue(
                                category="Documentation",
                                message=f"Public entity '{node.name}' lacks docstring",
                                severity=IssueSeverity.LOW,
                                file_path=rel_path,
                                line_number=node.lineno,
                                suggestion="Add concise docstring explaining behavior and arguments"
                            ))

        except SyntaxError as se:
            metrics["syntax_errors"] += 1
            issues.append(AuditIssue(
                category="Syntax Error",
                message=f"Syntax error: {se.msg}",
                severity=IssueSeverity.CRITICAL,
                file_path=rel_path,
                line_number=se.lineno,
                suggestion="Fix syntax error to ensure code executes without crash"
            ))
        except UnicodeDecodeError:
            issues.append(AuditIssue(
                category="Encoding",
                message="Non-UTF-8 encoding detected",
                severity=IssueSeverity.MEDIUM,
                file_path=rel_path,
                suggestion="Convert file encoding to standard UTF-8"
            ))

    def _check_whitespace(self, full_path: str, rel_path: str, metrics: Dict[str, Any]):
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.rstrip("\r\n") != line.rstrip():
                        metrics["trailing_whitespace_lines"] += 1
        except Exception:
            pass
