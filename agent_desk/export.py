"""把狀態整理成 dashboard 要讀的 JSON（data/agent_desk.json）。"""
from __future__ import annotations

import json
from datetime import datetime, timezone


def export_dashboard(cfg, state, bars: dict | None = None, mode: str = "paper") -> dict:
    s = state.data
    prices = {sym: p["last_price"] for sym, p in s["positions"].items()}
    equity = state.equity(prices)
    curve = s["equity_curve"]
    last = curve[-1] if curve else {}
    positions = []
    for sym, p in s["positions"].items():
        upl = (p["last_price"] - p["avg_price"]) * p["qty"]
        positions.append({
            "symbol": sym, "qty": p["qty"], "avg_price": p["avg_price"], "last_price": p["last_price"],
            "notional": round(p["qty"] * p["last_price"], 2), "unrealized": round(upl, 2),
            "unrealized_pct": round(upl / (p["avg_price"] * p["qty"]), 4) if p["qty"] else 0.0,
            "stop": p["stop"], "target": p["target"], "opened": p["opened"],
        })
    closed = [t for t in s["trades"] if t["side"] == "SELL"]
    wins = [t["pnl"] for t in closed if t["pnl"] > 0]
    losses = [-t["pnl"] for t in closed if t["pnl"] <= 0]
    avg_win = sum(wins) / len(wins) if wins else None
    avg_loss = sum(losses) / len(losses) if losses else None
    stats = {
        "n_trades": len(s["trades"]), "n_closed": len(closed),
        "n_wins": len(wins), "n_losses": len(losses),
        "win_rate": round(len(wins) / len(closed), 3) if closed else None,
        "avg_win": round(avg_win, 2) if avg_win is not None else None,
        "avg_loss": round(avg_loss, 2) if avg_loss is not None else None,
        # 盈虧比：平均獲利 / 平均虧損；獲利因子：總獲利 / 總虧損；期望值：每筆平均損益
        "payoff_ratio": round(avg_win / avg_loss, 2) if avg_win and avg_loss else None,
        "profit_factor": round(sum(wins) / sum(losses), 2) if wins and losses else None,
        "expectancy": round((sum(wins) - sum(losses)) / len(closed), 2) if closed else None,
        "realized_pnl": round(sum(t["pnl"] for t in closed), 2),
        "max_drawdown": round(max((c["drawdown"] for c in curve), default=0.0), 4),
        "total_return": round(equity / s["initial_cash"] - 1, 4) if s["initial_cash"] else 0.0,
    }
    watch = []
    for sym in cfg.watchlist:
        sig = s["signals"].get(sym, {})
        sent = s["sentiment"].get(sym, {})
        watch.append({
            "symbol": sym, "price": sig.get("price"), "side": sig.get("side", "—"), "strength": sig.get("strength", 0),
            "reason": sig.get("reason", ""), "indicators": sig.get("indicators", {}),
            "sentiment": sent.get("score"), "confidence": sent.get("confidence"),
            "event_type": sent.get("event_type"), "rationale": sent.get("rationale", ""),
            "headlines": sent.get("headlines", []), "sentiment_updated": sent.get("updated", ""),
        })
    payload = {
        "generated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": mode,
        "config": {
            "watchlist": cfg.watchlist, "initial_cash": s["initial_cash"], "approval_required": cfg.approval_required,
            "auto_execute_exits": cfg.auto_execute_exits, "risk": cfg.risk.__dict__,
            "llm": {"model": cfg.llm.model, "max_calls_per_day": cfg.llm.max_calls_per_day, "enabled": cfg.llm.enabled},
        },
        "kpi": {
            "equity": round(equity, 2), "cash": round(s["cash"], 2), "exposure": round(state.exposure(prices), 2),
            "daily_pnl": last.get("daily_pnl", 0.0), "drawdown": last.get("drawdown", 0.0),
            "peak_equity": s["peak_equity"], "n_positions": len(positions),
            "n_pending": len([o for o in s["pending"] if o["status"] == "pending"]),
            "kill_switch": s["kill_switch"], "last_trade_date": last.get("date", ""),
            "llm_usage": s["llm_usage"], **stats,
        },
        "equity_curve": curve[-250:],
        "positions": positions,
        "pending": [o for o in s["pending"] if o["status"] == "pending"],
        "decided": [o for o in s["pending"] if o["status"] != "pending"][-20:],
        "trades": s["trades"][-100:][::-1],
        "watchlist": watch,
        "alerts": s["alerts"][-30:][::-1],
        "run_log": s["run_log"][-80:][::-1],
        "reports": s["reports"][-5:][::-1],
    }
    out = cfg.data_path / "agent_desk.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1, default=str)
    return payload
