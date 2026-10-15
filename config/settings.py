"""
Configuration Management for GitHub Nightly Optimizer.
Loads, validates, and discovers repositories across monitored local roots.
"""

import os
import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

logger = logging.getLogger("NightlyOptimizer.Config")

CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "default_config.json")
CUSTOM_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "nightly_config.json")


@dataclass
class QualityGates:
    min_score_for_pr: float = 70.0
    allow_regression: bool = False
    require_tests_pass: bool = True


@dataclass
class ScheduleConfig:
    enabled: bool = True
    time: str = "02:00"
    task_name: str = "GitHubNightlyOptimizer"


@dataclass
class AppConfig:
    github_user: str = "ArdavanGhal-Eh"
    monitored_directories: List[str] = field(default_factory=list)
    target_repos: List[str] = field(default_factory=lambda: ["*"])
    excluded_repos: List[str] = field(default_factory=list)
    delivery_strategy: str = "pr"  # 'pr', 'direct_merge', 'branch_only'
    branch_prefix: str = "nightly/opt"
    nightly_schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    quality_gates: QualityGates = field(default_factory=QualityGates)
    enabled_analyzers: List[str] = field(default_factory=lambda: [
        "code_quality", "security", "test_suite", "documentation", "ci_cd"
    ])
    enabled_optimizers: List[str] = field(default_factory=lambda: [
        "code_cleaner", "test_synthesizer", "ci_cd_hardener", "doc_enhancer", "security_guard"
    ])

    @classmethod
    def load(cls, custom_path: Optional[str] = None) -> "AppConfig":
        """Loads configuration from custom file, nightly_config.json, or default."""
        target = custom_path or CUSTOM_CONFIG_PATH
        if not os.path.exists(target):
            target = CONFIG_FILE_PATH

        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)

            qg = QualityGates(**data.get("quality_gates", {}))
            sc = ScheduleConfig(**data.get("nightly_schedule", {}))

            return cls(
                github_user=data.get("github_user", "ArdavanGhal-Eh"),
                monitored_directories=data.get("monitored_directories", []),
                target_repos=data.get("target_repos", ["*"]),
                excluded_repos=data.get("excluded_repos", []),
                delivery_strategy=data.get("delivery_strategy", "pr"),
                branch_prefix=data.get("branch_prefix", "nightly/opt"),
                nightly_schedule=sc,
                quality_gates=qg,
                enabled_analyzers=data.get("enabled_analyzers", []),
                enabled_optimizers=data.get("enabled_optimizers", [])
            )
        except Exception as e:
            logger.warning(f"Failed to load custom config from {target}: {e}. Using defaults.")
            return cls()

    def discover_local_repos(self) -> List[Dict[str, str]]:
        """
        Discovers git repositories from monitored_directories.
        Returns a list of dicts: [{'name': '...', 'path': '...'}]
        """
        discovered = {}
        for base_dir in self.monitored_directories:
            if not os.path.exists(base_dir):
                continue

            # Check if base_dir itself is a git repo
            if os.path.isdir(os.path.join(base_dir, ".git")):
                repo_name = os.path.basename(os.path.normpath(base_dir))
                if repo_name not in discovered:
                    discovered[repo_name] = base_dir
                continue

            # Check immediate subdirectories
            try:
                for entry in os.scandir(base_dir):
                    if entry.is_dir():
                        git_path = os.path.join(entry.path, ".git")
                        if os.path.isdir(git_path):
                            if entry.name not in discovered:
                                discovered[entry.name] = entry.path
            except PermissionError:
                continue

        # Filter by inclusions / exclusions
        final_repos = []
        for name, path in discovered.items():
            if name in self.excluded_repos:
                continue
            if "*" in self.target_repos or name in self.target_repos:
                final_repos.append({"name": name, "path": path})

        return final_repos
