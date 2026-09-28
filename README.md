# Industry Risk & Return Analysis

A reusable, multi-company peer-comparison framework for historical
risk/return analysis on NSE-listed equities.

## Background — a generalized and extended version of the original single-stock analysis

This project builds on an earlier notebook, which analyzed a single company (Reliance Industries) against the
NIFTY 50 benchmark using monthly return, volatility, drawdown,
distribution, and market-relationship metrics.

This project extends that foundation in two ways, not just one:

- **Scope** — one company → a configurable **six-company peer
  comparison**, all benchmarked against the same index (NIFTY 50)
- **Metric set** — the original notebook deliberately did **not**
  compute Sharpe, Sortino, or Calmar ratios, since it assumed no
  risk-free rate. This version makes `RISK_FREE_RATE` an explicit,
  configurable value in `config.py`, which enables those three
  risk-adjusted ratios plus Downside Deviation.

This is a **historical, descriptive** study. Results characterize
observed behavior during the sample period and are **not** a forecast
of future returns; nothing here is investment advice.

## What's new compared to the original

| | Original (single stock) | This version (6-company peer comparison) |
|---|---|---|
| Companies analyzed | 1 (Reliance Industries) | 6, configurable via `config.py` |
| Series pulled per run | 2 (stock + NIFTY 50) | 7 (6 companies + NIFTY 50) |
| Return metrics | Avg monthly return, cumulative return, CAGR, best/worst month | Same, computed per company |
| Risk metrics | Volatility, max drawdown | Volatility, max drawdown, **+ Downside Deviation (new)** |
| Distribution | Skewness, kurtosis | Same |
| Market relationship | Beta (regression + covariance), correlation | Same, per company |
| Risk-adjusted ratios | **Not computed** (no risk-free rate assumed) | **Sharpe, Sortino, Calmar (new)** — enabled by explicit `RISK_FREE_RATE` |
| Cross-company comparison | N/A (single stock) | Metric-leader identification, per-company text profiles (new) |
| Charts | 7, single-company (price, returns, cumulative, drawdown, distribution, beta scatter) | 10, comparison-oriented (small-multiples price/growth/drawdown, per-metric bar charts, risk-return scatter, correlation heatmap) |

## What it does

Give it a list of NSE tickers for one industry and it will:

1. Download monthly price data for every company + the NIFTY 50 benchmark
2. Run data-quality checks and flag anomalies for manual review (never silently drop or auto-correct)
3. Compute the full return / risk / distribution / market-relationship / risk-adjusted metric set for each company
4. Build a peer-comparison table and identify the historical "leader" per metric (no arbitrary overall #1)
5. Generate a plain-text profile per company from the calculated values only
6. Produce 10 comparison charts and 3 CSV outputs

## Quick Start

​```bash
git clone <repo-url>
cd peer-risk-return-analysis
pip install -r requirements.txt
jupyter notebook notebooks/peer_risk_return_analysis.ipynb
​```

Then, inside the notebook:

1. *(Optional)* Edit `src/config.py` first if you want a different industry — the default is the IT Services set already configured. See **Configuration** below.
2. Run all cells top to bottom.
3. Results land in `outputs/*.csv` and `figures/*.png`.


## Configuration — choosing which companies to analyze

Everything that determines *what* gets analyzed lives in one place:
**`src/config.py`**. The company universe is a single dictionary:

```python
INDUSTRY = "Private Banking"

COMPANIES = {
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "Axis Bank": "AXISBANK.NS",
    "IndusInd Bank": "INDUSINDBK.NS",
    "Federal Bank": "FEDERALBNK.NS",
}
```

To analyze a **different industry**, just replace `COMPANIES` with a
different set of `"Display Name": "TICKER.NS"` pairs (see **Examples**
below for ready-to-paste sets) and re-run the notebook top to bottom —
nothing else in `src/` needs to change. Every downstream step — data
download, quality checks, returns, metrics, peer comparison, profiles,
and all 10 charts — reads from this dictionary and regenerates
automatically for whichever companies are listed. No per-company code
anywhere else in the project.

The framework can also be used to analyze a custom mix of companies across different industries. To do this, simply set INDUSTRY = "Mixed" in config.py and replace the COMPANIES dictionary with the companies of your choice. The companies do not need to belong to the same industry. For example see **INDUSTRY = "Mixed"** in **Examples**.

Other settings in the same file:

- **`BENCHMARK` / `BENCHMARK_NAME`** — the market index every company is compared against (default: NIFTY 50, `^NSEI`)
- **`START_DATE` / `END_DATE` / `INTERVAL`** — the date range and frequency, applied identically to every company and the benchmark
- **`RISK_FREE_RATE`** — annualized, decimal form; drives Sharpe/Sortino/Calmar, which the original single-stock analysis didn't compute at all. Set this to a real rate (e.g. the prevailing 10-year G-Sec yield) before trusting those ratios — it's a placeholder (`0.0`) until you do

`validate_config()` sanity-checks all of this (non-empty companies,
valid date range, supported interval, etc.) before anything downstream
runs, and prints a summary of what's configured.

## Project structure

```
industry-risk-return-analysis/
├── notebooks/
│   └── industry_risk_return_analysis.ipynb   # 21-section master notebook
├── src/
│   ├── config.py          # single source of truth — companies, benchmark, dates, risk-free rate
│   ├── data_loader.py     # download + yfinance header-fix reload
│   ├── preprocessing.py   # validation, data-quality table, returns, alignment
│   ├── metrics.py         # every return/risk/distribution/market/risk-adjusted metric
│   ├── comparison.py      # master peer table, metric leaders, company profiles
│   └── visualization.py   # the 10 comparison charts
├── data/
│   ├── raw/                 # untouched CSVs as downloaded
│   └── processed/           # reserved for any cleaned/derived data you add later
├── figures/                  # the 10 charts, written by src/visualization.py
├── outputs/
│   ├── company_metrics.csv    # full peer-comparison table
│   ├── annual_returns.csv     # calendar-year returns per company
│   └── findings.csv           # metric-by-metric historical leaders
└── README.md
```

## Dataset

- 6 companies (currently configured: IT Services — TCS, Infosys, Wipro, HCL Technologies, Tech Mahindra, Mphasis) + **NIFTY 50** benchmark = 7 series pulled and aligned each run
- Monthly OHLCV via `yfinance`, `auto_adjust=True`, same start/end date and interval applied identically to every series
- Data-quality checks (missing values, duplicate/unsorted dates, High<Low violations, insufficient history) run automatically for every series before any metric is computed
- Month-over-month moves beyond 35% are flagged for manual review rather than assumed to be data errors

## Metrics computed (per company)

- **Return** — Average Monthly Return, Cumulative Return, CAGR, Best/Worst Month
- **Risk** — Monthly & Annualized Volatility, Maximum Drawdown (with peak/trough/duration), **Downside Deviation** *(new vs. the original)*
- **Distribution** — Skewness, Kurtosis
- **Market Relationship** — Beta (regression + covariance, cross-validated), Correlation with benchmark
- **Risk-Adjusted** *(new vs. the original)* — Sharpe Ratio, Sortino Ratio, Calmar Ratio

## Design notes

- **Single config, no duplicated code.** No company name is hard-coded anywhere; changing `COMPANIES` retargets the whole pipeline.
- **The "Price"/"Date" fix is centralized.** `data_loader.load_price_csv()` applies the same header correction the original Reliance notebook used, once, for every series.
- **No arbitrary #1 ranking.** `comparison.identify_metric_leaders()` reports a leader per metric, with `higher` / `lower` / `descriptive` direction shown explicitly. Beta, correlation, skew, and kurtosis are reported as characteristics, never labeled good or bad.
- **Large price moves are flagged, not auto-corrected.** `preprocessing.check_corporate_action_discontinuities()` surfaces >35% monthly moves for manual review — it does not assume they're errors (genuine market shocks, like COVID, produce large moves too).
- **Risk-free rate is explicit.** `RISK_FREE_RATE` lives in `config.py` and is passed into every Sharpe/Sortino call — never assumed silently inside a formula, and never silently skipped either, unlike the original.
- **Charts stay readable regardless of company count.** Multi-line charts (price history, growth of ₹1, drawdown) render as small-multiples — one clean panel per company on a shared scale — rather than overlaying every company on one crowded axis.

## Examples — swapping industries

Any of these dictionaries can replace `COMPANIES` in `config.py` to
retarget the whole pipeline. All are NSE-listed, liquid, large-cap
names with price history well before the default `2011-01-01` start
date. Remember to also update `INDUSTRY` to a matching label so it
prints correctly in `validate_config()`'s summary.

**FMCG**
```python
COMPANIES = {
    "Hindustan Unilever": "HINDUNILVR.NS",
    "ITC": "ITC.NS",
    "Nestle India": "NESTLEIND.NS",
    "Britannia": "BRITANNIA.NS",
    "Dabur": "DABUR.NS",
    "Marico": "MARICO.NS",
}
```

**IT Services** 
```python
COMPANIES = {
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "Wipro": "WIPRO.NS",
    "HCL Technologies": "HCLTECH.NS",
    "Tech Mahindra": "TECHM.NS",
    "Mphasis": "MPHASIS.NS",
}
```

**Private Banking** *(currently configured)*
```python
COMPANIES = {
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "Axis Bank": "AXISBANK.NS",
    "IndusInd Bank": "INDUSINDBK.NS",
    "Federal Bank": "FEDERALBNK.NS",
}
```

**Pharma**
```python
COMPANIES = {
    "Sun Pharma": "SUNPHARMA.NS",
    "Dr Reddy's": "DRREDDY.NS",
    "Cipla": "CIPLA.NS",
    "Divi's Labs": "DIVISLAB.NS",
    "Lupin": "LUPIN.NS",
    "Aurobindo Pharma": "AUROPHARMA.NS",
}
```

**Auto**
```python
COMPANIES = {
    "Maruti Suzuki": "MARUTI.NS",
    "Mahindra & Mahindra": "M&M.NS",
    "Bajaj Auto": "BAJAJ-AUTO.NS",
    "Eicher Motors": "EICHERMOT.NS",
    "Hero MotoCorp": "HEROMOTOCO.NS",
}
```

**Mixed** 
```python
COMPANIES = {
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "Hero MotoCorp": "HEROMOTOCO.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Dabur": "DABUR.NS",
    "Cipla": "CIPLA.NS",
}
```

## Limitations

- Descriptive/historical only — not a forecast, not investment advice
- Sharpe/Sortino depend entirely on `RISK_FREE_RATE`; an unset or stale rate changes the results
- Dividend-reinvestment adjustment can't be verified from yfinance data alone
- No transaction costs, taxes, or investment strategy are modeled
- Large-move flags require manual review — not automatically corporate actions vs. genuine market moves
- Same industry ≠ same behavior — the correlation heatmap often shows this directly

## Adding a 7th or 8th company

Just add another `"Name": "TICKER.NS"` entry to `COMPANIES` in
`config.py` — nothing else needs to change.

## Related project

The original single-stock analysis this project generalizes and
extends: **Reliance Industries: 15-Year Risk & Return Analysis**
(`Reliance_Risk_Return_Analysis.ipynb`) — a single-company deep dive
against the NIFTY 50 benchmark that deliberately stopped short of
risk-adjusted ratios (no risk-free rate assumed). This project carries
its core methodology forward unchanged and builds on it: six companies
instead of one, plus Downside Deviation, Sharpe, Sortino, and Calmar
ratios enabled by an explicit, configurable risk-free rate.
