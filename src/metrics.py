"""
Metric calculation engine for the Industry Risk & Return Analysis project.

Every function takes a returns Series (and, where relevant, the market's
returns Series) and returns a single value or a small dict — no company
name is baked into any function, so the same code runs for all six
companies via calculate_all_metrics().
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# A. Return metrics
# ---------------------------------------------------------------------------

def average_monthly_return(returns):
    return returns.mean()


def annual_returns(returns):
    """Compound monthly returns within each calendar year into a yearly return."""
    return (1 + returns).groupby(returns.index.year).prod() - 1


def cumulative_return(returns):
    return (1 + returns).prod() - 1


def cagr(returns, periods_per_year):
    """
    CAGR = (Ending Value / Beginning Value)^(1/years) - 1, using the
    ACTUAL number of periods observed rather than assuming exactly N years.
    This is why CAGR differs from (average monthly return * 12): CAGR
    accounts for compounding and the true elapsed time, while a simple
    multiply-by-12 ignores both.
    """
    total_growth = (1 + returns).prod()
    n_years = len(returns) / periods_per_year
    if n_years <= 0:
        return np.nan
    return total_growth ** (1 / n_years) - 1


def best_worst_month(returns):
    """Returns (best_date, best_value, worst_date, worst_value)."""
    return returns.idxmax(), returns.max(), returns.idxmin(), returns.min()


# ---------------------------------------------------------------------------
# B. Risk metrics
# ---------------------------------------------------------------------------

def monthly_volatility(returns):
    return returns.std()


def annualized_volatility(returns, periods_per_year):
    return returns.std() * np.sqrt(periods_per_year)


def wealth_index(returns, start_value=1.0):
    return start_value * (1 + returns).cumprod()


def drawdown_series(returns):
    """Drawdown at each date = current wealth / running peak wealth - 1."""
    wealth = wealth_index(returns)
    running_max = wealth.cummax()
    return wealth / running_max - 1


def max_drawdown(returns):
    """
    Maximum drawdown, plus the peak date, trough date, and duration
    (in days) of that specific drawdown episode. Volatility measures
    total dispersion; max drawdown measures the single worst realized
    peak-to-trough loss — they answer different risk questions.
    """
    dd = drawdown_series(returns)
    trough_date = dd.idxmin()
    mdd = dd.loc[trough_date]

    # peak = the most recent date at/before the trough where drawdown was 0
    pre_trough = dd.loc[:trough_date]
    at_peak = pre_trough[pre_trough == 0]
    peak_date = at_peak.index.max() if len(at_peak) else dd.index.min()

    duration_days = (trough_date - peak_date).days if pd.notna(peak_date) else None

    return {
        "max_drawdown": mdd,
        "peak_date": peak_date,
        "trough_date": trough_date,
        "duration_days": duration_days,
    }


def downside_deviation(returns, mar=0.0):
    """Standard deviation of returns that fall below the minimum acceptable return (MAR)."""
    downside = returns[returns < mar] - mar
    if len(downside) == 0:
        return 0.0
    return np.sqrt((downside ** 2).mean())


def annualized_downside_deviation(returns, periods_per_year, mar=0.0):
    return downside_deviation(returns, mar) * np.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# C. Return distribution
# ---------------------------------------------------------------------------

def skewness(returns):
    return returns.skew()


def kurtosis(returns):
    """Excess kurtosis (0 = normal distribution), pandas' default convention."""
    return returns.kurt()


# ---------------------------------------------------------------------------
# D. Market relationship
# ---------------------------------------------------------------------------

def covariance_with_market(returns, market_returns):
    return returns.cov(market_returns)


def correlation_with_market(returns, market_returns):
    """Strength of co-movement with the benchmark — distinct from beta, which measures sensitivity."""
    return returns.corr(market_returns)


def beta_covariance(returns, market_returns):
    """Beta = Cov(stock, market) / Var(market)."""
    cov = returns.cov(market_returns)
    var = market_returns.var()
    return cov / var if var != 0 else np.nan


def beta_regression(returns, market_returns):
    """Cross-check: Beta = Correlation x (Stock Volatility / Market Volatility), via OLS slope."""
    slope, _intercept = np.polyfit(market_returns, returns, 1)
    return slope


# ---------------------------------------------------------------------------
# E. Risk-adjusted metrics
# ---------------------------------------------------------------------------
# None of these silently assume a risk-free rate — periods_per_year and
# risk_free_rate are always passed in explicitly by the caller (comparison.py),
# which reads them from config.RISK_FREE_RATE / config.PERIODS_PER_YEAR.

def _periodic_risk_free(periods_per_year, annual_risk_free_rate):
    return (1 + annual_risk_free_rate) ** (1 / periods_per_year) - 1


def sharpe_ratio(returns, periods_per_year, risk_free_rate):
    """Higher = more historical excess return per unit of total volatility."""
    rf = _periodic_risk_free(periods_per_year, risk_free_rate)
    excess = returns - rf
    ann_excess_return = excess.mean() * periods_per_year
    ann_vol = annualized_volatility(returns, periods_per_year)
    return ann_excess_return / ann_vol if ann_vol else np.nan


def sortino_ratio(returns, periods_per_year, risk_free_rate):
    """Like Sharpe, but penalizes only downside volatility (below the risk-free rate)."""
    rf = _periodic_risk_free(periods_per_year, risk_free_rate)
    excess = returns - rf
    ann_excess_return = excess.mean() * periods_per_year
    ann_downside = annualized_downside_deviation(returns, periods_per_year, mar=rf)
    return ann_excess_return / ann_downside if ann_downside else np.nan


def calmar_ratio(returns, periods_per_year):
    """Calmar = CAGR / abs(Maximum Drawdown)."""
    c = cagr(returns, periods_per_year)
    mdd = max_drawdown(returns)["max_drawdown"]
    return c / abs(mdd) if mdd else np.nan


# ---------------------------------------------------------------------------
# F. Aggregation
# ---------------------------------------------------------------------------

def calculate_return_metrics(returns, periods_per_year):
    best_date, best_val, worst_date, worst_val = best_worst_month(returns)
    return {
        "Avg Monthly Return": average_monthly_return(returns),
        "Cumulative Return": cumulative_return(returns),
        "CAGR": cagr(returns, periods_per_year),
        "Best Month": best_val,
        "Best Month Date": best_date,
        "Worst Month": worst_val,
        "Worst Month Date": worst_date,
    }


def calculate_risk_metrics(returns, periods_per_year):
    mdd_info = max_drawdown(returns)
    return {
        "Monthly Volatility": monthly_volatility(returns),
        "Annualized Volatility": annualized_volatility(returns, periods_per_year),
        "Max Drawdown": mdd_info["max_drawdown"],
        "Drawdown Peak Date": mdd_info["peak_date"],
        "Drawdown Trough Date": mdd_info["trough_date"],
        "Drawdown Duration (days)": mdd_info["duration_days"],
        "Downside Deviation": annualized_downside_deviation(returns, periods_per_year),
    }


def calculate_distribution_metrics(returns):
    return {
        "Skewness": skewness(returns),
        "Kurtosis": kurtosis(returns),
    }


def calculate_market_metrics(returns, market_returns):
    return {
        "Covariance": covariance_with_market(returns, market_returns),
        "Correlation": correlation_with_market(returns, market_returns),
        "Beta (Covariance)": beta_covariance(returns, market_returns),
        "Beta (Regression)": beta_regression(returns, market_returns),
    }


def calculate_risk_adjusted_metrics(returns, periods_per_year, risk_free_rate):
    return {
        "Sharpe Ratio": sharpe_ratio(returns, periods_per_year, risk_free_rate),
        "Sortino Ratio": sortino_ratio(returns, periods_per_year, risk_free_rate),
        "Calmar Ratio": calmar_ratio(returns, periods_per_year),
    }


def calculate_all_metrics(returns, market_returns, periods_per_year, risk_free_rate):
    """Run every metric group for one company and merge into a single flat dict."""
    metrics = {}
    metrics.update(calculate_return_metrics(returns, periods_per_year))
    metrics.update(calculate_risk_metrics(returns, periods_per_year))
    metrics.update(calculate_distribution_metrics(returns))
    metrics.update(calculate_market_metrics(returns, market_returns))
    metrics.update(calculate_risk_adjusted_metrics(returns, periods_per_year, risk_free_rate))
    return metrics
