"""
Git & GitHub CLI Service Layer.
Encapsulates all git operations, safe branching, staging, rollback, and GitHub PR creation.
"""

import os
import subprocess
import logging
from typing import Tuple, Optional, List, Dict, Any
from .models import GitInfo

logger = logging.getLogger("NightlyOptimizer.Git")


class GitService:
    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)

    def _run_git(self, args: List[str], check: bool = False) -> Tuple[int, str, str]:
        """Runs a git command inside the repository directory."""
        cmd = ["git"] + args
        try:
            proc = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if check and proc.returncode != 0:
                raise subprocess.CalledProcessError(proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr)
            return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
        except Exception as e:
            logger.error(f"Git command failed: {' '.join(cmd)} - Error: {e}")
            return -1, "", str(e)

    def is_git_repo(self) -> bool:
        """Verifies if the directory is a valid git repository."""
        code, out, _ = self._run_git(["rev-parse", "--is-inside-work-tree"])
        return code == 0 and out.strip() == "true"

    def get_git_info(self) -> Optional[GitInfo]:
        """Gathers repository state: branch, commit, dirty status, remote url."""
        if not self.is_git_repo():
            return None

        # Current branch
        _, branch, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if not branch:
            branch = "main"

        # Commit hash
        _, commit_hash, _ = self._run_git(["rev-parse", "--short", "HEAD"])

        # Commit message
        _, commit_msg, _ = self._run_git(["log", "-1", "--pretty=%s"])

        # Status check
        code, status_out, _ = self._run_git(["status", "--porcelain"])
        has_uncommitted = bool(status_out.strip())

        # Remote URL
        _, remote_url, _ = self._run_git(["config", "--get", "remote.origin.url"])

        return GitInfo(
            current_branch=branch,
            latest_commit_hash=commit_hash,
            latest_commit_msg=commit_msg,
            has_uncommitted_changes=has_uncommitted,
            remote_url=remote_url,
            default_branch="main"
        )

    def create_and_checkout_branch(self, branch_name: str) -> bool:
        """Safely creates and checks out a new branch for nightly enhancements."""
        code, _, err = self._run_git(["checkout", "-b", branch_name])
        if code != 0:
            # If already exists, just switch to it
            code, _, err = self._run_git(["checkout", branch_name])
        return code == 0

    def checkout_branch(self, branch_name: str) -> bool:
        """Switches to an existing branch."""
        code, _, _ = self._run_git(["checkout", branch_name])
        return code == 0

    def stage_all_and_commit(self, message: str) -> bool:
        """Stages all changes and creates a semantic commit."""
        self._run_git(["add", "-A"])
        # Check if there is anything staged
        code, diff_out, _ = self._run_git(["diff", "--cached", "--quiet"])
        if code == 0:
            # No changes to commit
            return False

        commit_code, _, commit_err = self._run_git(["commit", "-m", message])
        return commit_code == 0

    def rollback_uncommitted(self) -> None:
        """Discards all unstaged and staged changes safely."""
        self._run_git(["reset", "--hard", "HEAD"])
        self._run_git(["clean", "-fd"])

    def delete_branch(self, branch_name: str, force: bool = True) -> bool:
        """Deletes a local branch."""
        flag = "-D" if force else "-d"
        code, _, _ = self._run_git(["branch", flag, branch_name])
        return code == 0

    def push_branch(self, branch_name: str, remote: str = "origin") -> Tuple[bool, str]:
        """Pushes branch to remote repository."""
        code, stdout, stderr = self._run_git(["push", "-u", remote, branch_name])
        if code == 0:
            return True, "Successfully pushed branch."
        return False, stderr or stdout

    def create_github_pr(self, title: str, body: str, head_branch: str, base_branch: str = "main") -> Tuple[bool, Optional[str], Optional[int]]:
        """Uses GitHub CLI (`gh`) to open a Pull Request."""
        cmd = [
            "gh", "pr", "create",
            "--repo", self.repo_path,
            "--title", title,
            "--body", body,
            "--head", head_branch,
            "--base", base_branch
        ]
        try:
            proc = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if proc.returncode == 0:
                pr_url = proc.stdout.strip()
                # Parse PR number if possible from url (e.g. https://github.com/org/repo/pull/12)
                pr_number = None
                if "/pull/" in pr_url:
                    try:
                        pr_number = int(pr_url.split("/pull/")[-1].strip().split("#")[0])
                    except ValueError:
                        pass
                logger.info(f"GitHub PR created successfully: {pr_url}")
                return True, pr_url, pr_number
            else:
                logger.warning(f"gh pr create returned code {proc.returncode}: {proc.stderr}")
                return False, None, None
        except Exception as e:
            logger.error(f"Error executing gh pr create: {e}")
            return False, None, None
