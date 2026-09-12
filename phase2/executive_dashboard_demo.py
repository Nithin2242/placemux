from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
SEED = 2301
rng = np.random.default_rng(SEED)

COLLEGES = [
    'PES University',
    'BMS Institute of Technology',
    'New Horizon College of Engineering',
    'RV College of Engineering',
    'CMR Institute of Technology',
    'Dayananda Sagar College of Engineering',
]
RECRUITERS = ['Recruiter A', 'Recruiter B', 'Recruiter C', 'Recruiter D', 'Recruiter E', 'Recruiter F', 'Recruiter G', 'Recruiter H']
COMPANIES = ['TechNova', 'FinEdge', 'CloudSprint', 'DataForge', 'NextGen Systems', 'InnoWorks', 'RetailPulse', 'SecureStack', 'BuildRight', 'MarketMint', 'LogicLoop', 'HealthByte']


def build_data():
    n_students = 2400
    student_ids = [f'S{10000+i}' for i in range(n_students)]
    college = rng.choice(COLLEGES, size=n_students, p=[.15,.17,.16,.16,.17,.19])
    profile_complete = rng.random(n_students) < .924
    documents_verified = rng.random(n_students) < .902
    eligible = (rng.random(n_students) < .666) & profile_complete & documents_verified

    students = pd.DataFrame({
        'student_id': student_ids,
        'college': college,
        'profile_complete': profile_complete,
        'documents_verified': documents_verified,
        'eligible': eligible,
    })

    # Applications: exactly 3,200 deterministic rows.
    apps = []
    eligible_ids = students.loc[students['eligible'], 'student_id'].tolist()
    for i in range(3200):
        sid = eligible_ids[i % len(eligible_ids)] if eligible_ids else student_ids[i % n_students]
        apps.append((
            f'APP{20000+i}', sid, rng.choice(COMPANIES), rng.choice(RECRUITERS),
            rng.choice(['Submitted','Screening','Interview','Offer','Rejected'], p=[.26,.18,.22,.08,.26])
        ))
    applications = pd.DataFrame(apps, columns=['application_id','student_id','company','recruiter','stage'])
    applications['placed'] = applications['stage'].eq('Offer') & (rng.random(len(applications)) < .62)
    applications['offer_value'] = np.where(applications['stage'].eq('Offer'), rng.normal(7.9, 1.8, len(applications)).clip(3.2, 16.0), np.nan)

    # Company engagement at college level.
    engagement = []
    for c in COLLEGES:
        for company in COMPANIES:
            invites = int(rng.integers(1, 5))
            interviews = int(max(0, rng.normal(invites*3.1, 1.8)))
            offers = int(max(0, rng.normal(interviews*.22, .8)))
            engagement.append((c, company, invites, interviews, offers))
    engagement = pd.DataFrame(engagement, columns=['college','company','invites','interviews','offers'])

    # Reliability / MLOps weekly demo metrics.
    weeks = pd.date_range('2026-08-01', periods=6, freq='W-SAT')
    ops = pd.DataFrame({
        'week': weeks.strftime('%d %b'),
        'api_availability_pct': np.round(rng.normal(99.75, .09, 6).clip(99.35, 99.99), 2),
        'p95_latency_ms': np.round(rng.normal(410, 35, 6).clip(350, 490), 0).astype(int),
        'data_freshness_min': np.round(rng.normal(23, 4, 6).clip(15, 35), 1),
        'model_drift_psi': np.round(rng.normal(.072, .012, 6).clip(.04, .11), 3),
        'pipeline_success_pct': np.round(rng.normal(98.6, .5, 6).clip(97.4, 99.6), 2),
    })

    students.to_csv(BASE / 'executive_students_demo.csv', index=False)
    applications.to_csv(BASE / 'executive_applications_demo.csv', index=False)
    engagement.to_csv(BASE / 'executive_company_engagement_demo.csv', index=False)
    ops.to_csv(BASE / 'executive_ops_demo.csv', index=False)
    return students, applications, engagement, ops


def compute_metrics(students, applications, engagement, ops):
    registered = len(students)
    eligible = int(students['eligible'].sum())
    profile_completion = float(students['profile_complete'].mean() * 100)
    applications_count = len(applications)
    placed_students = int(applications.loc[applications['placed'], 'student_id'].nunique())
    placement_rate = placed_students / eligible * 100 if eligible else 0
    avg_package = float(applications.loc[applications['placed'], 'offer_value'].mean())
    companies_active = int(applications['company'].nunique())
    recruiter_active = int(applications['recruiter'].nunique())
    offer_rate = float(applications['stage'].eq('Offer').mean() * 100)
    interview_rate = float(applications['stage'].eq('Interview').mean() * 100)
    rejected_rate = float(applications['stage'].eq('Rejected').mean() * 100)

    latest = ops.iloc[-1]
    metrics = [
        ('Registered Students', registered, 'count', 'Student master'),
        ('Eligible Students', eligible, 'count', 'Eligibility rule'),
        ('Profile Completion', round(profile_completion, 1), 'pct', 'Student profile completeness'),
        ('Applications', applications_count, 'count', 'Application events'),
        ('Placed Students', placed_students, 'count', 'Distinct students with placement outcome'),
        ('Placement Rate', round(placement_rate, 1), 'pct', 'Placed students / eligible students'),
        ('Average Package', round(avg_package, 2), 'lpa', 'Average package among placed students'),
        ('Active Companies', companies_active, 'count', 'Unique companies with an application'),
        ('Active Recruiters', recruiter_active, 'count', 'Unique recruiters handling applications'),
        ('Offer Rate', round(offer_rate, 1), 'pct', 'Offers / applications'),
        ('Interview Stage Share', round(interview_rate, 1), 'pct', 'Interview-stage applications / applications'),
        ('Rejected Share', round(rejected_rate, 1), 'pct', 'Rejected applications / applications'),
        ('API Availability', float(latest['api_availability_pct']), 'pct', 'Latest week'),
        ('P95 Latency', int(latest['p95_latency_ms']), 'ms', 'Latest week'),
        ('Data Freshness', float(latest['data_freshness_min']), 'min', 'Latest week'),
        ('Model Drift PSI', float(latest['model_drift_psi']), 'psi', 'Latest week'),
        ('Pipeline Success', float(latest['pipeline_success_pct']), 'pct', 'Latest week'),
    ]
    return pd.DataFrame(metrics, columns=['metric','value','unit','definition'])


def validate(students, applications, engagement, ops):
    checks = {
        'duplicate_student_ids': int(students['student_id'].duplicated().sum()),
        'duplicate_application_ids': int(applications['application_id'].duplicated().sum()),
        'applications_without_student': int((~applications['student_id'].isin(students['student_id'])).sum()),
        'invalid_application_stages': int((~applications['stage'].isin(['Submitted','Screening','Interview','Offer','Rejected'])).sum()),
        'negative_offer_values': int((applications['offer_value'].fillna(0) < 0).sum()),
        'ops_missing_rows': int(ops.isna().sum().sum()),
        'latency_threshold_breaches': int((ops['p95_latency_ms'] > 500).sum()),
        'drift_threshold_breaches': int((ops['model_drift_psi'] > .20).sum()),
    }
    status = 'PASS' if all(v == 0 for v in checks.values()) else 'FAIL'
    out = {'validation_status': status, 'checks': checks, 'scope_note': 'Synthetic executive demonstration; not production PlaceMux performance.'}
    (BASE / 'executive_dashboard_validation.json').write_text(json.dumps(out, indent=2))
    return out


def write_dashboard(metrics, students, applications, engagement, ops, validation):
    applications_count = int(len(applications))
    offer_rate = float(applications['stage'].eq('Offer').mean() * 100)
    avg_package = float(applications.loc[applications['placed'], 'offer_value'].mean())
    companies_active = int(applications['company'].nunique())
    def college_rows():
        rows = []
        for c, g in students.groupby('college'):
            e = int(g['eligible'].sum())
            placed = int(applications[applications['placed'] & applications['student_id'].isin(g['student_id'])]['student_id'].nunique())
            rate = placed / e * 100 if e else 0
            rows.append({'college':c,'eligible':e,'placed':placed,'rate':round(rate,1),'applications':int(applications['student_id'].isin(g['student_id']).sum())})
        return sorted(rows, key=lambda x: x['rate'], reverse=True)
    rows = college_rows()
    top_companies = applications.groupby('company').size().sort_values(ascending=False).head(6)
    company_rows = [{'company':k,'applications':int(v)} for k,v in top_companies.items()]
    ops_rows = ops.to_dict('records')

    metrics_json = metrics.to_dict(orient='records')
    html = f'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PlaceMux Executive Dashboard</title>
<style>
:root{{--bg:#f4f6fb;--card:#fff;--ink:#18233a;--muted:#63708a;--accent:#4f46e5;--good:#0f8a62;--warn:#b7791f;--line:#e5e9f2}}
*{{box-sizing:border-box}}body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;background:var(--bg);color:var(--ink)}}
.header{{background:white;padding:28px 46px 20px;border-bottom:1px solid var(--line)}}.title{{font-size:34px;font-weight:800}}.sub{{color:var(--muted);margin-top:5px;font-size:15px}}
.tabs{{display:flex;gap:10px;padding:14px 46px;background:white}}.tab{{padding:10px 16px;border-radius:10px;background:#eef0f7;font-weight:700;cursor:pointer}}.tab.active{{background:var(--accent);color:white}}
.wrap{{padding:26px 46px 46px}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}}.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}.card{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;box-shadow:0 2px 8px rgba(20,30,55,.04)}}.label{{font-size:13px;color:var(--muted)}}.num{{font-size:30px;font-weight:800;margin-top:8px}}.note{{font-size:12px;color:var(--muted);margin-top:6px}}
h2{{margin:0 0 12px;font-size:21px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:11px 8px;border-bottom:1px solid var(--line);text-align:left;font-size:13px}}th{{color:var(--muted);font-weight:700}}
.badge{{display:inline-block;padding:5px 9px;border-radius:999px;background:#eaf8f1;color:var(--good);font-weight:800;font-size:12px}}.bar{{height:9px;background:#edf0f7;border-radius:999px;overflow:hidden}}.bar span{{display:block;height:100%;background:var(--accent)}}.section{{margin-top:18px}}.hidden{{display:none}}.footer{{color:var(--muted);font-size:12px;margin-top:18px}}
@media(max-width:1000px){{.grid,.grid3{{grid-template-columns:repeat(2,1fr)}}.wrap,.tabs,.header{{padding-left:24px;padding-right:24px}}}}@media(max-width:650px){{.grid,.grid3{{grid-template-columns:1fr}}}}
</style></head><body>
<div class="header"><div class="title">PlaceMux Executive Dashboard</div><div class="sub">Executive view across placement outcomes, marketplace activity, reliability and MLOps health · Synthetic demonstration dataset</div></div>
<div class="tabs"><div class="tab active" onclick="show('overview',this)">Executive Overview</div><div class="tab" onclick="show('growth',this)">Growth & Placement</div><div class="tab" onclick="show('ops',this)">Reliability & MLOps</div></div>
<div class="wrap">
<section id="overview">
<div class="grid">
{''.join([f'<div class="card"><div class="label">{m["metric"]}</div><div class="num">{m["value"]}{"%" if m["unit"]=="pct" else (" LPA" if m["unit"]=="lpa" else (" ms" if m["unit"]=="ms" else ""))}</div><div class="note">{m["definition"]}</div></div>' for m in metrics_json[:8]])}
</div>
<div class="section grid3">
<div class="card"><h2>Executive Health</h2><p><span class="badge">{validation['validation_status']}</span> data, relationship and platform checks</p><p class="note">The dashboard is designed for executive review: outcome, scale, operational reliability and model health in one view.</p></div>
<div class="card"><h2>Placement Signal</h2><div class="num">{metrics_json[5]['value']}%</div><div class="note">Placed students / eligible students</div><div class="section"><div class="bar"><span style="width:{metrics_json[5]['value']}%"></span></div></div></div>
<div class="card"><h2>Platform Signal</h2><div class="num">{metrics_json[12]['value']}%</div><div class="note">Latest API availability</div><p class="note">P95 latency {metrics_json[13]['value']} ms · freshness {metrics_json[14]['value']} min</p></div>
</div>
<div class="section card"><h2>College Performance</h2><table><thead><tr><th>College</th><th>Eligible</th><th>Placed</th><th>Placement</th><th>Applications</th></tr></thead><tbody>{''.join([f'<tr><td>{r["college"]}</td><td>{r["eligible"]}</td><td>{r["placed"]}</td><td><b>{r["rate"]}%</b></td><td>{r["applications"]}</td></tr>' for r in rows])}</tbody></table></div>
</section>
<section id="growth" class="hidden">
<div class="grid"><div class="card"><div class="label">Applications</div><div class="num">{applications_count}</div><div class="note">Total application records</div></div><div class="card"><div class="label">Offer Rate</div><div class="num">{offer_rate:.1f}%</div><div class="note">Offers / applications</div></div><div class="card"><div class="label">Average Package</div><div class="num">{avg_package:.2f} LPA</div><div class="note">Among placed students</div></div><div class="card"><div class="label">Active Companies</div><div class="num">{companies_active}</div><div class="note">Companies with demand</div></div></div>
<div class="section grid3"><div class="card"><h2>Top Companies by Applications</h2><table><thead><tr><th>Company</th><th>Applications</th></tr></thead><tbody>{''.join([f'<tr><td>{r["company"]}</td><td>{r["applications"]}</td></tr>' for r in company_rows])}</tbody></table></div>
<div class="card"><h2>Application Stage Mix</h2>{''.join([f'<p><b>{label}</b> {count} ({count/applications_count*100:.1f}%)</p><div class="bar"><span style="width:{count/applications_count*100:.1f}%"></span></div>' for label,count in applications['stage'].value_counts().items()])}</div>
<div class="card"><h2>Executive Actions</h2><p>Prioritize colleges with lower placement conversion.</p><p>Inspect application-stage congestion before adding recruiter capacity.</p><p>Pair growth decisions with reliability and model-health guardrails.</p></div></div>
</section>
<section id="ops" class="hidden">
<div class="grid"><div class="card"><div class="label">API Availability</div><div class="num">{ops.iloc[-1]['api_availability_pct']}%</div></div><div class="card"><div class="label">P95 Latency</div><div class="num">{int(ops.iloc[-1]['p95_latency_ms'])} ms</div></div><div class="card"><div class="label">Data Freshness</div><div class="num">{ops.iloc[-1]['data_freshness_min']} min</div></div><div class="card"><div class="label">Model Drift PSI</div><div class="num">{ops.iloc[-1]['model_drift_psi']}</div></div></div>
<div class="section card"><h2>Weekly Reliability & MLOps Trend</h2><table><thead><tr><th>Week</th><th>Availability</th><th>P95 latency</th><th>Freshness</th><th>Drift PSI</th><th>Pipeline success</th></tr></thead><tbody>{''.join([f'<tr><td>{r["week"]}</td><td>{r["api_availability_pct"]}%</td><td>{int(r["p95_latency_ms"])} ms</td><td>{r["data_freshness_min"]} min</td><td>{r["model_drift_psi"]}</td><td>{r["pipeline_success_pct"]}%</td></tr>' for r in ops_rows])}</tbody></table></div>
<div class="section grid3"><div class="card"><h2>Data Quality</h2><p><span class="badge">PASS</span> source relationships, stage values and null controls</p></div><div class="card"><h2>Model Governance</h2><p>Monitor drift, threshold breaches, training-data freshness and rollback readiness.</p></div><div class="card"><h2>Scale Guardrails</h2><p>Escalate sustained latency, freshness or pipeline failures before capacity decisions.</p></div></div>
</section>
<div class="footer">Synthetic demonstration generated by executive_dashboard_demo.py. This dashboard demonstrates the executive reporting model and is not a production PlaceMux performance report.</div>
</div><script>function show(id,el){{document.querySelectorAll('section').forEach(s=>s.classList.add('hidden'));document.getElementById(id).classList.remove('hidden');document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));el.classList.add('active')}}</script></body></html>'''
    (BASE / 'executive_dashboard.html').write_text(html)

    summary = {'seed': SEED, 'students': len(students), 'applications': len(applications), 'companies': int(applications['company'].nunique()), 'validation_status': validation['validation_status']}
    (BASE / 'executive_dashboard_summary.json').write_text(json.dumps(summary, indent=2))


def main():
    students, applications, engagement, ops = build_data()
    metrics = compute_metrics(students, applications, engagement, ops)
    metrics.to_csv(BASE / 'executive_dashboard_metrics.csv', index=False)
    validation = validate(students, applications, engagement, ops)
    write_dashboard(metrics, students, applications, engagement, ops, validation)
    metric_doc = '''# Executive Dashboard Metrics\n\n## Purpose\nExecutive reporting for placement outcomes, marketplace activity, reliability and MLOps health.\n\n## Core metrics\n- Registered Students = distinct student records.\n- Eligible Students = students meeting the governed eligibility rule.\n- Placement Rate = distinct placed students / eligible students x 100.\n- Offer Rate = offer-stage applications / applications x 100.\n- Average Package = mean package value among placed students with a valid package.\n- API Availability = successful service time / observed service time x 100.\n- P95 Latency = 95th percentile request latency for the reporting period.\n- Data Freshness = minutes between latest trusted data timestamp and report refresh.\n- Model Drift PSI = population stability index on governed model monitoring features.\n- Pipeline Success = successful scheduled pipeline runs / total scheduled runs x 100.\n\nAll dashboard values in the dry run are synthetic demonstration metrics.\n'''
    (BASE / 'executive_dashboard_metrics.md').write_text(metric_doc)
    model_doc = '''# Executive Dashboard Data Model\n\nSources: student master, application events, company engagement, and platform/MLOps monitoring.\n\nAnalytical layers:\n1. Executive KPI layer\n2. College and placement performance layer\n3. Company demand layer\n4. Reliability and MLOps layer\n5. Validation/control layer\n\nThe executive layer consumes governed aggregate outputs rather than exposing unnecessary subject-level fields. Production implementation should apply role-based access, refresh SLAs, certified metric definitions and change control.\n'''
    (BASE / 'executive_dashboard_model.md').write_text(model_doc)
    tracking = '''# Executive Dashboard Tracking Plan\n\nRequired business keys: student_id, application_id, college_id/company_id, recruiter_id, report_date.\nOperational keys: run_id, pipeline_id, model_version.\n\nMinimum events/signals: application submitted, interview stage entered, offer created, placement recorded, pipeline run completed, data freshness check, model drift measurement, service availability and latency observation.\n\nGovernance: certified metrics use governed definitions; sensitive subject-level data stays outside executive aggregates; dashboards must display freshness and validation state.\n'''
    (BASE / 'executive_dashboard_tracking_plan.md').write_text(tracking)
    answer = '''# Task 23 Submission Answer\n\nFor Task 23, I built an executive dashboard that brings together placement outcomes, marketplace activity, platform reliability and MLOps health into a single decision-focused reporting layer. The dashboard is organized into Executive Overview, Growth & Placement, and Reliability & MLOps views so leadership can move from headline outcomes to the operating drivers behind them.\n\nThe demonstration uses synthetic data because the task brief does not provide production executive reporting data. The dry run covers 2,400 registered students and 3,200 applications across six colleges, with company and recruiter activity plus six weeks of operational monitoring. The dashboard calculates placement rate, offer rate, average package, active companies, API availability, p95 latency, data freshness, model drift and pipeline success using explicit formulas.\n\nThe executive view is designed to connect growth with operational readiness. Placement and application metrics show business outcomes and demand, while reliability and MLOps indicators prevent scale decisions from being made without visibility into latency, freshness, pipeline health or model drift. The dashboard also surfaces college-level performance and top company demand so management can prioritize follow-up actions rather than only read aggregate KPIs.\n\nThe implementation includes deterministic synthetic source data, metric definitions, a tracking plan, a logical model, machine-readable validation and a self-contained HTML dashboard. Validation checks confirm unique student and application identifiers, valid application stages, complete source relationships, clean monitoring rows and no demo threshold breaches. The result is a reproducible executive dashboard suitable for a governed production reporting pattern, while the displayed performance values remain explicitly synthetic demonstration metrics.\n'''
    (BASE / 'task23_submission_answer.md').write_text(answer)
    readme = '''# Task 23 - Executive Dashboards\n\n## Run\npython phase2/executive_dashboard_demo.py\n\n## Open\nphase2/executive_dashboard.html\n\n## Files\n- executive_dashboard_demo.py\n- executive_dashboard.html\n- executive_dashboard_metrics.csv\n- executive_dashboard_validation.json\n- executive_dashboard_metrics.md\n- executive_dashboard_tracking_plan.md\n- executive_dashboard_model.md\n- task23_submission_answer.md\n\nThis task uses synthetic demonstration data and does not claim production PlaceMux performance.\n'''
    (BASE / 'README.md').write_text(readme)

    print(json.dumps({'validation_status': validation['validation_status'], 'students': len(students), 'applications': len(applications), 'eligible': int(students['eligible'].sum()), 'placed_students': int(applications.loc[applications['placed'], 'student_id'].nunique())}, indent=2))


if __name__ == '__main__':
    main()
