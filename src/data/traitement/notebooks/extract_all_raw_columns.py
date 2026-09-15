import os, glob, re, html, gc, ast
import numpy as np
import pandas as pd

PROJECT = r"C:\Users\semy4\OneDrive\Bureau\Fintech_project"
RAW_DIR = os.path.join(PROJECT, "data", "raw", "source_data_trouve_stocktwits", "StockTwits_2020_2022_Raw")
OUTPUT_PATH = os.path.join(PROJECT, "data", "processed", "StockTwits_ALL_RAW_COLUMNS_2020_2022.csv")
FOLDERS = ["AAPL_2020_2022", "AMZN2019-2022", "FB_2019_2022", "NVDA_2013_2022", "TSLA_2020_2022"]
VALID_TICKERS = {"AAPL", "AMZN", "META", "NVDA", "TSLA"}
SYMBOL_RE = re.compile(r"['\"]symbol['\"]\s*[:=]\s*['\"]([A-Z]+)['\"]")
CASHTAG_RE = re.compile(r"\$([A-Z]{1,5})\b")
assert os.path.isdir(RAW_DIR), RAW_DIR

CANONICAL = ["id", "body", "created_at", "user", "source", "symbols", "owned_symbols",
             "mentioned_users", "entities", "conversation", "likes", "links",
             "reshares", "reshare_message"]

def ticker_from_row(symbols, body):
    symbols = "" if pd.isna(symbols) else str(symbols)
    body = "" if pd.isna(body) else str(body)
    match = SYMBOL_RE.search(symbols) or CASHTAG_RE.search(body.upper())
    ticker = match.group(1) if match else ""
    ticker = "META" if ticker == "FB" else ticker
    return ticker if ticker in VALID_TICKERS else np.nan

def native_label(value):
    if pd.isna(value):
        return np.nan
    try:
        parsed = ast.literal_eval(str(value))
        sentiment = parsed.get("sentiment") if isinstance(parsed, dict) else None
        basic = sentiment.get("basic") if isinstance(sentiment, dict) else None
        if basic == "Bullish":
            return "positive"
        if basic == "Bearish":
            return "negative"
    except (ValueError, SyntaxError):
        pass
    return np.nan

def read_raw(path):
    available = pd.read_csv(path, nrows=0).columns
    cols = [c for c in CANONICAL if c in available]
    df = pd.read_csv(path, usecols=cols)
    symbols = df.get("symbols", pd.Series("", index=df.index))
    body = df.get("body", pd.Series("", index=df.index))
    df["Ticker"] = [ticker_from_row(s, b) for s, b in zip(symbols, body)]
    if "entities" in df.columns:
        df["native_label"] = df["entities"].map(native_label)
    else:
        df["native_label"] = np.nan
    return df

paths = []
for folder in FOLDERS:
    paths.extend(glob.glob(os.path.join(RAW_DIR, folder, "*.csv")))

COLS = CANONICAL + ["Ticker", "native_label", "Jour", "Heure_decimale"]

first = True
total = 0
for i, path in enumerate(paths):
    part = read_raw(path)
    if part.empty:
        continue
    part["Date"] = pd.to_datetime(part["created_at"], utc=True, errors="coerce")
    part = part.dropna(subset=["Date", "body"])
    part = part.drop_duplicates(subset=["Date", "body", "Ticker"], keep="first")
    part["Date_NY"] = part["Date"].dt.tz_convert("America/New_York")
    part = part[part["Date_NY"].dt.year.isin([2020, 2021, 2022])].copy()
    part["Jour"] = part["Date_NY"].dt.date.astype(str)
    part["Heure_decimale"] = part["Date_NY"].dt.hour + part["Date_NY"].dt.minute / 60
    part = part.drop(columns=["Date", "Date_NY"])
    part = part.reindex(columns=COLS)
    part.to_csv(OUTPUT_PATH, mode="a", header=first, index=False)
    first = False
    total += len(part)
    del part
    gc.collect()
    if (i + 1) % 20 == 0:
        print(f"{i+1}/{len(paths)} fichiers, {total:,} lignes")

print(f"{len(paths)} fichiers, {total:,} lignes")
print("Export :", OUTPUT_PATH)