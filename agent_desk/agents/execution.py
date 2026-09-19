"""執行層：紙上交易 + 人工審核閘門。

進場單一律先進 pending 佇列，等 `approve` 才成交。
出場（停損 / 停利 / 訊號翻空）依設定可自動成交，因為只會降低風險。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..events import Event
from ..state import now_iso


class PaperBroker:
    name = "execution"

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    # ---- proposals ----------------------------------------------------------
    def propose(self, symbol: str, side: str, qty: int, price_ref: float, reason: str,
                stop: float = 0.0, target: float = 0.0, today: str = "") -> dict:
        order = {
            "id": self.state.new_id("ORD"),
            "created": now_iso(),
            "trade_date": today,
            "expires": self._expiry(today),
            "symbol": symbol, "side": side, "qty": int(qty),
            "price_ref": round(price_ref, 4), "notional": round(qty * price_ref, 2),
            "stop": stop, "target": target, "reason": reason, "status": "pending",
        }
        self.state.data["pending"].append(order)
        self.state.log(self.name, "order.proposed", f"{order['id']} {side} {qty} {symbol} @ {price_ref:.2f} 待審核")
        return order

    def _expiry(self, today: str) -> str:
        base = datetime.fromisoformat(today) if today else datetime.now(timezone.utc)
        return (base + timedelta(days=self.cfg.approval_ttl_days)).date().isoformat()

    def pending(self) -> list[dict]:
        return [o for o in self.state.data["pending"] if o["status"] == "pending"]

    def _find(self, order_id: str) -> dict | None:
        return next((o for o in self.state.data["pending"] if o["id"] == order_id), None)

    def approve(self, order_id: str, price: float | None = None) -> dict | None:
        order = self._find(order_id)
        if not order or order["status"] != "pending":
            return None
        order["status"] = "approved"
        order["decided"] = now_iso()
        fill = self.execute(order, price or order["price_ref"], "人工核准")
        self._archive(order)
        return fill

    def reject(self, order_id: str, note: str = "") -> bool:
        order = self._find(order_id)
        if not order or order["status"] != "pending":
            return False
        order["status"] = "rejected"
        order["decided"] = now_iso()
        order["note"] = note
        self.state.log(self.name, "order.rejected", f"{order_id} 人工駁回 {note}")
        self._archive(order)
        return True

    def expire_pending(self, today: str) -> list[dict]:
        expired = []
        for order in self.pending():
            if today > order["expires"]:
                order["status"] = "expired"
                order["decided"] = now_iso()
                expired.append(order)
                self.state.log(self.name, "order.expired", f"{order['id']} 超過 {self.cfg.approval_ttl_days} 天未審核，作廢")
                self._archive(order)
        return expired

    def _archive(self, order: dict) -> None:
        """只保留最近 50 筆已決定的單，pending 的永遠保留。"""
        decided = [o for o in self.state.data["pending"] if o["status"] != "pending"]
        keep = set(o["id"] for o in decided[-50:])
        self.state.data["pending"] = [
            o for o in self.state.data["pending"] if o["status"] == "pending" or o["id"] in keep
        ]

    # ---- fills --------------------------------------------------------------
    def execute(self, order: dict, price: float, how: str) -> dict:
        slip = price * self.cfg.slippage_bps / 10_000
        fill_px = price + slip if order["side"] == "BUY" else price - slip
        qty = int(order["qty"])
        commission = round(qty * self.cfg.commission_per_share, 2)
        positions = self.state.data["positions"]
        pnl = 0.0

        if order["side"] == "BUY":
            cost = qty * fill_px + commission
            self.state.data["cash"] -= cost
            pos = positions.get(order["symbol"])
            if pos:
                total = pos["qty"] + qty
                pos["avg_price"] = (pos["avg_price"] * pos["qty"] + fill_px * qty) / total
                pos["qty"] = total
            else:
                positions[order["symbol"]] = {
                    "qty": qty, "avg_price": round(fill_px, 4), "opened": order.get("trade_date") or now_iso()[:10],
                    "stop": order.get("stop", 0.0), "target": order.get("target", 0.0),
                    "last_price": round(fill_px, 4), "entry_atr": order.get("atr", 0.0),
                }
        else:
            pos = positions.get(order["symbol"])
            if not pos:
                raise ValueError(f"沒有 {order['symbol']} 的部位可以賣")
            qty = min(qty, pos["qty"])
            proceeds = qty * fill_px - commission
            self.state.data["cash"] += proceeds
            pnl = round((fill_px - pos["avg_price"]) * qty - commission, 2)
            pos["qty"] -= qty
            if pos["qty"] <= 0:
                del positions[order["symbol"]]
                until = datetime.fromisoformat(order.get("trade_date") or now_iso()[:10]) + timedelta(days=self.cfg.risk.cooldown_days)
                self.state.data["cooldown"][order["symbol"]] = until.date().isoformat()

        trade = {
            "id": self.state.new_id("TRD"), "order_id": order["id"], "ts": now_iso(),
            "trade_date": order.get("trade_date") or now_iso()[:10],
            "symbol": order["symbol"], "side": order["side"], "qty": qty,
            "price": round(fill_px, 4), "notional": round(qty * fill_px, 2),
            "commission": commission, "pnl": pnl, "reason": order.get("reason", ""), "how": how,
        }
        self.state.data["trades"].append(trade)
        self.state.data["trades"] = self.state.data["trades"][-500:]
        self.state.log(self.name, "order.filled",
                       f"{trade['id']} {order['side']} {qty} {order['symbol']} @ {fill_px:.2f}（{how}）pnl {pnl:+,.2f}")
        return trade

    # ---- exits --------------------------------------------------------------
    def check_exits(self, bars: dict, signals: dict, today: str) -> list[Event]:
        """停損 / 停利 / 訊號翻空。回傳 order.proposed 或 order.filled 事件。"""
        events: list[Event] = []
        for sym, pos in list(self.state.data["positions"].items()):
            if sym not in bars:
                continue
            df = bars[sym]
            low, high, close = float(df["low"].iloc[-1]), float(df["high"].iloc[-1]), float(df["close"].iloc[-1])
            reason, px = "", close
            if pos.get("stop") and low <= pos["stop"]:
                reason, px = f"觸及停損 {pos['stop']:.2f}", min(pos["stop"], close)
            elif pos.get("target") and high >= pos["target"]:
                reason, px = f"觸及停利 {pos['target']:.2f}", max(pos["target"], close)
            elif signals.get(sym, {}).get("side") == "SELL":
                reason = f"訊號出場：{signals[sym].get('reason', '')}"
            if not reason:
                continue
            if any(o["symbol"] == sym and o["side"] == "SELL" and o["status"] == "pending" for o in self.state.data["pending"]):
                continue
            order = {
                "id": self.state.new_id("ORD"), "created": now_iso(), "trade_date": today,
                "expires": self._expiry(today), "symbol": sym, "side": "SELL", "qty": pos["qty"],
                "price_ref": round(px, 4), "notional": round(pos["qty"] * px, 2),
                "stop": 0.0, "target": 0.0, "reason": reason, "status": "pending",
            }
            if self.cfg.auto_execute_exits:
                order["status"] = "approved"
                trade = self.execute(order, px, "自動出場")
                events.append(Event("order.filled", sym, trade))
            else:
                self.state.data["pending"].append(order)
                self.state.log(self.name, "order.proposed", f"{order['id']} SELL {pos['qty']} {sym} 待審核（{reason}）")
                events.append(Event("order.proposed", sym, order))
        return events

    # ---- mark to market -----------------------------------------------------
    def mark_to_market(self, prices: dict[str, float], today: str) -> dict:
        for sym, pos in self.state.data["positions"].items():
            if sym in prices:
                pos["last_price"] = round(prices[sym], 4)
        equity = self.state.equity(prices)
        exposure = self.state.exposure(prices)
        curve = self.state.data["equity_curve"]
        prev_equity = curve[-1]["equity"] if curve and curve[-1]["date"] != today else (
            curve[-2]["equity"] if len(curve) >= 2 else self.state.data["initial_cash"]
        )
        if not curve:
            prev_equity = self.state.data["initial_cash"]
        self.state.data["peak_equity"] = max(self.state.data["peak_equity"], equity)
        peak = self.state.data["peak_equity"]
        snap = {
            "date": today, "equity": round(equity, 2), "cash": round(self.state.data["cash"], 2),
            "exposure": round(exposure, 2), "daily_pnl": round(equity - prev_equity, 2),
            "drawdown": round((peak - equity) / peak if peak else 0.0, 4),
            "n_positions": len(self.state.data["positions"]),
        }
        if curve and curve[-1]["date"] == today:
            curve[-1] = snap
        else:
            curve.append(snap)
        self.state.data["equity_curve"] = curve[-750:]
        return snap
