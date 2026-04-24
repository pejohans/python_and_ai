
import pandas as pd


def compute_features_for_symbol(symbol: str, reco_df: pd.DataFrame, as_of_date: str) -> dict:
    """MVP features baserade på senaste och föregående rekommendationsperiod."""
    reco_df = reco_df.sort_values("period")
    latest = reco_df.iloc[-1]
    prev = reco_df.iloc[-2] if len(reco_df) >= 2 else latest

    cols = ["strongBuy","buy","hold","sell","strongSell"]
    total = float(latest[cols].sum()) if float(latest[cols].sum()) > 0 else 1.0

    pos = float(latest["strongBuy"] + latest["buy"]) / total
    neg = float(latest["sell"] + latest["strongSell"]) / total
    net = (float(latest["strongBuy"] + latest["buy"]) - float(latest["sell"] + latest["strongSell"])) / total

    prev_pos = float(prev["strongBuy"] + prev["buy"]) / (float(prev[cols].sum()) if float(prev[cols].sum()) > 0 else 1.0)

    return {
        "symbol": symbol,
        "reco_pos": pos,
        "reco_neg": neg,
        "reco_net": net,
        "reco_pos_delta": pos - prev_pos,
        "as_of_date": as_of_date
    }
