import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import PercentFormatter


# ============================================================
# GLOBAL VISUALIZATION SETTINGS
# ============================================================

plt.rcParams.update({
    "figure.dpi": 120,
    "savefig.dpi": 200,
    "font.size": 10,
    "axes.titlesize": 14,
    "axes.labelsize": 11,
    "axes.titleweight": "bold",
    "axes.grid": True,
    "grid.alpha": 0.25,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.frameon": False,
})


def _get_colors(names):
    """Consistent color mapping, dynamic to however many companies are present."""
    cmap = plt.get_cmap("tab10")
    return {name: cmap(i % 10) for i, name in enumerate(names)}


def _prepare_figures_dir(figures_dir):
    os.makedirs(figures_dir, exist_ok=True)


def _save_figure(fig, figures_dir, filename):
    _prepare_figures_dir(figures_dir)
    path = os.path.join(figures_dir, filename)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.show()
    plt.close(fig)
    return path


def _format_date_axis(ax):
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)


def _facet_grid(n, ncols=3, panel_size=(4.2, 3.0)):
    """
    Build a grid of small-multiple subplots — one panel per series — instead
    of overlaying everything on one axis. Extra (unused) panels are hidden.
    """
    ncols = max(1, min(ncols, n))
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=(panel_size[0] * ncols, panel_size[1] * nrows),
        squeeze=False,
    )
    axes_flat = axes.flatten()
    for ax in axes_flat[n:]:
        ax.axis("off")
    return fig, axes_flat[:n]


# ============================================================
# 1. HISTORICAL PRICE (small multiples, shared scale)
# ============================================================

def plot_price_history(price_dict, figures_dir, normalize=True):

    names = list(price_dict.keys())
    colors = _get_colors(names)

    series_map = {}
    for name, df in price_dict.items():
        s = df["Close"].dropna()
        if normalize and not s.empty:
            s = s / s.iloc[0] * 100
        series_map[name] = s

    non_empty = [s for s in series_map.values() if not s.empty]
    if non_empty:
        y_min = min(s.min() for s in non_empty)
        y_max = max(s.max() for s in non_empty)
        pad = (y_max - y_min) * 0.05 or 1
    else:
        y_min, y_max, pad = 0, 1, 0.05

    fig, axes = _facet_grid(len(names), ncols=3)

    for ax, name in zip(axes, names):
        s = series_map[name]
        ax.plot(s.index, s.values, color=colors[name], linewidth=1.8)
        if normalize:
            ax.axhline(100, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
        ax.set_title(name, fontsize=10, fontweight="bold")
        ax.set_ylim(y_min - pad, y_max + pad)
        _format_date_axis(ax)
        ax.tick_params(labelsize=8)

    fig.suptitle(
        "Historical Stock Price" + (" — Normalized to 100, Same Scale" if normalize else ""),
        fontsize=14, y=1.02,
    )
    fig.supylabel("Indexed Price" if normalize else "Price (\u20b9)")
    fig.tight_layout()

    return _save_figure(fig, figures_dir, "01_price_history.png")


# ============================================================
# 2. GROWTH OF \u20b91 (small multiples, shared scale)
# ============================================================

def plot_growth_of_one_rupee(returns_dict, figures_dir):

    names = list(returns_dict.keys())
    colors = _get_colors(names)

    wealth_map = {name: (1 + r.dropna()).cumprod() for name, r in returns_dict.items()}
    non_empty = [w for w in wealth_map.values() if not w.empty]
    y_max = max((w.max() for w in non_empty), default=1)

    fig, axes = _facet_grid(len(names), ncols=3)

    for ax, name in zip(axes, names):
        w = wealth_map[name]
        ax.plot(w.index, w.values, color=colors[name], linewidth=1.8)
        ax.axhline(1, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
        ax.set_ylim(0, y_max * 1.05)
        final_val = w.iloc[-1] if not w.empty else float("nan")
        ax.set_title(f"{name}  (\u20b9{final_val:.2f})", fontsize=10, fontweight="bold")
        _format_date_axis(ax)
        ax.tick_params(labelsize=8)

    fig.suptitle("Growth of \u20b91 Investment — Same Scale Across Companies", fontsize=14, y=1.02)
    fig.supylabel("Portfolio Value (\u20b9)")
    fig.tight_layout()

    return _save_figure(fig, figures_dir, "02_growth_of_one_rupee.png")


# ============================================================
# GENERIC BAR CHART (unchanged — already clear with one bar per company)
# ============================================================

def _bar_chart(series, title, ylabel, figures_dir, filename, pct=True, horizontal=True, xlabel=None):

    series = series.dropna().sort_values()
    colors = _get_colors(series.index)

    fig, ax = plt.subplots(figsize=(10, 6))

    if horizontal:
        bars = ax.barh(series.index, series.values, color=[colors[n] for n in series.index])
        if pct:
            ax.xaxis.set_major_formatter(PercentFormatter(xmax=1))
        for bar, value in zip(bars, series.values):
            ax.text(value, bar.get_y() + bar.get_height() / 2,
                    f" {value:.2%}" if pct else f" {value:.2f}", va="center", fontsize=9)
    else:
        bars = ax.bar(series.index, series.values, color=[colors[n] for n in series.index])
        if pct:
            ax.yaxis.set_major_formatter(PercentFormatter(xmax=1))
        for bar, value in zip(bars, series.values):
            ax.text(bar.get_x() + bar.get_width() / 2, value,
                    f"{value:.2%}" if pct else f"{value:.2f}", ha="center", va="bottom", fontsize=9)
        plt.xticks(rotation=30, ha="right")

    ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x" if horizontal else "y", alpha=0.25)
    fig.tight_layout()

    return _save_figure(fig, figures_dir, filename)


# 3. CAGR
def plot_cagr_comparison(comparison_df, figures_dir):
    return _bar_chart(comparison_df["CAGR"], "Compound Annual Growth Rate (CAGR)", "Company",
                       figures_dir, "03_cagr_comparison.png", pct=True, horizontal=True)


# 4. VOLATILITY
def plot_volatility_comparison(comparison_df, figures_dir):
    return _bar_chart(comparison_df["Annualized Volatility"], "Annualized Volatility", "Company",
                       figures_dir, "04_volatility_comparison.png", pct=True, horizontal=True)


# 5. MAXIMUM DRAWDOWN (bar summary — kept alongside the new faceted curves below)
def plot_drawdown_comparison(comparison_df, figures_dir):
    return _bar_chart(comparison_df["Max Drawdown"], "Maximum Drawdown", "Company",
                       figures_dir, "05_drawdown_comparison.png", pct=True, horizontal=True)


# ============================================================
# 6. RISK VS RETURN (unchanged — 6 labeled points is already clear)
# ============================================================

def plot_risk_return_scatter(comparison_df, figures_dir):

    colors = _get_colors(comparison_df.index)
    fig, ax = plt.subplots(figsize=(10, 7))

    x = comparison_df["Annualized Volatility"]
    y = comparison_df["CAGR"]

    for name in comparison_df.index:
        ax.scatter(x[name], y[name], s=130, color=colors[name], edgecolor="black", linewidth=0.7, zorder=3)
        ax.annotate(name, (x[name], y[name]), xytext=(8, 8), textcoords="offset points",
                    fontsize=9, fontweight="bold")

    ax.xaxis.set_major_formatter(PercentFormatter(xmax=1))
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1))
    ax.set_xlabel("Annualized Volatility")
    ax.set_ylabel("CAGR")
    ax.set_title("Risk vs Return Profile")
    ax.grid(alpha=0.25)
    fig.tight_layout()

    return _save_figure(fig, figures_dir, "06_risk_return_scatter.png")


# 7. CORRELATION WITH BENCHMARK (unchanged)
def plot_correlation_with_benchmark(comparison_df, figures_dir):

    series = comparison_df["Correlation"].dropna().sort_values()
    colors = _get_colors(series.index)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(series.index, series.values, color=[colors[n] for n in series.index])
    ax.set_xlim(-1, 1)
    ax.axvline(0, color="black", linewidth=1)
    for bar, value in zip(bars, series.values):
        ax.text(value, bar.get_y() + bar.get_height() / 2, f" {value:.2f}", va="center", fontsize=9)
    ax.set_title("Correlation with Benchmark")
    ax.set_xlabel("Correlation Coefficient")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()

    return _save_figure(fig, figures_dir, "07_correlation_comparison.png")


# 8. BETA (unchanged)
def plot_beta_comparison(comparison_df, figures_dir):

    series = comparison_df["Beta (Regression)"].dropna().sort_values()
    colors = _get_colors(series.index)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(series.index, series.values, color=[colors[n] for n in series.index])
    ax.axvline(1, color="gray", linestyle="--", linewidth=1.5, label="Market Beta = 1")
    for bar, value in zip(bars, series.values):
        ax.text(value, bar.get_y() + bar.get_height() / 2, f" {value:.2f}", va="center", fontsize=9)
    ax.set_title("Beta Comparison")
    ax.set_xlabel("Beta")
    ax.legend()
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()

    return _save_figure(fig, figures_dir, "08_beta_comparison.png")


# ============================================================
# 9. DRAWDOWN CURVES (small multiples, shared scale — the crowded one)
# ============================================================

def plot_drawdown_curves(returns_dict, figures_dir):

    names = list(returns_dict.keys())
    colors = _get_colors(names)

    drawdowns = {}
    for name, returns in returns_dict.items():
        r = returns.dropna()
        wealth = (1 + r).cumprod()
        drawdowns[name] = wealth / wealth.cummax() - 1

    non_empty = [dd for dd in drawdowns.values() if not dd.empty]
    y_min = min((dd.min() for dd in non_empty), default=-0.1)

    fig, axes = _facet_grid(len(names), ncols=3)

    for ax, name in zip(axes, names):
        dd = drawdowns[name]
        ax.fill_between(dd.index, dd.values, 0, color=colors[name], alpha=0.35)
        ax.plot(dd.index, dd.values, color=colors[name], linewidth=1.4)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_ylim(y_min * 1.05, 0.02)
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1))
        worst = dd.min() if not dd.empty else float("nan")
        ax.set_title(f"{name}  (max {worst:.1%})", fontsize=10, fontweight="bold")
        _format_date_axis(ax)
        ax.tick_params(labelsize=8)

    fig.suptitle("Historical Drawdown — Same Scale Across Companies", fontsize=14, y=1.02)
    fig.supylabel("Drawdown")
    fig.tight_layout()

    return _save_figure(fig, figures_dir, "09_drawdown_curves.png")


# ============================================================
# 10. CORRELATION HEATMAP (unchanged — a matrix, not a line overlay)
# ============================================================

def plot_correlation_heatmap(returns_dict, figures_dir):

    combined = pd.DataFrame(returns_dict)
    corr = combined.corr()
    n = len(corr)
    fig_size = max(7, n * 1.2)

    fig, ax = plt.subplots(figsize=(fig_size, fig_size))
    im = ax.imshow(corr, cmap="RdYlGn", vmin=-1, vmax=1)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr.index)

    for i in range(n):
        for j in range(n):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=9, fontweight="bold")

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Correlation")
    ax.set_title("Company Return Correlation Matrix")
    fig.tight_layout()

    return _save_figure(fig, figures_dir, "10_correlation_heatmap.png")


# ============================================================
# GENERATE ALL VISUALIZATIONS
# ============================================================

def generate_all_visualizations(price_dict, company_returns_dict, comparison_df, figures_dir):

    paths = [
        plot_price_history(price_dict, figures_dir),
        plot_growth_of_one_rupee(company_returns_dict, figures_dir),
        plot_cagr_comparison(comparison_df, figures_dir),
        plot_volatility_comparison(comparison_df, figures_dir),
        plot_drawdown_comparison(comparison_df, figures_dir),
        plot_risk_return_scatter(comparison_df, figures_dir),
        plot_correlation_with_benchmark(comparison_df, figures_dir),
        plot_beta_comparison(comparison_df, figures_dir),
        plot_drawdown_curves(company_returns_dict, figures_dir),
        plot_correlation_heatmap(company_returns_dict, figures_dir),
    ]
    return paths