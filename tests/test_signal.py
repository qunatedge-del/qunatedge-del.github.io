import numpy as np
import pandas as pd

from agent_desk.agents.data import synthetic_bars
from agent_desk.agents.signal import atr, compute_signal, rsi, sma


def trending(n=120, drift=0.01, start=100.0):
    """有漲有跌的趨勢序列：drift 決定方向，正弦波讓 RSI 不會卡在 0 或 100。"""
    k = np.arange(n)
    rets = drift + 0.006 * np.sin(k * 1.3)
    close = start * np.cumprod(1 + rets)
    idx = pd.bdate_range("2025-01-01", periods=n)
    return pd.DataFrame({"open": close, "high": close * 1.002, "low": close * 0.998, "close": close, "volume": 1e6}, index=idx)


def breakout_df(drift=0.001):
    """溫和上升趨勢，最後一根 K 線突破 20 日高。"""
    df = trending(drift=drift)
    new_high = df["high"].iloc[-21:-1].max() * 1.005
    df.iloc[-1, df.columns.get_loc("close")] = new_high
    df.iloc[-1, df.columns.get_loc("high")] = new_high * 1.001
    return df


def test_indicators_shapes():
    df = synthetic_bars("TEST", 100)
    assert len(sma(df["close"], 20)) == 100
    assert 0 <= rsi(df["close"]).iloc[-1] <= 100
    assert atr(df).iloc[-1] > 0


def test_uptrend_breakout_is_buy_unless_rsi_overheated():
    df = breakout_df()
    sig = compute_signal(df)
    assert sig["side"] == "BUY"
    assert "突破 20 日高" in sig["reason"]
    assert 0 < sig["strength"] <= 1


def test_steep_uptrend_flags_rsi_exit():
    sig = compute_signal(trending(drift=0.01))
    assert sig["side"] == "SELL" and "RSI" in sig["reason"]


def test_downtrend_is_sell():
    sig = compute_signal(trending(drift=-0.005))
    assert sig["side"] == "SELL" and "SMA50" in sig["reason"]


def test_negative_sentiment_blocks_entry():
    df = breakout_df()
    assert compute_signal(df)["side"] == "BUY"
    sig = compute_signal(df, {"score": -0.8, "confidence": 0.9})
    assert sig["side"] == "SELL" and "負面" in sig["reason"]


def test_positive_sentiment_boosts_strength():
    df = breakout_df()
    base = compute_signal(df)["strength"]
    boosted = compute_signal(df, {"score": 0.6, "confidence": 0.8})["strength"]
    assert boosted > base


def test_too_little_data_holds():
    assert compute_signal(trending(n=30))["side"] == "HOLD"
