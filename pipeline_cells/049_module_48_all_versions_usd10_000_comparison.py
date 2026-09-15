# MODULE 48 — ALL VERSIONS $10,000 COMPARISON
# Run in the same notebook, in module order.

# MODULE 48 — ALL AVAILABLE VERSIONS, $10,000 REPORTING CAPITAL
# Use current-run snapshots only. Never substitute archived research constants.
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

REPORT_INITIAL_CAPITAL = 10_000.0
if 'RESTORED_VERSION_RESULTS' not in globals():
    raise RuntimeError('Run Module 24 and the version modules before the report.')

def restored_comparison_table(registry, capital):
    rows=[]
    for name, result in registry.items():
        final=float(result['final_wealth'])
        marks=result['marks'].sort_values('Date')
        # Include original starting wealth of 1.0. Never rebase at first
        # already-invested mark, which would remove the first period return.
        wealth=np.r_[1.,marks.Wealth.to_numpy(dtype=float)]
        drawdown=wealth/np.maximum.accumulate(wealth)-1.
        years=(result['end']-result['first_execution']).days/365.25
        rows.append(dict(Version=name,Start=result['first_execution'].date(),End=result['end'].date(),
                         Final_Wealth=final,Net_Return_Pct=100*(final-1),
                         Ending_USD=capital*final,Profit_Loss_USD=capital*(final-1),
                         CAGR_Pct=100*(final**(1/years)-1) if years>0 else np.nan,
                         Event_Mark_Max_Drawdown_Pct=100*float(drawdown.min()),
                         Accounting=result['basis'],Historical_Status=result['historical_status'],
                         Current_Run_Status=result['current_status']))
    return pd.DataFrame(rows)

ALL_VERSION_10000_SUMMARY=restored_comparison_table(RESTORED_VERSION_RESULTS,REPORT_INITIAL_CAPITAL)
expected=['V8','V9','V10','V11','V12','V13','V14','V15','V16']
coverage_versions=['V1','V2','V3','V4 RIDGE','V4 HGB','V5','V6','V7']+expected+['TQQQ','CASH']
ALL_VERSION_RUN_COVERAGE=pd.DataFrame([
    dict(Version=v,Available=v in RESTORED_VERSION_RESULTS,
         Status='COMPUTED' if v in RESTORED_VERSION_RESULTS else 'NOT RUN / NO RESULT SUBSTITUTED')
    for v in coverage_versions
])
print('='*110)
print('ALL VERSIONS — $10,000 HISTORICAL RETURN SCALING')
print('Actual computed results only. Archived success/failure labels are context, not current results.')
print('Reporting scales frozen strategy wealth by $10,000. Market-impact models were NOT rerun at $10,000 AUM.')
print('Accounting conventions differ across versions; do not interpret this as a uniform-cost optimization ranking.')
print('Drawdowns below use event marks, NOT full daily NAV.')
display(ALL_VERSION_RUN_COVERAGE)
display(ALL_VERSION_10000_SUMMARY.round(6))

fig,ax=plt.subplots(figsize=(15,8))
for version,result in RESTORED_VERSION_RESULTS.items():
    marks=result['marks']
    ax.plot([result['first_execution']]+list(marks.Date),REPORT_INITIAL_CAPITAL*np.r_[1.,marks.Wealth.to_numpy()],label=version,
            linewidth=2.5 if version in ['V8','V16'] else 1.2)
ax.axhline(REPORT_INITIAL_CAPITAL,color='gray',linestyle='--',linewidth=1)
ax.set(title='$10,000 — event-mark wealth (original accounting per version)',xlabel='Valuation date',ylabel='USD')
ax.grid(alpha=.2);ax.legend(ncol=3);fig.tight_layout()
plt.show()

# Dedicated V16/V8 comparison is presented only if date endpoints match.
ALL_VERSION_V16_V8=None
if all(v in RESTORED_VERSION_RESULTS for v in ['V8','V16']):
    base,challenger=(RESTORED_VERSION_RESULTS[v] for v in ['V8','V16'])
    if (base['first_execution'],base['end'],base['basis']) != (challenger['first_execution'],challenger['end'],challenger['basis']):
        raise RuntimeError('V16/V8 accounting dates or cost bases differ; pairwise comparison stopped.')
    delta=challenger['final_wealth']-base['final_wealth']
    ALL_VERSION_V16_V8=pd.DataFrame([dict(
        V8_Ending_USD=REPORT_INITIAL_CAPITAL*base['final_wealth'],
        V16_Ending_USD=REPORT_INITIAL_CAPITAL*challenger['final_wealth'],
        V16_Minus_V8_USD=REPORT_INITIAL_CAPITAL*delta,
        V16_Minus_V8_Return_pp=100*delta,
        V16_Over_V8_Relative_Wealth=challenger['final_wealth']/base['final_wealth'],
    )])
    print('\nV16 VS V8 — SAME CLOSE/ADDITIVE-COST BASIS INCLUDING TERMINAL REBALANCE')
    display(ALL_VERSION_V16_V8.round(6))

report_dir=Path('restored_reports');report_dir.mkdir(exist_ok=True)
ALL_VERSION_10000_SUMMARY.to_csv(report_dir/'all_versions_10000.csv',index=False)
ALL_VERSION_RUN_COVERAGE.to_csv(report_dir/'run_coverage.csv',index=False)
if ALL_VERSION_V16_V8 is not None:
    ALL_VERSION_V16_V8.to_csv(report_dir/'v16_vs_v8_10000.csv',index=False)
fig.savefig(report_dir/'all_versions_10000.png',dpi=160,bbox_inches='tight')
for name,result in RESTORED_VERSION_RESULTS.items():
    result['marks'].to_csv(report_dir/(name.replace(' ','_')+'_wealth_marks.csv'),index=False)
print(f'[+] Reports saved to {report_dir.resolve()}')
print('[+] Historical research only; this report does not convert the backcast into prospective OOS.')
