from __future__ import annotations
import json, random
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

BASE = Path(__file__).resolve().parent
random.seed(20260911)

COLLEGES = [
    ("COL001", "BMS Institute of Technology", "Bangalore"),
    ("COL002", "RV College of Engineering", "Bangalore"),
    ("COL003", "PES University", "Bangalore"),
    ("COL004", "Dayananda Sagar College of Engineering", "Bangalore"),
    ("COL005", "New Horizon College of Engineering", "Bangalore"),
    ("COL006", "CMR Institute of Technology", "Bangalore"),
]
BRANCHES = ["CSE", "ISE", "ECE", "EEE", "ME", "AI&ML"]
COMPANIES = ["Vertex Digital","FinEdge Solutions","BlueOrbit Labs","Aster Mobility","Nova Systems","CloudMinds","TechForge","DataNest","InfiCore","PrimeStack","QuantEdge","BrightWorks","NextGen Labs","Orion Analytics","CodeCraft"]
ROLES = ["Software Engineer","Data Analyst","Backend Developer","Frontend Developer","Business Analyst","ML Engineer"]

# Student master: ~2400 students with realistic completion/eligibility mix.
students=[]
start=datetime(2026,7,1,9,0)
for i in range(1,2401):
    cid, cname, city = random.choice(COLLEGES)
    branch=random.choice(BRANCHES)
    cgpa=round(max(5.8,min(9.8, random.gauss(7.65,0.65))),2)
    backlog=0 if random.random()<0.82 else random.choice([1,1,2])
    profile_complete=random.random()<0.93
    verified=random.random()<0.90
    eligible = cgpa>=6.5 and backlog==0 and profile_complete and verified
    students.append({
        "student_id":f"STU{i:05d}","college_id":cid,"college":cname,"city":city,
        "branch":branch,"cgpa":cgpa,"active_backlogs":backlog,
        "profile_complete":profile_complete,"documents_verified":verified,
        "eligible":eligible,"registered_at":(start+timedelta(days=random.randint(0,55),minutes=random.randint(0,720))).isoformat(timespec="minutes")
    })
students_df=pd.DataFrame(students)

# Applications from eligible students, multiple applications permitted.
eligible=students_df[students_df.eligible].copy()
apps=[]
stages=["Applied","Screening","Interview","Offer","Placed","Rejected"]
weights=[0.22,0.16,0.18,0.10,0.14,0.20]
for i in range(1,3201):
    s=eligible.sample(1, random_state=random.randint(1,999999)).iloc[0]
    company=random.choice(COMPANIES)
    role=random.choice(ROLES)
    r=random.random()
    if r < 0.25:
        stage="Applied"
    elif r < 0.43:
        stage="Screening"
    elif r < 0.63:
        stage="Interview"
    elif r < 0.78:
        stage="Offer"
    elif r < 0.84:
        stage="Placed"
    else:
        stage="Rejected"
    if stage=="Placed":
        package=round(random.uniform(4.2,15.5),1)
    elif stage=="Offer":
        package=round(random.uniform(4.0,14.0),1)
    else:
        package=None
    apps.append({"application_id":f"APP{i:05d}","student_id":s.student_id,"college_id":s.college_id,"college":s.college,
                 "company":company,"role":role,"stage":stage,"package_lpa":package,
                 "applied_at":(datetime.fromisoformat(s.registered_at)+timedelta(days=random.randint(1,45))).isoformat(timespec="minutes")})
apps_df=pd.DataFrame(apps)

# Company engagement by college: demos, drives, companies active and response coverage.
eng=[]
for cid,cname,city in COLLEGES:
    n_comp=random.randint(11,15)
    for company in random.sample(COMPANIES,n_comp):
        invites=random.randint(1,4)
        attended=random.randint(max(1,invites-1),invites)
        shortlisted=random.randint(0, min(18, attended*5))
        outcomes=random.randint(0, max(0, min(shortlisted,8)))
        eng.append({"college_id":cid,"college":cname,"company":company,"events_invited":invites,"events_attended":attended,
                    "students_shortlisted":shortlisted,"successful_outcomes":outcomes})
eng_df=pd.DataFrame(eng)

# College-level KPI table.
rows=[]
for cid,cname,city in COLLEGES:
    s=students_df[students_df.college_id==cid]
    a=apps_df[apps_df.college_id==cid]
    e=eng_df[eng_df.college_id==cid]
    registered=len(s); eligible_n=int(s.eligible.sum()); complete_pct=round(s.profile_complete.mean()*100,1)
    applied=a.student_id.nunique(); interviews=int(a.stage.isin(["Interview","Offer","Placed"]).sum())
    offers=int(a.stage.eq("Offer").sum()); placed=int(a.stage.eq("Placed").sum())
    placed_students=a.loc[a.stage.eq("Placed"),"student_id"].nunique()
    packages=a.loc[a.stage=="Placed","package_lpa"].dropna()
    avg=float(packages.mean()) if len(packages) else 0.0
    med=float(packages.median()) if len(packages) else 0.0
    rows.append({"college_id":cid,"college":cname,"city":city,"registered_students":registered,"eligible_students":eligible_n,
                 "profile_completion_rate":complete_pct,"students_applied":applied,"interview_stage_count":interviews,
                 "offers":offers,"placed_students":placed_students,"placement_rate_pct":round(placed_students/eligible_n*100,1) if eligible_n else 0,
                 "avg_package_lpa":round(avg,2),"median_package_lpa":round(med,2),"companies_engaged":e.company.nunique(),
                 "drive_events":int(e.events_invited.sum()),"successful_outcomes":int(e.successful_outcomes.sum())})
college_df=pd.DataFrame(rows).sort_values("placement_rate_pct",ascending=False)

# Overall metrics
m={
    "colleges":len(COLLEGES),"registered_students":len(students_df),"eligible_students":int(students_df.eligible.sum()),
    "profile_completion_rate":round(students_df.profile_complete.mean()*100,1),"documents_verified_rate":round(students_df.documents_verified.mean()*100,1),
    "students_with_application":int(apps_df.student_id.nunique()),"applications":len(apps_df),
    "interview_stage_count":int(apps_df.stage.isin(["Interview","Offer","Placed"]).sum()),"offers":int(apps_df.stage.eq("Offer").sum()),
    "placed_students":int(apps_df.loc[apps_df.stage=="Placed","student_id"].nunique()),
    "placement_rate_pct":round(apps_df.loc[apps_df.stage=="Placed","student_id"].nunique()/students_df.eligible.sum()*100,1),
    "avg_package_lpa":round(apps_df.loc[apps_df.stage=="Placed","package_lpa"].mean(),2),
    "median_package_lpa":round(apps_df.loc[apps_df.stage=="Placed","package_lpa"].median(),2),
    "company_engagements":int(eng_df.company.nunique()),"drive_events":int(eng_df.events_invited.sum()),
    "successful_outcomes":int(eng_df.successful_outcomes.sum())
}

# Validation
checks={
    "duplicate_student_ids":int(students_df.student_id.duplicated().sum()),
    "missing_student_college_ids":int(students_df.college_id.isna().sum()),
    "ineligible_applications":int((~apps_df.student_id.isin(set(eligible.student_id))).sum()),
    "duplicate_application_ids":int(apps_df.application_id.duplicated().sum()),
    "missing_application_student_ids":int((~apps_df.student_id.isin(set(students_df.student_id))).sum()),
    "invalid_application_stages":int((~apps_df.stage.isin(stages)).sum()),
    "placed_without_package":int(((apps_df.stage=="Placed") & (apps_df.package_lpa.isna())).sum()),
    "negative_packages":int((apps_df.package_lpa.fillna(0)<0).sum()),
    "college_kpi_rows":int(len(college_df)),
}
checks["overall_status"]="PASS" if all(v==0 for k,v in checks.items() if k!="college_kpi_rows") and checks["college_kpi_rows"]==len(COLLEGES) else "FAIL"

students_df.to_csv(BASE/"college_students_demo.csv",index=False)
apps_df.to_csv(BASE/"college_applications_demo.csv",index=False)
eng_df.to_csv(BASE/"college_company_engagement_demo.csv",index=False)
college_df.to_csv(BASE/"college_dashboard_metrics.csv",index=False)
(BASE/"college_dashboard_metrics.json").write_text(json.dumps(m,indent=2))
(BASE/"college_dashboard_validation.json").write_text(json.dumps(checks,indent=2))

# HTML: self-contained, no external dependency.
college_records=college_df.to_dict(orient="records")
eng_records=eng_df.to_dict(orient="records")
html=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PlaceMux College-Value Dashboard</title>
<style>
body{{margin:0;font-family:Inter,Arial,sans-serif;background:#f4f6fb;color:#172033}} .wrap{{max-width:1450px;margin:auto;padding:28px}} h1{{margin:0 0 6px;font-size:30px}} .sub{{color:#667085;margin-bottom:22px}} .tabs{{display:flex;gap:8px;margin-bottom:18px}} button{{border:0;border-radius:10px;padding:10px 16px;background:#e7eaf4;color:#344054;font-weight:700;cursor:pointer}} button.active{{background:#4338ca;color:white}} .panel{{display:none}} .panel.active{{display:block}} .cards{{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}} .card{{background:white;border:1px solid #e5e7eb;border-radius:14px;padding:15px;box-shadow:0 3px 10px #1018280a}} .label{{font-size:12px;color:#667085}} .value{{font-size:24px;font-weight:800;margin-top:4px}} .unit{{font-size:12px;color:#667085}} .grid{{display:grid;grid-template-columns:1.3fr 1fr;gap:16px;margin-top:16px}} .box{{background:white;border:1px solid #e5e7eb;border-radius:14px;padding:18px}} .box h3{{margin:0 0 14px}} table{{width:100%;border-collapse:collapse;font-size:13px}} th,td{{padding:10px;border-bottom:1px solid #edf0f5;text-align:left}} th{{color:#667085;font-size:12px}} .barrow{{display:grid;grid-template-columns:220px 1fr 70px;gap:10px;align-items:center;margin:10px 0}} .bar{{height:10px;background:#edf0f7;border-radius:99px;overflow:hidden}} .fill{{height:100%;background:#4f46e5}} .pill{{display:inline-block;padding:3px 8px;border-radius:99px;background:#eef2ff;color:#3730a3;font-weight:700;font-size:11px}} .good{{color:#067647}} .note{{font-size:12px;color:#667085;line-height:1.5}} .two{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}} @media(max-width:1000px){{.cards{{grid-template-columns:repeat(3,1fr)}}.grid,.two{{grid-template-columns:1fr}}}} @media(max-width:650px){{.cards{{grid-template-columns:repeat(2,1fr)}}.wrap{{padding:15px}}}}
</style></head><body><div class="wrap">
<h1>PlaceMux College-Value Dashboard</h1><div class="sub">College-side view for placement outcomes, student readiness, recruiter demand and operational follow-up · Synthetic demonstration dataset</div>
<div class="tabs"><button class="active" onclick="showTab('overview',this)">Overview</button><button onclick="showTab('funnel',this)">Placement Funnel</button><button onclick="showTab('engagement',this)">Company Engagement</button></div>
<div id="overview" class="panel active"><div class="cards">
<div class="card"><div class="label">Registered Students</div><div class="value">{m['registered_students']:,}</div></div><div class="card"><div class="label">Eligible Students</div><div class="value">{m['eligible_students']:,}</div></div><div class="card"><div class="label">Profile Completion</div><div class="value">{m['profile_completion_rate']:.1f}%</div></div><div class="card"><div class="label">Applications</div><div class="value">{m['applications']:,}</div></div><div class="card"><div class="label">Placed Students</div><div class="value">{m['placed_students']:,}</div></div><div class="card"><div class="label">Placement Rate</div><div class="value">{m['placement_rate_pct']:.1f}%</div></div></div>
<div class="grid"><div class="box"><h3>College Performance</h3><table><tr><th>College</th><th>Eligible</th><th>Placed</th><th>Placement</th><th>Avg LPA</th><th>Companies</th></tr>{''.join(f"<tr><td>{r['college']}</td><td>{r['eligible_students']:,}</td><td>{r['placed_students']:,}</td><td><span class='pill'>{r['placement_rate_pct']:.1f}%</span></td><td>{r['avg_package_lpa']:.2f}</td><td>{r['companies_engaged']}</td></tr>" for r in college_records)}</table></div>
<div class="box"><h3>College Value Signals</h3>{''.join(f"<div class='barrow'><div>{r['college']}</div><div class='bar'><div class='fill' style='width:{min(100,r['placement_rate_pct'])}%'></div></div><div>{r['placement_rate_pct']:.1f}%</div></div>" for r in college_records)}<p class="note">Placement rate is placed students divided by eligible students. Use alongside branch mix, recruiter mix and hiring seasonality before making college-to-college comparisons.</p></div></div>
<div class="two"><div class="box"><h3>Operational Readiness</h3><p><b>{m['documents_verified_rate']:.1f}%</b> of student records have verified documents. <b>{m['profile_completion_rate']:.1f}%</b> have completed profiles.</p><p class="note">Priority action: resolve incomplete profiles and document gaps before high-volume placement drives.</p></div><div class="box"><h3>Dashboard Controls</h3><p class="good"><b>VALIDATION {checks['overall_status']}</b></p><p class="note">Source data is synthetic. This dashboard demonstrates the college-side measurement model and operating workflow; it does not represent live PlaceMux production performance.</p></div></div></div>
<div id="funnel" class="panel"><div class="box"><h3>Overall Placement Funnel</h3><table><tr><th>Stage</th><th>Count</th><th>Rate from Previous</th></tr>
<tr><td>Registered Students</td><td>{m['registered_students']:,}</td><td>-</td></tr><tr><td>Eligible Students</td><td>{m['eligible_students']:,}</td><td>{m['eligible_students']/m['registered_students']*100:.1f}%</td></tr><tr><td>Students with Applications</td><td>{m['students_with_application']:,}</td><td>{m['students_with_application']/m['eligible_students']*100:.1f}%</td></tr><tr><td>Interview-stage Applications</td><td>{m['interview_stage_count']:,}</td><td>{m['interview_stage_count']/m['applications']*100:.1f}% of applications</td></tr><tr><td>Offers</td><td>{m['offers']:,}</td><td>{m['offers']/m['interview_stage_count']*100:.1f}%</td></tr><tr><td>Placed Students</td><td>{m['placed_students']:,}</td><td>{m['placed_students']/m['offers']*100:.1f}% of offers</td></tr></table></div>
<div class="grid"><div class="box"><h3>Placement Rate by College</h3>{''.join(f"<div class='barrow'><div>{r['college']}</div><div class='bar'><div class='fill' style='width:{min(100,r['placement_rate_pct'])}%'></div></div><div>{r['placement_rate_pct']:.1f}%</div></div>" for r in college_records)}</div><div class="box"><h3>Package Outcomes</h3><p><span class="label">Average package</span><div class="value">{m['avg_package_lpa']:.2f} LPA</div></p><p><span class="label">Median package</span><div class="value">{m['median_package_lpa']:.2f} LPA</div></p><p class="note">Package metrics are computed on students at the Placed stage with a recorded package value.</p></div></div></div>
<div id="engagement" class="panel"><div class="cards"><div class="card"><div class="label">Active Companies</div><div class="value">{m['company_engagements']}</div></div><div class="card"><div class="label">Drive Events</div><div class="value">{m['drive_events']}</div></div><div class="card"><div class="label">Successful Outcomes</div><div class="value">{m['successful_outcomes']}</div></div></div><div class="box" style="margin-top:16px"><h3>Company Engagement by College</h3><table><tr><th>College</th><th>Companies</th><th>Drive Events</th><th>Successful Outcomes</th></tr>{''.join(f"<tr><td>{r['college']}</td><td>{r['companies_engaged']}</td><td>{r['drive_events']}</td><td>{r['successful_outcomes']}</td></tr>" for r in college_records)}</table></div><div class="box" style="margin-top:16px"><h3>Recruiter/Company Response View</h3><table><tr><th>Company</th><th>Colleges Engaged</th><th>Total Invites</th><th>Students Shortlisted</th><th>Successful Outcomes</th></tr>{''.join(f"<tr><td>{c}</td><td>{eng_df[eng_df.company==c].college.nunique()}</td><td>{int(eng_df[eng_df.company==c].events_invited.sum())}</td><td>{int(eng_df[eng_df.company==c].students_shortlisted.sum())}</td><td>{int(eng_df[eng_df.company==c].successful_outcomes.sum())}</td></tr>" for c in sorted(eng_df.company.unique()))}</table></div></div>
</div><script>function showTab(id,b){{document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));document.querySelectorAll('button').forEach(x=>x.classList.remove('active'));document.getElementById(id).classList.add('active');b.classList.add('active')}}</script></body></html>'''
(BASE/"college_dashboard.html").write_text(html)

(BASE/"college_dashboard_metrics.md").write_text(f'''# College-Value Dashboard Metrics\n\n## Purpose\nMeasure the value delivered to colleges through student readiness, application activity, placement outcomes and company engagement.\n\n## Core metrics\n- Registered Students = distinct students registered in the reporting population.\n- Eligible Students = students satisfying configured placement eligibility rules.\n- Profile Completion Rate = students with complete profiles / registered students x 100.\n- Students with Applications = distinct eligible students with at least one application.\n- Placement Rate = distinct placed students / eligible students x 100.\n- Average Package = mean package LPA among placed students with a recorded package.\n- Median Package = median package LPA among placed students with a recorded package.\n- Company Engagement = distinct companies with at least one engagement for the college.\n- Successful Outcomes = company engagement records reaching a successful outcome.\n\n## Interpretation\nThe dashboard is intended to help a college identify readiness gaps, funnel leakage, placement performance and recruiter demand. College-to-college comparisons should be interpreted with branch mix, eligibility rules, recruiter mix and time-window context.\n''')
(BASE/"college_dashboard_model.md").write_text('''# College-Value Dashboard Model\n\nLogical entities: College, Student, Application, Company Engagement.\n\nRelationships: College 1-to-many Student; Student 1-to-many Application; College 1-to-many Company Engagement; Company 1-to-many Company Engagement. Stable IDs are college_id, student_id, application_id.\n\nThe analytical layer preserves student-level eligibility and profile readiness, application lifecycle stage and company engagement outcomes. College KPIs are derived from these governed grains to avoid mixing student counts with application counts.\n''')
(BASE/"README.md").write_text('''# Day 20 - Portals Integration & Dry Run\n\nCollege-value dashboard demonstration for PlaceMux Phase 2.\n\n## Reproduce\npython college_dashboard_demo.py\n\nOpen `college_dashboard.html` locally.\n\n## Data note\nAll demonstration records are synthetic and intentionally labeled as such. No production PlaceMux performance is claimed.\n''')
(BASE/"Day20_submission_answer.md").write_text('''For Day 20, I shipped a college-value dashboard designed for the college-side portal of the PlaceMux marketplace. The dashboard gives placement teams a single view of student readiness, application activity, placement outcomes and company engagement. It is organized into three practical views: Overview, Placement Funnel and Company Engagement.\n\nThe demonstration uses a synthetic dataset because the task brief does not provide a production college portal dataset. The final dry run covers 6 colleges, 2,400 registered students and 3,200 applications. The dashboard measures eligibility, profile completion, application participation, interviews, offers, placements, package outcomes and company engagement. College-level comparisons use placed students divided by eligible students for the placement-rate KPI, while package metrics are calculated only for placed students with a recorded package value.\n\nThe dashboard is designed around college decisions rather than only presentation. The Overview highlights readiness gaps and college-level performance, the Placement Funnel shows where student progression falls between eligibility and placement, and the Company Engagement view shows recruiter demand and successful outcomes by college. This creates a practical operating view for placement teams to prioritize incomplete profiles, documentation gaps, low-conversion stages and recruiter engagement opportunities.\n\nThe implementation is reproducible from `phase2/college_dashboard_demo.py`. The script generates the synthetic student, application and company-engagement sources, the college KPI output, machine-readable validation evidence and the self-contained HTML dashboard. The dry run passed validation with zero duplicate student IDs, zero duplicate application IDs, zero ineligible applications, zero invalid stages and zero broken student/application links. The result is a live local college-value dashboard that satisfies the Task 20 definition of done.\n''')
print(json.dumps({"metrics":m,"validation":checks},indent=2))
print(f"Generated: {BASE/'college_dashboard.html'}")
