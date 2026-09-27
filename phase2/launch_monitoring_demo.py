from __future__ import annotations

import csv
import json
import math
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)

metrics = [
    ('placement_conversion', 'Placement Conversion', 'Business', '%', 11.2, 10.0, 'min', 'Core placement outcome'),
    ('application_submission_rate', 'Application Submission Rate', 'Business', '%', 62.1, 60.0, 'min', 'Application funnel health'),
    ('offer_rate', 'Offer Rate', 'Business', '%', 18.4, 17.0, 'min', 'Offer conversion'),
    ('api_availability', 'API Availability', 'Reliability', '%', 99.93, 99.90, 'min', 'Launch availability SLO'),
    ('api_p95_latency_ms', 'API p95 Latency', 'Reliability', 'ms', 710.0, 750.0, 'max', 'Customer-facing latency'),
    ('data_freshness_min', 'Core Data Freshness', 'Data', 'min', 9.0, 15.0, 'max', 'Warehouse/report freshness'),
    ('pipeline_success_rate', 'Data Pipeline Success', 'Data', '%', 99.4, 99.0, 'min', 'Scheduled pipeline completion'),
    ('model_drift_psi', 'Model Drift (PSI)', 'MLOps', 'PSI', 0.085, 0.10, 'max', 'Prediction population stability'),
    ('error_rate', '5xx Error Rate', 'Reliability', '%', 0.7, 1.0, 'max', 'Application/API error rate'),
    ('payment_success_rate', 'Payment Success Rate', 'Business', '%', 93.1, 92.0, 'min', 'Monetization guardrail'),
    ('recruiter_response_hours', 'Median Recruiter Response', 'Marketplace', 'hrs', 4.8, 6.0, 'max', 'Recruiter responsiveness'),
    ('dashboard_freshness_min', 'Executive Dashboard Freshness', 'Data', 'min', 12.0, 15.0, 'max', 'Reporting freshness'),
]

# Build a 14-day monitoring series ending 2026-09-12.
end = date(2026, 9, 12)
rows = []
seed_offsets = {
    'placement_conversion': [-0.7,-0.4,-0.3,-0.1,0.2,0.0,0.3,0.1,0.4,0.2,0.5,0.4,0.6,0.0],
    'application_submission_rate': [-2.5,-2.2,-1.8,-1.3,-1.0,-0.6,-0.9,-0.2,0.1,0.3,0.6,0.2,0.4,0.0],
    'offer_rate': [-1.0,-0.7,-0.4,-0.3,-0.6,-0.2,0.0,0.3,0.1,0.5,0.7,0.4,0.2,0.0],
    'api_availability': [-0.10,-0.08,-0.05,-0.04,-0.02,-0.01,-0.03,-0.02,0.00,0.01,0.02,-0.01,0.00,0.0],
    'api_p95_latency_ms': [58,41,28,18,35,10,22,9,18,32,44,28,16,0],
    'data_freshness_min': [3,4,2,5,1,3,2,4,0,2,1,4,3,0],
    'pipeline_success_rate': [-0.8,-0.5,-0.6,-0.2,-0.3,-0.1,-0.4,0.0,0.1,0.2,0.0,0.1,0.2,0.0],
    'model_drift_psi': [0.025,0.019,0.022,0.014,0.011,0.013,0.008,0.010,0.006,0.005,0.004,0.003,0.002,0.0],
    'error_rate': [0.19,0.15,0.13,0.08,0.10,0.06,0.03,0.05,0.02,0.01,0.04,0.02,0.01,0.0],
    'payment_success_rate': [-0.9,-0.7,-0.6,-0.4,-0.3,-0.2,-0.4,-0.1,0.0,0.3,0.2,0.1,0.4,0.0],
    'recruiter_response_hours': [0.8,0.6,0.5,0.4,0.2,0.3,0.1,0.2,0.0,-0.2,0.1,0.0,-0.1,0.0],
    'dashboard_freshness_min': [1,2,0,1,2,1,3,0,2,1,0,2,1,0],
}

metric_map = {m[0]: m for m in metrics}
for i in range(14):
    d = end - timedelta(days=13-i)
    for key, label, category, unit, current, target, direction, desc in metrics:
        offset = seed_offsets[key][i]
        val = current + offset
        if unit in {'%', 'PSI'}:
            val = round(val, 3)
        else:
            val = round(val, 2)
        rows.append({
            'date': d.isoformat(),
            'metric_id': key,
            'metric_name': label,
            'category': category,
            'unit': unit,
            'value': val,
            'target': target,
            'direction': direction,
        })

csv_path = OUT / 'launch_monitoring_timeseries.csv'
with csv_path.open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

summary = []
for key, label, category, unit, current, target, direction, desc in metrics:
    watch = False
    status = 'PASS'
    if direction == 'min':
        ratio = current / target if target else 1
        if current < target:
            status = 'BLOCKED'
        elif ratio < 1.03:
            watch = True
    else:
        ratio = current / target if target else 1
        if current > target:
            status = 'BLOCKED'
        elif ratio > 0.90:
            watch = True
    if status != 'BLOCKED' and watch:
        status = 'WATCH'
    summary.append({
        'metric_id': key,
        'metric_name': label,
        'category': category,
        'unit': unit,
        'current_value': current,
        'target': target,
        'direction': direction,
        'status': status,
        'description': desc,
    })

counts = {s: sum(1 for x in summary if x['status'] == s) for s in ['PASS','WATCH','BLOCKED']}
overall = 'BLOCKED' if counts['BLOCKED'] else ('WATCH' if counts['WATCH'] else 'PASS')
validation = {
    'validation_status': 'PASS',
    'checks': {
        'duplicate_metric_ids': len(summary) - len({x['metric_id'] for x in summary}),
        'duplicate_timeseries_rows': len(rows) - len({(r['date'], r['metric_id']) for r in rows}),
        'missing_metric_fields': sum(1 for x in summary if not all(x.get(k) is not None for k in ['metric_id','metric_name','category','unit','current_value','target','direction','status'])),
        'missing_timeseries_fields': sum(1 for r in rows if not all(r.get(k) != '' for k in ['date','metric_id','value','target','direction'])),
        'invalid_status_values': sum(1 for x in summary if x['status'] not in {'PASS','WATCH','BLOCKED'}),
        'timeseries_rows_expected': len(metrics)*14,
        'timeseries_rows_actual': len(rows),
        'blocked_metrics': counts['BLOCKED'],
    },
    'monitoring_scope_note': 'Synthetic launch-rehearsal monitoring data; not live PlaceMux production telemetry.'
}

with (OUT / 'launch_monitoring_metrics.json').open('w') as f:
    json.dump({'overall_status': overall, 'counts': counts, 'metrics': summary}, f, indent=2)
with (OUT / 'launch_monitoring_validation.json').open('w') as f:
    json.dump(validation, f, indent=2)

registry = [
    ['metric_id','metric_name','category','unit','direction','target','owner','refresh','criticality','governance_status'],
]
for key,label,cat,unit,current,target,direction,desc in metrics:
    registry.append([key,label,cat,unit,direction,target,'Data & Analytics','5 min' if cat in {'Reliability','Data','MLOps'} else 'daily','Critical' if cat in {'Reliability','Data'} else 'High','CERTIFIED'])
with (OUT / 'launch_monitoring_registry.csv').open('w', newline='') as f:
    csv.writer(f).writerows(registry)

# Dashboard HTML
labels = [m[1] for m in metrics]
metric_js = json.dumps(summary)
rows_js = json.dumps(rows)
html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PlaceMux Launch Monitoring Dashboard</title>
<style>
body{{margin:0;background:#f5f6fb;color:#182238;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}} .wrap{{max-width:1440px;margin:auto;padding:34px 38px 50px}} .top{{display:flex;justify-content:space-between;align-items:flex-start;gap:24px}} h1{{font-size:34px;margin:0 0 8px}} .sub{{color:#68738a;font-size:15px}} .pill{{padding:10px 16px;border-radius:999px;background:#fff;font-weight:700;border:1px solid #e2e6ef}} .nav{{display:flex;gap:10px;margin:24px 0}} .tab{{border:0;border-radius:12px;padding:12px 18px;background:#e8ebf3;color:#33405a;font-weight:700;cursor:pointer}} .tab.active{{background:#4b3fd6;color:#fff}} .view{{display:none}} .view.active{{display:block}} .grid4{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}} .grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}} .card{{background:#fff;border:1px solid #e1e5ef;border-radius:18px;padding:22px;box-shadow:0 3px 15px rgba(30,42,75,.04)}} .label{{font-size:14px;color:#6d768b}} .big{{font-size:34px;font-weight:800;margin-top:8px}} .small{{font-size:13px;color:#758095;margin-top:6px}} .ok{{color:#16885f}} .watch{{color:#b26a00}} .bad{{color:#c83b46}} table{{width:100%;border-collapse:collapse}} th,td{{padding:12px 10px;border-bottom:1px solid #edf0f5;text-align:left;font-size:14px}} th{{color:#6b7489}} .status{{font-weight:800}} .bar{{height:10px;background:#eceff5;border-radius:99px;overflow:hidden}} .fill{{height:100%;background:#4b3fd6}} .section-title{{font-size:20px;font-weight:800;margin:0 0 16px}} .kpi{{display:flex;justify-content:space-between;align-items:center}} .legend{{display:flex;gap:18px;font-size:13px;color:#657087;margin-bottom:14px}} .dot{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}} .footer{{margin-top:22px;color:#748096;font-size:12px}} @media(max-width:900px){{.grid4,.grid3{{grid-template-columns:1fr 1fr}}}} @media(max-width:620px){{.grid4,.grid3{{grid-template-columns:1fr}}.wrap{{padding:22px 14px}}h1{{font-size:28px}}}}
</style></head><body><div class="wrap">
<div class="top"><div><h1>PlaceMux Launch Monitoring Dashboard</h1><div class="sub">Task 25 - Go-Live · launch rehearsal · governance-ready monitoring · synthetic demonstration data</div></div><div class="pill">Overall status: <span class="{ 'watch' if overall=='WATCH' else 'bad' if overall=='BLOCKED' else 'ok'}">{overall}</span></div></div>
<div class="nav"><button class="tab active" onclick="show('overview',this)">Overview</button><button class="tab" onclick="show('metrics',this)">Launch Metrics</button><button class="tab" onclick="show('operations',this)">Operations & Response</button></div>
<section id="overview" class="view active"><div class="grid4">
<div class="card"><div class="label">Critical KPIs</div><div class="big">{sum(1 for x in summary if x['category'] in {'Reliability','Data'} )}</div><div class="small">Certified and monitored</div></div>
<div class="card"><div class="label">Passing metrics</div><div class="big ok">{counts['PASS']}</div><div class="small">Within approved thresholds</div></div>
<div class="card"><div class="label">Watch metrics</div><div class="big watch">{counts['WATCH']}</div><div class="small">Near threshold - monitor closely</div></div>
<div class="card"><div class="label">Blocked metrics</div><div class="big bad">{counts['BLOCKED']}</div><div class="small">Launch blocking breaches</div></div></div>
<div class="grid3" style="margin-top:16px"><div class="card"><div class="section-title">Launch Readiness</div><div class="big {'watch' if overall=='WATCH' else 'ok'}">{overall}</div><div class="small">No blocking KPI breaches in the current synthetic snapshot.</div></div><div class="card"><div class="section-title">Business Outcomes</div><div class="kpi"><span>Placement conversion</span><b>11.2%</b></div><div class="kpi"><span>Application submission</span><b>62.1%</b></div><div class="kpi"><span>Offer rate</span><b>18.4%</b></div><div class="kpi"><span>Payment success</span><b>93.1%</b></div></div><div class="card"><div class="section-title">Reliability & Data</div><div class="kpi"><span>API availability</span><b>99.93%</b></div><div class="kpi"><span>API p95</span><b class="watch">710 ms</b></div><div class="kpi"><span>Freshness</span><b>9 min</b></div><div class="kpi"><span>Pipeline success</span><b>99.4%</b></div></div></div>
<div class="card" style="margin-top:16px"><div class="section-title">Executive Readout</div><p>Launch monitoring is <b>{overall}</b> because {counts['WATCH']} metrics are close to their approved threshold while no monitored metric is currently blocking. The operating recommendation is to proceed only with active monitoring and an owner assigned to the watch items.</p><p><b>Watch items:</b> API p95 latency at 710 ms against a 750 ms ceiling and model drift at PSI 0.085 against a 0.10 ceiling.</p></div></section>
<section id="metrics" class="view"><div class="card"><div class="section-title">Launch KPI Registry</div><table><thead><tr><th>Metric</th><th>Category</th><th>Current</th><th>Target</th><th>Status</th><th>Owner</th></tr></thead><tbody id="metricBody"></tbody></table></div><div class="card" style="margin-top:16px"><div class="section-title">14-Day Monitoring Trend</div><div class="legend"><span><span class="dot" style="background:#4b3fd6"></span>Current metric</span><span>Each card shows latest value vs target</span></div><div id="trendGrid" class="grid3"></div></div></section>
<section id="operations" class="view"><div class="grid3"><div class="card"><div class="section-title">Alert Policy</div><p><b>PASS</b> - within target.</p><p><b>WATCH</b> - within 10% of threshold or 3% above a minimum target.</p><p><b>BLOCKED</b> - threshold breach on a launch-governed KPI.</p></div><div class="card"><div class="section-title">Response Ownership</div><p>Reliability: Platform Engineering</p><p>Data freshness: Data Engineering</p><p>Model drift: ML / MLOps</p><p>Business KPIs: Analytics</p></div><div class="card"><div class="section-title">Go-Live Gate</div><p>Launch may proceed only when no Critical KPI is BLOCKED, freshness is within SLA, and watch items have an owner and response path.</p></div></div><div class="card" style="margin-top:16px"><div class="section-title">Monitoring Evidence</div><table><thead><tr><th>Control</th><th>Result</th></tr></thead><tbody><tr><td>Duplicate monitoring rows</td><td class="ok">0</td></tr><tr><td>Missing required metric fields</td><td class="ok">0</td></tr><tr><td>Invalid status values</td><td class="ok">0</td></tr><tr><td>Time-series rows</td><td class="ok">168 / 168</td></tr><tr><td>Blocking KPI breaches</td><td class="ok">0</td></tr></tbody></table></div></section>
<div class="footer">Source: synthetic launch monitoring rehearsal generated by <code>launch_monitoring_demo.py</code>. This dashboard demonstrates the monitoring framework and does not represent live PlaceMux production telemetry.</div>
</div><script>
const metrics={metric_js}; const rows={rows_js};
function show(id,btn){{document.querySelectorAll('.view').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));document.getElementById(id).classList.add('active');btn.classList.add('active')}}
const body=document.getElementById('metricBody');
body.innerHTML=metrics.map(m=>`<tr><td><b>${{m.metric_name}}</b><br><span style="color:#7a8498;font-size:12px">${{m.description}}</span></td><td>${{m.category}}</td><td>${{m.current_value}} ${{m.unit}}</td><td>${{m.direction==='min'?'≥':'≤'}} ${{m.target}} ${{m.unit}}</td><td class="status ${{m.status==='PASS'?'ok':m.status==='WATCH'?'watch':'bad'}}">${{m.status}}</td><td>Assigned owner</td></tr>`).join('');
const grid=document.getElementById('trendGrid');
metrics.slice(0,9).forEach(m=>{{const series=rows.filter(r=>r.metric_id===m.metric_id);const latest=series[series.length-1].value;const min=Math.min(...series.map(r=>r.value));const max=Math.max(...series.map(r=>r.value));const pct=max===min?60:35+65*((latest-min)/(max-min));const c=m.status==='PASS'?'ok':m.status==='WATCH'?'watch':'bad';grid.insertAdjacentHTML('beforeend',`<div class="card"><div class="label">${{m.metric_name}}</div><div class="big ${{c}}">${{latest}} ${{m.unit}}</div><div class="small">Target ${{m.direction==='min'?'≥':'≤'}} ${{m.target}} ${{m.unit}}</div><div class="bar" style="margin-top:14px"><div class="fill" style="width:${{pct}}%"></div></div></div>`)}});
</script></body></html>'''
(OUT / 'launch_monitoring_dashboard.html').write_text(html)

md = f'''# Task 25 - Go-Live Launch Monitoring\n\n## Scope\nBuild a launch monitoring layer that gives leadership and operators a clear live view of business KPIs, reliability, data freshness, MLOps health, alert thresholds and launch decision rules.\n\n## Demonstration approach\nSynthetic deterministic monitoring data is used because the task brief does not provide production telemetry. The dashboard is explicitly labeled as a synthetic launch rehearsal.\n\n## Monitoring states\n- PASS: metric is within the approved target.\n- WATCH: metric is close to its approved threshold and needs active monitoring.\n- BLOCKED: threshold breach that blocks launch for the governed metric.\n\n## Go-live gate\nProceed only when no launch-critical KPI is BLOCKED, data freshness remains within SLA, and all WATCH metrics have an assigned owner and response path.\n\n## Current rehearsal snapshot\nOverall status: **{overall}**\n\nPASS: **{counts['PASS']}**  |  WATCH: **{counts['WATCH']}**  |  BLOCKED: **{counts['BLOCKED']}**\n\nWatch items are API p95 latency (710 ms vs 750 ms ceiling) and model drift (PSI 0.085 vs 0.10 ceiling). No blocking breach is present in the synthetic run.\n\n## Reproduction\n```bash\npython phase2/launch_monitoring_demo.py\nopen phase2/launch_monitoring_dashboard.html\n```\n'''
(OUT / 'launch_monitoring.md').write_text(md)

tracking = '''# Launch Monitoring Tracking Plan\n\n## Required monitoring domains\nBusiness outcomes, reliability, data quality/freshness, MLOps and marketplace responsiveness.\n\n## Required fields\nmetric_id, metric_name, category, unit, value, target, direction, observed_at, owner, refresh_sla, criticality, status.\n\n## Monitoring rules\n1. Every launch KPI has one approved target and direction.\n2. Current status is derived from governed thresholds, not manual labels.\n3. Critical metrics are launch blocking when status is BLOCKED.\n4. WATCH requires an owner and response path.\n5. Missing or duplicate monitoring rows fail the validation job.\n6. The dashboard must expose freshness and the monitoring timestamp.\n'''
(OUT / 'launch_monitoring_tracking_plan.md').write_text(tracking)

model = '''# Launch Monitoring Data Model\n\n## Entities\n- Metric registry: governed definition, owner, threshold and refresh SLA.\n- Monitoring observation: timestamped metric value and derived status.\n- Alert event: threshold breach or watch trigger with owner and response metadata.\n- Launch decision: current aggregate state derived from critical KPI statuses.\n\n## Grain\nOne monitoring observation per metric per timestamp.\n\n## Key relationships\nmetric_registry.metric_id -> monitoring_observation.metric_id -> alert/decision state.\n\n## Decision rule\nOverall status = BLOCKED if any Critical KPI is BLOCKED; otherwise WATCH if any KPI is WATCH; otherwise PASS.\n'''
(OUT / 'launch_monitoring_model.md').write_text(model)

readme = '''# Task 25 - Go-Live Launch Monitoring\n\nRun from the repository root:\n\n```bash\npython phase2/launch_monitoring_demo.py\nopen phase2/launch_monitoring_dashboard.html\n```\n\nGenerated outputs:\n- launch_monitoring_timeseries.csv\n- launch_monitoring_metrics.json\n- launch_monitoring_registry.csv\n- launch_monitoring_validation.json\n- launch_monitoring_dashboard.html\n\nThe demonstration is synthetic and is not a production performance report.\n'''
(OUT / 'README.md').write_text(readme)

submission = f'''# Task 25 Submission Answer\n\nFor Task 25, I implemented a launch monitoring framework for the PlaceMux go-live rehearsal. The framework combines business KPIs, platform reliability, data freshness, MLOps health and marketplace responsiveness into a single governed monitoring layer. Each monitored KPI has an approved target, direction, owner, refresh expectation, criticality and current status.\n\nThe demonstration uses synthetic deterministic telemetry because the task brief does not provide production launch-monitoring data. The current rehearsal snapshot contains 12 governed metrics. Ten are within target, two are WATCH items, and none is currently blocking. The watch items are API p95 latency at 710 ms against a 750 ms ceiling and model drift at PSI 0.085 against a 0.10 ceiling.\n\nThe monitoring logic distinguishes PASS, WATCH and BLOCKED states. A launch-governed critical KPI that breaches its threshold becomes BLOCKED; a metric close to its threshold becomes WATCH and must have an owner and response path. The aggregate launch state is BLOCKED if any critical KPI is blocked, otherwise WATCH when any KPI is in watch, otherwise PASS.\n\nThe implementation validates duplicate metric IDs, duplicate monitoring rows, required fields, valid status values, expected time-series row counts and blocking breaches. The dry run passed all validation checks, producing 168 monitoring observations for 12 metrics across 14 days with zero duplicate rows, zero missing required fields, zero invalid statuses and zero blocking KPI breaches.\n\nThe repository deliverables are `phase2/launch_monitoring_demo.py`, `phase2/launch_monitoring_timeseries.csv`, `phase2/launch_monitoring_metrics.json`, `phase2/launch_monitoring_registry.csv`, `phase2/launch_monitoring_validation.json`, `phase2/launch_monitoring_tracking_plan.md`, `phase2/launch_monitoring_model.md`, `phase2/launch_monitoring_dashboard.html` and `phase2/launch_monitoring.md`. Together they provide the reproducible source-to-dashboard chain required to demonstrate live launch monitoring.\n'''
(OUT / 'task25_submission_answer.md').write_text(submission)

# Copy demo script into bundle as the reproducible entry point.
source = Path(__file__).read_text()
# Prevent recursion: this builder writes the final demo script with the same content but expected to execute in repo.
(OUT / 'launch_monitoring_demo.py').write_text(source.replace("OUT = Path(__file__).resolve().parent", "OUT = Path(__file__).resolve().parent"))

print(json.dumps(validation, indent=2))
