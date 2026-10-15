"""
Windows Task Scheduler Integration.
Configures and manages native Windows scheduled tasks (schtasks) for unattended overnight execution.
"""

import os
import sys
import subprocess
import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger("NightlyOptimizer.WinScheduler")


class WindowsTaskScheduler:
    def __init__(self, task_name: str = "GitHubNightlyOptimizer"):
        self.task_name = task_name
        self.python_exe = sys.executable
        self.main_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))

    def register_daily_task(self, execution_time: str = "02:00") -> Tuple[bool, str]:
        """
        Registers a daily scheduled task running at execution_time (e.g. '02:00').
        Uses elevated or standard schtasks.
        """
        task_action = f'"{self.python_exe}" "{self.main_script}" run'

        cmd = [
            "schtasks", "/Create",
            "/TN", self.task_name,
            "/TR", task_action,
            "/SC", "DAILY",
            "/ST", execution_time,
            "/F"
        ]

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if proc.returncode == 0:
                logger.info(f"Successfully registered Windows Scheduled Task '{self.task_name}' at {execution_time} daily.")
                return True, f"Task '{self.task_name}' registered successfully for daily execution at {execution_time}."
            else:
                logger.warning(f"schtasks returned {proc.returncode}: {proc.stderr or proc.stdout}")
                return False, proc.stderr or proc.stdout
        except Exception as e:
            logger.error(f"Failed to execute schtasks: {e}")
            return False, str(e)

    def query_task(self) -> Dict[str, Any]:
        """Queries the current status of the scheduled task."""
        cmd = ["schtasks", "/Query", "/TN", self.task_name, "/FO", "LIST", "/V"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if proc.returncode == 0:
                details = {}
                for line in proc.stdout.splitlines():
                    if ":" in line:
                        parts = line.split(":", 1)
                        details[parts[0].strip()] = parts[1].strip()
                return {"registered": True, "details": details}
            else:
                return {"registered": False, "message": "Task not found"}
        except Exception as e:
            return {"registered": False, "error": str(e)}

    def delete_task(self) -> Tuple[bool, str]:
        """Removes the scheduled task."""
        cmd = ["schtasks", "/Delete", "/TN", self.task_name, "/F"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if proc.returncode == 0:
                return True, f"Task '{self.task_name}' removed."
            return False, proc.stderr or proc.stdout
        except Exception as e:
            return False, str(e)
