"""
Unit Tests for Safety Gate and Orchestrator Logic.
"""

import os
import subprocess
import tempfile
import pytest
from core.models import RepoHealthReport, CategoryScore
from core.git_service import GitService
from config.settings import AppConfig, QualityGates
from engine.safety_gate import SafetyGate
from engine.orchestrator import NightlyOrchestrator
from config.settings import AppConfig


def init_mock_git_repo(path: str):
    """Initializes a local git repository in path for testing."""
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "TestUser"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=path, capture_output=True, check=True)

    # Initial file and commit
    with open(os.path.join(path, "README.md"), "w", encoding="utf-8") as f:
        f.write("# Mock Project\n\nInitial content.")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=path, capture_output=True, check=True)


def test_safety_gate_regression_prevention():
    qg = QualityGates(allow_regression=False, min_score_for_pr=60.0)
    gate = SafetyGate(qg)

    with tempfile.TemporaryDirectory() as tmpdir:
        init_mock_git_repo(tmpdir)
        git_svc = GitService(tmpdir)

        before = RepoHealthReport(
            repo_name="mock", local_path=tmpdir, remote_url="", timestamp="", total_score=85.0
        )
        # Artificially degraded report
        after = RepoHealthReport(
            repo_name="mock", local_path=tmpdir, remote_url="", timestamp="", total_score=70.0
        )

        passed, msg = gate.evaluate_transition(before, after, git_svc, "main")
        assert passed is False
        assert "Regression detected" in msg


def test_safety_gate_approval():
    qg = QualityGates(allow_regression=False, min_score_for_pr=60.0)
    gate = SafetyGate(qg)

    with tempfile.TemporaryDirectory() as tmpdir:
        init_mock_git_repo(tmpdir)
        git_svc = GitService(tmpdir)

        before = RepoHealthReport(
            repo_name="mock", local_path=tmpdir, remote_url="", timestamp="", total_score=75.0
        )
        after = RepoHealthReport(
            repo_name="mock", local_path=tmpdir, remote_url="", timestamp="", total_score=88.0
        )

        passed, msg = gate.evaluate_transition(before, after, git_svc, "main")
        assert passed is True


def test_orchestrator_dry_run():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = os.path.join(tmpdir, "test_repo")
        os.makedirs(repo_dir)
        init_mock_git_repo(repo_dir)

        config = AppConfig(
            monitored_directories=[tmpdir],
            target_repos=["*"],
            delivery_strategy="branch_only"
        )
        orchestrator = NightlyOrchestrator(config)
        summary = orchestrator.run_nightly_cycle(dry_run=True)

        assert summary.total_repos_inspected == 1
        assert summary.reports[0].repo_name == "test_repo"
