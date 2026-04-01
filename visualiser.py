"""
visualiser.py
=============
Generates a self-contained, interactive HTML dashboard from a list of
CropFeverResult objects. The output file has no external dependencies —
it embeds Chart.js via CDN and all data as JSON.
"""

from __future__ import annotations

import json
from calculator import CropFeverResult, NPC_SELL_PRICES


# Pretty display names for crop IDs
CROP_DISPLAY_NAMES: dict[str, str] = {
    "MELON": "Melon",
    "PUMPKIN": "Pumpkin",
    "CACTUS": "Cactus",
    "INK_SACK:3": "Cocoa Beans",
    "CARROT_ITEM": "Carrot",
    "WHEAT": "Wheat",
    "SUGAR_CANE": "Sugar Cane",
    "NETHER_STALK": "Nether Wart",
    "POTATO_ITEM": "Potato",
    "RED_MUSHROOM": "Mushroom",
    "MOONFLOWER": "Moonflower",
    "WILD_ROSE": "Wild Rose",
    "DOUBLE_PLANT": "Sunflower",
}

LEVEL_COLOURS = {
    1: "#4ade80",
    2: "#facc15",
    3: "#fb923c",
    4: "#f87171",
    5: "#c084fc",
}


def _serialize(results: list[CropFeverResult]) -> str:
    """Convert results to a JSON string for embedding in the HTML."""
    rows = []
    for r in results:
        rows.append({
            "cropId": r.crop_id,
            "cropName": CROP_DISPLAY_NAMES.get(r.crop_id, r.crop_id),
            "level": r.level,
            "upgradeCost": r.upgrade_cost,
            "profitPerHour": round(r.extra_profit_per_hour, 2),
            "roiHours": round(r.roi_hours, 2),
            "roiDays": round(r.roi_days, 3),
        })
    return json.dumps(rows)


def build_dashboard(results: list[CropFeverResult]) -> str:
    data_json = _serialize(results)
    crop_names_json = json.dumps({k: v for k, v in CROP_DISPLAY_NAMES.items()})
    level_colours_json = json.dumps(LEVEL_COLOURS)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Crop Fever ROI Calculator – SkyBlock</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;700;800&display=swap');

  :root {{
    --bg: #0b0f14;
    --surface: #111820;
    --surface2: #182030;
    --border: #1e2d40;
    --accent: #38bdf8;
    --accent2: #818cf8;
    --text: #e2eaf5;
    --muted: #64748b;
    --green: #4ade80;
    --yellow: #facc15;
    --orange: #fb923c;
    --red: #f87171;
    --purple: #c084fc;
  }}

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Syne', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
  }}

  /* ---- Layout ---- */
  .page {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem 1.5rem 4rem;
  }}

  /* ---- Header ---- */
  header {{
    display: flex;
    align-items: flex-end;
    gap: 1.5rem;
    padding-bottom: 2rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
  }}
  .logo {{
    font-size: 2.4rem;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}
  .subtitle {{
    color: var(--muted);
    font-size: 0.85rem;
    font-family: 'DM Mono', monospace;
    padding-bottom: 0.2rem;
  }}

  /* ---- Controls ---- */
  .controls {{
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 2rem;
    align-items: flex-end;
  }}
  .control-group {{
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }}
  label {{
    font-size: 0.75rem;
    font-family: 'DM Mono', monospace;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }}
  select, input[type=range] {{
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 0.4rem 0.7rem;
    border-radius: 6px;
    font-family: 'DM Mono', monospace;
    font-size: 0.9rem;
    cursor: pointer;
    outline: none;
    transition: border-color .2s;
  }}
  select:hover, select:focus {{ border-color: var(--accent); }}
  .range-row {{ display: flex; align-items: center; gap: 0.6rem; }}
  .range-val {{
    font-family: 'DM Mono', monospace;
    font-size: 0.9rem;
    color: var(--accent);
    min-width: 3.5ch;
    text-align: right;
  }}
  input[type=range] {{
    padding: 0;
    width: 140px;
    accent-color: var(--accent);
  }}

  /* ---- KPI cards ---- */
  .kpis {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }}
  .kpi {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.1rem 1.4rem;
    position: relative;
    overflow: hidden;
  }}
  .kpi::before {{
    content: '';
    position: absolute;
    inset: 0 0 auto 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
  }}
  .kpi-label {{
    font-size: 0.72rem;
    font-family: 'DM Mono', monospace;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.4rem;
  }}
  .kpi-value {{
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--accent);
    letter-spacing: -0.02em;
  }}
  .kpi-sub {{
    font-size: 0.78rem;
    color: var(--muted);
    margin-top: 0.2rem;
    font-family: 'DM Mono', monospace;
  }}

  /* ---- Charts grid ---- */
  .charts {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.2rem;
    margin-bottom: 2rem;
  }}
  @media (max-width: 860px) {{ .charts {{ grid-template-columns: 1fr; }} }}
  .chart-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.4rem;
  }}
  .chart-card.wide {{ grid-column: span 2; }}
  @media (max-width: 860px) {{ .chart-card.wide {{ grid-column: span 1; }} }}
  .chart-title {{
    font-size: 0.8rem;
    font-family: 'DM Mono', monospace;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 1rem;
  }}
  canvas {{ max-height: 320px; }}

  /* ---- Data table ---- */
  .table-wrap {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: auto;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
  }}
  thead tr {{
    background: var(--surface2);
    border-bottom: 1px solid var(--border);
  }}
  th {{
    padding: 0.7rem 1rem;
    text-align: left;
    font-size: 0.72rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
  }}
  th:hover {{ color: var(--accent); }}
  th.sorted {{ color: var(--accent); }}
  td {{
    padding: 0.6rem 1rem;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
  }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: var(--surface2); }}
  .badge {{
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
  }}
  .num {{ text-align: right; color: var(--accent); }}
  .muted {{ color: var(--muted); }}

  /* ---- Footer ---- */
  footer {{
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border);
    font-size: 0.75rem;
    font-family: 'DM Mono', monospace;
    color: var(--muted);
    line-height: 1.7;
  }}
  .tag {{ background: var(--surface2); border-radius: 4px; padding: 0.1rem 0.4rem; }}
</style>
</head>
<body>
<div class="page">

  <header>
    <div>
      <div class="logo">Crop Fever</div>
      <div class="logo" style="font-size:1.1rem;margin-top:0.15rem;">ROI Calculator</div>
    </div>
    <div class="subtitle">Hypixel SkyBlock · farming investment analysis</div>
  </header>

  <!-- Controls -->
  <div class="controls">
    <div class="control-group">
      <label>Metric</label>
      <select id="metricSel">
        <option value="roiHours">ROI (hours)</option>
        <option value="roiDays">ROI (days)</option>
        <option value="profitPerHour">Extra profit / hr</option>
      </select>
    </div>
    <div class="control-group">
      <label>CF Level filter</label>
      <select id="levelSel">
        <option value="0">All levels</option>
        <option value="1">Level 1</option>
        <option value="2">Level 2</option>
        <option value="3">Level 3</option>
        <option value="4">Level 4</option>
        <option value="5">Level 5</option>
      </select>
    </div>
    <div class="control-group">
      <label>Blocks / second — <span id="bpsLabel">19.5</span></label>
      <div class="range-row">
        <input type="range" id="bpsRange" min="0" max="20" step="0.5" value="19.5" />
      </div>
    </div>
  </div>

  <!-- KPI row -->
  <div class="kpis">
    <div class="kpi">
      <div class="kpi-label">Best crop (fastest ROI)</div>
      <div class="kpi-value" id="kpiBestCrop">—</div>
      <div class="kpi-sub" id="kpiBestSub">—</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Highest profit / hr</div>
      <div class="kpi-value" id="kpiTopProfit">—</div>
      <div class="kpi-sub" id="kpiTopProfitSub">—</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Avg ROI across all crops</div>
      <div class="kpi-value" id="kpiAvgROI">—</div>
      <div class="kpi-sub">hours (selected level)</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Blocks per hour</div>
      <div class="kpi-value" id="kpiBph">—</div>
      <div class="kpi-sub">at current BPS setting</div>
    </div>
  </div>

  <!-- Charts -->
  <div class="charts">
    <div class="chart-card wide">
      <div class="chart-title">Extra profit per hour by crop &amp; level</div>
      <canvas id="profitChart"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">ROI (hours) — selected level</div>
      <canvas id="roiChart"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">ROI by level for selected crop</div>
      <canvas id="levelChart"></canvas>
    </div>
  </div>

  <!-- Table -->
  <div class="table-wrap">
    <table id="dataTable">
      <thead>
        <tr>
          <th data-col="cropName">Crop</th>
          <th data-col="level">Level</th>
          <th data-col="upgradeCost" class="sorted">Upgrade Cost</th>
          <th data-col="profitPerHour">Extra Profit / hr</th>
          <th data-col="roiHours">ROI (hours)</th>
          <th data-col="roiDays">ROI (days)</th>
        </tr>
      </thead>
      <tbody id="tableBody"></tbody>
    </table>
  </div>

  <footer>
    <p><span class="tag">NOTE</span> ROI and profit figures are <em>expectations</em> (long-run averages).
       Crop Fever drop tables include high-variance "PRAY TO RNGESUS" tiers — actual results will
       fluctuate significantly in shorter sessions.</p>
    <p style="margin-top:0.5rem"><span class="tag">NOTE</span> Rare-crop contribution uses the flat
       +15% spawn-chance bonus during an active Crop Fever window.  Additional bonuses from Rarefinder
       chip or Rose Dragon are <em>not</em> included and will increase your actual profit.</p>
    <p style="margin-top:0.5rem">Source: Hypixel SkyBlock Wiki · calculator by github.com/you</p>
  </footer>

</div>

<script>
// ---- Embedded data ----
const RAW = {data_json};
const CROP_NAMES = {crop_names_json};
const LEVEL_COLOURS = {level_colours_json};

// ---- State ----
let sortCol = 'upgradeCost', sortAsc = true;
let chartProfit, chartRoi, chartLevel;

// ---- Helpers ----
const fmt = (n, dp=0) => Number(n).toLocaleString('en-US', {{minimumFractionDigits: dp, maximumFractionDigits: dp}});
const fmtCoins = n => n >= 1e6 ? (n/1e6).toFixed(2)+'M' : n >= 1e3 ? (n/1e3).toFixed(1)+'K' : fmt(n);

function getLevel() {{ return parseInt(document.getElementById('levelSel').value) || 0; }}
function getMetric() {{ return document.getElementById('metricSel').value; }}
function getBps() {{ return parseFloat(document.getElementById('bpsRange').value); }}

// Re-scale data whenever BPS changes (recalculate approximation client-side)
// We store base values at bps=19.5 and scale linearly (profit ∝ bps, roi ∝ 1/bps)
const BASE_BPS = 19.5;
function scaled(row) {{
  const bps = getBps();
  const factor = bps / BASE_BPS;
  return {{
    ...row,
    profitPerHour: row.profitPerHour * factor,
    roiHours: row.roiHours / factor,
    roiDays: row.roiDays / factor,
  }};
}}

function filtered() {{
  const lvl = getLevel();
  return RAW.map(scaled).filter(r => lvl === 0 || r.level === lvl);
}}

function filteredAtLevel(lvl) {{
  return RAW.map(scaled).filter(r => r.level === lvl);
}}

// ---- Chart: profit bars (all levels, one crop group) ----
function buildProfitChart() {{
  const crops = [...new Set(RAW.map(r => r.cropId))];
  const levels = [1,2,3,4,5];
  const datasets = levels.map(lvl => ({{
    label: `Lv ${{lvl}}`,
    backgroundColor: LEVEL_COLOURS[lvl] + 'cc',
    borderColor: LEVEL_COLOURS[lvl],
    borderWidth: 1,
    borderRadius: 3,
    data: crops.map(c => {{
      const row = RAW.map(scaled).find(r => r.cropId === c && r.level === lvl);
      return row ? Math.round(row.profitPerHour) : 0;
    }}),
  }}));

  const ctx = document.getElementById('profitChart').getContext('2d');
  if (chartProfit) chartProfit.destroy();
  chartProfit = new Chart(ctx, {{
    type: 'bar',
    data: {{ labels: crops.map(c => CROP_NAMES[c] || c), datasets }},
    options: {{
      plugins: {{ legend: {{ labels: {{ color: '#94a3b8', font: {{ family: 'DM Mono', size: 11 }} }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#64748b', font: {{ family: 'DM Mono', size: 10 }} }}, grid: {{ color: '#1e2d40' }} }},
        y: {{ ticks: {{ color: '#64748b', font: {{ family: 'DM Mono', size: 10 }}, callback: v => fmtCoins(v) }}, grid: {{ color: '#1e2d40' }} }},
      }},
      responsive: true,
      animation: {{ duration: 300 }},
    }},
  }});
}}

// ---- Chart: ROI bar for selected level ----
function buildRoiChart() {{
  const lvl = getLevel() || 5;
  const rows = filteredAtLevel(lvl).sort((a,b) => a.roiHours - b.roiHours);

  const ctx = document.getElementById('roiChart').getContext('2d');
  if (chartRoi) chartRoi.destroy();
  chartRoi = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: rows.map(r => r.cropName),
      datasets: [{{
        label: 'ROI (hours)',
        backgroundColor: rows.map(r => LEVEL_COLOURS[r.level] + 'bb'),
        borderColor: rows.map(r => LEVEL_COLOURS[r.level]),
        borderWidth: 1,
        borderRadius: 4,
        data: rows.map(r => +r.roiHours.toFixed(1)),
      }}],
    }},
    options: {{
      indexAxis: 'y',
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ ticks: {{ color: '#64748b', font: {{ family: 'DM Mono', size: 10 }} }}, grid: {{ color: '#1e2d40' }} }},
        y: {{ ticks: {{ color: '#94a3b8', font: {{ family: 'DM Mono', size: 10 }} }}, grid: {{ color: '#1e2d40' }} }},
      }},
      responsive: true,
      animation: {{ duration: 300 }},
    }},
  }});
}}

// ---- Chart: level vs ROI for a single crop ----
function buildLevelChart(cropId) {{
  const crop = cropId || RAW[0].cropId;
  const rows = [1,2,3,4,5].map(lvl => RAW.map(scaled).find(r => r.cropId === crop && r.level === lvl));

  const ctx = document.getElementById('levelChart').getContext('2d');
  if (chartLevel) chartLevel.destroy();
  chartLevel = new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: ['Lv 1','Lv 2','Lv 3','Lv 4','Lv 5'],
      datasets: [{{
        label: 'ROI (hours)',
        borderColor: '#38bdf8',
        backgroundColor: '#38bdf820',
        pointBackgroundColor: '#38bdf8',
        fill: true,
        tension: 0.3,
        data: rows.map(r => r ? +r.roiHours.toFixed(1) : null),
      }}, {{
        label: 'Profit / hr (÷1000)',
        borderColor: '#818cf8',
        backgroundColor: '#818cf820',
        pointBackgroundColor: '#818cf8',
        fill: true,
        tension: 0.3,
        yAxisID: 'y2',
        data: rows.map(r => r ? Math.round(r.profitPerHour / 1000) : null),
      }}],
    }},
    options: {{
      plugins: {{
        legend: {{ labels: {{ color: '#94a3b8', font: {{ family: 'DM Mono', size: 11 }} }} }},
        title: {{ display: true, text: (CROP_NAMES[crop] || crop) + ' — by level', color: '#94a3b8', font: {{ family: 'DM Mono', size: 11 }} }},
      }},
      scales: {{
        x: {{ ticks: {{ color: '#64748b', font: {{ family: 'DM Mono', size: 10 }} }}, grid: {{ color: '#1e2d40' }} }},
        y: {{ ticks: {{ color: '#64748b', font: {{ family: 'DM Mono', size: 10 }} }}, grid: {{ color: '#1e2d40' }} }},
        y2: {{ position: 'right', ticks: {{ color: '#818cf8', font: {{ family: 'DM Mono', size: 10 }} }}, grid: {{ drawOnChartArea: false }} }},
      }},
      responsive: true,
      animation: {{ duration: 300 }},
    }},
  }});
}}

// ---- Table ----
function renderTable() {{
  const rows = filtered().sort((a,b) => {{
    const va = a[sortCol], vb = b[sortCol];
    return typeof va === 'string'
      ? (sortAsc ? va.localeCompare(vb) : vb.localeCompare(va))
      : (sortAsc ? va - vb : vb - va);
  }});

  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = rows.map(r => `
    <tr data-crop="${{r.cropId}}" style="cursor:pointer">
      <td>${{r.cropName}}</td>
      <td><span class="badge" style="background:${{LEVEL_COLOURS[r.level]}}22;color:${{LEVEL_COLOURS[r.level]}};border:1px solid ${{LEVEL_COLOURS[r.level]}}55">Lv ${{r.level}}</span></td>
      <td class="num">${{fmtCoins(r.upgradeCost)}}</td>
      <td class="num">${{fmtCoins(r.profitPerHour)}}</td>
      <td class="num">${{r.roiHours.toFixed(1)}}</td>
      <td class="num muted">${{r.roiDays.toFixed(2)}}</td>
    </tr>
  `).join('');

  tbody.querySelectorAll('tr').forEach(tr => {{
    tr.addEventListener('click', () => buildLevelChart(tr.dataset.crop));
  }});
}}

// ---- KPIs ----
function updateKpis() {{
  const bps = getBps();
  const lvl = getLevel() || 5;
  const rows = filteredAtLevel(lvl);
  const best = rows.reduce((a,b) => a.roiHours < b.roiHours ? a : b, rows[0]);
  const topProfit = rows.reduce((a,b) => a.profitPerHour > b.profitPerHour ? a : b, rows[0]);
  const avgRoi = rows.reduce((s,r) => s + r.roiHours, 0) / rows.length;

  document.getElementById('kpiBestCrop').textContent = best ? (CROP_NAMES[best.cropId] || best.cropId) : '—';
  document.getElementById('kpiBestSub').textContent = best ? `ROI: ${{best.roiHours.toFixed(1)}} hrs` : '';
  document.getElementById('kpiTopProfit').textContent = topProfit ? fmtCoins(topProfit.profitPerHour) : '—';
  document.getElementById('kpiTopProfitSub').textContent = topProfit ? (CROP_NAMES[topProfit.cropId] || '') : '';
  document.getElementById('kpiAvgROI').textContent = avgRoi ? avgRoi.toFixed(1) : '—';
  document.getElementById('kpiBph').textContent = fmt(Math.round(bps * 3600));
}}

// ---- Sort headers ----
document.querySelectorAll('th[data-col]').forEach(th => {{
  th.addEventListener('click', () => {{
    const col = th.dataset.col;
    if (sortCol === col) sortAsc = !sortAsc;
    else {{ sortCol = col; sortAsc = true; }}
    document.querySelectorAll('th').forEach(t => t.classList.remove('sorted'));
    th.classList.add('sorted');
    renderTable();
  }});
}});

// ---- Reactive controls ----
function refresh() {{
  updateKpis();
  buildProfitChart();
  buildRoiChart();
  renderTable();
}}

document.getElementById('levelSel').addEventListener('change', refresh);
document.getElementById('metricSel').addEventListener('change', refresh);
document.getElementById('bpsRange').addEventListener('input', () => {{
  document.getElementById('bpsLabel').textContent = getBps();
  refresh();
}});

// ---- Init ----
refresh();
buildLevelChart(RAW[0].cropId);
</script>
</body>
</html>"""
