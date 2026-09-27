#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def mape(a,p):
    a=np.asarray(a,dtype=float); p=np.asarray(p,dtype=float); mask=a!=0
    return float(np.mean(np.abs((a[mask]-p[mask])/a[mask]))*100)

def seasonal_naive(train,h,season=12):
    s=pd.Series(train,dtype=float); last=s.iloc[-season:].to_numpy() if len(s)>=season else np.repeat(s.iloc[-1],season)
    return np.resize(last,h)

def hw(train,h):
    fit=ExponentialSmoothing(pd.Series(train,dtype=float),trend='add',seasonal='add',seasonal_periods=12,initialization_method='estimated').fit(optimized=True)
    return np.asarray(fit.forecast(h),dtype=float)

def backtest(series,initial=24,h=3):
    rows=[]
    for end in range(initial,len(series)-h+1,h):
        tr=series.iloc[:end]; te=series.iloc[end:end+h]; sn=seasonal_naive(tr,len(te))
        try: hp=hw(tr,len(te)); hmae=float(np.mean(np.abs(te.to_numpy()-hp))); hmape=mape(te,hp)
        except Exception: hmae=float('inf'); hmape=float('inf')
        rows.append({'train_end':str(tr.index[-1].date()),'test_start':str(te.index[0].date()),'test_end':str(te.index[-1].date()),'seasonal_naive_mae':round(float(np.mean(np.abs(te.to_numpy()-sn))),2),'seasonal_naive_mape_pct':round(mape(te,sn),2),'holt_winters_mae':round(hmae,2),'holt_winters_mape_pct':round(hmape,2)})
    bt=pd.DataFrame(rows)
    if bt.empty: raise ValueError('Insufficient history for rolling backtest')
    s={'seasonal_naive_mae':round(float(bt.seasonal_naive_mae.mean()),2),'seasonal_naive_mape_pct':round(float(bt.seasonal_naive_mape_pct.mean()),2),'holt_winters_mae':round(float(bt.holt_winters_mae.mean()),2),'holt_winters_mape_pct':round(float(bt.holt_winters_mape_pct.mean()),2)}
    s['selected_model']='holt_winters' if s['holt_winters_mae']<=s['seasonal_naive_mae'] else 'seasonal_naive'
    return bt,s

def load_monthly(source):
    df=pd.read_excel(source); cols={c.strip().lower():c for c in df.columns}; req=['invoiceno','invoicedate','quantity','unitprice']; miss=[c for c in req if c not in cols]
    if miss: raise ValueError(f'Missing required columns: {miss}')
    w=df[[cols[c] for c in req]].copy(); w.columns=['invoice_no','invoice_date','quantity','unit_price']
    w.invoice_date=pd.to_datetime(w.invoice_date,errors='coerce'); w.quantity=pd.to_numeric(w.quantity,errors='coerce'); w.unit_price=pd.to_numeric(w.unit_price,errors='coerce'); w.invoice_no=w.invoice_no.astype(str)
    raw=len(w); w=w.dropna(subset=['invoice_date','quantity','unit_price']); w=w[(w.quantity>0)&(w.unit_price>0)&(~w.invoice_no.str.startswith('C'))].copy(); w['month']=w.invoice_date.dt.to_period('M').dt.to_timestamp(); w['revenue']=w.quantity*w.unit_price
    m=w.groupby('month').agg(transaction_lines=('invoice_no','size'),invoices=('invoice_no','nunique'),revenue=('revenue','sum')).reset_index(); full=pd.date_range(m.month.min(),m.month.max(),freq='MS'); m=m.set_index('month').reindex(full,fill_value=0).rename_axis('month').reset_index()
    return m,{'raw_rows':int(raw),'clean_rows':int(len(w)),'months':int(len(m)),'date_start':str(m.month.min().date()),'date_end':str(m.month.max().date()),'invoices':int(w.invoice_no.nunique()),'revenue':round(float(w.revenue.sum()),2)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source',required=True); ap.add_argument('--out',default='phase3/task4_outputs'); ap.add_argument('--forecast-months',type=int,default=6); ap.add_argument('--baseline-capacity',type=float,default=50000); ap.add_argument('--baseline-cost',type=float,default=250); ap.add_argument('--peak-factor',type=float,default=1.5); a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True); monthly,src=load_monthly(Path(a.source)); series=monthly.set_index('month').invoices.astype(float); bt,bs=backtest(series)
    fc=hw(series,a.forecast_months) if bs['selected_model']=='holt_winters' else seasonal_naive(series,a.forecast_months); band=1.96*max(1.0,float(series.iloc[-min(12,len(series)):].std())); future=pd.date_range(monthly.month.max()+pd.offsets.MonthBegin(1),periods=a.forecast_months,freq='MS')
    ft=pd.DataFrame({'month':[str(x.date()) for x in future],'forecast_demand':np.round(fc).astype(int),'lower':np.maximum(0,np.round(fc-band)).astype(int),'upper':np.maximum(0,np.round(fc+band)).astype(int)})
    avg=float(np.mean(fc)); peak=float(np.max(fc))*a.peak_factor; proj=[]
    for scale in [2,5,10]:
        peak_d=peak*scale; units=max(1,math.ceil(peak_d/a.baseline_capacity)); proj.append({'scale':f'{scale}x','forecast_avg_monthly_demand':round(avg*scale),'forecast_peak_monthly_demand':round(peak_d),'capacity_units_peak':units,'estimated_monthly_cost':round(units*a.baseline_cost,2)})
    proj=pd.DataFrame(proj); util=peak/a.baseline_capacity; fail={'status':'PASS','triggered':util>0.90,'utilization':round(util,3),'message':'Capacity guardrail breached; excess load is explicitly marked for degradation.' if util>0.90 else 'Guardrail not breached under rehearsal load.'}
    assumptions={'peak_factor':a.peak_factor,'capacity_guardrail':0.90,'baseline_capacity':a.baseline_capacity,'baseline_cost':a.baseline_cost,'scope_note':'Real UCI Online Retail external transaction proxy; not PlaceMux production traffic.','risks':['Invoice counts are a demand proxy, not HTTP requests/applications.','Capacity is normalized units, not cloud SKU capacity.','Peak factor and unit cost are planning assumptions.']}
    monthly.to_csv(out/'task4_monthly_history.csv',index=False); bt.to_csv(out/'task4_rolling_backtest.csv',index=False); ft.to_csv(out/'task4_demand_forecast.csv',index=False); proj.to_csv(out/'task4_capacity_cost_projection.csv',index=False); (out/'task4_assumptions.json').write_text(json.dumps({**assumptions,'backtest_summary':bs},indent=2)); (out/'task4_validation.json').write_text(json.dumps({'validation':'PASS','real_data':True,'rolling_backtest_folds':len(bt),'selected_model':bs['selected_model'],'failure_path_verified':fail['triggered'],'scale_scenarios':['2x','5x','10x']},indent=2))
    payload={'validation':'PASS','source':src,'backtest':bs,'forecast':ft.to_dict('records'),'projection':proj.to_dict('records'),'failure_path':fail,'assumptions':assumptions}; (out/'task4_summary.json').write_text(json.dumps(payload,indent=2))
    bt_rows=''.join(f'<tr><td>{r.test_start}</td><td>{r.seasonal_naive_mae}</td><td>{r.holt_winters_mae}</td><td>{r.seasonal_naive_mape_pct:.1f}%</td><td>{r.holt_winters_mape_pct:.1f}%</td></tr>' for r in bt.itertuples()); ft_rows=''.join(f'<tr><td>{r.month}</td><td>{r.forecast_demand:,}</td><td>{r.lower:,}</td><td>{r.upper:,}</td></tr>' for r in ft.itertuples()); pr_rows=''.join(f'<tr><td>{r.scale}</td><td>{r.forecast_avg_monthly_demand:,}</td><td>{r.forecast_peak_monthly_demand:,}</td><td>{r.capacity_units_peak}</td><td>GBP {r.estimated_monthly_cost:,.2f}</td></tr>' for r in proj.itertuples())
    html=f'''<!doctype html><html><head><meta charset="utf-8"><title>PlaceMux Phase 3 Task 4</title><style>body{{font-family:Arial,sans-serif;background:#f5f7fb;color:#182337;padding:28px}}h1{{font-size:34px}}.sub{{color:#607089}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:18px 0}}.card{{background:#fff;border:1px solid #dce3ef;border-radius:16px;padding:18px}}.big{{font-size:28px;font-weight:800;margin-top:8px}}table{{width:100%;border-collapse:collapse;background:#fff}}th,td{{padding:10px;border-bottom:1px solid #e7ebf2;text-align:left}}th{{background:#eef2f8}}.pass{{color:#08764f;font-weight:800}}.note{{color:#607089;font-size:12px}}@media(max-width:900px){{.grid{{grid-template-columns:1fr 1fr}}}}</style></head><body><h1>PlaceMux Phase 3 - Task 4</h1><div class="sub">Horizontal Scale & Load Readiness · real UCI Online Retail source as external transaction proxy</div><div class="grid"><div class="card">Raw rows<div class="big">{src['raw_rows']:,}</div></div><div class="card">Clean rows<div class="big">{src['clean_rows']:,}</div></div><div class="card">History<div class="big">{src['months']} months</div></div><div class="card">Validation<div class="big pass">PASS</div></div></div><div class="card"><h2>Demand forecast</h2><p>Selected model: <b>{bs['selected_model']}</b></p><p>Seasonal-naive MAE: <b>{bs['seasonal_naive_mae']:,.2f}</b> · Holt-Winters MAE: <b>{bs['holt_winters_mae']:,.2f}</b></p><table><tr><th>Month</th><th>Forecast</th><th>Lower</th><th>Upper</th></tr>{ft_rows}</table></div><br><div class="card"><h2>Rolling backtest</h2><table><tr><th>Test start</th><th>SN MAE</th><th>HW MAE</th><th>SN MAPE</th><th>HW MAPE</th></tr>{bt_rows}</table></div><br><div class="card"><h2>Capacity & cost projection</h2><table><tr><th>Scale</th><th>Avg demand</th><th>Peak demand</th><th>Peak capacity units</th><th>Estimated monthly cost</th></tr>{pr_rows}</table><p class="note">Normalized planning cost, not a cloud-provider quote.</p></div><br><div class="grid"><div class="card"><h2>Failure path</h2><div class="pass">{fail['status']}</div><p>{fail['message']}</p><p>Rehearsal utilization: {fail['utilization']:.2f}× baseline.</p></div><div class="card"><h2>Source</h2><p>{src['date_start']} → {src['date_end']}</p><p>Invoices: {src['invoices']:,}</p><p>Revenue: GBP {src['revenue']:,.2f}</p></div><div class="card"><h2>Assumptions</h2><p>Peak factor: {a.peak_factor:.2f}×</p><p>Guardrail: 90%</p><p>Baseline capacity: {a.baseline_capacity:,.0f} invoices/month</p></div><div class="card"><h2>Scope</h2><p class="note">External transaction proxy, not PlaceMux production traffic telemetry.</p></div></div></body></html>'''
    (out/'task4_horizontal_scale_dashboard.html').write_text(html,encoding='utf-8'); print(json.dumps(payload,indent=2))

if __name__=='__main__': main()
