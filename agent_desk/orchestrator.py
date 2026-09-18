"""總控：一次 run_cycle 就是一個交易日的完整流程。

  DataAgent → (news.new) SentimentAgent → SignalAgent → RiskAgent
  → PaperBroker（出場自動、進場排隊審核）→ mark-to-market
  → MonitorAgent → (bar.updated 且今日未寫) ReportAgent → 匯出 dashboard JSON
"""
from __future__ import annotations

from datetime import datetime, timezone

from .agents.data import DataAgent
from .agents.execution import PaperBroker
from .agents.reporter import MonitorAgent, ReportAgent
from .agents.risk import RiskAgent
from .agents.sentiment import SentimentAgent, stale_sentiment
from .agents.signal import SignalAgent
from .config import Config
from .events import Event, filter_events
from .export import export_dashboard
from .llm import LLMClient
from .state import StateStore


class Desk:
    def __init__(self, cfg: Config, state: StateStore, offline: bool = False,
                 seed: int = 42, demo_news: bool = False):
        self.cfg = cfg
        self.state = state
        self.llm = LLMClient(cfg, state)
        self.data = DataAgent(cfg, state, offline=offline, seed=seed, demo_news=demo_news)
        self.sentiment = SentimentAgent(cfg, state, self.llm)
        self.signal = SignalAgent(cfg, state)
        self.risk = RiskAgent(cfg, state)
        self.broker = PaperBroker(cfg, state)
        self.monitor = MonitorAgent(cfg, state, self.llm)
        self.report = ReportAgent(cfg, state, self.llm)
        self.mode = "paper-offline-demo" if offline else "paper"

    # ------------------------------------------------------------------------
    def run_cycle(self, write: bool = True) -> dict:
        s = self.state
        s.log("desk", "cycle.start", f"llm={'on' if self.llm.available else 'off'} calls_left={self.llm.calls_left()}")
        events: list[Event] = []

        bars, ev = self.data.run()
        events += ev
        if not bars:
            s.alert("critical", "沒有任何 K 線資料，本輪中止", "desk")
            if write:
                s.save()
            return {"today": "", "events": [e.type for e in events], "snapshot": None}

        today = max(df.index[-1] for df in bars.values()).date().isoformat()
        prices = {sym: float(df["close"].iloc[-1]) for sym, df in bars.items()}

        # 過期的情緒不該再影響訊號
        for sym, entry in list(s.data["sentiment"].items()):
            if stale_sentiment(entry, today):
                entry["score"], entry["confidence"] = 0.0, 0.0

        events += self.sentiment.run(events)          # 只在 news.new 時喚醒 LLM
        events += self.signal.run(bars)               # 純規則
        expired = self.broker.expire_pending(today)
        events += [Event("order.expired", o["symbol"], o) for o in expired]

        # 先處理出場（自動），再看進場
        events += self.broker.check_exits(bars, s.data["signals"], today)

        equity = s.equity(prices)
        self.risk.check_kill_switch(equity)
        today_pnl = equity - self._prev_close_equity(today)   # 用最新價估今天到目前的損益

        for e in filter_events(events, "signal.new"):
            if e.payload["side"] != "BUY":
                continue
            d = self.risk.evaluate_entry(e.symbol, e.payload["price"], e.payload["atr"], equity, today_pnl, today)
            if not d.approved:
                s.log("risk", "entry.blocked", f"{e.symbol}: {'; '.join(d.reasons)}")
                events.append(Event("risk.blocked", e.symbol, {"reasons": d.reasons}))
                continue
            reason = f"{e.payload['reason']}｜{d.reasons[0]}"
            if self.cfg.approval_required:
                order = self.broker.propose(e.symbol, "BUY", d.qty, e.payload["price"], reason,
                                            stop=d.stop, target=d.target, today=today)
                order["atr"] = e.payload["atr"]
                events.append(Event("order.proposed", e.symbol, order))
            else:
                order = {"id": s.new_id("ORD"), "trade_date": today, "symbol": e.symbol, "side": "BUY",
                         "qty": d.qty, "stop": d.stop, "target": d.target, "reason": reason, "atr": e.payload["atr"]}
                events.append(Event("order.filled", e.symbol, self.broker.execute(order, e.payload["price"], "自動核准")))

        snap = self.broker.mark_to_market(prices, today)
        self.risk.check_kill_switch(snap["equity"])
        alerts = self.monitor.run(snap, bars, today)

        report = None
        if self.report.due(today, events):
            report = self.report.run(snap, alerts, today, events)

        s.log("desk", "cycle.end", f"{len(events)} 個事件, equity {snap['equity']:,.0f}")
        if write:
            s.save()
            export_dashboard(self.cfg, s, bars, mode=self.mode)
        return {"today": today, "events": [f"{e.type}:{e.symbol}" for e in events],
                "snapshot": snap, "alerts": alerts, "report": report,
                "pending": self.broker.pending()}

    def _prev_close_equity(self, today: str) -> float:
        curve = self.state.data["equity_curve"]
        for snap in reversed(curve):
            if snap["date"] != today:
                return snap["equity"]
        return self.state.data["initial_cash"]

    # ---- 人工閘門 -------------------------------------------------------------
    def approve(self, order_id: str) -> dict | None:
        fill = self.broker.approve(order_id)
        self._after_manual()
        return fill

    def reject(self, order_id: str, note: str = "") -> bool:
        ok = self.broker.reject(order_id, note)
        self._after_manual()
        return ok

    def set_kill_switch(self, active: bool, reason: str = "人工") -> None:
        ks = self.state.data["kill_switch"]
        ks.update({"active": active, "reason": reason if active else "",
                   "since": datetime.now(timezone.utc).isoformat() if active else ""})
        self.state.log("desk", "killswitch", "啟動" if active else "解除")
        if active:
            self.state.data["peak_equity"] = self.state.data["peak_equity"]
        else:
            # 人工解除時把 peak 重設為目前權益，否則下一輪又會被同一個回撤觸發
            self.state.data["peak_equity"] = self.state.equity()
        self._after_manual()

    def _after_manual(self) -> None:
        curve = self.state.data["equity_curve"]
        if curve:
            prices = {s: p["last_price"] for s, p in self.state.data["positions"].items()}
            self.broker.mark_to_market(prices, curve[-1]["date"])
        self.state.save()
        export_dashboard(self.cfg, self.state, {}, mode=self.mode)
