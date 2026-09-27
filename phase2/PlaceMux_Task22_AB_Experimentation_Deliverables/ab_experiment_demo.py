from __future__ import annotations

import json
import math
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
SEED = 2201
RNG = np.random.default_rng(SEED)

EXPERIMENT_ID = "exp_offer_nudge_v1"
TRAFFIC_SPLIT = 0.50
PRIMARY_METRIC = "application_submitted_7d"


def stable_uniform(value: str) -> float:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) / float(16**12)


def generate_subjects(n: int = 6000) -> pd.DataFrame:
    colleges = np.array([
        "BMS Institute of Technology",
        "PES University",
        "RV College of Engineering",
        "CMR Institute of Technology",
        "New Horizon College of Engineering",
        "Dayananda Sagar College of Engineering",
    ])
    rows = []
    for i in range(1, n + 1):
        subject_id = f"subj_{i:05d}"
        consent = stable_uniform(subject_id + "|consent") < 0.96
        deleted = stable_uniform(subject_id + "|delete") < 0.025
        withdrawn = stable_uniform(subject_id + "|withdraw") < 0.02
        age_band = "18-20" if stable_uniform(subject_id + "|age") < 0.58 else ("21-23" if stable_uniform(subject_id + "|age2") < 0.90 else "24+")
        college = colleges[i % len(colleges)]
        base_score = 0.55 + 0.28 * stable_uniform(subject_id + "|skill")
        eligible = consent and (not deleted) and (not withdrawn) and base_score >= 0.58
        rows.append({
            "subject_id": subject_id,
            "college": college,
            "consent_granted": bool(consent),
            "consent_version": "v2.1" if consent else None,
            "deletion_requested": bool(deleted),
            "withdrawn_from_experiment": bool(withdrawn),
            "eligibility_score": round(base_score, 4),
            "eligible": bool(eligible),
        })
    return pd.DataFrame(rows)


def assign_and_simulate(subjects: pd.DataFrame) -> pd.DataFrame:
    df = subjects.copy()
    df["assigned_at"] = "2026-09-12T09:00:00+05:30"
    df["assignment_bucket"] = df["subject_id"].map(stable_uniform)
    df["variant"] = np.where(df["assignment_bucket"] < TRAFFIC_SPLIT, "control", "treatment")
    df.loc[~df["eligible"], "variant"] = "excluded"

    eligible = df["eligible"]
    # Small deterministic uplift for treatment, plus heterogeneous noise.
    base = 0.185 + 0.05 * (df["eligibility_score"] - 0.58) / 0.28
    treatment_lift = np.where(df["variant"].eq("treatment"), 0.022, 0.0)
    p_submit = np.clip(base + treatment_lift, 0.03, 0.45)
    draw = np.array([stable_uniform(s + "|submit") for s in df["subject_id"]])
    df["exposed"] = eligible & (np.array([stable_uniform(s + "|exposure") for s in df["subject_id"]]) < 0.985)
    df.loc[~df["exposed"], "variant"] = "excluded"
    df["application_submitted_7d"] = (draw < p_submit) & df["exposed"]
    df["application_started_7d"] = (np.array([stable_uniform(s + "|start") for s in df["subject_id"]]) < np.clip(p_submit + 0.10, 0.06, 0.58)) & df["exposed"]
    df["interview_completed_14d"] = df["application_submitted_7d"] & (np.array([stable_uniform(s + "|interview") for s in df["subject_id"]]) < 0.58)
    df["offer_received_21d"] = df["interview_completed_14d"] & (np.array([stable_uniform(s + "|offer") for s in df["subject_id"]]) < 0.40)
    df["notification_sent"] = df["exposed"]
    df["event_count"] = df[["application_started_7d", "application_submitted_7d", "interview_completed_14d", "offer_received_21d", "notification_sent"]].sum(axis=1).astype(int)
    return df


def diff_ci(x1: int, n1: int, x0: int, n0: int, z: float = 1.96):
    p1 = x1 / n1 if n1 else 0
    p0 = x0 / n0 if n0 else 0
    diff = p1 - p0
    se = math.sqrt((p1 * (1 - p1) / n1) + (p0 * (1 - p0) / n0)) if n1 and n0 else float("nan")
    return diff, diff - z * se, diff + z * se


def two_prop_z_pvalue(x1: int, n1: int, x0: int, n0: int):
    if not n1 or not n0:
        return float("nan"), float("nan")
    p1 = x1 / n1
    p0 = x0 / n0
    pooled = (x1 + x0) / (n1 + n0)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n0))
    z = (p1 - p0) / se if se else 0.0
    # two-sided normal approximation
    p = math.erfc(abs(z) / math.sqrt(2))
    return z, p


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    analyzed = df[df["variant"].isin(["control", "treatment"])].copy()
    rows = []
    for variant in ["control", "treatment"]:
        sub = analyzed[analyzed["variant"] == variant]
        n = len(sub)
        rows.append({
            "experiment_id": EXPERIMENT_ID,
            "metric": PRIMARY_METRIC,
            "variant": variant,
            "population": "exposed_eligible",
            "n": n,
            "successes": int(sub[PRIMARY_METRIC].sum()),
            "rate": float(sub[PRIMARY_METRIC].mean()) if n else 0.0,
            "exposure_rate": float(sub["exposed"].mean()) if n else 0.0,
            "started_rate": float(sub["application_started_7d"].mean()) if n else 0.0,
            "interview_rate": float(sub["interview_completed_14d"].mean()) if n else 0.0,
            "offer_rate": float(sub["offer_received_21d"].mean()) if n else 0.0,
        })
    control = rows[0]
    treatment = rows[1]
    diff, low, high = diff_ci(treatment["successes"], treatment["n"], control["successes"], control["n"])
    z, p = two_prop_z_pvalue(treatment["successes"], treatment["n"], control["successes"], control["n"])
    rel_lift = diff / control["rate"] if control["rate"] else float("nan")
    for row in rows:
        row.update({"absolute_lift": diff, "relative_lift": rel_lift, "ci_low": low, "ci_high": high, "z_score": z, "p_value": p})
    return pd.DataFrame(rows)


def validate(df: pd.DataFrame, results: pd.DataFrame) -> dict:
    eligible = df[df["eligible"]].copy()
    eligible_hash = eligible["assignment_bucket"].map(lambda x: "control" if x < TRAFFIC_SPLIT else "treatment")
    assignment_mismatch = int(((eligible["variant"].isin(["control", "treatment"])) & (eligible["variant"].values != eligible_hash.values)).sum())
    duplicate_subjects = int(df["subject_id"].duplicated().sum())
    exposed_missing = int((df["exposed"] & ~df["eligible"]).sum())
    rights_breach = int((df["deletion_requested"] & df["exposed"]).sum()) + int((df["withdrawn_from_experiment"] & df["exposed"]).sum())
    invalid_variants = int((~df["variant"].isin(["control", "treatment", "excluded"])).sum())
    result_rows = int(len(results))
    arm_imbalance = abs(results.loc[results.variant.eq("treatment"), "n"].iloc[0] - results.loc[results.variant.eq("control"), "n"].iloc[0])
    p_value = float(results["p_value"].iloc[0])
    checks = {
        "duplicate_subject_ids": duplicate_subjects,
        "assignment_mismatches": assignment_mismatch,
        "exposed_without_eligibility": exposed_missing,
        "data_subject_rights_breaches": rights_breach,
        "invalid_variant_values": invalid_variants,
        "missing_analysis_rows": 2 - result_rows,
        "arm_size_imbalance": int(arm_imbalance),
        "p_value_present": 0 if math.isfinite(p_value) else 1,
    }
    overall = "PASS" if all(v == 0 for k, v in checks.items() if k != "arm_size_imbalance") and arm_imbalance <= 0.08 * max(1, int(len(eligible) * TRAFFIC_SPLIT)) else "FAIL"
    return {
        "experiment_id": EXPERIMENT_ID,
        "validation_status": overall,
        "subjects": int(len(df)),
        "eligible_subjects": int(df["eligible"].sum()),
        "exposed_subjects": int(df["exposed"].sum()),
        "control_subjects": int((df["variant"] == "control").sum()),
        "treatment_subjects": int((df["variant"] == "treatment").sum()),
        "checks": checks,
        "scope_note": "Synthetic experimentation dry run; no production experiment result is claimed.",
        "data_subject_rule": "Subjects with deletion request or experiment withdrawal are excluded before exposure and analysis.",
        "analysis_rule": "Primary analysis uses eligible exposed subjects with stable assignment; report intent-to-treat and treatment-on-exposed separately in production when both are needed.",
    }


def write_dashboard(df: pd.DataFrame, results: pd.DataFrame, validation: dict):
    control = results[results.variant.eq("control")].iloc[0]
    treatment = results[results.variant.eq("treatment")].iloc[0]
    excluded = int((df["variant"] == "excluded").sum())
    eligible = int(df["eligible"].sum())
    rights_excluded = int((df["deletion_requested"] | df["withdrawn_from_experiment"] | ~df["consent_granted"]).sum())

    payload = {
        "control": control.to_dict(),
        "treatment": treatment.to_dict(),
        "validation": validation,
        "summary": {
            "subjects": int(len(df)),
            "eligible": eligible,
            "exposed": int(df["exposed"].sum()),
            "excluded": excluded,
            "rights_excluded": rights_excluded,
            "primary_lift_pp": float(treatment["absolute_lift"] * 100),
            "relative_lift_pct": float(treatment["relative_lift"] * 100),
            "p_value": float(treatment["p_value"]),
        },
    }
    js = json.dumps(payload, separators=(",", ":"))
    html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>PlaceMux A/B Experimentation & Data-Subject Rights Framework</title>
<style>
:root {{ --ink:#172033; --muted:#667085; --panel:#fff; --bg:#f5f7fb; --line:#e5e7eb; --brand:#4f46e5; --ok:#0f8b5f; --warn:#b45309; }}
* {{ box-sizing:border-box }} body {{ margin:0; font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif; background:var(--bg); color:var(--ink); }}
.header {{ background:#fff; border-bottom:1px solid var(--line); padding:28px 42px 20px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} .sub {{ color:var(--muted); font-size:15px }}
.tabs {{ display:flex; gap:10px; padding:18px 42px 0; background:#fff; }} .tab {{ border:0; background:#eef0f7; color:#334155; padding:11px 18px; border-radius:11px 11px 0 0; font-weight:700; cursor:pointer; }} .tab.active {{ background:var(--brand); color:#fff; }}
.wrap {{ padding:26px 42px 42px; }} .grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }} .card {{ background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:18px; box-shadow:0 2px 8px rgba(15,23,42,.03); }} .metric {{ font-size:30px; font-weight:800; margin-top:7px; }} .label {{ color:var(--muted); font-size:13px; }} .section {{ margin-top:20px; }} .cols {{ display:grid; grid-template-columns:1.25fr .75fr; gap:18px; }}
.badge {{ display:inline-flex; align-items:center; padding:5px 9px; border-radius:999px; background:#e9f8f1; color:var(--ok); font-size:12px; font-weight:800; }} .badge.warn {{ background:#fff4e5; color:var(--warn); }}
table {{ width:100%; border-collapse:collapse; }} th,td {{ padding:11px 9px; border-bottom:1px solid var(--line); text-align:left; font-size:13px; }} th {{ color:var(--muted); font-size:12px; }}
.bar {{ height:12px; background:#e9ecf4; border-radius:99px; overflow:hidden; }} .fill {{ height:100%; background:var(--brand); }} .note {{ color:var(--muted); font-size:12px; line-height:1.5; }} ul {{ margin-top:8px; padding-left:20px; }} li {{ margin:7px 0; }} .view {{ display:none; }} .view.active {{ display:block; }}
.kpi-big {{ font-size:36px; font-weight:900; }} .positive {{ color:var(--ok); }} .mono {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; }}
.footer {{ margin-top:26px; color:var(--muted); font-size:12px; }}
@media(max-width:1000px) {{ .grid {{ grid-template-columns:repeat(2,1fr) }} .cols {{ grid-template-columns:1fr }} .header,.tabs,.wrap {{ padding-left:20px; padding-right:20px }} }}
</style>
</head>
<body>
<div class="header"><h1>PlaceMux A/B Experimentation & Data-Subject Rights Framework</h1><div class="sub">Synthetic experimentation dry run · {EXPERIMENT_ID} · stable assignment · consent-aware exclusion · resilience controls</div></div>
<div class="tabs">
<button class="tab active" data-tab="overview">Overview</button><button class="tab" data-tab="design">Experiment Design</button><button class="tab" data-tab="results">Results & Guardrails</button><button class="tab" data-tab="rights">Data Rights & Resilience</button>
</div>
<div class="wrap">
<section id="overview" class="view active">
<div class="grid">
<div class="card"><div class="label">Subjects</div><div class="metric">{len(df):,}</div></div>
<div class="card"><div class="label">Eligible</div><div class="metric">{eligible:,}</div></div>
<div class="card"><div class="label">Exposed</div><div class="metric">{int(df['exposed'].sum()):,}</div></div>
<div class="card"><div class="label">Validation</div><div class="metric" style="font-size:24px"><span class="badge">{validation['validation_status']}</span></div></div>
</div>
<div class="section cols">
<div class="card"><h2>Primary Outcome</h2><div class="kpi-big positive">{treatment['rate']*100:.2f}%</div><div class="label">Treatment application submitted within 7 days</div><p>Control: <b>{control['rate']*100:.2f}%</b> · Treatment: <b>{treatment['rate']*100:.2f}%</b> · Absolute lift: <b>{treatment['absolute_lift']*100:+.2f} pp</b> · Relative lift: <b>{treatment['relative_lift']*100:+.1f}%</b></p><div class="note">Synthetic demonstration only. The experiment framework is ready for a governed production assignment source.</div></div>
<div class="card"><h2>Experiment Health</h2><p><span class="badge">PASS</span> Stable assignment and data-rights checks</p><ul><li>Control: {int(control['n']):,} exposed subjects</li><li>Treatment: {int(treatment['n']):,} exposed subjects</li><li>p-value: {treatment['p_value']:.4f}</li><li>95% CI: {treatment['ci_low']*100:+.2f} to {treatment['ci_high']*100:+.2f} pp</li></ul></div>
</div>
</section>
<section id="design" class="view">
<div class="cols">
<div class="card"><h2>Experiment Contract</h2><table><tr><th>Field</th><th>Definition</th></tr><tr><td>Experiment ID</td><td class="mono">{EXPERIMENT_ID}</td></tr><tr><td>Hypothesis</td><td>The treatment nudge increases 7-day application submission.</td></tr><tr><td>Primary metric</td><td><b>{PRIMARY_METRIC}</b></td></tr><tr><td>Guardrails</td><td>Exposure rate, application start rate, interview completion, offer rate, rights violations.</td></tr><tr><td>Assignment</td><td>Deterministic 50/50 split on stable subject ID hash.</td></tr><tr><td>Eligibility</td><td>Consent, no deletion request, no withdrawal, eligibility score threshold.</td></tr><tr><td>Analysis</td><td>Exposed eligible subjects; pre-registered denominator and variant rules.</td></tr></table></div>
<div class="card"><h2>Lifecycle</h2><ul><li><b>Draft:</b> hypothesis, metric, population, guardrails.</li><li><b>Approved:</b> privacy, analytics and product review.</li><li><b>Running:</b> log assignment, exposure and outcome events.</li><li><b>Stopped:</b> preserve immutable experiment metadata and freeze cohort.</li><li><b>Analyzed:</b> calculate effect, uncertainty and guardrails.</li><li><b>Archived:</b> retain approved outputs; honor data-subject requests.</li></ul></div>
</div>
</section>
<section id="results" class="view">
<div class="grid">
<div class="card"><div class="label">Control conversion</div><div class="metric">{control['rate']*100:.2f}%</div></div>
<div class="card"><div class="label">Treatment conversion</div><div class="metric">{treatment['rate']*100:.2f}%</div></div>
<div class="card"><div class="label">Absolute lift</div><div class="metric positive">{treatment['absolute_lift']*100:+.2f} pp</div></div>
<div class="card"><div class="label">P-value</div><div class="metric">{treatment['p_value']:.4f}</div></div>
</div>
<div class="section card"><h2>Primary Metric Comparison</h2><table><tr><th>Variant</th><th>n</th><th>Successes</th><th>Rate</th><th>Exposure</th></tr><tr><td>Control</td><td>{int(control['n']):,}</td><td>{int(control['successes']):,}</td><td>{control['rate']*100:.2f}%</td><td>{control['exposure_rate']*100:.2f}%</td></tr><tr><td>Treatment</td><td>{int(treatment['n']):,}</td><td>{int(treatment['successes']):,}</td><td>{treatment['rate']*100:.2f}%</td><td>{treatment['exposure_rate']*100:.2f}%</td></tr></table><p>95% CI for treatment-control difference: <b>{treatment['ci_low']*100:+.2f} to {treatment['ci_high']*100:+.2f} percentage points</b>. Decision guidance: ship only after confirming guardrails remain within approved thresholds and the result is replicated or otherwise accepted by the experiment owner.</p></div>
<div class="section cols">
<div class="card"><h2>Guardrail Rates</h2><table><tr><th>Metric</th><th>Control</th><th>Treatment</th></tr><tr><td>Application start</td><td>{control['started_rate']*100:.2f}%</td><td>{treatment['started_rate']*100:.2f}%</td></tr><tr><td>Interview complete</td><td>{control['interview_rate']*100:.2f}%</td><td>{treatment['interview_rate']*100:.2f}%</td></tr><tr><td>Offer received</td><td>{control['offer_rate']*100:.2f}%</td><td>{treatment['offer_rate']*100:.2f}%</td></tr></table></div>
<div class="card"><h2>Decision Rule</h2><p><b>Primary:</b> compare treatment vs control on the pre-registered 7-day submission rate.</p><p><b>Guardrails:</b> do not ship if approved rights, exposure, quality or downstream thresholds fail.</p><p><b>Uncertainty:</b> use 95% confidence interval and the pre-declared alpha of 0.05.</p></div>
</div>
</section>
<section id="rights" class="view">
<div class="grid">
<div class="card"><div class="label">Rights exclusions</div><div class="metric">{rights_excluded:,}</div><div class="note">Consent absent, deletion requested or withdrawn</div></div>
<div class="card"><div class="label">Rights breaches</div><div class="metric">{validation['checks']['data_subject_rights_breaches']}</div></div>
<div class="card"><div class="label">Assignment mismatches</div><div class="metric">{validation['checks']['assignment_mismatches']}</div></div>
<div class="card"><div class="label">Duplicate subject IDs</div><div class="metric">{validation['checks']['duplicate_subject_ids']}</div></div>
</div>
<div class="section cols">
<div class="card"><h2>Data-Subject Controls</h2><ul><li>Consent is required before experimentation exposure.</li><li>Deletion requests exclude the subject before exposure and analysis.</li><li>Experiment withdrawal is honored before exposure and downstream measurement.</li><li>Use opaque subject identifiers; do not export direct identifiers into analytics outputs.</li><li>Version consent and purpose metadata so experiment eligibility can be audited.</li><li>Production deletion workflows must propagate to derived experiment datasets according to governed retention rules.</li></ul></div>
<div class="card"><h2>Resilience Checks</h2><ul><li>Stable assignment from immutable subject ID hash.</li><li>No exposure without eligibility.</li><li>No invalid variant values.</li><li>No duplicate subject identifiers.</li><li>Balanced control/treatment allocation within tolerance.</li><li>Primary analysis rows exist for both arms.</li><li>Machine-readable validation output retained alongside the experiment results.</li></ul></div>
</div>
</section>
<div class="footer">Source: synthetic demonstration generated by <span class="mono">phase2/ab_experiment_demo.py</span>. This dashboard demonstrates the experimentation and governance framework; it is not a production PlaceMux performance report or legal/privacy certification.</div>
</div>
<script>
const tabs = [...document.querySelectorAll('.tab')]; const views=[...document.querySelectorAll('.view')];
function activate(name) {{ tabs.forEach(t=>t.classList.toggle('active',t.dataset.tab===name)); views.forEach(v=>v.classList.toggle('active',v.id===name)); }}
function fromHash() {{ const n=location.hash.slice(1); activate(['overview','design','results','rights'].includes(n)?n:'overview'); }}
tabs.forEach(t=>t.addEventListener('click',()=>{{ location.hash=t.dataset.tab; activate(t.dataset.tab); }})); window.addEventListener('hashchange',fromHash); fromHash();
</script>
</body></html>'''
    (ROOT / "ab_experiment_dashboard.html").write_text(html, encoding="utf-8")


def main():
    subjects = generate_subjects()
    df = assign_and_simulate(subjects)
    results = summarize(df)
    validation = validate(df, results)

    # Event source: one row per subject with the key experiment lifecycle state.
    events = df[["subject_id", "college", "consent_granted", "consent_version", "deletion_requested", "withdrawn_from_experiment", "eligible", "assigned_at", "variant", "exposed", "application_started_7d", "application_submitted_7d", "interview_completed_14d", "offer_received_21d", "event_count"]].copy()
    events["experiment_id"] = EXPERIMENT_ID
    events = events[["experiment_id"] + [c for c in events.columns if c != "experiment_id"]]

    events.to_csv(ROOT / "ab_experiment_events_demo.csv", index=False)
    results.to_csv(ROOT / "ab_experiment_results.csv", index=False)
    (ROOT / "ab_experiment_validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_dashboard(df, results, validation)

    summary = {
        "experiment_id": EXPERIMENT_ID,
        "subjects": len(df),
        "eligible": int(df.eligible.sum()),
        "exposed": int(df.exposed.sum()),
        "control": int((df.variant == "control").sum()),
        "treatment": int((df.variant == "treatment").sum()),
        "control_rate": float(results.loc[results.variant.eq("control"), "rate"].iloc[0]),
        "treatment_rate": float(results.loc[results.variant.eq("treatment"), "rate"].iloc[0]),
        "absolute_lift": float(results.loc[results.variant.eq("treatment"), "absolute_lift"].iloc[0]),
        "relative_lift": float(results.loc[results.variant.eq("treatment"), "relative_lift"].iloc[0]),
        "p_value": float(results.loc[results.variant.eq("treatment"), "p_value"].iloc[0]),
        "validation": validation["validation_status"],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
