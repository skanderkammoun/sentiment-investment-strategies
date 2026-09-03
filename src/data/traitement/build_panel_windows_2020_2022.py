"""
Construction du panel de sentiment par fenetres de seance — Phase 5bis.

Entree  : data/processed/02_StockTwits_SCORED_2020_2022.csv  (3.7M tweets scores FinBERT)
          data/raw/finance_2020_2022_5T.csv  (ou dataset_finance_hybride_2010_2026.csv)
Sortie  : data/processed/PANEL_SENTIMENT_WINDOWS_2020_2022.csv

Principe : le texte horodate est agrege en fenetres calees sur la seance US (Eastern Time),
puis aligne sur les 3 rendements quotidiens naturels (gap / intra-seance / close-to-close).

REGLE ANTI-FUITE : pour une cible realisee a l'instant t, seules les fenetres entierement
anterieures a t sont utilisables. Les colonnes sont suffixees pour rendre cette regle explicite :
  *_night_full  -> utilisable pour gap_J, ret_oc_J, ret_cc_J
  *_open30      -> utilisable pour ret_oc_J, ret_cc_J   (PAS pour gap_J)
  *_mkt, *_post -> CONTEMPORAINES de J : utilisables uniquement en lag (J-1) pour predire J

Auteur : Kammoun Skander — PFE Actuariat & Finance Quantitative
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
BASE = Path(__file__).resolve().parents[3]
SCORED = BASE / "data" / "processed" / "02_StockTwits_SCORED_2020_2022.csv"
FINANCE = BASE / "data" / "raw" / "dataset_finance_hybride_2010_2026.csv"
FINANCE_2020 = BASE / "data" / "raw" / "finance_2020_2022_5T.csv"   # prioritaire si present
OUT = BASE / "data" / "processed" / "PANEL_SENTIMENT_WINDOWS_2020_2022.csv"

TICKERS = ["AAPL", "AMZN", "META", "NVDA", "TSLA"]
DATE_MIN, DATE_MAX = "2020-01-02", "2022-03-04"
CHUNKSIZE = 1_000_000
ROLL_ATTENTION = 20   

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger("panel_windows")


# --------------------------------------------------------------------------- #
# 1. Chargement du corpus score
# --------------------------------------------------------------------------- #
def load_scored(path: Path) -> pd.DataFrame:
    """Charge le CSV de 954 Mo par morceaux en ne gardant que le strict necessaire."""
    cols = ["Ticker", "Jour", "Heure_decimale",
            "FinBERT_Positive", "FinBERT_Negative", "FinBERT_Neutral"]
    parts = []
    for i, ch in enumerate(pd.read_csv(path, usecols=cols, chunksize=CHUNKSIZE,
                                       on_bad_lines="skip", low_memory=False)):
        ch["Heure_decimale"] = pd.to_numeric(ch["Heure_decimale"], errors="coerce")
        for c in ("FinBERT_Positive", "FinBERT_Negative", "FinBERT_Neutral"):
            ch[c] = pd.to_numeric(ch[c], errors="coerce")
        ch = ch.dropna()
        ch = ch[ch["Ticker"].isin(TICKERS)]
        ch = ch[(ch["Heure_decimale"] >= 0) & (ch["Heure_decimale"] < 24)]
        parts.append(ch)
        log.info("chunk %d charge (%d lignes retenues)", i + 1, len(ch))
    df = pd.concat(parts, ignore_index=True)
    df["Jour"] = pd.to_datetime(df["Jour"], errors="coerce")
    df = df.dropna(subset=["Jour"])
    df["net"] = df["FinBERT_Positive"] - df["FinBERT_Negative"]
    log.info("Corpus : %s tweets | %s -> %s",
             f"{len(df):,}", df["Jour"].min().date(), df["Jour"].max().date())
    return df


# --------------------------------------------------------------------------- #
# 2. Decoupage en fenetres de seance (Eastern Time)
# --------------------------------------------------------------------------- #
# Verifie empiriquement : la distribution horaire du corpus pique entre 09h et 16h
# et creuse entre 01h et 05h -> Heure_decimale est bien en ET.
OPEN_H, CLOSE_H, OPEN30_H = 9.5, 16.0, 10.0


def tag_windows(df: pd.DataFrame) -> pd.DataFrame:
    h = df["Heure_decimale"]
    df["win"] = np.select(
        [h < OPEN_H,
         (h >= OPEN_H) & (h < OPEN30_H),
         (h >= OPEN30_H) & (h < CLOSE_H),
         h >= CLOSE_H],
        ["pre", "open30", "mkt_rest", "post"],
        default="na",
    )
    return df


def aggregate(sub: pd.DataFrame, name: str) -> pd.DataFrame:
    """Statistiques de sentiment d'une fenetre, par (Ticker, Jour calendaire)."""
    g = sub.groupby(["Ticker", "Jour"])
    out = pd.DataFrame({
        f"n_{name}":   g["net"].size(),
        f"mu_{name}":  g["net"].mean(),
        f"sd_{name}":  g["net"].std(),          # desaccord des investisseurs
        f"p10_{name}": g["net"].quantile(0.10),
        f"p90_{name}": g["net"].quantile(0.90),
        f"pos_{name}": g["FinBERT_Positive"].mean(),
        f"neg_{name}": g["FinBERT_Negative"].mean(),
    }).reset_index()
    return out


# --------------------------------------------------------------------------- #
# 3. Donnees financieres
# --------------------------------------------------------------------------- #
def load_finance() -> pd.DataFrame:
    path = FINANCE_2020 if FINANCE_2020.exists() else FINANCE
    log.info("Prix quotidiens : %s", path.name)
    fin = pd.read_csv(path, parse_dates=["Date"])
    fin = fin[fin["Ticker"].isin(TICKERS)].copy()
    missing = sorted(set(TICKERS) - set(fin["Ticker"].unique()))
    if missing:
        log.warning("Tickers SANS prix quotidiens : %s "
                    "-> executer d'abord la collecte yfinance (etape 0 du plan)", missing)
    fin = fin.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    grp = fin.groupby("Ticker")
    fin["prev_close"] = grp["Close"].shift(1)
    fin["gap"] = fin["Open"] / fin["prev_close"] - 1.0        # cible M1 (realisee a 09:30)
    fin["ret_oc"] = (fin["Close"] - fin["Open"]) / fin["Open"]  # cible M2 (realisee a 16:00)
    fin["ret_cc"] = grp["Close"].pct_change()                  # cible M3
    fin["prev_ret_cc"] = grp["ret_cc"].shift(1)
    fin["prev_volume"] = grp["Volume"].shift(1)
    fin["vol_20d"] = grp["ret_cc"].transform(
        lambda s: s.shift(1).rolling(20, min_periods=10).std())
    return fin


# --------------------------------------------------------------------------- #
# 4. Fenetre night_full : 16:00 (jour de bourse precedent) -> 09:30 (jour J)
# --------------------------------------------------------------------------- #
def build_night_full(post: pd.DataFrame, pre: pd.DataFrame,
                     fin: pd.DataFrame) -> pd.DataFrame:
    """Somme ponderee des tweets 'post' de tous les jours calendaires separant deux
    seances (week-ends et jours feries inclus) + les tweets 'pre' du jour J."""
    rows = []
    for tic, fs in fin.groupby("Ticker"):
        sessions = fs.sort_values("Date")["Date"].tolist()
        p = post[post["Ticker"] == tic].set_index("Jour").sort_index()
        for i, day in enumerate(sessions):
            if i == 0:
                rows.append({"Ticker": tic, "Date": day,
                             "n_overnight": 0.0, "mu_overnight": np.nan,
                             "sd_overnight": np.nan, "pos_overnight": np.nan,
                             "neg_overnight": np.nan})
                continue
            prev = sessions[i - 1]
            seg = p.loc[(p.index >= prev) & (p.index < day)]
            if seg.empty or seg["n_post"].sum() == 0:
                rows.append({"Ticker": tic, "Date": day, "n_overnight": 0.0,
                             "mu_overnight": np.nan, "sd_overnight": np.nan,
                             "pos_overnight": np.nan, "neg_overnight": np.nan})
                continue
            w = seg["n_post"]
            rows.append({
                "Ticker": tic, "Date": day,
                "n_overnight": float(w.sum()),
                "mu_overnight": float((seg["mu_post"] * w).sum() / w.sum()),
                "sd_overnight": float((seg["sd_post"].fillna(0) * w).sum() / w.sum()),
                "pos_overnight": float((seg["pos_post"] * w).sum() / w.sum()),
                "neg_overnight": float((seg["neg_post"] * w).sum() / w.sum()),
            })
    ov = pd.DataFrame(rows)

    pre_ = pre.rename(columns={"Jour": "Date"})
    ov = ov.merge(pre_, on=["Ticker", "Date"], how="left")

    n_o, n_p = ov["n_overnight"].fillna(0), ov["n_pre"].fillna(0)
    tot = (n_o + n_p).replace(0, np.nan)
    ov["n_night_full"] = n_o + n_p
    ov["mu_night_full"] = (ov["mu_overnight"].fillna(0) * n_o
                           + ov["mu_pre"].fillna(0) * n_p) / tot
    ov["pos_night_full"] = (ov["pos_overnight"].fillna(0) * n_o
                            + ov["pos_pre"].fillna(0) * n_p) / tot
    ov["neg_night_full"] = (ov["neg_overnight"].fillna(0) * n_o
                            + ov["neg_pre"].fillna(0) * n_p) / tot
    ov["sd_night_full"] = (ov["sd_overnight"].fillna(0) * n_o
                           + ov["sd_pre"].fillna(0) * n_p) / tot
    return ov


# --------------------------------------------------------------------------- #
# 5. Pipeline
# --------------------------------------------------------------------------- #
def main() -> None:
    if not SCORED.exists():
        raise FileNotFoundError(f"Corpus score introuvable : {SCORED}")

    df = tag_windows(load_scored(SCORED))
    log.info("Volume par fenetre :\n%s",
             df.groupby(["Ticker", "win"]).size().unstack(fill_value=0))

    pre = aggregate(df[df["win"] == "pre"], "pre")
    op30 = aggregate(df[df["win"] == "open30"], "open30")
    mkt = aggregate(df[df["win"].isin(["open30", "mkt_rest"])], "mkt")
    post = aggregate(df[df["win"] == "post"], "post")

    fin = load_finance()
    fin = fin[(fin["Date"] >= "2019-12-01") & (fin["Date"] <= "2022-03-31")]

    panel = build_night_full(post, pre, fin)

    for tab in (op30, mkt, post):
        panel = panel.merge(tab.rename(columns={"Jour": "Date"}),
                            on=["Ticker", "Date"], how="left")

    panel = fin.merge(panel, on=["Ticker", "Date"], how="left")
    panel = panel.sort_values(["Ticker", "Date"]).reset_index(drop=True)

    # ---- Features derivees ------------------------------------------------- #
    g = panel.groupby("Ticker")
    for w in ("night_full", "open30", "mkt", "post"):
        n = panel[f"n_{w}"].fillna(0)
        panel[f"nlog_{w}"] = np.log1p(n)
        # choc d'attention : volume de messages vs sa moyenne mobile 20 seances (decalee)
        panel[f"nabn_{w}"] = panel[f"nlog_{w}"] - g[f"nlog_{w}"].transform(
            lambda s: s.shift(1).rolling(ROLL_ATTENTION, min_periods=5).mean())
        # dispersion normalisee (desaccord)
        panel[f"disp_{w}"] = panel[f"p90_{w}"] - panel[f"p10_{w}"] \
            if f"p90_{w}" in panel.columns else np.nan

    # dynamique du signal principal
    panel["dmu_night"] = g["mu_night_full"].diff()
    panel["mu_night_ma3"] = g["mu_night_full"].transform(
        lambda s: s.rolling(3, min_periods=2).mean())
    panel["mu_night_z20"] = g["mu_night_full"].transform(
        lambda s: (s - s.shift(1).rolling(20, min_periods=10).mean())
        / s.shift(1).rolling(20, min_periods=10).std())

    # lags des fenetres CONTEMPORAINES (seule facon legale de les utiliser)
    for w in ("mkt", "post"):
        for c in (f"mu_{w}", f"nlog_{w}", f"sd_{w}"):
            panel[f"{c}_lag1"] = g[c].shift(1)

    # cibles binaires
    for tgt, name in (("gap", "y_gap"), ("ret_oc", "y_oc"), ("ret_cc", "y_cc")):
        panel[name] = (panel[tgt] > 0).astype("Int64")
        panel.loc[panel[tgt].isna(), name] = pd.NA

    panel = panel[(panel["Date"] >= DATE_MIN) & (panel["Date"] <= DATE_MAX)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUT, index=False)
    log.info("Panel ecrit : %s | %d lignes x %d colonnes",
             OUT.name, len(panel), panel.shape[1])
    log.info("Couverture :\n%s", panel.groupby("Ticker")["Date"].agg(["count", "min", "max"]))

    # ---- Controle de qualite : correlations attendues ---------------------- #
    log.info("Controle — correlations (doit retrouver ~+0.17 sur gap, ~0.00 sur ret_oc) :")
    for tgt in ("gap", "ret_oc", "ret_cc"):
        s = panel[["mu_night_full", tgt]].dropna()
        log.info("  mu_night_full vs %-7s : rho=%+.4f (n=%d)",
                 tgt, s["mu_night_full"].corr(s[tgt]), len(s))


if __name__ == "__main__":
    main()
