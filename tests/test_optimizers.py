"""
Unit Tests for Autonomous Optimizers.
"""

import os
import tempfile
import pytest
from core.models import RepoHealthReport
from optimizers import (
    CodeCleanerOptimizer,
    SecurityGuardOptimizer,
    DocEnhancerOptimizer,
    TestSynthesizerOptimizer,
    CiCdHardenerOptimizer
)


def create_dummy_report(lang="Python", score=50.0) -> RepoHealthReport:
    return RepoHealthReport(
        repo_name="dummy",
        local_path="",
        remote_url="",
        timestamp="",
        total_score=score,
        primary_language=lang
    )


def test_security_guard_optimizer():
    opt = SecurityGuardOptimizer()
    with tempfile.TemporaryDirectory() as tmpdir:
        report = create_dummy_report()
        changes = opt.optimize(tmpdir, report)

        assert len(changes) > 0
        gitignore_path = os.path.join(tmpdir, ".gitignore")
        assert os.path.exists(gitignore_path)
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert ".env" in content
            assert "__pycache__/" in content


def test_code_cleaner_optimizer():
    opt = CodeCleanerOptimizer()
    with tempfile.TemporaryDirectory() as tmpdir:
        py_file = os.path.join(tmpdir, "main.py")
        with open(py_file, "w", encoding="utf-8") as f:
            f.write("def foo():   \n    x = 1    \n")

        report = create_dummy_report()
        changes = opt.optimize(tmpdir, report)

        assert len(changes) > 0
        with open(py_file, "r", encoding="utf-8") as f:
            cleaned = f.read()
            assert cleaned == "def foo():\n    x = 1\n"


def test_doc_enhancer_rule_004():
    opt = DocEnhancerOptimizer()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create README.md and separate forbidden README_FA.md
        readme_path = os.path.join(tmpdir, "README.md")
        readme_fa_path = os.path.join(tmpdir, "README_FA.md")

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("# Project Name\n\nEnglish description here.")
        with open(readme_fa_path, "w", encoding="utf-8") as f:
            f.write("این پروژه یک ابزار مهندسی است.")

        report = create_dummy_report()
        changes = opt.optimize(tmpdir, report)

        assert not os.path.exists(readme_fa_path), "Separate README_FA.md should be deleted per RULE-004"
        with open(readme_path, "r", encoding="utf-8") as f:
            consolidated = f.read()
            assert "راهنمای فارسی" in consolidated
            assert "این پروژه یک ابزار مهندسی است." in consolidated


def test_test_synthesizer_optimizer():
    opt = TestSynthesizerOptimizer()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a module
        with open(os.path.join(tmpdir, "calculator.py"), "w", encoding="utf-8") as f:
            f.write("def add(a, b): return a + b\n")

        report = create_dummy_report()
        changes = opt.optimize(tmpdir, report)

        test_file = os.path.join(tmpdir, "tests", "test_integrity.py")
        assert os.path.exists(test_file)
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "test_module_import_integrity" in content
