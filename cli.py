"""
Command Line Interface for GitHub Nightly Optimizer.
Provides operational control for auditing, executing nightly cycles, scheduling, and reporting.
"""

import os
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import webbrowser
import logging
from typing import Optional

from config.settings import AppConfig
from core.logger import get_logger
from engine.orchestrator import NightlyOrchestrator
from reporting.markdown_generator import MarkdownReportGenerator
from reporting.dashboard_generator import DashboardGenerator
from scheduler.win_scheduler import WindowsTaskScheduler
from scheduler.daemon import NightlyDaemon

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
LOGS_DIR = os.path.join(BASE_DIR, "logs")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nightly",
        description="GitHub Nightly Autonomous Optimizer & Continuous Development Engine"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Execute nightly optimization cycle")
    run_parser.add_argument("--dry-run", action="store_true", help="Run in simulation mode without writing changes")
    run_parser.add_argument("--repo", type=str, default=None, help="Target specific repository by name")
    run_parser.add_argument("--strategy", type=str, choices=["pr", "direct_merge", "branch_only"], default=None, help="Override delivery strategy")

    # Command: audit
    audit_parser = subparsers.add_parser("audit", help="Run non-destructive diagnostics on repositories")
    audit_parser.add_argument("--repo", type=str, default=None, help="Target specific repository by name")

    # Command: list
    subparsers.add_parser("list", help="List all discovered local and remote repositories")

    # Command: schedule
    sched_parser = subparsers.add_parser("schedule", help="Manage Windows Task Scheduler integration")
    sched_parser.add_argument("--action", choices=["register", "status", "delete"], default="status", help="Scheduler action")
    sched_parser.add_argument("--time", type=str, default="02:00", help="Daily execution time (HH:MM)")

    # Command: daemon
    daemon_parser = subparsers.add_parser("daemon", help="Run as persistent in-process background daemon")
    daemon_parser.add_argument("--hour", type=int, default=2, help="Target execution hour (0-23)")
    daemon_parser.add_argument("--minute", type=int, default=0, help="Target execution minute (0-59)")

    # Command: report
    report_parser = subparsers.add_parser("report", help="Inspect or open latest morning dashboard")
    report_parser.add_argument("--open", action="store_true", help="Open latest HTML report in default browser")

    return parser


def handle_cli():
    parser = build_parser()
    args = parser.parse_args()

    logger = get_logger("NightlyOptimizer", log_dir=LOGS_DIR)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    config = AppConfig.load()
    orchestrator = NightlyOrchestrator(config)

    if args.command == "list":
        repos = config.discover_local_repos()
        print(f"\nDiscovered {len(repos)} repositories under monitoring:")
        print(f"{'#':<4} {'Repository Name':<35} {'Local Path'}")
        print("-" * 90)
        for idx, r in enumerate(repos, start=1):
            print(f"{idx:<4} {r['name']:<35} {r['path']}")
        print()

    elif args.command == "audit":
        reports = orchestrator.run_audit_only(target_repo_name=args.repo)

        print(f"\nAudit Diagnostic Results ({len(reports)} Repositories):")
        print(f"{'Repository':<35} {'Lang':<10} {'Health Score':<14} {'Issues'}")
        print("-" * 75)
        for r in reports:
            print(f"{r.repo_name:<35} {r.primary_language:<10} {r.total_score:<14.1f} {len(r.all_issues)} issues")
        print()

    elif args.command == "run":
        if args.strategy:
            config.delivery_strategy = args.strategy

        summary = orchestrator.run_nightly_cycle(dry_run=args.dry_run, target_repo_name=args.repo)

        # Generate Reports
        md_content = MarkdownReportGenerator.generate(summary)
        print("\n" + md_content + "\n")

        # Save HTML dashboard
        html_filename = f"dashboard_{summary.run_id}.html"
        html_path = os.path.join(REPORTS_DIR, html_filename)
        latest_html_path = os.path.join(REPORTS_DIR, "latest_dashboard.html")

        DashboardGenerator.generate_html(summary, html_path)
        DashboardGenerator.generate_html(summary, latest_html_path)

        logger.info(f"Morning Executive HTML Dashboard saved to: {latest_html_path}")

    elif args.command == "schedule":
        scheduler = WindowsTaskScheduler(task_name=config.nightly_schedule.task_name)
        if args.action == "register":
            ok, msg = scheduler.register_daily_task(args.time)
            print(f"[{'SUCCESS' if ok else 'FAILED'}] {msg}")
        elif args.action == "status":
            res = scheduler.query_task()
            if res.get("registered"):
                print(f"\nWindows Scheduled Task '{config.nightly_schedule.task_name}' is ACTIVE.")
                for k, v in res.get("details", {}).items():
                    print(f"  {k}: {v}")
            else:
                print(f"\nTask '{config.nightly_schedule.task_name}' is not currently registered.")
                print(f"To register run: python main.py schedule --action register --time 02:00")
        elif args.action == "delete":
            ok, msg = scheduler.delete_task()
            print(f"[{'SUCCESS' if ok else 'FAILED'}] {msg}")

    elif args.command == "daemon":
        daemon = NightlyDaemon(orchestrator, target_hour=args.hour, target_minute=args.minute)
        daemon.start()

    elif args.command == "report":
        latest_path = os.path.join(REPORTS_DIR, "latest_dashboard.html")
        if os.path.exists(latest_path):
            print(f"Latest HTML Dashboard: {latest_path}")
            if args.open:
                webbrowser.open(f"file://{latest_path}")
        else:
            print("No reports generated yet. Run 'python main.py run' to execute your first cycle.")
