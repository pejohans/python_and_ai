
import pandas as pd
import numpy as np


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
