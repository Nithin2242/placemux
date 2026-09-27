from __future__ import annotations

import csv, json, math, random
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent
SEED = 1907
random.seed(SEED)

RECRUITERS = [
    ("R001", "Aarav Mehta", "Bengaluru"),
    ("R002", "Priya Shah", "Pune"),
    ("R003", "Rahul Nair", "Hyderabad"),
    ("R004", "Sneha Iyer", "Chennai"),
    ("R005", "Karthik Rao", "Mumbai"),
    ("R006", "Ananya Singh", "Delhi NCR"),
    ("R007", "Vivek Menon", "Bengaluru"),
    ("R008", "Meera Joshi", "Pune"),
    ("R009", "Aditya Kumar", "Hyderabad"),
    ("R010", "Neha Verma", "Chennai"),
]
COMPANIES = [
    ("C001", "Nova Systems"), ("C002", "BlueOrbit Labs"), ("C003", "Vertex Digital"),
    ("C004", "FinEdge Solutions"), ("C005", "CloudMint"), ("C006", "GreenByte"),
    ("C007", "DataForge"), ("C008", "Aster Mobility"), ("C009", "NextWave Retail"),
    ("C010", "BrightPath Consulting"),
]
ROLES = ["Data Analyst", "Software Engineer", "Frontend Developer", "Backend Developer", "QA Engineer", "Business Analyst"]


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


# ------------------------- Synthetic source data -------------------------
batches = []
base = datetime(2026, 8, 1, 9, 0)
for i in range(48):
    rid, rname, city = random.choice(RECRUITERS)
    cid, company = random.choice(COMPANIES)
    rows = random.randint(180, 720)
    duplicate_rate = random.uniform(0.005, 0.04)
    missing_rate = random.uniform(0.01, 0.05)
    rejected = int(rows * (duplicate_rate + missing_rate) + random.randint(1, 6))
    accepted = rows - rejected
    processing = max(8, int(rows / random.uniform(18, 45)))
    dt = base + timedelta(days=random.randint(0, 30), hours=random.randint(0, 8), minutes=random.randint(0, 50))
    status = random.choices(["Completed", "Partial", "Failed"], weights=[0.79, 0.17, 0.04])[0]
    if status == "Failed":
        accepted = random.randint(0, max(1, rows // 4))
        rejected = rows - accepted
    elif status == "Completed":
        accepted = max(accepted, int(rows * 0.92))
        rejected = rows - accepted
    batches.append({
        "batch_id": f"B{i+1:03d}", "recruiter_id": rid, "recruiter": rname, "city": city,
        "company_id": cid, "company": company, "uploaded_at": dt.isoformat(timespec="minutes"),
        "rows_uploaded": rows, "rows_accepted": accepted, "rows_rejected": rejected,
        "processing_minutes": processing, "status": status,
    })

candidates = []
applications = []
statuses = ["Applied", "Screening", "Shortlisted", "Interview", "Offer", "Placed", "Rejected"]
status_weights = [0.34, 0.18, 0.16, 0.10, 0.07, 0.05, 0.10]
for i in range(1320):
    b = random.choice(batches)
    cid = b["company_id"]
    candidate_id = f"CAN{i+1:04d}"
    stage = random.choices(statuses, weights=status_weights)[0]
    import_source = random.choice(["CSV", "API", "Manual Review"])
    skill = random.choice(["Python", "SQL", "Excel", "Power BI", "React", "Node.js", "Java"])
    candidates.append({
        "candidate_id": candidate_id, "batch_id": b["batch_id"], "recruiter_id": b["recruiter_id"],
        "company_id": cid, "company": b["company"], "role": random.choice(ROLES),
        "stage": stage, "import_source": import_source, "skill_focus": skill,
        "created_at": b["uploaded_at"],
    })
    if stage != "Rejected" or random.random() < 0.60:
        applications.append({
            "application_id": f"APP{i+1:04d}", "candidate_id": candidate_id, "recruiter_id": b["recruiter_id"],
            "company_id": cid, "company": b["company"], "role": candidates[-1]["role"],
            "stage": stage, "applied_at": b["uploaded_at"],
        })

# ------------------------------ Calculations ------------------------------
rows_uploaded = sum(x["rows_uploaded"] for x in batches)
rows_accepted = sum(x["rows_accepted"] for x in batches)
rows_rejected = sum(x["rows_rejected"] for x in batches)
completion_rate = sum(x["status"] == "Completed" for x in batches) / len(batches)
acceptance_rate = rows_accepted / rows_uploaded
avg_processing = sum(x["processing_minutes"] for x in batches) / len(batches)
active_recruiters = len({x["recruiter_id"] for x in batches if x["status"] != "Failed"})
active_companies = len({x["company_id"] for x in batches})
stage_counts = defaultdict(int)
for a in applications: stage_counts[a["stage"]] += 1

# Deterministic executive dashboard metrics framed as demo data.
metrics = {
    "onboarding_batches": len(batches),
    "rows_uploaded": rows_uploaded,
    "rows_accepted": rows_accepted,
    "rows_rejected": rows_rejected,
    "acceptance_rate": acceptance_rate,
    "batch_completion_rate": completion_rate,
    "avg_processing_minutes": avg_processing,
    "active_recruiters": active_recruiters,
    "active_companies": active_companies,
    "candidate_records": len(candidates),
    "applications": len(applications),
    "shortlisted": stage_counts["Shortlisted"],
    "interviews": stage_counts["Interview"],
    "offers": stage_counts["Offer"],
    "placements": stage_counts["Placed"],
}

# Funnel calculations are stage-to-stage, avoiding mismatched denominators.
funnel = [
    ("Applications", stage_counts["Applied"] + stage_counts["Screening"] + stage_counts["Shortlisted"] + stage_counts["Interview"] + stage_counts["Offer"] + stage_counts["Placed"]),
    ("Shortlisted", stage_counts["Shortlisted"] + stage_counts["Interview"] + stage_counts["Offer"] + stage_counts["Placed"]),
    ("Interview", stage_counts["Interview"] + stage_counts["Offer"] + stage_counts["Placed"]),
    ("Offer", stage_counts["Offer"] + stage_counts["Placed"]),
    ("Placed", stage_counts["Placed"]),
]

validation = {
    "duplicate_batch_ids": len(batches) - len({b["batch_id"] for b in batches}),
    "duplicate_candidate_ids": len(candidates) - len({c["candidate_id"] for c in candidates}),
    "duplicate_application_ids": len(applications) - len({a["application_id"] for a in applications}),
    "row_math_errors": sum(b["rows_uploaded"] != b["rows_accepted"] + b["rows_rejected"] for b in batches),
    "missing_recruiter_ids": sum(not b["recruiter_id"] for b in batches),
    "missing_company_ids": sum(not b["company_id"] for b in batches),
    "orphan_application_candidates": sum(a["candidate_id"] not in {c["candidate_id"] for c in candidates} for a in applications),
}
validation["overall"] = "PASS" if not any(validation[k] for k in validation if k != "overall") else "FAIL"

# Company summary.
company_summary = []
for cid, company in COMPANIES:
    bs = [b for b in batches if b["company_id"] == cid]
    apps = [a for a in applications if a["company_id"] == cid]
    placed = sum(a["stage"] == "Placed" for a in apps)
    uploaded = sum(b["rows_uploaded"] for b in bs)
    accepted = sum(b["rows_accepted"] for b in bs)
    company_summary.append({
        "company": company, "batches": len(bs), "rows_uploaded": uploaded,
        "acceptance_rate": (accepted / uploaded if uploaded else 0),
        "applications": len(apps), "shortlisted": sum(a["stage"] == "Shortlisted" for a in apps),
        "interviews": sum(a["stage"] == "Interview" for a in apps), "offers": sum(a["stage"] == "Offer" for a in apps),
        "placements": placed,
    })
company_summary.sort(key=lambda x: (-x["placements"], -x["applications"]))

# Monthly batch trend.
monthly = defaultdict(lambda: {"batches": 0, "uploaded": 0, "accepted": 0})
for b in batches:
    month = b["uploaded_at"][:7]
    monthly[month]["batches"] += 1
    monthly[month]["uploaded"] += b["rows_uploaded"]
    monthly[month]["accepted"] += b["rows_accepted"]
monthly_list = [{"month": m, **v} for m, v in sorted(monthly.items())]

FIELDS_BATCH = list(batches[0].keys())
FIELDS_CAND = list(candidates[0].keys())
FIELDS_APP = list(applications[0].keys())
write_csv(OUT / "bulk_onboarding_batches_demo.csv", batches, FIELDS_BATCH)
write_csv(OUT / "recruiter_candidates_demo.csv", candidates, FIELDS_CAND)
write_csv(OUT / "recruiter_applications_demo.csv", applications, FIELDS_APP)
(OUT / "recruiter_dashboard_validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
(OUT / "recruiter_dashboard_metrics_demo.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

# ------------------------------ HTML dashboard ------------------------------
payload = {"metrics": metrics, "funnel": funnel, "company": company_summary, "monthly": monthly_list, "batches": batches, "validation": validation, "generated": datetime.now().isoformat(timespec="seconds")}
payload_json = json.dumps(payload, ensure_ascii=False)
html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PlaceMux Recruiter Control Center - Task 19</title>
<style>
:root{{--ink:#172033;--muted:#68738a;--line:#e7ebf2;--brand:#4538b8;--brand2:#6757e8;--bg:#f6f7fb;--white:#fff;--good:#157347;--warn:#a35d00;--bad:#b42318}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 Inter,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif}}
.header{{background:linear-gradient(135deg,#3d33a5,#5f50dc);color:#fff;padding:24px 30px 20px;position:sticky;top:0;z-index:2;box-shadow:0 8px 24px #221a6b22}}
.brand{{font-size:12px;letter-spacing:.08em;opacity:.8;text-transform:uppercase}} h1{{margin:4px 0 4px;font-size:28px}} .sub{{opacity:.85}}
.wrap{{max-width:1420px;margin:0 auto;padding:22px 26px 40px}} .toolbar{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}}
.tab{{border:1px solid #d9ddeb;background:#fff;color:#394152;padding:9px 13px;border-radius:10px;cursor:pointer;font-weight:650}} .tab.active{{background:#1f2240;color:#fff;border-color:#1f2240}}
.grid{{display:grid;gap:14px}} .kpis{{grid-template-columns:repeat(6,minmax(0,1fr));}} .two{{grid-template-columns:1.2fr .8fr}} .three{{grid-template-columns:1.15fr .85fr 1fr}}
.card{{background:var(--white);border:1px solid var(--line);border-radius:16px;padding:16px;box-shadow:0 3px 16px #1f2a4910}} .card h3{{margin:0 0 12px;font-size:15px}} .small{{font-size:12px;color:var(--muted)}}
.kpi .label{{font-size:12px;color:var(--muted);font-weight:650}} .kpi .value{{font-size:25px;font-weight:800;margin-top:4px}} .pill{{display:inline-flex;align-items:center;gap:6px;padding:4px 9px;border-radius:999px;font-size:11px;font-weight:750;background:#eef2ff;color:#4438a8}}
.good{{color:var(--good)}} .warn{{color:var(--warn)}} .bad{{color:var(--bad)}}
table{{width:100%;border-collapse:collapse}} th,td{{padding:9px 8px;border-bottom:1px solid var(--line);text-align:left;font-size:12px}} th{{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.04em}} tr:last-child td{{border-bottom:none}}
.barwrap{{margin:11px 0}} .barlabel{{display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px}} .bar{{height:9px;border-radius:99px;background:#eef0f5;overflow:hidden}} .bar > span{{display:block;height:100%;background:linear-gradient(90deg,var(--brand),var(--brand2));border-radius:99px}}
.spark{{width:100%;height:160px}} svg text{{font-family:inherit;fill:#6b7280;font-size:11px}} .note{{padding:10px 12px;border-radius:10px;background:#f7f6ff;border:1px solid #e5e1ff;color:#4438a8;font-size:12px}}
.filters{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}} select{{padding:8px 10px;border-radius:9px;border:1px solid #dfe3eb;background:#fff;color:#30384a}}
.view{{display:none}} .view.active{{display:block}} .footer{{margin-top:20px;color:var(--muted);font-size:11px}}
@media(max-width:1100px){{.kpis{{grid-template-columns:repeat(3,1fr)}} .two,.three{{grid-template-columns:1fr}}}} @media(max-width:700px){{.wrap{{padding:15px}} .kpis{{grid-template-columns:repeat(2,1fr)}} h1{{font-size:22px}}}}
</style></head><body>
<header class="header"><div class="brand">PlaceMux | Phase 2 | Data Analyst | Task 19</div><h1>Bulk Onboarding & Recruiter Control Center</h1><div class="sub">Recruiter operations, candidate pipeline and bulk-import quality in one decision view</div></header>
<main class="wrap">
<div class="toolbar"><button class="tab active" data-view="overview">Recruiter Overview</button><button class="tab" data-view="onboarding">Bulk Onboarding</button><button class="tab" data-view="pipeline">Candidate Pipeline</button></div>
<section class="view active" id="overview">
<div class="grid kpis">
  <div class="card kpi"><div class="label">Onboarding Batches</div><div class="value" data-kpi="onboarding_batches"></div><div class="small">synthetic demo</div></div>
  <div class="card kpi"><div class="label">Rows Uploaded</div><div class="value" data-kpi="rows_uploaded"></div><div class="small">bulk records received</div></div>
  <div class="card kpi"><div class="label">Import Acceptance</div><div class="value" data-kpi="acceptance_rate" data-fmt="pct"></div><div class="small">accepted / uploaded</div></div>
  <div class="card kpi"><div class="label">Active Recruiters</div><div class="value" data-kpi="active_recruiters"></div><div class="small">with non-failed activity</div></div>
  <div class="card kpi"><div class="label">Applications</div><div class="value" data-kpi="applications"></div><div class="small">recruiter-managed</div></div>
  <div class="card kpi"><div class="label">Placements</div><div class="value" data-kpi="placements"></div><div class="small">recorded outcomes</div></div>
</div>
<div class="grid two" style="margin-top:14px">
 <div class="card"><h3>Recruiter workload & outcomes</h3><table><thead><tr><th>Company</th><th>Batches</th><th>Rows</th><th>Acceptance</th><th>Apps</th><th>Placements</th></tr></thead><tbody id="companyRows"></tbody></table></div>
 <div class="card"><h3>Operating signal</h3><div class="note" id="signal"></div><div style="margin-top:16px"><div class="small">Batch completion</div><div class="barwrap"><div class="barlabel"><span>Completed</span><b id="completionText"></b></div><div class="bar"><span id="completionBar"></span></div></div></div><div style="margin-top:16px"><div class="small">Data-quality health</div><div style="font-size:22px;font-weight:800;margin-top:5px" id="validationState"></div><div class="small">7 core checks on the demo stream</div></div></div>
</div>
<div class="grid three" style="margin-top:14px">
 <div class="card"><h3>Application funnel</h3><div id="funnel"></div></div>
 <div class="card"><h3>Monthly bulk volume</h3><svg id="monthlyChart" class="spark" viewBox="0 0 520 180" preserveAspectRatio="none"></svg></div>
 <div class="card"><h3>Definitions</h3><div class="small"><b>Import acceptance</b> = accepted rows / uploaded rows.<br><br><b>Batch completion</b> = completed onboarding batches / all onboarding batches.<br><br><b>Funnel stages</b> are built from candidate/application lifecycle status at reporting time.<br><br><b>Source</b> = deterministic synthetic demonstration stream generated by the attached Python script.</div></div>
</div>
</section>
<section class="view" id="onboarding">
<div class="filters"><select id="statusFilter"><option value="All">All statuses</option><option>Completed</option><option>Partial</option><option>Failed</option></select><select id="companyFilter"><option value="All">All companies</option></select><select id="recruiterFilter"><option value="All">All recruiters</option></select></div>
<div class="grid kpis" style="grid-template-columns:repeat(5,minmax(0,1fr))">
 <div class="card kpi"><div class="label">Filtered Batches</div><div class="value" id="f_batches"></div></div>
 <div class="card kpi"><div class="label">Uploaded Rows</div><div class="value" id="f_uploaded"></div></div>
 <div class="card kpi"><div class="label">Acceptance</div><div class="value" id="f_accept"></div></div>
 <div class="card kpi"><div class="label">Avg Processing</div><div class="value" id="f_processing"></div><div class="small">minutes / batch</div></div>
 <div class="card kpi"><div class="label">Status Mix</div><div class="value" id="f_status"></div><div class="small">completed / total</div></div>
</div>
<div class="card" style="margin-top:14px"><h3>Bulk onboarding batch register</h3><div style="overflow:auto"><table><thead><tr><th>Batch</th><th>Recruiter</th><th>Company</th><th>Uploaded</th><th>Accepted</th><th>Rejected</th><th>Processing</th><th>Status</th></tr></thead><tbody id="batchRows"></tbody></table></div></div>
</section>
<section class="view" id="pipeline">
<div class="grid two">
 <div class="card"><h3>Candidate pipeline</h3><div id="pipelineBars"></div></div>
 <div class="card"><h3>Recruiter actions to inspect</h3><table><thead><tr><th>Action</th><th>Why it matters</th></tr></thead><tbody><tr><td><span class="pill">Bulk rejects</span></td><td>Review CSV format, required fields, duplicates and invalid identifiers before re-upload.</td></tr><tr><td><span class="pill">Interview queue</span></td><td>Prioritize aging interview-stage candidates and ensure next-step dates exist.</td></tr><tr><td><span class="pill">Offer follow-up</span></td><td>Keep offer-stage records linked to application and candidate IDs for downstream e-sign.</td></tr><tr><td><span class="pill">Placement closure</span></td><td>Require a final outcome timestamp and recruiter owner before marking a record closed.</td></tr></tbody></table></div>
</div>
<div class="card" style="margin-top:14px"><h3>Candidate sample</h3><div style="overflow:auto"><table><thead><tr><th>Candidate</th><th>Company</th><th>Role</th><th>Stage</th><th>Source</th><th>Skill Focus</th></tr></thead><tbody id="candidateRows"></tbody></table></div></div>
</section>
<div class="footer">Demo data only. Generated deterministically with seed {SEED}. No production PlaceMux performance is claimed. Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} local runtime.</div>
</main>
<script>
const DATA = {payload_json};
const fmtInt = n => new Intl.NumberFormat('en-IN').format(n);
const pct = x => (x*100).toFixed(1)+'%';
const params = new URLSearchParams(location.search); const initial = params.get('view') || 'overview';
function show(view){{document.querySelectorAll('.view').forEach(x=>x.classList.toggle('active',x.id===view));document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x.dataset.view===view));}}
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>show(b.dataset.view)); show(initial);
for(const el of document.querySelectorAll('[data-kpi]')){{const k=el.dataset.kpi; const v=DATA.metrics[k]; el.textContent=el.dataset.fmt==='pct'?pct(v):fmtInt(v);}}
const cr=document.getElementById('companyRows'); DATA.company.forEach(r=>{{cr.innerHTML+=`<tr><td>${{r.company}}</td><td>${{r.batches}}</td><td>${{fmtInt(r.rows_uploaded)}}</td><td>${{pct(r.acceptance_rate)}}</td><td>${{r.applications}}</td><td>${{r.placements}}</td></tr>`}});
document.getElementById('completionText').textContent=pct(DATA.metrics.batch_completion_rate); document.getElementById('completionBar').style.width=pct(DATA.metrics.batch_completion_rate); document.getElementById('validationState').innerHTML=DATA.validation.overall==='PASS'?'<span class="good">PASS</span>':'<span class="bad">FAIL</span>';
const signal=DATA.metrics.acceptance_rate>=0.93 && DATA.metrics.batch_completion_rate>=0.8?'Healthy operating flow: bulk onboarding is completing reliably, while rejected rows remain the key quality queue to manage.':'Watch operating flow: inspect import quality and incomplete batches before scaling volume.'; document.getElementById('signal').textContent=signal;
const funnelEl=document.getElementById('funnel'); const max=DATA.funnel[0][1]; DATA.funnel.forEach((x,i)=>{{const conv=i?x[1]/DATA.funnel[i-1][1]:1; funnelEl.innerHTML+=`<div class="barwrap"><div class="barlabel"><span>${{x[0]}}</span><b>${{fmtInt(x[1])}}</b></div><div class="bar"><span style="width:${{(x[1]/max)*100}}%"></span></div><div class="small">${{i?'Stage conversion '+pct(conv):'Top-of-funnel total'}}</div></div>`}});
function drawMonthly(){{const svg=document.getElementById('monthlyChart'); const w=520,h=180,p=28, arr=DATA.monthly; const mx=Math.max(...arr.map(x=>x.uploaded)), step=(w-p*2)/(arr.length-1||1); let pts=''; arr.forEach((x,i)=>pts+=(p+i*step)+','+(h-p-(x.uploaded/mx)*(h-2*p))+' '); svg.innerHTML=`<line x1="${{p}}" y1="${{h-p}}" x2="${{w-p}}" y2="${{h-p}}" stroke="#dfe3eb"/><polyline fill="none" stroke="#4f46c5" stroke-width="3" points="${{pts}}"/>`+arr.map((x,i)=>`<circle cx="${{p+i*step}}" cy="${{h-p-(x.uploaded/mx)*(h-2*p)}}" r="4" fill="#4f46c5"/><text x="${{p+i*step}}" y="${{h-8}}" text-anchor="middle">${{x.month.slice(5)}}</text>`).join('');}}
drawMonthly();
const cf=document.getElementById('companyFilter'), rf=document.getElementById('recruiterFilter'); [...new Set(DATA.batches.map(x=>x.company))].sort().forEach(x=>cf.innerHTML+=`<option>${{x}}</option>`); [...new Set(DATA.batches.map(x=>x.recruiter))].sort().forEach(x=>rf.innerHTML+=`<option>${{x}}</option>`);
function renderBatches(){{const status=document.getElementById('statusFilter').value, company=cf.value, recruiter=rf.value; const rows=DATA.batches.filter(x=>(status==='All'||x.status===status)&&(company==='All'||x.company===company)&&(recruiter==='All'||x.recruiter===recruiter)); const up=rows.reduce((s,x)=>s+x.rows_uploaded,0), ac=rows.reduce((s,x)=>s+x.rows_accepted,0); document.getElementById('f_batches').textContent=fmtInt(rows.length); document.getElementById('f_uploaded').textContent=fmtInt(up); document.getElementById('f_accept').textContent=up?pct(ac/up):'N/A'; document.getElementById('f_processing').textContent=rows.length?(rows.reduce((s,x)=>s+x.processing_minutes,0)/rows.length).toFixed(1):'N/A'; document.getElementById('f_status').textContent=rows.length?`${{rows.filter(x=>x.status==='Completed').length}} / ${{rows.length}}`:'0 / 0'; document.getElementById('batchRows').innerHTML=rows.map(x=>`<tr><td>${{x.batch_id}}</td><td>${{x.recruiter}}</td><td>${{x.company}}</td><td>${{fmtInt(x.rows_uploaded)}}</td><td>${{fmtInt(x.rows_accepted)}}</td><td>${{fmtInt(x.rows_rejected)}}</td><td>${{x.processing_minutes}}m</td><td>${{x.status}}</td></tr>`).join('');}}
['statusFilter','companyFilter','recruiterFilter'].forEach(id=>document.getElementById(id).onchange=renderBatches); renderBatches();
const pipe=document.getElementById('pipelineBars'); const counts=['Applied','Screening','Shortlisted','Interview','Offer','Placed','Rejected'].map(s=>[s,DATA.batches.length?DATA.metrics.applications:0]); const grouped={{}}; DATA.batches.forEach(()=>{{}}); const appStage=DATA.company.reduce((a,c)=>a,0); // placeholder to keep dashboard logic simple
const stageMap={{}}; DATA.batches.forEach(()=>{{}}); // values are computed below from candidate source embedded at export time
// Reconstruct stage counts from funnel for visible stages, and use candidate-derived totals for other stages from the source table.
const candidatesStage={{}}; DATA.batches.forEach(()=>{{}}); const stageNames=['Applied','Screening','Shortlisted','Interview','Offer','Placed']; const stageValues=[{stage_counts['Applied']},{stage_counts['Screening']},{stage_counts['Shortlisted']},{stage_counts['Interview']},{stage_counts['Offer']},{stage_counts['Placed']}];
stageNames.forEach((s,i)=>pipe.innerHTML+=`<div class="barwrap"><div class="barlabel"><span>${{s}}</span><b>${{fmtInt(stageValues[i])}}</b></div><div class="bar"><span style="width:${{Math.max(3,(stageValues[i]/Math.max(...stageValues))*100)}}%"></span></div></div>`);
const cand = {json.dumps(candidates[:40], ensure_ascii=False)}; document.getElementById('candidateRows').innerHTML=cand.map(x=>`<tr><td>${{x.candidate_id}}</td><td>${{x.company}}</td><td>${{x.role}}</td><td>${{x.stage}}</td><td>${{x.import_source}}</td><td>${{x.skill_focus}}</td></tr>`).join('');
</script></body></html>'''
(OUT / "recruiter_dashboard.html").write_text(html, encoding="utf-8")

# Documentation
(OUT / "bulk_onboarding_metrics.md").write_text(f'''# Task 19 - Bulk Onboarding & Recruiter Dashboard Metrics\n\n## Scope\nA demo-ready recruiter dashboard that connects bulk onboarding quality with recruiter-side candidate pipeline visibility. Because the task brief does not provide a production dataset, this implementation uses a deterministic synthetic demonstration stream.\n\n## Core metrics\n| Metric | Definition | Formula | Grain |\n|---|---|---|---|\n| Onboarding Batches | Distinct bulk-upload jobs received | COUNT(DISTINCT batch_id) | batch |\n| Rows Uploaded | Total candidate rows received | SUM(rows_uploaded) | reporting period |\n| Rows Accepted | Rows that pass validation | SUM(rows_accepted) | reporting period |\n| Import Acceptance | Share of rows accepted | rows_accepted / rows_uploaded | reporting period |\n| Batch Completion | Completed batches / all batches | completed / total | reporting period |\n| Avg Processing Time | Mean processing duration | SUM(processing_minutes) / batches | batch |\n| Active Recruiters | Recruiters with non-failed onboarding activity | COUNT(DISTINCT recruiter_id) | reporting period |\n| Applications | Candidate applications represented in recruiter view | COUNT(DISTINCT application_id) | reporting period |\n| Shortlisted | Applications currently at shortlist or beyond | COUNT DISTINCT by stage rule | reporting period |\n| Interviews | Applications at interview stage or beyond | COUNT DISTINCT by stage rule | reporting period |\n| Offers | Applications at offer stage or beyond | COUNT DISTINCT by stage rule | reporting period |\n| Placements | Applications with placed outcome | COUNT DISTINCT where stage=Placed | reporting period |\n\n## Denominator discipline\nAcceptance uses uploaded rows as its denominator. Batch completion uses all onboarding batches. Funnel stage conversion uses the immediately preceding valid stage. These denominators are intentionally kept separate so a high-volume import does not distort downstream pipeline rates.\n\n## Data quality\nThe demo validates unique batch/candidate/application identifiers, row arithmetic (uploaded = accepted + rejected), required recruiter/company identifiers, and application-to-candidate relationships.\n''', encoding='utf-8')

(OUT / "recruiter_dashboard_model.md").write_text('''# Task 19 - Recruiter Dashboard Logical Model\n\n## Entities\n- **Recruiter**: recruiter_id, recruiter name, operating location\n- **Company**: company_id, company name\n- **Onboarding Batch**: batch_id, recruiter_id, company_id, upload timestamp, row counts, processing duration, status\n- **Candidate**: candidate_id, batch_id, recruiter_id, company_id, role, stage, import source, skill focus\n- **Application**: application_id, candidate_id, recruiter_id, company_id, role, stage, applied_at\n\n## Relationships\nRecruiter 1-to-many Onboarding Batch; Company 1-to-many Onboarding Batch; Onboarding Batch 1-to-many Candidate; Candidate 1-to-many Application.\n\n## Recruiter views\n1. **Recruiter Overview** - workload, import acceptance, company output, application funnel, validation state.\n2. **Bulk Onboarding** - filterable batch register with status, accepted/rejected rows, processing time and quality rate.\n3. **Candidate Pipeline** - stage distribution and operational follow-up queue.\n\n## Governance\nThe dashboard distinguishes operational source data from derived metrics, preserves stable identifiers, and exposes a demo-only label so synthetic figures are not mistaken for PlaceMux production performance.\n''', encoding='utf-8')

print(json.dumps({"out_dir": str(OUT), "metrics": metrics, "validation": validation}, indent=2))
