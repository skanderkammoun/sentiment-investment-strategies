"""
Etape 0 de la Phase 5bis : prix quotidiens des 5 tickers du corpus StockTwits.

NVDA est absent de dataset_finance_hybride_2010_2026.csv -> il faut le collecter.
En interval='1d', yfinance n'a AUCUNE limite d'historique (contrairement a l'intraday :
1m -> 30 jours, 1h -> 730 jours). La collecte quotidienne 2020-2022 est donc triviale.

Sortie : data/raw/finance_2020_2022_5T.csv
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import yfinance as yf

BASE = Path(__file__).resolve().parents[3]
OUT = BASE / "data" / "raw" / "finance_2020_2022_5T.csv"

TICKERS = ["AAPL", "AMZN", "META", "NVDA", "TSLA"]
START, END = "2019-11-01", "2022-04-01"   # marge avant/apres pour les lags et rolling

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)-7s | %(message)s")
log = logging.getLogger("collecte_2020_2022")


def main() -> None:
    frames = []
    for tic in TICKERS:
        log.info("Telechargement %s ...", tic)
        d = yf.download(tic, start=START, end=END, interval="1d",
                        auto_adjust=False, progress=False)
        if d.empty:
            log.error("Aucune donnee pour %s", tic)
            continue
        if isinstance(d.columns, pd.MultiIndex):        # yfinance >= 0.2.51
            d.columns = d.columns.get_level_values(0)
        d = d.reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]]
        d["Ticker"] = tic
        frames.append(d)
        log.info("  %s : %d seances (%s -> %s)", tic, len(d),
                 d["Date"].min().date(), d["Date"].max().date())

    df = pd.concat(frames, ignore_index=True).sort_values(["Ticker", "Date"])
    g = df.groupby("Ticker")
    df["prev_close"] = g["Close"].shift(1)
    df["gap"] = df["Open"] / df["prev_close"] - 1.0
    df["ret_oc"] = (df["Close"] - df["Open"]) / df["Open"]
    df["ret_cc"] = g["Close"].pct_change()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    log.info("Ecrit : %s | %d lignes", OUT.name, len(df))
    log.info("\n%s", df.groupby("Ticker")["Date"].agg(["count", "min", "max"]))


if __name__ == "__main__":
    main()
