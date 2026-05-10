import pandas as pd


def compute_features_for_symbol(
    symbol: str,
    window_prices: pd.Series,
    window_returns: pd.Series,
    symbol_id: int,
    as_of_date: str
) -> dict:
    """
    Compute financial features for a single symbol based on price history.
    """

    # -----------------------------
    # ✅ Safety check
    # -----------------------------
    if len(window_prices) < 20:
        raise ValueError(f"Not enough data for {symbol}")

    # -----------------------------
    # ✅ Latest price
    # -----------------------------
    recent_price = window_prices.iloc[-1]

    # -----------------------------
    # ✅ Moving averages
    # -----------------------------
    ma5 = window_prices.rolling(5).mean().iloc[-1]
    ma10 = window_prices.rolling(10).mean().iloc[-1]

    # -----------------------------
    # ✅ Returns
    # -----------------------------
    ret_1d = window_returns.iloc[-1]
    ret_3d = window_prices.pct_change(3).iloc[-1]
    ret_7d = window_prices.pct_change(7).iloc[-1]

    # -----------------------------
    # ✅ Volatility
    # -----------------------------
    vol_7d = window_returns.rolling(7).std().iloc[-1]
    vol_14d = window_returns.rolling(14).std().iloc[-1]

    # -----------------------------
    # ✅ Return feature dict
    # -----------------------------
    return {
        "symbol": symbol,
        "symbol_id": symbol_id,

        # ✅ Model features
        "ret_1d": float(ret_1d),
        "ret_3d": float(ret_3d),
        "ret_7d": float(ret_7d),
        "vol_7d": float(vol_7d),
        "vol_14d": float(vol_14d),
        "price_vs_ma5": float(recent_price / ma5),
        "price_vs_ma10": float(recent_price / ma10),

        # ✅ Needed later for prediction scaling
        "recent_price": float(recent_price),

        "as_of_date": as_of_date
    }