"""
Peer comparison for the Industry Risk & Return Analysis project.

Builds the master comparison DataFrame (one row per company), identifies
the historical leader for each metric (without producing an arbitrary
overall #1/#2/#3 ranking), and generates a per-company text profile from
the calculated values only.
"""

import pandas as pd
from src import metrics as m


def compare_companies(returns_dict, market_returns, periods_per_year, risk_free_rate):
    """
    Build one master DataFrame: rows = companies, columns = every metric.
    `returns_dict` should contain ONLY companies (not the benchmark itself).
    """
    rows = {
        name: m.calculate_all_metrics(returns, market_returns, periods_per_year, risk_free_rate)
        for name, returns in returns_dict.items()
    }
    return pd.DataFrame(rows).T


# Direction each metric should be read in when identifying a "leader".
# "higher" / "lower" = that direction is generally more desirable.
# "descriptive" = there is no universally better direction (e.g. beta) —
# these are reported as characteristics, never labeled better/worse.
METRIC_DIRECTIONS = {
    "CAGR": "higher",
    "Cumulative Return": "higher",
    "Avg Monthly Return": "higher",
    "Annualized Volatility": "lower",
    "Monthly Volatility": "lower",
    "Downside Deviation": "lower",
    "Max Drawdown": "higher",     # less negative (closer to 0) = smaller loss = "higher" numerically
    "Sharpe Ratio": "higher",
    "Sortino Ratio": "higher",
    "Calmar Ratio": "higher",
    "Beta (Regression)": "descriptive",
    "Beta (Covariance)": "descriptive",
    "Correlation": "descriptive",
    "Skewness": "descriptive",
    "Kurtosis": "descriptive",
}


def identify_metric_leaders(comparison_df):
    """
    For every metric with a clear "higher"/"lower" direction, find which
    company had the best historical value. Descriptive metrics (beta,
    correlation, skew, kurtosis) are reported as characteristics instead —
    their "leader" is whichever company has the most extreme value, labeled
    as such rather than as good/bad.
    """
    rows = []
    for metric, direction in METRIC_DIRECTIONS.items():
        if metric not in comparison_df.columns:
            continue
        col = comparison_df[metric].astype(float)

        if direction == "higher":
            leader, value, note = col.idxmax(), col.max(), "highest"
        elif direction == "lower":
            leader, value, note = col.idxmin(), col.min(), "lowest"
        else:
            leader, value, note = col.abs().idxmax(), col.loc[col.abs().idxmax()], "most extreme"

        rows.append({
            "Metric": metric,
            "Direction": direction,
            "Historical Leader": leader,
            "Value": value,
            "Note": note,
        })
    return pd.DataFrame(rows)


def generate_company_profile(name, comparison_df):
    """Build a text profile for one company, reading only from calculated values — nothing invented."""
    row = comparison_df.loc[name]

    def pct(x):
        return f"{x:.2%}" if pd.notna(x) else "n/a"

    def num(x):
        return f"{x:.2f}" if pd.notna(x) else "n/a"

    lines = [
        f"{name}",
        "",
        "Return Profile",
        f"  - CAGR: {pct(row['CAGR'])}",
        f"  - Cumulative Return: {pct(row['Cumulative Return'])}",
        f"  - Average Monthly Return: {pct(row['Avg Monthly Return'])}",
        "",
        "Risk Profile",
        f"  - Annualized Volatility: {pct(row['Annualized Volatility'])}",
        f"  - Maximum Drawdown: {pct(row['Max Drawdown'])}",
        f"  - Downside Deviation: {pct(row['Downside Deviation'])}",
        "",
        "Risk-Adjusted Profile",
        f"  - Sharpe: {num(row['Sharpe Ratio'])}",
        f"  - Sortino: {num(row['Sortino Ratio'])}",
        f"  - Calmar: {num(row['Calmar Ratio'])}",
        "",
        "Market Relationship",
        f"  - Beta: {num(row['Beta (Regression)'])}",
        f"  - Correlation: {num(row['Correlation'])}",
    ]
    return "\n".join(lines)


def generate_all_profiles(comparison_df):
    return {name: generate_company_profile(name, comparison_df) for name in comparison_df.index}
