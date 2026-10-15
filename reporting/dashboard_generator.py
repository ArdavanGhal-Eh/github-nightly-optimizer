"""
Interactive Executive HTML Dashboard Generator.
Builds modern, clean, high-signal morning executive briefings for software repositories.
"""

import os
import json
from typing import Dict, Any
from core.models import NightlyRunSummary


class DashboardGenerator:
    @staticmethod
    def generate_html(summary: NightlyRunSummary, output_path: str) -> str:
        data = summary.to_dict()
        score_delta = summary.average_score_after - summary.average_score_before
        sign = "+" if score_delta >= 0 else ""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Nightly Optimization Executive Dashboard | {summary.run_id}</title>
  <style>
    :root {{
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --text: #e6edf3;
      --text-muted: #8b949e;
      --accent: #58a6ff;
      --success: #238636;
      --success-text: #3fb950;
      --warning: #d29922;
      --danger: #f85149;
      --purple: #bc8cff;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
    body {{ background-color: var(--bg); color: var(--text); padding: 24px; line-height: 1.5; }}
    .container {{ max-width: 1320px; margin: 0 auto; }}
    
    header {{ display: flex; justify-content: space-between; align-items: center; padding-bottom: 24px; border-bottom: 1px solid var(--border); margin-bottom: 24px; }}
    .title-group h1 {{ font-size: 24px; font-weight: 600; color: #fff; display: flex; align-items: center; gap: 10px; }}
    .title-group p {{ color: var(--text-muted); font-size: 14px; margin-top: 4px; }}
    .meta-tag {{ background: rgba(88, 166, 255, 0.15); color: var(--accent); border: 1px solid rgba(88, 166, 255, 0.3); padding: 4px 12px; border-radius: 20px; font-size: 13px; font-mono: true; }}

    .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }}
    .kpi-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 20px; }}
    .kpi-label {{ font-size: 12px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }}
    .kpi-value {{ font-size: 28px; font-weight: 700; color: #fff; margin: 6px 0 2px; }}
    .kpi-delta {{ font-size: 13px; font-weight: 500; }}
    .delta-pos {{ color: var(--success-text); }}
    .delta-neutral {{ color: var(--text-muted); }}

    .controls {{ display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}
    .search-input {{ flex: 1; min-width: 260px; background: var(--card-bg); border: 1px solid var(--border); color: var(--text); padding: 10px 14px; border-radius: 6px; font-size: 14px; }}
    .search-input:focus {{ outline: none; border-color: var(--accent); }}
    .filter-btn {{ background: var(--card-bg); border: 1px solid var(--border); color: var(--text-muted); padding: 8px 16px; border-radius: 6px; font-size: 13px; cursor: pointer; }}
    .filter-btn.active {{ background: rgba(88, 166, 255, 0.2); color: var(--accent); border-color: var(--accent); }}

    .table-container {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
    table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }}
    th {{ background: #1c2128; color: var(--text-muted); font-weight: 600; padding: 12px 16px; border-bottom: 1px solid var(--border); }}
    td {{ padding: 14px 16px; border-bottom: 1px solid var(--border); vertical-align: middle; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}

    .badge {{ display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; }}
    .badge-success {{ background: rgba(63, 185, 80, 0.15); color: var(--success-text); border: 1px solid rgba(63, 185, 80, 0.3); }}
    .badge-optimal {{ background: rgba(139, 148, 158, 0.15); color: var(--text-muted); border: 1px solid rgba(139, 148, 158, 0.3); }}
    .badge-reverted {{ background: rgba(248, 81, 73, 0.15); color: var(--danger); border: 1px solid rgba(248, 81, 73, 0.3); }}
    
    .score-bar-bg {{ width: 100px; height: 6px; background: rgba(255, 255, 255, 0.1); border-radius: 3px; overflow: hidden; display: inline-block; margin-left: 8px; vertical-align: middle; }}
    .score-bar-fill {{ height: 100%; border-radius: 3px; background: var(--accent); }}

    .details-row {{ display: none; background: #13171f; padding: 16px 20px; }}
    .details-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
    .details-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 6px; padding: 14px; }}
    .details-card h4 {{ font-size: 13px; color: var(--text-muted); margin-bottom: 10px; text-transform: uppercase; }}
    .change-list {{ list-style-type: none; font-size: 13px; }}
    .change-list li {{ padding: 4px 0; color: var(--text); }}
    .change-list li::before {{ content: "✓ "; color: var(--success-text); font-weight: bold; }}

    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="title-group">
        <h1>🌙 GitHub Nightly Optimizer & Continuous Dev Engine</h1>
        <p>Autonomous Overnight Multi-Repository Diagnostics, Testing & Quality Synthesis</p>
      </div>
      <div class="meta-tag">{summary.run_id}</div>
    </header>

    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Audited Repositories</div>
        <div class="kpi-value">{summary.total_repos_inspected}</div>
        <div class="kpi-delta delta-neutral">Targeting @ArdavanGhal-Eh</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Optimized Repos</div>
        <div class="kpi-value">{summary.repos_optimized}</div>
        <div class="kpi-delta delta-pos">Enhancements verified</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Pull Requests Created</div>
        <div class="kpi-value">{summary.prs_created}</div>
        <div class="kpi-delta delta-pos">Ready for morning review</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Average Health Score</div>
        <div class="kpi-value">{summary.average_score_after:.1f}</div>
        <div class="kpi-delta delta-pos">{sign}{score_delta:.1f} vs baseline ({summary.average_score_before:.1f})</div>
      </div>
    </div>

    <div class="controls">
      <input type="text" id="searchInput" class="search-input" placeholder="Search repository by name or primary language..." onkeyup="filterTable()">
      <button class="filter-btn active" onclick="setFilter('all', this)">All Repos</button>
      <button class="filter-btn" onclick="setFilter('SUCCESS', this)">Optimized</button>
      <button class="filter-btn" onclick="setFilter('SKIPPED', this)">Optimal State</button>
    </div>

    <div class="table-container">
      <table id="reposTable">
        <thead>
          <tr>
            <th>Repository</th>
            <th>Language</th>
            <th>Status</th>
            <th>Health Score</th>
            <th>Score Delta</th>
            <th>PR Link</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
"""

        results_map = {r.repo_name: r for r in summary.results}

        for idx, report in enumerate(summary.reports):
            res = results_map.get(report.repo_name)
            status = res.status if res else "SKIPPED"
            b_score = res.score_before if res else report.total_score
            a_score = res.score_after if res else report.total_score
            delta = a_score - b_score
            d_sign = "+" if delta >= 0 else ""

            badge_class = "badge-success" if status == "SUCCESS" else ("badge-reverted" if status == "REVERTED_REGRESSION" else "badge-optimal")
            pr_cell = f"<a href='{res.pr_url}' target='_blank'>PR #{res.pr_number}</a>" if (res and res.pr_url) else "<span style='color:var(--text-muted)'>—</span>"

            changes_html = ""
            if res and res.changes_applied:
                changes_html = "".join([f"<li>{c}</li>" for c in res.changes_applied])
            else:
                changes_html = "<li style='color:var(--text-muted)'>Zero modifications required. Repository conforms to all standards.</li>"

            # Category scores breakdown
            cat_breakdown_html = ""
            for cat_name, cat in report.category_scores.items():
                cat_breakdown_html += f"<div style='display:flex; justify-content:space-between; margin-bottom:6px; font-size:12px;'><span>{cat_name}</span><span><b>{cat.score:.1f}</b>/100</span></div>"

            html += f"""
          <tr data-status="{status}" data-lang="{report.primary_language.lower()}" data-name="{report.repo_name.lower()}">
            <td><b>{report.repo_name}</b></td>
            <td><code>{report.primary_language}</code></td>
            <td><span class="badge {badge_class}">{status}</span></td>
            <td>
              <b>{a_score:.1f}</b>
              <div class="score-bar-bg"><div class="score-bar-fill" style="width: {min(100, max(0, a_score))}%;"></div></div>
            </td>
            <td><span class="{ 'delta-pos' if delta > 0 else 'delta-neutral' }">{d_sign}{delta:.1f}</span></td>
            <td>{pr_cell}</td>
            <td><button style="background:transparent; border:1px solid var(--border); color:var(--accent); padding:4px 8px; border-radius:4px; font-size:12px; cursor:pointer;" onclick="toggleDetails({idx})">Details</button></td>
          </tr>
          <tr id="details-{idx}" class="details-row">
            <td colspan="7">
              <div class="details-grid">
                <div class="details-card">
                  <h4>Category Health Breakdown</h4>
                  {cat_breakdown_html}
                </div>
                <div class="details-card">
                  <h4>Overnight Enhancements Applied</h4>
                  <ul class="change-list">
                    {changes_html}
                  </ul>
                </div>
              </div>
            </td>
          </tr>
"""

        html += """
        </tbody>
      </table>
    </div>
  </div>

  <script>
    let currentFilter = 'all';

    function setFilter(filter, btn) {
      currentFilter = filter;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      filterTable();
    }

    function filterTable() {
      const query = document.getElementById('searchInput').value.toLowerCase();
      const rows = document.querySelectorAll('#reposTable tbody tr[data-name]');
      rows.forEach(row => {
        const name = row.getAttribute('data-name');
        const lang = row.getAttribute('data-lang');
        const status = row.getAttribute('data-status');
        const detailsRow = document.getElementById(row.id.replace('details-', ''));

        const matchesQuery = name.includes(query) || lang.includes(query);
        const matchesFilter = currentFilter === 'all' || status === currentFilter;

        if (matchesQuery && matchesFilter) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
          const nextRow = row.nextElementSibling;
          if (nextRow && nextRow.classList.contains('details-row')) {
            nextRow.style.display = 'none';
          }
        }
      });
    }

    function toggleDetails(idx) {
      const row = document.getElementById(`details-${idx}`);
      if (row.style.display === 'table-row') {
        row.style.display = 'none';
      } else {
        row.style.display = 'table-row';
      }
    }
  </script>
</body>
</html>
"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path
