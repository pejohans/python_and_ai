import yfinance as yf
import pandas as pd
import numpy as np
import logging
import time

def fetch_price_data(symbols, lookback_days=40) -> pd.DataFrame:
    all_data = []

    for symbol in symbols:
        for attempt in range(3):  # ✅ retry loop
            try:
                df = yf.download(
                    symbol,
                    period=f"{lookback_days}d",
                    progress=False
                )

                if df is None or df.empty:
                    logging.warning(f"{symbol}: empty response (attempt {attempt+1})")
                    time.sleep(2)
                    continue

                df = df[["Close"]].rename(columns={"Close": symbol})
                all_data.append(df)
                break  # ✅ success → exit retry loop

            except Exception as e:
                logging.warning(f"{symbol}: failed (attempt {attempt+1}) → {e}")
                time.sleep(2)

    if not all_data:
        logging.error("No symbols fetched — skipping run")
        return pd.DataFrame()   # ✅ do NOT crash

    # ✅ merge data
    result = pd.concat(all_data, axis=1)

    logging.info(f"Fetched data for {len(result.columns)} symbols")

    return result


def fetch_recommendations(symbol: str) -> pd.DataFrame:
    """MVP stub: skapar en rekommendations-trend dataframe.

    Byt denna till Finnhub / annan datakälla.
    Krav: kolumner: period, strongBuy, buy, hold, sell, strongSell
    """
    # deterministic pseudo data per symbol
    seed = abs(hash(symbol)) % (2**32)
    rng = np.random.default_rng(seed)

    periods = pd.date_range(end=pd.Timestamp.utcnow().normalize(), periods=6, freq='MS')
    rows = []
    for p in periods:
        sb = int(rng.integers(0, 6))
        b = int(rng.integers(0, 10))
        h = int(rng.integers(0, 10))
        s = int(rng.integers(0, 6))
        ss = int(rng.integers(0, 4))
        rows.append({
            "period": p.strftime('%Y-%m-%d'),
            "strongBuy": sb,
            "buy": b,
            "hold": h,
            "sell": s,
            "strongSell": ss
        })

    return pd.DataFrame(rows)
