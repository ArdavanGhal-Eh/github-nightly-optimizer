#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Nightly Autonomous Optimizer & Continuous Development Engine.
Main Entry Point.
"""

import sys
import os

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure package root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from cli import handle_cli

if __name__ == "__main__":
    handle_cli()
