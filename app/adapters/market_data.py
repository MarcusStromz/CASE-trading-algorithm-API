import pandas as pd
import yfinance as yf

def _normalize_yf_df(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["date","open","high","low","close","volume"])

    if isinstance(df.columns, pd.MultiIndex):
        try:
            df = df.xs(ticker, axis=1, level=1, drop_level=True)
        except Exception:
            df.columns = df.columns.get_level_values(0)

    df = df.rename(columns={c: c.title() for c in df.columns})
    df = df[["Open","High","Low","Close","Volume"]].copy()

    df = df.reset_index().rename(columns={"Date": "date"})
    df["date"] = pd.to_datetime(df["date"]).dt.date

    df = df.rename(columns=str.lower)
    for c in ["open","high","low","close","volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df

def fetch_ohlcv_yf(ticker: str, start: str, end: str) -> pd.DataFrame:
    raw = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False, group_by="column")
    return _normalize_yf_df(raw, ticker)
