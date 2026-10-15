"""
Continuous Background Daemon Runner.
Maintains persistent in-process timer loop for containerized or terminal-based execution.
"""

import time
import datetime
import logging
import signal
from typing import Optional
from engine.orchestrator import NightlyOrchestrator
from reporting.markdown_generator import MarkdownReportGenerator
from reporting.dashboard_generator import DashboardGenerator

logger = logging.getLogger("NightlyOptimizer.Daemon")


class NightlyDaemon:
    def __init__(self, orchestrator: NightlyOrchestrator, target_hour: int = 2, target_minute: int = 0):
        self.orchestrator = orchestrator
        self.target_hour = target_hour
        self.target_minute = target_minute
        self.running = True

        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)

    def _handle_exit(self, signum, frame):
        logger.info("Daemon received shutdown signal. Terminating safely...")
        self.running = False

    def get_seconds_until_next_run(self) -> float:
        now = datetime.datetime.now()
        target = now.replace(hour=self.target_hour, minute=self.target_minute, second=0, microsecond=0)
        if target <= now:
            target += datetime.timedelta(days=1)
        return (target - now).total_seconds()

    def start(self):
        logger.info(f"Nightly Daemon initialized. Daily target run scheduled at {self.target_hour:02d}:{self.target_minute:02d}.")

        while self.running:
            wait_sec = self.get_seconds_until_next_run()
            wait_hours = wait_sec / 3600.0
            logger.info(f"Daemon sleeping for {wait_hours:.2f} hours until next nightly maintenance window.")

            # Sleep in intervals to allow responsive shutdown
            while wait_sec > 0 and self.running:
                sleep_chunk = min(30.0, wait_sec)
                time.sleep(sleep_chunk)
                wait_sec -= sleep_chunk

            if not self.running:
                break

            logger.info("Nightly scheduled trigger activated. Commencing optimization cycle...")
            try:
                summary = self.orchestrator.run_nightly_cycle(dry_run=False)
                # Output reports
                md_report = MarkdownReportGenerator.generate(summary)
                logger.info(md_report)
            except Exception as e:
                logger.error(f"Error executing nightly cycle in daemon: {e}")
