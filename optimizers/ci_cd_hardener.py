"""
CI/CD Hardening Optimizer.
Synthesizes and deploys robust, multi-platform GitHub Actions workflows tailored to repository language.
"""

import os
from typing import List
from .base import BaseOptimizer
from core.models import RepoHealthReport


PYTHON_CI_WORKFLOW = """name: Continuous Integration

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  test:
    name: Test & Lint (${{ matrix.os }} - Py${{ matrix.python-version }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.11", "3.12"]

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          pip install pytest pytest-cov
        shell: bash

      - name: Run Test Suite
        run: |
          pytest -v --maxfail=10
        shell: bash
"""

RUST_CI_WORKFLOW = """name: Continuous Integration

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  check-and-test:
    name: Cargo Check & Test (${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Install Rust Toolchain
        uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy, rustfmt

      - name: Cargo Cache
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/bin/
            ~/.cargo/registry/index/
            ~/.cargo/registry/cache/
            ~/.cargo/git/db/
            target/
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
          restore-keys: |
            ${{ runner.os }}-cargo-

      - name: Check Formatting
        run: cargo fmt --all -- --check

      - name: Run Tests
        run: cargo test --verbose
"""

GO_CI_WORKFLOW = """name: Continuous Integration

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  test:
    name: Go Test (${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.22'

      - name: Test
        run: go test -v ./...
"""


class CiCdHardenerOptimizer(BaseOptimizer):
    def __init__(self):
        super().__init__(name="CI/CD Hardener")

    def optimize(self, repo_path: str, report: RepoHealthReport) -> List[str]:
        changes: List[str] = []
        workflows_dir = os.path.join(repo_path, ".github", "workflows")
        ci_path = os.path.join(workflows_dir, "ci.yml")

        # If workflows already exist, do not overwrite unless no files exist
        if os.path.exists(ci_path):
            return changes

        os.makedirs(workflows_dir, exist_ok=True)
        primary_lang = report.primary_language

        if primary_lang == "Rust":
            workflow_content = RUST_CI_WORKFLOW
        elif primary_lang == "Go":
            workflow_content = GO_CI_WORKFLOW
        else:
            workflow_content = PYTHON_CI_WORKFLOW

        with open(ci_path, "w", encoding="utf-8") as f:
            f.write(workflow_content.strip() + "\n")

        changes.append(f"Injected automated GitHub Actions CI workflow for {primary_lang} in .github/workflows/ci.yml")
        return changes
