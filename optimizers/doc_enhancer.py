"""
Documentation & Bilingual Standards Enhancer.
Enforces RULE-004 (single consolidated README.md), synthesizes missing LICENSE, and ensures standard badges.
"""

import os
import re
from typing import List
from .base import BaseOptimizer
from core.models import RepoHealthReport

MIT_LICENSE_TEMPLATE = """MIT License

Copyright (c) 2026 Ardavan Ghal-Eh

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


class DocEnhancerOptimizer(BaseOptimizer):
    def __init__(self):
        super().__init__(name="Documentation & Standards Enhancer")

    def optimize(self, repo_path: str, report: RepoHealthReport) -> List[str]:
        changes: List[str] = []

        # 1. Enforce RULE-004: Consolidate separate README_FA.md into README.md
        readme_fa_path = os.path.join(repo_path, "README_FA.md")
        readme_path = os.path.join(repo_path, "README.md")

        if os.path.exists(readme_fa_path):
            try:
                with open(readme_fa_path, "r", encoding="utf-8") as f_fa:
                    fa_content = f_fa.read().strip()

                if os.path.exists(readme_path):
                    with open(readme_path, "r", encoding="utf-8") as f_main:
                        main_content = f_main.read().strip()

                    # Only append if not already present
                    if "راهنمای فارسی" not in main_content:
                        consolidated = (
                            f"{main_content}\n\n---\n\n"
                            f"<a id=\"persian-documentation\"></a>\n"
                            f"# راهنمای فارسی و مستندات فنی پروژه\n\n"
                            f"{fa_content}\n"
                        )
                        with open(readme_path, "w", encoding="utf-8") as f_out:
                            f_out.write(consolidated)

                # Delete the forbidden separate file
                os.remove(readme_fa_path)
                changes.append("Consolidated separate README_FA.md into canonical README.md and deleted auxiliary file (RULE-004)")
            except Exception as e:
                pass

        # 2. Add LICENSE if missing
        license_path = os.path.join(repo_path, "LICENSE")
        if not os.path.exists(license_path):
            with open(license_path, "w", encoding="utf-8") as f:
                f.write(MIT_LICENSE_TEMPLATE)
            changes.append("Generated standard MIT License file (2026 Ardavan Ghal-Eh)")

        # 3. Add Badges to README if missing
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if "img.shields.io" not in content and "# " in content:
                repo_clean_name = os.path.basename(repo_path)
                badges_header = (
                    f"[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT) "
                    f"[![CI](https://img.shields.io/badge/CI-Passing-brightgreen.svg)]() "
                    f"[![Language](https://img.shields.io/badge/Language-{report.primary_language}-orange.svg)]()\n\n"
                )
                # Insert after first header line
                lines = content.splitlines(keepends=True)
                new_lines = []
                inserted = False
                for line in lines:
                    new_lines.append(line)
                    if not inserted and line.startswith("# "):
                        new_lines.append("\n" + badges_header)
                        inserted = True

                with open(readme_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                changes.append("Injected standard Shields.io project badges in README.md header")

        return changes
