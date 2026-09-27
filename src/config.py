"""
Configuration for the Industry Risk & Return Analysis project.

This module is the single source of truth for every parameter that must
stay IDENTICAL across companies so that comparisons are fair: the
benchmark, the date range, the frequency, and the company universe.

To analyze a different industry, change INDUSTRY and COMPANIES below.
Nothing else in the pipeline should need to change.
"""

import os
import datetime

# ---------------------------------------------------------------------------
# 1. Company universe
# ---------------------------------------------------------------------------
# Placeholders — replace with the real industry/companies when you're ready.
# Do not hard-code company-specific logic anywhere else in the project;
# every downstream function will read from this dictionary.

INDUSTRY = "IT Services"

COMPANIES = {
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "Wipro": "WIPRO.NS",
    "HCL Technologies": "HCLTECH.NS",
    "Tech Mahindra": "TECHM.NS",
    "Mphasis": "MPHASIS.NS",
}

BENCHMARK_NAME = "NIFTY 50"
BENCHMARK = "^NSEI"

# ---------------------------------------------------------------------------
# 2. Date range & frequency
# ---------------------------------------------------------------------------
# Same window and frequency for every company AND the benchmark — this is
# what makes the peer comparison fair.

START_DATE = "2011-01-01"
END_DATE = "2025-12-31"
INTERVAL = "1mo"           # yfinance interval string
PERIODS_PER_YEAR = 12      # used later to annualize volatility, CAGR, etc.

# ---------------------------------------------------------------------------
# 3. Risk-free rate (placeholder)
# ---------------------------------------------------------------------------
# Kept as an explicit, named constant rather than a silent assumption inside
# a formula. We'll revisit how to set this defensibly at the Sharpe/Sortino
# stage (Section 4 of the spec) rather than deciding it here.

RISK_FREE_RATE = 0.070   # annualized
# ---------------------------------------------------------------------------
# 4. yfinance download settings
# ---------------------------------------------------------------------------
AUTO_ADJUST = True

# ---------------------------------------------------------------------------
# 5. Project directories
# ---------------------------------------------------------------------------
# Paths are resolved relative to this file's location, so the project works
# no matter which directory it's run from.

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
FIGURES_DIR = os.path.join(BASE_DIR, "figures")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

REQUIRED_DIRS = [RAW_DIR, PROCESSED_DIR, FIGURES_DIR, OUTPUTS_DIR]


def ensure_directories():
    """Create every required project directory if it doesn't already exist."""
    for directory in REQUIRED_DIRS:
        os.makedirs(directory, exist_ok=True)


# ---------------------------------------------------------------------------
# 6. Configuration validation
# ---------------------------------------------------------------------------

def validate_config():
    """
    Sanity-check the configuration before anything downstream uses it.

    Raises AssertionError with a clear message if something is wrong.
    Returns True and prints a short summary if everything checks out.
    """
    assert isinstance(COMPANIES, dict) and len(COMPANIES) > 0, \
        "COMPANIES must be a non-empty dict of {company_name: ticker}"

    for name, ticker in COMPANIES.items():
        assert isinstance(name, str) and name.strip(), \
            f"Company name must be a non-empty string, got: {name!r}"
        assert isinstance(ticker, str) and ticker.strip(), \
            f"Ticker for '{name}' must be a non-empty string, got: {ticker!r}"

    assert isinstance(BENCHMARK, str) and BENCHMARK.strip(), \
        "BENCHMARK must be a non-empty string (e.g. '^NSEI')"

    start = datetime.datetime.strptime(START_DATE, "%Y-%m-%d")
    end = datetime.datetime.strptime(END_DATE, "%Y-%m-%d")
    assert start < end, "START_DATE must be earlier than END_DATE"

    assert INTERVAL in ("1d", "1wk", "1mo"), f"Unexpected INTERVAL: {INTERVAL!r}"

    assert PERIODS_PER_YEAR in (12, 52, 252), \
        f"PERIODS_PER_YEAR ({PERIODS_PER_YEAR}) doesn't match a standard frequency"

    ensure_directories()

    print("Configuration validated successfully.\n")
    print(f"Industry     : {INDUSTRY}")
    print(f"Companies    : {len(COMPANIES)} configured")
    for name, ticker in COMPANIES.items():
        print(f"  - {name:<12} -> {ticker}")
    print(f"Benchmark    : {BENCHMARK_NAME} ({BENCHMARK})")
    print(f"Period       : {START_DATE} to {END_DATE}")
    print(f"Interval     : {INTERVAL}  ({PERIODS_PER_YEAR} periods/year)")
    print("\nDirectories ready:")
    for d in REQUIRED_DIRS:
        print(f"  - {d}")

    return True


if __name__ == "__main__":
    validate_config()
