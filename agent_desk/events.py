"""事件：代理之間只用事件溝通，LLM 代理只在收到事件時才會被喚醒。"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Event:
    type: str            # bar.updated / news.new / sentiment.updated / signal.new / order.proposed / ...
    symbol: str = ""
    payload: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"Event({self.type}, {self.symbol})"


def filter_events(events: list[Event], type_: str) -> list[Event]:
    return [e for e in events if e.type == type_]
