"""風控：純程式碼、硬上限。這一層永遠不呼叫 LLM，也永遠不能被其他代理繞過。"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class Decision:
    approved: bool
    qty: int = 0
    stop: float = 0.0
    target: float = 0.0
    notional: float = 0.0
    reasons: list[str] = field(default_factory=list)


class RiskAgent:
    name = "risk"

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.limits = cfg.risk
        self.state = state

    # ---- kill switch --------------------------------------------------------
    def check_kill_switch(self, equity: float) -> bool:
        ks = self.state.data["kill_switch"]
        if ks["active"]:
            return True
        peak = max(self.state.data["peak_equity"], equity)
        dd = (peak - equity) / peak if peak > 0 else 0.0
        if dd >= self.limits.max_drawdown_pct:
            from ..state import now_iso

            ks.update({"active": True, "since": now_iso(),
                       "reason": f"回撤 {dd:.1%} 達上限 {self.limits.max_drawdown_pct:.0%}"})
            self.state.alert("critical", f"KILL SWITCH 啟動：{ks['reason']}，停止所有新進場，需人工解除", self.name)
            return True
        return False

    # ---- entry sizing -------------------------------------------------------
    def evaluate_entry(self, symbol: str, price: float, atr_value: float, equity: float,
                       today_pnl: float, today: str) -> Decision:
        d = Decision(approved=False)
        L = self.limits
        positions = self.state.data["positions"]

        if self.state.data["kill_switch"]["active"]:
            d.reasons.append("kill switch 啟動中")
        if equity > 0 and -today_pnl / equity >= L.max_daily_loss_pct:
            d.reasons.append(f"當日虧損 {today_pnl / equity:.2%} 已達上限")
        if symbol in positions:
            d.reasons.append("已持有，不加碼")
        if len(positions) >= L.max_positions:
            d.reasons.append(f"持倉數已達上限 {L.max_positions}")
        cooldown_until = self.state.data["cooldown"].get(symbol)
        if cooldown_until and today < cooldown_until:
            d.reasons.append(f"冷卻期至 {cooldown_until}")
        if any(p["symbol"] == symbol and p["status"] == "pending" for p in self.state.data["pending"]):
            d.reasons.append("已有待審核單")
        if price <= 0 or atr_value <= 0 or not math.isfinite(atr_value):
            d.reasons.append("價格或 ATR 無效")
        if d.reasons:
            return d

        stop_dist = L.stop_loss_atr * atr_value
        qty_by_risk = (equity * L.risk_per_trade_pct) / stop_dist
        qty_by_position = (equity * L.max_position_pct) / price
        gross_room = equity * L.max_gross_exposure_pct - self.state.exposure()
        qty_by_gross = max(gross_room, 0.0) / price
        qty_by_cash = self.state.data["cash"] / (price * (1 + self.cfg.slippage_bps / 10_000))
        qty = int(math.floor(min(qty_by_risk, qty_by_position, qty_by_gross, qty_by_cash)))

        notional = qty * price
        if qty <= 0 or notional < L.min_trade_notional:
            d.reasons.append(f"可用部位太小（{notional:,.0f} < {L.min_trade_notional:,.0f}）")
            return d

        d.approved = True
        d.qty = qty
        d.notional = round(notional, 2)
        d.stop = round(price - stop_dist, 4)
        d.target = round(price + L.take_profit_atr * atr_value, 4)
        d.reasons.append(
            f"風險 {L.risk_per_trade_pct:.0%} / 停損 {L.stop_loss_atr}ATR → {qty} 股，"
            f"名目 {notional:,.0f}（{notional / equity:.1%} equity）"
        )
        return d
