"""Claude API 封裝：預算閘門、結構化輸出、成本記錄。

所有 LLM 呼叫都經過這裡，所以「一天最多幾次」的硬上限只需要在一個地方管。
沒有 API 金鑰時 `available` 為 False，呼叫端要自己退回規則式行為。
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

try:
    import anthropic
except ImportError:  # 測試環境沒裝也能 import 本模組
    anthropic = None


class BudgetExceeded(RuntimeError):
    pass


class LLMClient:
    def __init__(self, cfg, state):
        self.cfg = cfg.llm
        self.state = state
        self._client = None
        self.available = bool(
            self.cfg.enabled and anthropic is not None
            and (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))
        )

    @property
    def client(self):
        if self._client is None:
            self._client = anthropic.Anthropic()
        return self._client

    # ---- budget -------------------------------------------------------------
    def _usage(self) -> dict:
        usage = self.state.data["llm_usage"]
        today = datetime.now(timezone.utc).date().isoformat()
        if usage.get("date") != today:
            usage.update({"date": today, "calls": 0, "input_tokens": 0, "output_tokens": 0, "est_cost_usd": 0.0})
        return usage

    def calls_left(self) -> int:
        return max(self.cfg.max_calls_per_day - self._usage()["calls"], 0)

    def _record(self, response) -> None:
        usage = self._usage()
        usage["calls"] += 1
        u = getattr(response, "usage", None)
        if u:
            usage["input_tokens"] += int(getattr(u, "input_tokens", 0) or 0)
            usage["output_tokens"] += int(getattr(u, "output_tokens", 0) or 0)
            usage["est_cost_usd"] = round(
                usage["input_tokens"] / 1e6 * self.cfg.price_in_per_mtok
                + usage["output_tokens"] / 1e6 * self.cfg.price_out_per_mtok, 4,
            )

    # ---- calls --------------------------------------------------------------
    def structured(self, system: str, user: str, schema: dict, effort: str = "low",
                   max_tokens: int = 4096, agent: str = "llm") -> dict | None:
        """回傳符合 schema 的 dict；被拒絕、超預算、或出錯時回傳 None 並記錄告警。"""
        if not self.available:
            return None
        if self.calls_left() <= 0:
            self.state.alert("warn", f"LLM 今日呼叫數已達上限 {self.cfg.max_calls_per_day}，{agent} 略過", agent)
            return None
        try:
            response = self.client.messages.create(
                model=self.cfg.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
            )
        except anthropic.RateLimitError:
            self.state.alert("warn", f"{agent}: API 速率限制，稍後再試", agent)
            return None
        except anthropic.APIStatusError as exc:
            self.state.alert("warn", f"{agent}: API 錯誤 {exc.status_code}: {exc.message}", agent)
            return None
        except anthropic.APIConnectionError as exc:
            self.state.alert("warn", f"{agent}: 連線失敗 {exc}", agent)
            return None
        self._record(response)
        if response.stop_reason == "refusal":
            details = getattr(response, "stop_details", None)
            self.state.alert("warn", f"{agent}: 模型拒絕回答（{getattr(details, 'category', '')}）", agent)
            return None
        if response.stop_reason == "max_tokens":
            self.state.alert("warn", f"{agent}: 輸出被 max_tokens 截斷", agent)
            return None
        text = next((b.text for b in response.content if b.type == "text"), "")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            self.state.alert("warn", f"{agent}: 回傳不是合法 JSON", agent)
            return None

    def text(self, system: str, user: str, effort: str = "medium", max_tokens: int = 4096,
             agent: str = "llm") -> str | None:
        if not self.available:
            return None
        if self.calls_left() <= 0:
            self.state.alert("warn", f"LLM 今日呼叫數已達上限 {self.cfg.max_calls_per_day}，{agent} 略過", agent)
            return None
        try:
            response = self.client.messages.create(
                model=self.cfg.model, max_tokens=max_tokens, system=system,
                messages=[{"role": "user", "content": user}],
                output_config={"effort": effort},
            )
        except anthropic.RateLimitError:
            self.state.alert("warn", f"{agent}: API 速率限制，稍後再試", agent)
            return None
        except anthropic.APIStatusError as exc:
            self.state.alert("warn", f"{agent}: API 錯誤 {exc.status_code}: {exc.message}", agent)
            return None
        except anthropic.APIConnectionError as exc:
            self.state.alert("warn", f"{agent}: 連線失敗 {exc}", agent)
            return None
        self._record(response)
        if response.stop_reason == "refusal":
            self.state.alert("warn", f"{agent}: 模型拒絕回答", agent)
            return None
        return "".join(b.text for b in response.content if b.type == "text").strip() or None
