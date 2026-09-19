"""持久化狀態：單一 JSON 檔，原子寫入。所有代理只透過這裡讀寫。"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_state(initial_cash: float) -> dict:
    return {
        "version": 1,
        "created": now_iso(),
        "updated": now_iso(),
        "initial_cash": initial_cash,
        "cash": initial_cash,
        "peak_equity": initial_cash,
        "positions": {},        # symbol -> {qty, avg_price, opened, stop, target, last_price, entry_atr}
        "trades": [],           # 成交紀錄
        "pending": [],          # 待人工審核的單
        "equity_curve": [],     # 每交易日一筆 {date, equity, cash, exposure, daily_pnl, drawdown}
        "kill_switch": {"active": False, "reason": "", "since": ""},
        "seen_news": {},        # headline hash -> date
        "sentiment": {},        # symbol -> {score, confidence, event_type, rationale, updated, n_headlines}
        "signals": {},          # symbol -> {side, strength, reason, date, price, atr}
        "cooldown": {},         # symbol -> 可再進場日期
        "last_bar_date": {},    # symbol -> 最新 K 線日期
        "last_report_date": "",
        "llm_usage": {"date": "", "calls": 0, "input_tokens": 0, "output_tokens": 0, "est_cost_usd": 0.0},
        "reports": [],          # 最近 30 份日報
        "alerts": [],           # 最近 100 筆告警
        "run_log": [],          # 最近 300 筆代理執行紀錄
        "next_id": 1,
    }


class StateStore:
    def __init__(self, path: Path, initial_cash: float):
        self.path = Path(path)
        self.initial_cash = initial_cash
        self.data = self.load()

    def load(self) -> dict:
        if self.path.exists():
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            base = default_state(self.initial_cash)
            for key, value in base.items():
                data.setdefault(key, value)
            return data
        return default_state(self.initial_cash)

    def save(self) -> None:
        self.data["updated"] = now_iso()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".state-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=1, default=str)
        os.replace(tmp, self.path)

    def reset(self) -> None:
        self.data = default_state(self.initial_cash)
        self.save()

    # ---- helpers -------------------------------------------------------
    def new_id(self, prefix: str) -> str:
        n = self.data["next_id"]
        self.data["next_id"] = n + 1
        return f"{prefix}-{n:05d}"

    def log(self, agent: str, event: str, detail: str = "") -> None:
        entry = {"ts": now_iso(), "agent": agent, "event": event, "detail": detail}
        self.data["run_log"].append(entry)
        self.data["run_log"] = self.data["run_log"][-300:]

    def alert(self, level: str, msg: str, agent: str = "monitor") -> None:
        entry = {"ts": now_iso(), "level": level, "msg": msg, "agent": agent}
        self.data["alerts"].append(entry)
        self.data["alerts"] = self.data["alerts"][-100:]
        self.log(agent, f"alert.{level}", msg)

    def positions(self) -> dict:
        return self.data["positions"]

    def equity(self, prices: dict[str, float] | None = None) -> float:
        prices = prices or {}
        total = self.data["cash"]
        for sym, pos in self.data["positions"].items():
            px = prices.get(sym, pos.get("last_price", pos["avg_price"]))
            total += pos["qty"] * px
        return total

    def exposure(self, prices: dict[str, float] | None = None) -> float:
        prices = prices or {}
        return sum(
            abs(pos["qty"]) * prices.get(sym, pos.get("last_price", pos["avg_price"]))
            for sym, pos in self.data["positions"].items()
        )

    def today_pnl(self) -> float:
        curve = self.data["equity_curve"]
        return curve[-1]["daily_pnl"] if curve else 0.0

    def drawdown(self) -> float:
        curve = self.data["equity_curve"]
        return curve[-1]["drawdown"] if curve else 0.0
