import yfinance as yf
import pandas as pd
import numpy as np
import logging
import time
import traceback

def fetch_price_data(symbols, lookback_days=40) -> pd.DataFrame:
    all_data = []

    for symbol in symbols:
        success = False
        
        for attempt in range(3):  # retry loop
            try:
                df = yf.download(
                    symbol,
                    period=f"{lookback_days}d",
                    progress=False
                )
                
                logging.info(f"Fetched data for {symbol}: DF={df} - {len(df)} rows")
                
                if df is not None and not df.empty:
                    success = True
                    df = df[["Close"]].rename(columns={"Close": symbol})
                    all_data.append(df)
                    break  # success → exit retry loop
                
                if df is None or df.empty:
                    logging.warning(f"{symbol}: empty response (attempt {attempt+1}) - DF={df}")
                    time.sleep(2)
                    continue               

            except Exception as e:
                logging.warning(f"{symbol}: failed (attempt {attempt+1}) → {e}")                
                logging.error(f"{symbol}: exception occurred")
                logging.error(traceback.format_exc())
                time.sleep(2)
                
        # After retries, if still not successful, log detailed info
        if not success:
            try:
                import requests
                r = requests.get(f"https://query1.finance.yahoo.com/v7/finance/download/{symbol}")

                logging.error(f"{symbol}: HTTP test status={r.status_code}")
                logging.error(f"{symbol}: response snippet={r.text[:200]}")

            except Exception as e:
                logging.error(f"{symbol}: HTTP test failed: {e}")
            

    if not all_data:
        logging.error("No symbols fetched — skipping run")
        return pd.DataFrame()   #Do NOT crash

    # Merge data
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
