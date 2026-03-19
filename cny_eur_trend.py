"""Plot a 7-day CNY->EUR exchange-rate trend using ECB data.

Data source:
European Central Bank Data API (EXR series D.CNY.EUR.SP00.A)
"""

from __future__ import annotations

import argparse
from io import StringIO

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import requests
import seaborn as sns


ECB_CSV_URL = (
    "https://data-api.ecb.europa.eu/service/data/EXR/"
    "D.CNY.EUR.SP00.A?lastNObservations=30&format=csvdata"
)


def fetch_recent_cny_to_eur(days: int = 7) -> pd.DataFrame:
    """Fetch recent ECB EUR/CNY rates and convert to CNY/EUR."""
    response = requests.get(ECB_CSV_URL, timeout=20)
    response.raise_for_status()

    raw_df = pd.read_csv(StringIO(response.text))

    required_cols = {"TIME_PERIOD", "OBS_VALUE"}
    missing_cols = required_cols - set(raw_df.columns)
    if missing_cols:
        raise ValueError(f"ECB response missing columns: {missing_cols}")

    df = raw_df[["TIME_PERIOD", "OBS_VALUE"]].copy()
    df["Date"] = pd.to_datetime(df["TIME_PERIOD"], errors="coerce")
    df["EUR_to_CNY"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
    df = df.dropna(subset=["Date", "EUR_to_CNY"]).sort_values("Date")

    if df.empty:
        raise ValueError("No valid exchange-rate data returned by ECB API.")

    # Convert from "1 EUR = x CNY" to "1 CNY = y EUR".
    df["CNY_to_EUR"] = 1.0 / df["EUR_to_CNY"]

    recent = df.tail(days).reset_index(drop=True)
    return recent[["Date", "CNY_to_EUR", "EUR_to_CNY"]]


def plot_cny_eur_trend(
    df: pd.DataFrame,
    output_path: str = "cny_eur_7d_trend.png",
    show_plot: bool = True,
) -> None:
    """Plot and save CNY->EUR trend chart."""
    plot_df = df.copy().sort_values("Date")
    window = min(5, len(plot_df))
    rolling = plot_df["CNY_to_EUR"].rolling(window=window, min_periods=2)
    plot_df["RollingMean"] = rolling.mean()
    plot_df["RollingStd"] = rolling.std()
    plot_df["RollingN"] = rolling.count()
    plot_df["RollingSEM"] = (plot_df["RollingStd"] / plot_df["RollingN"].pow(0.5)).fillna(0.0)
    plot_df["CI95"] = 1.96 * plot_df["RollingSEM"]
    plot_df["CI95_LOW"] = plot_df["RollingMean"].fillna(plot_df["CNY_to_EUR"]) - plot_df["CI95"]
    plot_df["CI95_HIGH"] = plot_df["RollingMean"].fillna(plot_df["CNY_to_EUR"]) + plot_df["CI95"]

    sns.set_theme(
        context="paper",
        style="ticks",
        palette="colorblind",
        font_scale=1.1,
        rc={
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "axes.linewidth": 1.2,
            "grid.linestyle": "--",
            "grid.alpha": 0.35,
            "figure.dpi": 120,
        },
    )

    fig, ax = plt.subplots(figsize=(10, 5.2))
    sns.lineplot(
        data=plot_df,
        x="Date",
        y="CNY_to_EUR",
        marker="o",
        linewidth=2.2,
        markersize=6,
        label="Observed CNY/EUR",
        ax=ax,
    )

    ax.plot(
        plot_df["Date"],
        plot_df["RollingMean"],
        color="#1f3b4d",
        linestyle="-.",
        linewidth=1.8,
        label=f"Rolling Mean (window={window})",
    )
    ax.fill_between(
        plot_df["Date"],
        plot_df["CI95_LOW"],
        plot_df["CI95_HIGH"],
        color="#87a8c5",
        alpha=0.25,
        label="95% CI band",
    )

    for x, y in zip(plot_df["Date"], plot_df["CNY_to_EUR"]):
        ax.annotate(f"{y:.4f}", (x, y), textcoords="offset points", xytext=(0, 8), ha="center")

    ax.set_title("CNY to EUR Exchange Rate Trend (Recent 7 Trading Days)", pad=10)
    ax.set_xlabel("Date")
    ax.set_ylabel("1 CNY = ? EUR")
    date_locator = mdates.AutoDateLocator(minticks=5, maxticks=8)
    ax.xaxis.set_major_locator(date_locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(date_locator))
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.4f}"))
    ax.grid(True)
    ax.legend(frameon=False, loc="best")
    sns.despine(ax=ax)
    fig.text(0.99, 0.01, "Source: ECB Data API", ha="right", va="bottom", fontsize=9, alpha=0.8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    if show_plot:
        plt.show()
    else:
        plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot 7-day CNY to EUR trend from ECB API")
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Save figure only, do not open a matplotlib window",
    )
    parser.add_argument(
        "--output",
        default="cny_eur_7d_trend.png",
        help="Output image path (default: cny_eur_7d_trend.png)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = fetch_recent_cny_to_eur(days=7)
    print("Recent CNY->EUR rates from ECB:")
    print(data[["Date", "CNY_to_EUR"]].to_string(index=False))
    plot_cny_eur_trend(data, output_path=args.output, show_plot=not args.no_show)


if __name__ == "__main__":
    main()
