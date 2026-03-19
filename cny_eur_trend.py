"""Plot a 7-day CNY->EUR exchange-rate trend using ECB data.

Data source:
European Central Bank Data API (EXR series D.CNY.EUR.SP00.A)
"""

from __future__ import annotations

import argparse
from io import StringIO

import matplotlib.pyplot as plt
import pandas as pd
import requests


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
    plt.figure(figsize=(10, 5))
    plt.plot(df["Date"], df["CNY_to_EUR"], marker="o", linewidth=2)

    for x, y in zip(df["Date"], df["CNY_to_EUR"]):
        plt.annotate(f"{y:.4f}", (x, y), textcoords="offset points", xytext=(0, 8), ha="center")

    plt.title("CNY to EUR Exchange Rate Trend (Recent 7 Trading Days)")
    plt.xlabel("Date")
    plt.ylabel("1 CNY = ? EUR")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
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
