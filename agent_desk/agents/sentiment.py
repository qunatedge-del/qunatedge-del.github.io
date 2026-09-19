"""新聞情緒代理（LLM）。只在 DataAgent 發出 news.new 事件時才呼叫模型，
而且把所有標的的新標題打包成一次呼叫。"""
from __future__ import annotations

import json

from ..events import Event, filter_events
from ..state import now_iso

SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "score": {"type": "number", "description": "-1 極負面 到 +1 極正面"},
                    "confidence": {"type": "number", "description": "0 到 1"},
                    "event_type": {
                        "type": "string",
                        "enum": ["earnings", "guidance", "macro", "product", "legal", "m_and_a", "analyst", "other"],
                    },
                    "horizon_days": {"type": "integer", "description": "影響大概持續幾個交易日"},
                    "rationale": {"type": "string", "description": "一句話，繁體中文"},
                },
                "required": ["symbol", "score", "confidence", "event_type", "horizon_days", "rationale"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}

SYSTEM = (
    "你是交易桌上的新聞分析員。你會收到幾檔股票的最新新聞標題（與摘要），"
    "請對每一檔給出一個整體情緒分數與信心度，並判斷主要事件類型。\n"
    "原則：\n"
    "- 只評估「這些標題對該股未來幾天股價」的方向性影響，不預測長期價值。\n"
    "- 純粹的行情報導（例如「股價今日上漲 2%」）情緒給 0、信心給低，因為那不是新資訊。\n"
    "- 財報、財測、監管、訴訟、併購才是高信心事件。\n"
    "- 標題互相矛盾時降低信心，不要硬選方向。\n"
    "- rationale 用繁體中文，一句話。"
)


class SentimentAgent:
    name = "sentiment"

    def __init__(self, cfg, state, llm):
        self.cfg = cfg
        self.state = state
        self.llm = llm

    def run(self, events: list[Event]) -> list[Event]:
        news_events = filter_events(events, "news.new")
        if not news_events:
            return []  # 沒有新標題就不喚醒模型：這就是「事件觸發」
        batch = {e.symbol: e.payload["items"] for e in news_events}
        n_titles = sum(len(v) for v in batch.values())

        result = None
        if self.llm.available:
            result = self.llm.structured(
                SYSTEM, self._prompt(batch), SCHEMA,
                effort=self.cfg.llm.sentiment_effort, agent=self.name,
            )
        out: list[Event] = []
        if result and isinstance(result.get("items"), list):
            for item in result["items"]:
                sym = item.get("symbol")
                if sym not in batch:
                    continue
                entry = {
                    "score": max(-1.0, min(1.0, float(item.get("score", 0)))),
                    "confidence": max(0.0, min(1.0, float(item.get("confidence", 0)))),
                    "event_type": item.get("event_type", "other"),
                    "horizon_days": int(item.get("horizon_days", 3)),
                    "rationale": item.get("rationale", ""),
                    "updated": now_iso(), "n_headlines": len(batch[sym]),
                    "headlines": [i["title"] for i in batch[sym]][:5],
                    "source": "llm",
                }
                self.state.data["sentiment"][sym] = entry
                out.append(Event("sentiment.updated", sym, entry))
            self.state.log(self.name, "run", f"{n_titles} 則標題 → {len(out)} 檔情緒更新（1 次 LLM 呼叫）")
        else:
            # 沒有金鑰、超預算或出錯：退回中性，但仍記錄看過哪些標題
            for sym, items in batch.items():
                self.state.data["sentiment"][sym] = {
                    "score": 0.0, "confidence": 0.0, "event_type": "other", "horizon_days": 0,
                    "rationale": "未使用 LLM（無金鑰、超預算或呼叫失敗），視為中性",
                    "updated": now_iso(), "n_headlines": len(items),
                    "headlines": [i["title"] for i in items][:5], "source": "neutral",
                }
            self.state.log(self.name, "run", f"{n_titles} 則標題，LLM 不可用，情緒設為中性")
        return out

    def _prompt(self, batch: dict[str, list[dict]]) -> str:
        lines = ["請評估以下新聞。回傳每一檔一筆。", ""]
        for sym, items in batch.items():
            lines.append(f"## {sym}")
            for i in items[: self.cfg.llm.max_headlines_per_symbol]:
                line = f"- [{i.get('publisher', '')} {i.get('published', '')[:10]}] {i['title']}"
                if i.get("summary"):
                    line += f"\n  摘要：{i['summary'][:300]}"
                lines.append(line)
            lines.append("")
        return "\n".join(lines)


def stale_sentiment(entry: dict, today: str) -> bool:
    """情緒超過 horizon 天就不該再影響訊號。"""
    if not entry or not entry.get("updated"):
        return True
    from datetime import date

    try:
        age = (date.fromisoformat(today) - date.fromisoformat(entry["updated"][:10])).days
    except ValueError:
        return True
    return age > max(int(entry.get("horizon_days", 3)), 1)
