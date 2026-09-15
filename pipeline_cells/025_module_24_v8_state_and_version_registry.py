# MODULE 24 — V8 STATE AND VERSION REGISTRY
# Run in the same notebook, in module order.

# MODULE 24 — RESTORED V8 STATE + INDEPENDENT VERSION RESULT REGISTRY
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

_m24_required = ['V8_FINAL_TARGET_MATRIX', 'V8_FINAL_RESEARCH_PATH',
                 'V8_FINAL_RESEARCH_WEALTH', 'V8_FINAL_TQQQ_WEALTH',
                 'V8_FINAL_REPLICATION_AUDIT', 'V7_PATH', 'B38_ALL_PRICES']
_m24_missing = [n for n in _m24_required if n not in globals()]
if _m24_missing:
    raise RuntimeError(f'Complete Module 23 first: {_m24_missing}')
if not V8_FINAL_REPLICATION_AUDIT.Matches_6dp.all():
    raise RuntimeError('V8 historical replication must pass before continuation.')

# Exact aliases for the old V8 reporting objects used by V9/V12/V16. No refit.
V8Q_WEIGHT_MATRIX = V8_FINAL_TARGET_MATRIX.copy()
V8Q_TQQQ_WEIGHT = V8Q_WEIGHT_MATRIX['TQQQ'].copy()
V8Q_ALPHA_WEIGHT = 1.0 - V8Q_TQQQ_WEIGHT
RESTORE_FIRST_SIGNAL_DATE = pd.Timestamp(V7_PATH.Signal_Date.min()).normalize()
RESTORE_INITIAL_V8_PATH = V8_PATH.copy(deep=True)
RESTORE_INITIAL_V8_TARGETS = V8Q_WEIGHT_MATRIX.copy(deep=True)

RESTORED_VERSION_RESULTS = {}

def restored_register(version, final_wealth, path, wealth_column, basis, historical_status,
                      terminal_date=None):
    """Copy results now, before legacy code reuses global variable names.

    A terminal cost-only adjustment is preserved in the final mark. Original
    completed-period path is retained in raw_path; no missing daily NAV is invented.
    """
    import numpy as np
    import pandas as pd
    p = path.copy(deep=True)
    if wealth_column not in p:
        raise RuntimeError(f'{version}: missing exact wealth column {wealth_column}')
    if 'Exit_Date' in p:
        dates = pd.to_datetime(p['Exit_Date'], errors='coerce')
        if 'Execution_Date' in p:
            dates = dates.fillna(pd.to_datetime(p.Execution_Date))
    elif 'Execution_Date' in p:
        dates = pd.to_datetime(p.Execution_Date)
    else:
        dates = pd.Series(pd.to_datetime(p.index), index=p.index)
    values = pd.to_numeric(p[wealth_column], errors='raise').to_numpy(dtype=float)
    if not len(values) or not np.isfinite(values).all() or (values <= 0).any():
        raise RuntimeError(f'{version}: invalid wealth path')
    if not np.isfinite(final_wealth) or float(final_wealth) <= 0:
        raise RuntimeError(f'{version}: invalid terminal wealth')
    marks = pd.DataFrame({'Date': np.asarray(dates), 'Wealth': values})
    if marks.Date.isna().any():
        raise RuntimeError(f'{version}: missing valuation dates')
    if not np.isclose(values[-1], final_wealth, rtol=1e-10, atol=1e-12):
        if terminal_date is None:
            raise RuntimeError(f'{version}: path and scalar disagree without an explicit terminal cost date')
        marks = pd.concat([marks, pd.DataFrame({'Date':[pd.Timestamp(terminal_date)],
                                              'Wealth':[float(final_wealth)]})], ignore_index=True)
    marks = marks.drop_duplicates('Date', keep='last').sort_values('Date')
    first_execution = pd.Timestamp(p.Execution_Date.min()) if 'Execution_Date' in p else pd.Timestamp(marks.Date.min())
    RESTORED_VERSION_RESULTS[version] = dict(
        final_wealth=float(final_wealth), raw_path=p, marks=marks,
        first_execution=first_execution, end=pd.Timestamp(marks.Date.max()),
        basis=basis, historical_status=historical_status,
        current_status='COMPUTED_IN_THIS_RUN',
    )
    print(f'[RESULT SNAPSHOT] {version}: {float(final_wealth):.6f} | {basis}')

restored_register('V8', V8_FINAL_RESEARCH_WEALTH, V8_FINAL_RESEARCH_PATH, 'Wealth',
                  'Close / additive TCA / terminal rebalance', 'Historical champion before V16')
restored_register('V8 original', V8_ONE_SHOT_FINAL_WEALTH, RESTORE_INITIAL_V8_PATH, 'V8_Wealth',
                  'Open / multiplicative TCA', 'Original research freeze')
restored_register('V7', V7_FINAL_WEALTH, V7_PATH, 'Wealth',
                  'Open / multiplicative TCA', 'Historical V7')
RESTORE_REPORT_TQQQ_WEALTH = float(V8_FINAL_TQQQ_WEALTH)
_m24_benchmark_dates = pd.DatetimeIndex(V8_FINAL_RESEARCH_PATH.Exit_Date)
_m24_benchmark_start = pd.Timestamp(V8_FINAL_RESEARCH_PATH.Execution_Date.iloc[0])
_m24_benchmark_prices = V8_FINAL_CLOSE_LEDGER['TQQQ']
_m24_benchmark_values = (1.-B40_TCA_RATE)*_m24_benchmark_prices.reindex(_m24_benchmark_dates).to_numpy()/float(_m24_benchmark_prices.loc[_m24_benchmark_start])
restored_register('TQQQ', V8_FINAL_TQQQ_WEALTH,
    pd.DataFrame({'Execution_Date':V8_FINAL_RESEARCH_PATH.Execution_Date.to_numpy(),
                  'Exit_Date':_m24_benchmark_dates,'Wealth':_m24_benchmark_values}),
    'Wealth','Close / initial multiplicative entry cost','Historical benchmark')
restored_register('CASH', 1.,
    pd.DataFrame({'Execution_Date':[_m24_benchmark_start],
                  'Exit_Date':[_m24_benchmark_dates[-1]],'Wealth':[1.]}),
    'Wealth','Zero cash return as declared in original project','Declared baseline')

# Capture optional earlier versions only when their actual paths exist.
for _ver, _pname, _wname in [('V5','V5_PATH','Wealth'), ('V6','V6_PATH','Wealth')]:
    if _pname in globals() and _wname in globals()[_pname]:
        _p = globals()[_pname]
        restored_register(_ver, float(_p[_wname].iloc[-1]), _p, _wname,
                          'Open / original historical accounting', 'Earlier challenger')
if 'BLOCK40_PATH' in globals():
    for _model, _p in BLOCK40_PATH.groupby('Model'):
        restored_register('V4 '+str(_model), float(_p.Wealth.iloc[-1]), _p, 'Wealth',
                          'Open / original historical accounting', 'Earlier challenger')

def restored_yf_download(*args, **kwargs):
    """Preserve the first original HLX data-repair response for deterministic reruns.
    No download is performed while preparing this module; this runs in notebook.
    """
    import yfinance as yf
    key = hashlib.sha256(json.dumps([args,kwargs], sort_keys=True, default=str).encode()).hexdigest()
    folder = Path('restored_source_cache'); folder.mkdir(exist_ok=True)
    file = folder / (key + '.pkl')
    if file.exists():
        return pd.read_pickle(file)
    result = yf.download(*args, **kwargs)
    if result is None or result.empty:
        raise RuntimeError('Original lifecycle repair returned no price data; it was not substituted.')
    result.to_pickle(file, protocol=4)
    return result

print('[+] V8 state preserved. Continue with Module 25.')
