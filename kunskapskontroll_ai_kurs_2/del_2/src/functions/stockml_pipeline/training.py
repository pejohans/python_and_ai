
import io
import json
import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from mapie.regression import SplitConformalRegressor

MODEL_FEATURE_COLS = [
    "symbol_id",
    "ret_1d",
    "ret_3d",
    "ret_7d",
    "vol_7d",
    "vol_14d",
    "price_vs_ma5",
    "price_vs_ma10",
]

def build_trainset(
    hist_data: pd.DataFrame,
    symbol_map: dict,
    horizon_days: int = 7,
    lookback: int = 30,
    min_points: int = 20
) -> pd.DataFrame:
    """
    Build a supervised training set from historical close prices.

    Each row corresponds to a time t for a symbol:
      X(t)  = features computed from the last `lookback` days ending at t-1
      y(t)  = target_return = (price[t + horizon_days] / price[t]) - 1

    hist_data:
        DataFrame with index = date, columns = symbols, values = Close prices
    symbol_map:
        dict mapping symbol -> symbol_id (stable)
    """

    rows = []

    # We compute returns per symbol from prices
    # (we do it per symbol below to keep alignment with each symbol's NaNs)
    for sym in hist_data.columns:
        if sym not in symbol_map:
            continue

        prices = hist_data[sym].dropna()
        if len(prices) < (lookback + horizon_days + 1):
            continue

        returns = prices.pct_change()

        # Iterate over time to create many samples per symbol
        # i represents "today index" in the full prices series
        for i in range(lookback, len(prices) - horizon_days):

            # Feature window uses only the past `lookback` days ending at i-1
            window_prices = prices.iloc[i - lookback:i]
            window_returns = returns.iloc[i - lookback:i]

            # Safety: rolling stats need enough data, avoid NaNs
            if len(window_prices) < min_points:
                continue
            if window_prices.isna().any() or window_returns.isna().any():
                continue

            recent_price = window_prices.iloc[-1]
            ma5 = window_prices.rolling(5).mean().iloc[-1]
            ma10 = window_prices.rolling(10).mean().iloc[-1]

            feat = {
                "symbol": sym,
                "symbol_id": int(symbol_map[sym]),
                "as_of_date": prices.index[i].date().isoformat() if hasattr(prices.index[i], "date") else str(prices.index[i]),

                # Keep recent_price for later conversion/debugging (NOT required in model X)
                "recent_price": float(recent_price),

                # Features (same as your EDA)
                "ret_1d": float(window_returns.iloc[-1]),
                "ret_3d": float(window_prices.pct_change(3).iloc[-1]),
                "ret_7d": float(window_prices.pct_change(7).iloc[-1]),
                "vol_7d": float(window_returns.rolling(7).std().iloc[-1]),
                "vol_14d": float(window_returns.rolling(14).std().iloc[-1]),
                "price_vs_ma5": float(recent_price / ma5),
                "price_vs_ma10": float(recent_price / ma10),
            }

            # Label from price at t and t+horizon
            p_t = prices.iloc[i]
            p_f = prices.iloc[i + horizon_days]
            feat["target_return"] = float((p_f / p_t) - 1.0)

            rows.append(feat)

    train_df = pd.DataFrame(rows).dropna()

    # Optional: keep only columns you need + target
    # (But leaving symbol/as_of_date can help debugging)
    return train_df



def train_model(train_df: pd.DataFrame, confidence_level: float = 0.9):
    """
    Train LightGBM model + conformal prediction (MAPIE)
    using proper time-series split.
    """

    # ✅ Features + target
    X = train_df[MODEL_FEATURE_COLS]
    y = train_df["target_return"]

    n = len(X)

    if n < 200:
        raise ValueError(f"Training set too small ({n} rows)")

    # -----------------------------
    # ✅ Time-based split
    # -----------------------------
    train_end = int(n * 0.6)
    cal_end   = int(n * 0.8)

    # -----------------------------
    # Train set (60%)
    # -----------------------------
    X_train = X.iloc[:train_end]
    y_train = y.iloc[:train_end]

    # -----------------------------
    # Calibration set (20%)
    # -----------------------------
    X_cal = X.iloc[train_end:cal_end]
    y_cal = y.iloc[train_end:cal_end]

    # -----------------------------
    # Test set (20%) ← UNSEEN DATA
    # -----------------------------
    X_test = X.iloc[cal_end:]
    y_test = y.iloc[cal_end:]

    # -----------------------------
    # ✅ Train LightGBM (tuned params)
    # -----------------------------
    model = LGBMRegressor(
        learning_rate=0.01,
        max_depth=5,
        n_estimators=100,
        num_leaves=31,
        random_state=42
    )

    model.fit(X_train, y_train)

    # -----------------------------
    # ✅ Conformal prediction (correct usage)
    # -----------------------------
    mapie = SplitConformalRegressor(
        estimator=model,
        confidence_level=confidence_level,
        prefit=True
    )

    mapie.conformalize(X_cal, y_cal)

    # -----------------------------
    # ✅ Evaluate on TEST set
    # -----------------------------
    y_pred_test, y_interval_test = mapie.predict_interval(X_test)
    
    #y_pred = y_pred_test.ravel()

    # RMSE
    #rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_test)))

    # Intervals
    lower = y_interval_test[:, 0, 0]
    upper = y_interval_test[:, 1, 0]
    
    y_true = y_test.values
    coverage = float(np.mean((y_true >= lower) & (y_true <= upper)))
    avg_width = float(np.mean(upper - lower))

    # -----------------------------
    # ✅ Metrics
    # -----------------------------
    metrics = {
        "rmse_test": rmse,
        "coverage_test": coverage,
        "avg_width_test": avg_width,
        "confidence_level": confidence_level,
        "n_train": int(len(X_train)),
        "n_cal": int(len(X_cal)),
        "n_test": int(len(X_test))
    }

    return model, mapie, metrics


def serialize_joblib(obj) -> bytes:
    bio = io.BytesIO()
    joblib.dump(obj, bio)
    return bio.getvalue()
