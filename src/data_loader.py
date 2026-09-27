"""
Data acquisition for the Industry Risk & Return Analysis project.

Handles downloading price data for every company + the benchmark, saving
it to data/raw/, and reloading it in a clean, consistent shape.

Why save-then-reload instead of using the in-memory download directly?
Two reasons: (1) it matches "save raw data separately from processed data"
from the project spec, so we always have the untouched source on disk,
and (2) yfinance's CSV export for a ticker with auto_adjust=True writes a
multi-row header (a "Price" row, a "Ticker" row, then the real header)
that must be corrected on reload — the same fix your original Reliance
notebook applied ("Price" column renamed to "Date", first two rows
skipped). Centralizing that fix here means every caller gets clean data
automatically, instead of re-applying the fix ad hoc in every notebook.
"""

import os
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None  # allows the module to be imported/tested without yfinance installed


def download_stock_data(ticker, start, end, interval, auto_adjust, raw_dir):
    """
    Download one ticker's OHLCV history via yfinance and save it as a raw CSV.

    Parameters
    ----------
    ticker : str            e.g. "RELIANCE.NS" or "^NSEI"
    start, end : str        "YYYY-MM-DD"
    interval : str          e.g. "1mo"
    auto_adjust : bool      whether yfinance should adjust for splits/bonuses/dividends
    raw_dir : str           directory to write the raw CSV into

    Returns
    -------
    str : path to the saved raw CSV
    """
    if yf is None:
        raise ImportError("yfinance is not installed. Run: pip install yfinance")

    df = yf.download(
        ticker, start=start, end=end, interval=interval,
        auto_adjust=auto_adjust, progress=False,
    )
    if df.empty:
        raise ValueError(f"yfinance returned no data for {ticker} ({start} to {end})")

    safe_name = ticker.replace("^", "").replace(".", "_")
    raw_path = os.path.join(raw_dir, f"{safe_name}.csv")
    df.to_csv(raw_path)
    return raw_path


def load_price_csv(path):
    """
    Reload a raw CSV saved by download_stock_data(), correcting the known
    yfinance header quirk: row 0 is the real header, but rows 1-2 are an
    extra "Ticker" row and a blank/"Date" row rather than data, and the
    date column is labeled "Price" rather than "Date".

    """
    df = pd.read_csv(path, skiprows=[1, 2])
    df = df.rename(columns={"Price": "Date"})
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    for col in ("Open", "High", "Low", "Close", "Volume"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def download_all(companies, benchmark, benchmark_name, start, end, interval,
                  auto_adjust, raw_dir):
    """
    Download every company plus the benchmark, using identical settings
    for all of them, and return {name: DataFrame} with clean OHLCV data.

    `companies` is the {company_name: ticker} dict from config.COMPANIES.
    The benchmark is added under `benchmark_name` so downstream code can
    treat it just like any other series in the dict.
    """
    universe = dict(companies)
    universe[benchmark_name] = benchmark

    data = {}
    for name, ticker in universe.items():
        raw_path = download_stock_data(ticker, start, end, interval, auto_adjust, raw_dir)
        data[name] = load_price_csv(raw_path)
    return data
