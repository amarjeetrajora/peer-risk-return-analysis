"""
Preprocessing for the Industry Risk & Return Analysis project.

Validates raw price data, builds a data-quality summary table, flags
(but does not auto-remove) suspicious price discontinuities, converts
prices to monthly returns, and aligns every series onto a common set of
dates so companies are compared apples-to-apples.
"""

import numpy as np
import pandas as pd


def validate_price_data(df, name):
    """
    Run the same data-quality checks the original Reliance notebook ran,
    generalized to any company. Returns a dict describing what was found
    — never silently mutates or drops data.
    """
    issues = []

    required_cols = {"Open", "High", "Low", "Close"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        issues.append(f"missing columns: {sorted(missing_cols)}")

    present_cols = [c for c in ("Open", "High", "Low", "Close") if c in df.columns]
    missing_values = int(df[present_cols].isna().sum().sum()) if present_cols else None
    if missing_values:
        issues.append(f"{missing_values} missing OHLC values")

    dup_dates = int(df.index.duplicated().sum())
    if dup_dates:
        issues.append(f"{dup_dates} duplicate dates")

    if not df.index.is_monotonic_increasing:
        issues.append("dates not sorted ascending")

    if {"High", "Low"} <= set(df.columns):
        bad_hl = int((df["High"] < df["Low"]).sum())
        if bad_hl:
            issues.append(f"{bad_hl} rows with High < Low")

    return {
        "Company": name,
        "Start": df.index.min(),
        "End": df.index.max(),
        "Observations": len(df),
        "Missing": missing_values,
        "Status": "OK" if not issues else "FLAGGED",
        "Issues": "; ".join(issues),
    }


def data_quality_summary(data_dict):
    """Build the project's data-quality summary table across every series."""
    rows = [validate_price_data(df, name) for name, df in data_dict.items()]
    summary = pd.DataFrame(rows).set_index("Company")
    return summary.sort_index()


def flag_insufficient_history(quality_summary, min_observations):
    """
    Return the list of company names whose observation count falls below
    `min_observations`. The caller decides what to do with them — this
    function only flags, it never silently drops a company.
    """
    short = quality_summary[quality_summary["Observations"] < min_observations]
    return list(short.index)


def check_corporate_action_discontinuities(df, threshold=0.35):
    """
    Flag month-over-month Close price moves larger than `threshold`
    (default 35%) for manual review. This does NOT assume every large
    move is a data error — corporate actions and genuine market shocks
    both produce large moves (e.g. the ~+31.6% / -16.2% COVID months in
    the original Reliance analysis were genuine, not data problems).
    """
    move = df["Close"].pct_change()
    return move[move.abs() > threshold]


def prepare_monthly_returns(df):
    """
    Compute R_t = P_t / P_(t-1) - 1 on the monthly Close series.
    The first observation is dropped since R_t is undefined without P_(t-1).
    """
    returns = df["Close"].pct_change().dropna()
    returns.name = "Monthly_Return"
    return returns


def align_returns(returns_dict):
    """
    Combine every company's + benchmark's return Series into one
    DataFrame on a shared date index, keeping only dates where ALL
    series have a value. This is what makes covariance/correlation/beta
    calculations comparable across companies.
    """
    combined = pd.DataFrame(returns_dict)
    before = len(combined)
    combined = combined.dropna(how="any")
    after = len(combined)
    if after < before:
        print(f"align_returns: dropped {before - after} dates not common to all series "
              f"({after} common months remain)")
    return combined
