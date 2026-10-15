"""
Base Optimizer Contract for Autonomous Enhancement.
"""

from abc import ABC, abstractmethod
from typing import List
from core.models import RepoHealthReport


class BaseOptimizer(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def optimize(self, repo_path: str, report: RepoHealthReport) -> List[str]:
        """
        Applies automated enhancements to repo_path based on health report.
        Returns a list of strings describing the changes made.
        """
        pass
