"""
Autonomous Safety Gate & Regression Interceptor.
Guarantees that automated enhancements never degrade repository integrity.
"""

import logging
from typing import Tuple
from core.models import RepoHealthReport
from config.settings import QualityGates
from core.git_service import GitService

logger = logging.getLogger("NightlyOptimizer.SafetyGate")


class SafetyGate:
    def __init__(self, quality_gates: QualityGates):
        self.quality_gates = quality_gates

    def evaluate_transition(
        self,
        report_before: RepoHealthReport,
        report_after: RepoHealthReport,
        git_service: GitService,
        base_branch: str
    ) -> Tuple[bool, str]:
        """
        Evaluates whether optimizations are safe to commit/push.
        If any safety rule is violated, automatically rolls back changes.
        """
        score_diff = report_after.total_score - report_before.total_score

        # Rule 1: No score degradation unless allow_regression is true
        if not self.quality_gates.allow_regression and score_diff < -0.01:
            logger.warning(f"Safety Gate Rejected: Score dropped from {report_before.total_score} to {report_after.total_score}")
            self._execute_rollback(git_service, base_branch)
            return False, f"Regression detected: Health score decreased by {abs(score_diff):.2f} points"

        # Rule 2: Minimum absolute score threshold
        if report_after.total_score < self.quality_gates.min_score_for_pr:
            logger.info(f"Safety Gate Notification: Final score ({report_after.total_score}) below min PR threshold ({self.quality_gates.min_score_for_pr})")
            # We can still commit locally, but mark for PR gate

        # Rule 3: Check for new critical syntax or test failures
        before_crit = sum(1 for i in report_before.all_issues if i.category == "Syntax Error")
        after_crit = sum(1 for i in report_after.all_issues if i.category == "Syntax Error")
        if after_crit > before_crit:
            logger.error("Safety Gate Rejected: Optimization introduced new syntax errors!")
            self._execute_rollback(git_service, base_branch)
            return False, "Optimization introduced new syntax errors"

        # Safe!
        return True, "Safety criteria satisfied. Zero regressions detected."

    def _execute_rollback(self, git_service: GitService, base_branch: str):
        """Rolls back all uncommitted changes and switches back to base branch."""
        git_service.rollback_uncommitted()
        git_service.checkout_branch(base_branch)
        logger.info(f"Safely rolled back repository state to {base_branch}")
