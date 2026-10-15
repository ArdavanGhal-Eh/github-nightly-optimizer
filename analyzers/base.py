"""
Base Analyzer Contract for Repository Auditing.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from core.models import CategoryScore


class BaseAnalyzer(ABC):
    def __init__(self, name: str, weight: float):
        self.name = name
        self.weight = weight

    @abstractmethod
    def analyze(self, repo_path: str, context: Dict[str, Any]) -> CategoryScore:
        """
        Executes audit inspection on repo_path and returns CategoryScore.
        """
        pass
