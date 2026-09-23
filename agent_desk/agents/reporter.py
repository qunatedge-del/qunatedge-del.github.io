"""監控（規則式告警）與日報（LLM，每交易日最多一次）。"""
from __future__ import annotations

from datetime import date, datetime, timezone

from ..events import Event
from ..state import now_iso


class MonitorAgent:
    """純規則。輸出告警清單，不呼叫 LLM。"""
    name = "monitor"

    def __init__(self, cfg, state, llm):
        self.cfg = cfg
        self.state = state
        self.llm = llm

    def run(self, snap: dict, bars: dict, today: str) -> list[str]:
        alerts: list[str] = []
        L = self.cfg.risk
        if snap["drawdown"] >= L.max_drawdown_pct * 0.7 and not self.state.data["kill_switch"]["active"]:
            alerts.append(f"回撤 {snap['drawdown']:.1%} 已達 kill switch 門檻的 70%")
        if snap["equity"] > 0 and -snap["daily_pnl"] / snap["equity"] >= L.max_daily_loss_pct * 0.75:
            alerts.append(f"當日虧損 {snap['daily_pnl']:+,.0f}，接近日虧損上限")
        if snap["equity"] > 0 and snap["exposure"] / snap["equity"] > L.max_gross_exposure_pct * 1.05:
            alerts.append(f"總曝險 {snap['exposure'] / snap['equity']:.0%} 超過上限（價格漂移造成）")

        pending = [o for o in self.state.data["pending"] if o["status"] == "pending"]
        old = [o for o in pending if o["trade_date"] and o["trade_date"] < today]
        if old:
            alerts.append(f"{len(old)} 張待審核單已隔夜未處理：{', '.join(o['id'] for o in old)}")

        missing = [s for s in self.cfg.watchlist if s not in bars]
        if missing:
            alerts.append(f"缺少 K 線資料：{', '.join(missing)}")
        try:
            newest = max(df.index[-1].date() for df in bars.values()) if bars else None
        except ValueError:
            newest = None
        if newest and (date.fromisoformat(today) - newest).days > 4:
            alerts.append(f"行情資料已 {(date.fromisoformat(today) - newest).days} 天沒更新")

        usage = self.state.data["llm_usage"]
        if usage.get("date") == datetime.now(timezone.utc).date().isoformat() and usage["calls"] >= self.cfg.llm.max_calls_per_day:
            alerts.append("LLM 今日呼叫數已用完")

        for msg in alerts:
            self.state.alert("warn", msg, self.name)
        self.state.log(self.name, "run", f"{len(alerts)} 個告警")
        return alerts


REPORT_SYSTEM = (
    "你是交易桌的營運助理，每個交易日收盤後寫一份給老闆看的日報。\n"
    "讀者是這個系統的唯一操作者，他要在 60 秒內知道：今天發生什麼、哪裡有風險、明天要做什麼決定。\n"
    "規則：\n"
    "- 繁體中文，Markdown，250 字以內。\n"
    "- 只能引用提供的數據，不要編造價格或新聞。\n"
    "- 第一段是結論。有待審核單一定要列出並給出你的建議（核准 / 駁回）與一句理由。\n"
    "- 告警要逐條回應。沒有告警就明說。\n"
    "- 這是紙上交易，不要寫成真實資金。"
)


class ReportAgent:
    name = "report"

    def __init__(self, cfg, state, llm):
        self.cfg = cfg
        self.state = state
        self.llm = llm

    def due(self, today: str, events: list[Event]) -> bool:
        """只在「這個交易日有新 K 線」且「今天還沒寫過」時才觸發。"""
        has_new_bar = any(e.type == "bar.updated" for e in events)
        return has_new_bar and self.state.data["last_report_date"] != today

    def run(self, snap: dict, alerts: list[str], today: str, cycle_events: list[Event]) -> dict:
        context = self._context(snap, alerts, cycle_events)
        text = None
        if self.llm.available:
            text = self.llm.text(REPORT_SYSTEM, context, effort=self.cfg.llm.report_effort,
                                 max_tokens=2048, agent=self.name)
        source = "llm"
        if not text:
            text, source = self._template(snap, alerts), "template"
        report = {"date": today, "ts": now_iso(), "text": text, "source": source}
        reports = [r for r in self.state.data["reports"] if r["date"] != today]
        reports.append(report)
        self.state.data["reports"] = reports[-30:]
        self.state.data["last_report_date"] = today
        self.state.log(self.name, "run", f"日報完成（{source}）")
        return report

    def _context(self, snap: dict, alerts: list[str], events: list[Event]) -> str:
        s = self.state.data
        lines = [f"# 交易日 {snap['date']}（紙上交易）", "",
                 f"權益 {snap['equity']:,.0f}（初始 {s['initial_cash']:,.0f}），現金 {snap['cash']:,.0f}，"
                 f"曝險 {snap['exposure']:,.0f}，當日損益 {snap['daily_pnl']:+,.0f}，回撤 {snap['drawdown']:.1%}",
                 f"Kill switch：{'啟動 - ' + s['kill_switch']['reason'] if s['kill_switch']['active'] else '未啟動'}", ""]
        lines.append("## 持倉")
        for sym, p in s["positions"].items():
            upl = (p["last_price"] - p["avg_price"]) * p["qty"]
            lines.append(f"- {sym} {p['qty']} 股 @ {p['avg_price']:.2f}，現價 {p['last_price']:.2f}，"
                         f"未實現 {upl:+,.0f}，停損 {p['stop']:.2f} 停利 {p['target']:.2f}")
        if not s["positions"]:
            lines.append("- 空手")
        lines.append("")
        lines.append("## 今日成交")
        todays = [t for t in s["trades"] if t["trade_date"] == snap["date"]]
        for t in todays:
            lines.append(f"- {t['side']} {t['qty']} {t['symbol']} @ {t['price']:.2f}（{t['how']}，{t['reason']}）pnl {t['pnl']:+,.0f}")
        if not todays:
            lines.append("- 無")
        lines.append("")
        lines.append("## 待審核單")
        pend = [o for o in s["pending"] if o["status"] == "pending"]
        for o in pend:
            lines.append(f"- {o['id']} {o['side']} {o['qty']} {o['symbol']} @ {o['price_ref']:.2f}，"
                         f"名目 {o['notional']:,.0f}，停損 {o['stop']:.2f}，理由：{o['reason']}，到期 {o['expires']}")
        if not pend:
            lines.append("- 無")
        lines.append("")
        lines.append("## 訊號與情緒")
        for sym, sig in s["signals"].items():
            sent = s["sentiment"].get(sym, {})
            line = f"- {sym}: {sig['side']}（{sig['reason']}）"
            if sent:
                line += f"；情緒 {sent['score']:+.2f} 信心 {sent['confidence']:.1f}，{sent['rationale']}"
            lines.append(line)
        lines.append("")
        lines.append("## 告警")
        lines += [f"- {a}" for a in alerts] or ["- 無"]
        u = s["llm_usage"]
        lines += ["", f"LLM 今日用量：{u['calls']} 次，約 ${u['est_cost_usd']:.2f}"]
        return "\n".join(lines)

    def _template(self, snap: dict, alerts: list[str]) -> str:
        s = self.state.data
        pend = [o for o in s["pending"] if o["status"] == "pending"]
        parts = [f"**{snap['date']} 日報（模板，未使用 LLM）**", "",
                 f"權益 {snap['equity']:,.0f}，當日 {snap['daily_pnl']:+,.0f}，回撤 {snap['drawdown']:.1%}，"
                 f"持倉 {len(s['positions'])} 檔，現金 {snap['cash']:,.0f}。"]
        if pend:
            parts.append("")
            parts.append(f"待審核 {len(pend)} 張：" + "；".join(
                f"{o['id']} {o['side']} {o['qty']} {o['symbol']} @ {o['price_ref']:.2f}" for o in pend))
        parts.append("")
        parts.append("告警：" + ("；".join(alerts) if alerts else "無"))
        return "\n".join(parts)
