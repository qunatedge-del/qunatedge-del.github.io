"""資料層：抓 K 線和新聞。只有「新的 K 線」或「沒看過的標題」才會發事件。"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from ..events import Event

BAR_COLUMNS = ["open", "high", "low", "close", "volume"]


def headline_hash(symbol: str, title: str, link: str) -> str:
    return hashlib.sha1(f"{symbol}|{title.strip().lower()}|{link}".encode()).hexdigest()[:16]


def synthetic_bars(symbol: str, days: int, seed: int = 42, end: datetime | None = None) -> pd.DataFrame:
    """離線模式用的隨機漫步 K 線。

    整條序列從固定起點一次產生，再依 end 切窗，所以「把 end 往後推一天」
    看到的是同一條路徑多一根新 K 線，和真實資料的行為一致，測試才能重現多日流程。
    """
    rng = np.random.default_rng(seed + sum(map(ord, symbol)))
    total = 1500
    dates = pd.bdate_range(start="2022-01-03", periods=total)
    rets = rng.normal(loc=0.0004, scale=0.015, size=total)
    close = 100 * np.exp(np.cumsum(rets))
    spread = np.abs(rng.normal(0.008, 0.004, size=total))
    high = close * (1 + spread)
    low = close * (1 - spread)
    open_ = np.concatenate([[close[0]], close[:-1]]) * (1 + rng.normal(0, 0.003, size=total))
    vol = rng.integers(1_000_000, 5_000_000, size=total)
    df = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": vol}, index=dates)
    df.index.name = "date"
    end_ts = pd.Timestamp((end or datetime.now(timezone.utc)).date())
    return df[df.index <= end_ts].tail(days)


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).lower() for c in df.columns]
    df = df[[c for c in BAR_COLUMNS if c in df.columns]].dropna()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "date"
    return df


class DataAgent:
    name = "data"

    def __init__(self, cfg, state, offline: bool = False, seed: int = 42, demo_news: bool = False):
        self.cfg = cfg
        self.state = state
        self.offline = offline
        self.seed = seed
        self.demo_news = demo_news

    # ---- bars -------------------------------------------------------------
    def fetch_bars(self) -> dict[str, pd.DataFrame]:
        if self.offline:
            return {s: synthetic_bars(s, self.cfg.lookback_days, self.seed) for s in self.cfg.watchlist}
        import yfinance as yf  # 延遲載入，離線測試不需要

        raw = yf.download(
            self.cfg.watchlist,
            period=f"{max(self.cfg.lookback_days + 30, 60)}d",
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
        bars: dict[str, pd.DataFrame] = {}
        for sym in self.cfg.watchlist:
            try:
                df = raw[sym] if isinstance(raw.columns, pd.MultiIndex) else raw
                df = _normalize(df)
                if len(df) >= 60:
                    bars[sym] = df.tail(self.cfg.lookback_days)
                else:
                    self.state.alert("warn", f"{sym} 只有 {len(df)} 根 K 線，略過", self.name)
            except Exception as exc:  # noqa: BLE001
                self.state.alert("warn", f"{sym} K 線抓取失敗: {exc}", self.name)
        return bars

    # ---- news -------------------------------------------------------------
    def fetch_news(self) -> list[dict]:
        if self.offline:
            return self._demo_news() if self.demo_news else []
        import yfinance as yf

        items: list[dict] = []
        for sym in self.cfg.watchlist:
            try:
                raw = yf.Ticker(sym).news or []
            except Exception as exc:  # noqa: BLE001
                self.state.alert("warn", f"{sym} 新聞抓取失敗: {exc}", self.name)
                continue
            for n in raw[: self.cfg.llm.max_headlines_per_symbol]:
                item = self._parse_news(sym, n)
                if item:
                    items.append(item)
        return items

    @staticmethod
    def _parse_news(sym: str, n: dict) -> dict | None:
        content = n.get("content", n)  # yfinance 1.x 把欄位包在 content 裡，舊版直接平鋪
        title = content.get("title") or ""
        if not title:
            return None
        link = ""
        url = content.get("canonicalUrl") or content.get("clickThroughUrl") or {}
        if isinstance(url, dict):
            link = url.get("url", "")
        elif isinstance(url, str):
            link = url
        link = link or n.get("link", "")
        provider = content.get("provider") or {}
        publisher = provider.get("displayName") if isinstance(provider, dict) else n.get("publisher", "")
        published = content.get("pubDate") or content.get("displayTime") or ""
        if not published and n.get("providerPublishTime"):
            published = datetime.fromtimestamp(n["providerPublishTime"], tz=timezone.utc).isoformat()
        return {
            "symbol": sym,
            "title": title.strip(),
            "summary": (content.get("summary") or "")[:400],
            "publisher": publisher or "",
            "link": link,
            "published": str(published),
            "hash": headline_hash(sym, title, link),
        }

    def _demo_news(self) -> list[dict]:
        today = datetime.now(timezone.utc).date().isoformat()
        samples = [
            (self.cfg.watchlist[0], "Index funds see record inflows as rate cut hopes build"),
            (self.cfg.watchlist[2], "Company beats quarterly estimates, raises full-year guidance"),
            (self.cfg.watchlist[3], "Regulator opens antitrust probe into cloud pricing practices"),
        ]
        return [
            {
                "symbol": s, "title": t, "summary": "", "publisher": "demo", "link": f"demo://{today}/{i}",
                "published": today, "hash": headline_hash(s, t, f"demo://{today}/{i}"),
            }
            for i, (s, t) in enumerate(samples)
        ]

    # ---- run --------------------------------------------------------------
    def run(self) -> tuple[dict[str, pd.DataFrame], list[Event]]:
        events: list[Event] = []
        bars = self.fetch_bars()
        last_dates = self.state.data["last_bar_date"]
        for sym, df in bars.items():
            latest = df.index[-1].date().isoformat()
            if last_dates.get(sym) != latest:
                last_dates[sym] = latest
                events.append(Event("bar.updated", sym, {"date": latest, "close": float(df["close"].iloc[-1])}))

        seen = self.state.data["seen_news"]
        fresh = []
        for item in self.fetch_news():
            if item["hash"] in seen:
                continue
            seen[item["hash"]] = datetime.now(timezone.utc).date().isoformat()
            fresh.append(item)
        # 只保留 30 天內看過的 hash，避免檔案無限長大
        cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
        for h in [h for h, d in seen.items() if d < cutoff]:
            del seen[h]
        if fresh:
            by_symbol: dict[str, list[dict]] = {}
            for item in fresh:
                by_symbol.setdefault(item["symbol"], []).append(item)
            for sym, items in by_symbol.items():
                events.append(Event("news.new", sym, {"items": items}))

        self.state.log(self.name, "run", f"{len(bars)} 檔 K 線, {len(fresh)} 則新標題, {len(events)} 個事件")
        return bars, events
