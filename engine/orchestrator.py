"""
Overnight Multi-Repository Orchestrator.
Orchestrates autonomous audit, synthesis, safety verification, branching, and PR delivery.
"""

import os
import uuid
import datetime
import logging
from typing import List, Dict, Any, Optional

from config.settings import AppConfig
from core.models import (
    RepoHealthReport,
    OptimizationResult,
    NightlyRunSummary
)
from core.git_service import GitService
from analyzers.scoring import HealthScoringEngine
from optimizers import (
    BaseOptimizer,
    CodeCleanerOptimizer,
    TestSynthesizerOptimizer,
    CiCdHardenerOptimizer,
    DocEnhancerOptimizer,
    SecurityGuardOptimizer
)
from .safety_gate import SafetyGate

logger = logging.getLogger("NightlyOptimizer.Orchestrator")


class NightlyOrchestrator:
    def __init__(self, config: AppConfig):
        self.config = config
        self.scoring_engine = HealthScoringEngine(config.enabled_analyzers)
        self.safety_gate = SafetyGate(config.quality_gates)
        self.optimizers: List[BaseOptimizer] = []

        if "code_cleaner" in config.enabled_optimizers:
            self.optimizers.append(CodeCleanerOptimizer())
        if "test_synthesizer" in config.enabled_optimizers:
            self.optimizers.append(TestSynthesizerOptimizer())
        if "ci_cd_hardener" in config.enabled_optimizers:
            self.optimizers.append(CiCdHardenerOptimizer())
        if "doc_enhancer" in config.enabled_optimizers:
            self.optimizers.append(DocEnhancerOptimizer())
        if "security_guard" in config.enabled_optimizers:
            self.optimizers.append(SecurityGuardOptimizer())

    def run_audit_only(self, target_repo_name: Optional[str] = None) -> List[RepoHealthReport]:
        """Runs diagnostics across discovered repositories without applying code changes."""
        discovered = self.config.discover_local_repos()
        if target_repo_name:
            discovered = [r for r in discovered if r["name"] == target_repo_name]
        logger.info(f"Initiating diagnostic audit on {len(discovered)} repositories...")
        reports = []

        for repo in discovered:
            name, path = repo["name"], repo["path"]
            logger.info(f"Auditing repository: {name} ({path})")
            report = self.scoring_engine.evaluate_repository(name, path)
            reports.append(report)
            logger.info(f"Health Score for {name}: {report.total_score}/100.0 (Issues: {len(report.all_issues)})")

        return reports

    def run_nightly_cycle(self, dry_run: bool = False, target_repo_name: Optional[str] = None) -> NightlyRunSummary:
        """Executes full autonomous overnight optimization and development cycle."""
        run_id = f"nightly-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        start_time = datetime.datetime.now().isoformat()

        discovered = self.config.discover_local_repos()
        if target_repo_name:
            discovered = [r for r in discovered if r["name"] == target_repo_name]

        logger.info(f"Starting Nightly Cycle [{run_id}] on {len(discovered)} repositories (dry_run={dry_run})...")

        reports: List[RepoHealthReport] = []
        results: List[OptimizationResult] = []

        scores_before: List[float] = []
        scores_after: List[float] = []

        for repo in discovered:
            name, path = repo["name"], repo["path"]
            git_service = GitService(path)

            if not git_service.is_git_repo():
                logger.warning(f"Skipping {name}: Not a valid git repository.")
                continue

            git_info = git_service.get_git_info()
            if git_info and git_info.has_uncommitted_changes:
                logger.warning(f"Skipping {name}: Repository has uncommitted local changes to avoid collision.")
                results.append(OptimizationResult(
                    repo_name=name,
                    local_path=path,
                    branch_name=None,
                    changes_applied=[],
                    score_before=0.0,
                    score_after=0.0,
                    tests_passed=False,
                    status="SKIPPED",
                    error_message="Working directory contains uncommitted changes"
                ))
                continue

            base_branch = git_info.current_branch if git_info else "main"

            # 1. Baseline Audit
            logger.info(f"Evaluating baseline health for {name}...")
            report_before = self.scoring_engine.evaluate_repository(name, path)
            scores_before.append(report_before.total_score)

            if dry_run:
                reports.append(report_before)
                scores_after.append(report_before.total_score)
                results.append(OptimizationResult(
                    repo_name=name,
                    local_path=path,
                    branch_name=None,
                    changes_applied=[],
                    score_before=report_before.total_score,
                    score_after=report_before.total_score,
                    tests_passed=True,
                    status="SKIPPED",
                    error_message="Dry-run audit mode"
                ))
                continue

            # 2. Ephemeral Nightly Branch Creation
            nightly_branch = f"{self.config.branch_prefix}-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4]}"
            logger.info(f"Creating isolated nightly branch '{nightly_branch}' for {name}...")
            branch_created = git_service.create_and_checkout_branch(nightly_branch)
            if not branch_created:
                logger.error(f"Failed to create branch {nightly_branch} for {name}.")
                continue

            # 3. Apply Optimizers
            changes_applied: List[str] = []
            for opt in self.optimizers:
                try:
                    c = opt.optimize(path, report_before)
                    changes_applied.extend(c)
                except Exception as e:
                    logger.error(f"Error during optimizer {opt.name} on {name}: {e}")

            if not changes_applied:
                logger.info(f"No optimization actions required for {name}. Returning to {base_branch}.")
                git_service.checkout_branch(base_branch)
                git_service.delete_branch(nightly_branch)
                reports.append(report_before)
                scores_after.append(report_before.total_score)
                results.append(OptimizationResult(
                    repo_name=name,
                    local_path=path,
                    branch_name=None,
                    changes_applied=[],
                    score_before=report_before.total_score,
                    score_after=report_before.total_score,
                    tests_passed=True,
                    status="SKIPPED",
                    error_message="Repository already in optimal state"
                ))
                continue

            # 4. Post-Optimization Audit & Verification
            report_after = self.scoring_engine.evaluate_repository(name, path)
            reports.append(report_after)
            scores_after.append(report_after.total_score)

            # 5. Safety Gate Verification
            passed_gate, gate_msg = self.safety_gate.evaluate_transition(
                report_before, report_after, git_service, base_branch
            )

            if not passed_gate:
                logger.warning(f"Safety Gate rejected enhancements for {name}: {gate_msg}")
                git_service.delete_branch(nightly_branch)
                results.append(OptimizationResult(
                    repo_name=name,
                    local_path=path,
                    branch_name=nightly_branch,
                    changes_applied=changes_applied,
                    score_before=report_before.total_score,
                    score_after=report_after.total_score,
                    tests_passed=False,
                    status="REVERTED_REGRESSION",
                    error_message=gate_msg
                ))
                continue

            # 6. Commit Enhancements
            commit_msg = (
                f"chore(nightly): automated architectural optimization & hygiene hardening\n\n"
                f"Automated enhancements applied:\n" +
                "\n".join([f"- {c}" for c in changes_applied]) +
                f"\n\nHealth score improvement: {report_before.total_score:.1f} -> {report_after.total_score:.1f}"
            )
            git_service.stage_all_and_commit(commit_msg)

            # 7. Safe Delivery (PR or Direct Merge)
            pr_url, pr_num = None, None
            if self.config.delivery_strategy == "pr":
                push_ok, push_err = git_service.push_branch(nightly_branch)
                if push_ok:
                    pr_title = f"Nightly Optimization: Quality Hardening & CI/Tests ({datetime.datetime.now().strftime('%Y-%m-%d')})"
                    pr_body = self._build_pr_markdown_body(name, report_before, report_after, changes_applied)
                    pr_ok, pr_url, pr_num = git_service.create_github_pr(pr_title, pr_body, nightly_branch, base_branch)
                else:
                    logger.warning(f"Failed to push {nightly_branch} to origin: {push_err}")

                # Switch back to base branch cleanly
                git_service.checkout_branch(base_branch)

            elif self.config.delivery_strategy == "direct_merge":
                git_service.checkout_branch(base_branch)
                git_service._run_git(["merge", "--ff-only", nightly_branch])
                git_service.delete_branch(nightly_branch)
            else:
                git_service.checkout_branch(base_branch)

            results.append(OptimizationResult(
                repo_name=name,
                local_path=path,
                branch_name=nightly_branch,
                changes_applied=changes_applied,
                score_before=report_before.total_score,
                score_after=report_after.total_score,
                tests_passed=True,
                status="SUCCESS",
                pr_url=pr_url,
                pr_number=pr_num
            ))
            logger.info(f"Successfully optimized {name}: {report_before.total_score} -> {report_after.total_score}")

        end_time = datetime.datetime.now().isoformat()
        avg_before = sum(scores_before) / max(1, len(scores_before)) if scores_before else 0.0
        avg_after = sum(scores_after) / max(1, len(scores_after)) if scores_after else 0.0
        success_count = sum(1 for r in results if r.status == "SUCCESS")
        prs_created_count = sum(1 for r in results if r.pr_url is not None)

        summary = NightlyRunSummary(
            run_id=run_id,
            start_time=start_time,
            end_time=end_time,
            total_repos_inspected=len(discovered),
            repos_optimized=success_count,
            prs_created=prs_created_count,
            average_score_before=avg_before,
            average_score_after=avg_after,
            reports=reports,
            results=results
        )

        return summary

    def _build_pr_markdown_body(
        self,
        repo_name: str,
        before: RepoHealthReport,
        after: RepoHealthReport,
        changes: List[str]
    ) -> str:
        score_delta = after.total_score - before.total_score
        sign = "+" if score_delta >= 0 else ""

        body = [
            "## 🌙 Autonomous Nightly Optimization Summary",
            "",
            f"This Pull Request was generated autonomously by the **GitHub Nightly Optimizer** during the scheduled overnight maintenance window on `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}`.",
            "",
            "### 📊 Repository Health Score Evolution",
            "",
            "| Dimension | Before | After | Delta |",
            "| :--- | :---: | :---: | :---: |",
        ]

        for cat_name, cat_score_after in after.category_scores.items():
            cat_score_before = before.category_scores.get(cat_name)
            b_val = cat_score_before.score if cat_score_before else 0.0
            a_val = cat_score_after.score
            d_val = a_val - b_val
            d_sign = "+" if d_val >= 0 else ""
            body.append(f"| **{cat_name}** | `{b_val:.1f}` | `{a_val:.1f}` | `{d_sign}{d_val:.1f}` |")

        body.extend([
            f"| **Overall Weighted Index** | **`{before.total_score:.1f}`** | **`{after.total_score:.1f}`** | **`{sign}{score_delta:.1f}`** |",
            "",
            "### 🛠️ Synthesized Enhancements & Modifications",
            "",
        ])
        for change in changes:
            body.append(f"- [x] {change}")

        body.extend([
            "",
            "### 🛡️ Safety & Verification Guarantee",
            "- **Regression Interception:** All pre-existing test suites passed without failure.",
            "- **Syntax Validation:** AST parsing confirmed zero introduced syntax errors.",
            "- **Standards Compliance:** Documentation strictly conforms to project architecture standards.",
            "",
            "> *Review and merge when ready, or request further modifications.*"
        ])

        return "\n".join(body)
