"""
Unit Tests for Audit Analyzers.
"""

import os
import tempfile
import pytest
from analyzers import (
    CodeQualityAnalyzer,
    SecurityAnalyzer,
    DocumentationAnalyzer,
    CiCdAnalyzer,
    HealthScoringEngine
)


def test_code_quality_analyzer_python():
    analyzer = CodeQualityAnalyzer()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a sample python file with a wildcard import
        py_file = os.path.join(tmpdir, "sample.py")
        with open(py_file, "w", encoding="utf-8") as f:
            f.write("from math import *\n\ndef compute(x):\n    return x * 2\n")

        context = {}
        score = analyzer.analyze(tmpdir, context)

        assert score.score > 0
        assert context.get("primary_language") == "Python"
        assert score.metrics["wildcard_imports"] == 1


def test_security_analyzer_secret_detection():
    analyzer = SecurityAnalyzer()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a sample file with a fake GitHub token
        py_file = os.path.join(tmpdir, "config.py")
        with open(py_file, "w", encoding="utf-8") as f:
            f.write("TOKEN = 'ghp_123456789012345678901234567890123456'\n")

        context = {}
        score = analyzer.analyze(tmpdir, context)

        assert score.metrics["leaked_secrets_count"] == 1
        assert any(i.category == "Leaked Secret" for i in score.issues)


def test_documentation_analyzer_rules():
    analyzer = DocumentationAnalyzer()
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Missing readme
        score = analyzer.analyze(tmpdir, {})
        assert score.score <= 30.0

        # 2. Add README and LICENSE
        with open(os.path.join(tmpdir, "README.md"), "w", encoding="utf-8") as f:
            f.write("# Sample Project\n\n[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)]()\n\n## معماری\nتوضیحات سیستم.\n")
        with open(os.path.join(tmpdir, "LICENSE"), "w", encoding="utf-8") as f:
            f.write("MIT License\n")

        score2 = analyzer.analyze(tmpdir, {})
        assert score2.score > 70.0
        assert score2.metrics["has_persian_section"] is True
