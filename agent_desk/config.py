"""設定：所有硬上限都放在這裡，程式碼裡不散落魔術數字。"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "agent_desk" / "config.json"


@dataclass
class RiskLimits:
    risk_per_trade_pct: float = 0.01      # 每筆交易最多虧 equity 的 1%（用停損距離反推部位）
    max_position_pct: float = 0.10        # 單一部位名目 / equity 上限
    max_gross_exposure_pct: float = 0.60  # 總曝險 / equity 上限
    max_positions: int = 6                # 最多同時持有幾檔
    max_daily_loss_pct: float = 0.02      # 當日虧損達 2% 就停止開新倉
    max_drawdown_pct: float = 0.10        # 回撤達 10% 觸發 kill switch（需人工解除）
    stop_loss_atr: float = 2.0            # 停損 = 進場價 - 2 ATR
    take_profit_atr: float = 4.0          # 停利 = 進場價 + 4 ATR
    cooldown_days: int = 3                # 出場後同一檔 N 天內不再進場
    min_trade_notional: float = 500.0     # 太小的單不做


@dataclass
class LLMConfig:
    enabled: bool = True
    model: str = "claude-opus-5"
    max_calls_per_day: int = 20           # 成本硬上限：一天最多呼叫幾次
    sentiment_effort: str = "low"         # 情緒分類是簡單任務，低 effort 就夠
    report_effort: str = "medium"
    max_headlines_per_symbol: int = 8
    price_in_per_mtok: float = 5.0        # 用來估算成本（claude-opus-5）
    price_out_per_mtok: float = 25.0


@dataclass
class Config:
    watchlist: list[str] = field(default_factory=lambda: [
        "SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META",
    ])
    initial_cash: float = 100_000.0
    approval_required: bool = True        # 進場單一律要人工審核
    auto_execute_exits: bool = True       # 停損 / 停利 / 訊號出場自動執行（只會降低風險）
    approval_ttl_days: int = 2            # 待審核單超過 N 個交易日自動作廢
    slippage_bps: float = 5.0             # 紙上成交滑價
    commission_per_share: float = 0.005
    lookback_days: int = 250
    data_dir: str = "data"
    risk: RiskLimits = field(default_factory=RiskLimits)
    llm: LLMConfig = field(default_factory=LLMConfig)

    @property
    def data_path(self) -> Path:
        return ROOT / self.data_dir

    def to_dict(self) -> dict:
        return asdict(self)


def _merge(dc, data: dict):
    """把 dict 覆蓋進 dataclass（巢狀也處理）。"""
    for key, value in data.items():
        if not hasattr(dc, key):
            continue
        current = getattr(dc, key)
        if hasattr(current, "__dataclass_fields__") and isinstance(value, dict):
            _merge(current, value)
        else:
            setattr(dc, key, value)
    return dc


def load_config(path: Path | None = None) -> Config:
    cfg = Config()
    path = path or CONFIG_PATH
    if path.exists():
        with open(path, encoding="utf-8") as f:
            _merge(cfg, json.load(f))
    model = os.environ.get("AGENT_DESK_MODEL")
    if model:
        cfg.llm.model = model
    return cfg
