"""訊號層：純量化規則，沒有任何 LLM。輸入 K 線和情緒分數，輸出 BUY / SELL / HOLD。"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..events import Event


def sma(series: pd.Series, n: int) -> pd.Series:
    return series.rolling(n).mean()


def rsi(series: pd.Series, n: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    # 沒有下跌日時 loss 為 0：只要有上漲就是 100，完全沒動才是 50
    out = out.where(loss > 0, np.where(gain > 0, 100.0, 50.0))
    return out.fillna(50.0)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev_close).abs(), (df["low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def compute_signal(df: pd.DataFrame, sentiment: dict | None = None) -> dict:
    """回傳 {side, strength, reason, price, atr, indicators}。

    規則（刻意簡單，重點在流程而不是策略）：
      趨勢：close > SMA50 且 SMA20 > SMA50
      進場：趨勢向上，且（突破 20 日高點 或 回檔到 SMA20 附近且 RSI 40-60）
      出場：close < SMA50，或 RSI > 80，或新聞情緒強烈負面
      情緒：score <= -0.5 且 confidence >= 0.6 → 禁止進場；score >= 0.3 → 強度加分
    """
    if len(df) < 60:
        return {"side": "HOLD", "strength": 0.0, "reason": "資料不足", "price": float(df["close"].iloc[-1]), "atr": 0.0}

    close = df["close"]
    s20, s50 = sma(close, 20), sma(close, 50)
    r = rsi(close)
    a = atr(df)
    hi20 = df["high"].rolling(20).max().shift(1)

    px = float(close.iloc[-1])
    ind = {
        "sma20": float(s20.iloc[-1]), "sma50": float(s50.iloc[-1]),
        "rsi": float(r.iloc[-1]), "atr": float(a.iloc[-1]), "high20": float(hi20.iloc[-1]),
    }
    trend_up = px > ind["sma50"] and ind["sma20"] > ind["sma50"]
    breakout = px >= ind["high20"]
    pullback = trend_up and abs(px - ind["sma20"]) / px < 0.02 and 40 <= ind["rsi"] <= 60

    score = float((sentiment or {}).get("score", 0.0))
    conf = float((sentiment or {}).get("confidence", 0.0))
    sent_block = score <= -0.5 and conf >= 0.6
    sent_boost = score >= 0.3 and conf >= 0.5

    reasons = []
    side = "HOLD"
    strength = 0.0
    if px < ind["sma50"] or ind["rsi"] > 80 or sent_block:
        side = "SELL"
        if px < ind["sma50"]:
            reasons.append("跌破 SMA50")
        if ind["rsi"] > 80:
            reasons.append(f"RSI {ind['rsi']:.0f} 過熱")
        if sent_block:
            reasons.append(f"新聞情緒 {score:+.2f} 強烈負面")
        strength = 1.0
    elif trend_up and (breakout or pullback):
        side = "BUY"
        strength = 0.5
        reasons.append("趨勢向上")
        if breakout:
            reasons.append("突破 20 日高")
            strength += 0.2
        if pullback:
            reasons.append("回檔至 SMA20")
            strength += 0.1
        if sent_boost:
            reasons.append(f"新聞情緒 {score:+.2f} 正面")
            strength += 0.2
        strength = min(strength, 1.0)
    else:
        reasons.append("趨勢向上但無進場點" if trend_up else "趨勢不明")

    return {
        "side": side, "strength": round(strength, 2), "reason": "、".join(reasons),
        "price": px, "atr": ind["atr"], "indicators": {k: round(v, 4) for k, v in ind.items()},
    }


class SignalAgent:
    name = "signal"

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def run(self, bars: dict[str, pd.DataFrame]) -> list[Event]:
        events: list[Event] = []
        stored = self.state.data["signals"]
        for sym, df in bars.items():
            sig = compute_signal(df, self.state.data["sentiment"].get(sym))
            sig["date"] = df.index[-1].date().isoformat()
            prev = stored.get(sym)
            changed = prev is None or prev.get("side") != sig["side"]
            stored[sym] = sig
            if changed and sig["side"] != "HOLD":
                events.append(Event("signal.new", sym, sig))
        self.state.log(self.name, "run", f"{len(bars)} 檔評估, {len(events)} 個新訊號")
        return events
