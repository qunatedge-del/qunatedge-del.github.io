import pandas as pd
import pytest

from agent_desk.agents.execution import PaperBroker
from agent_desk.config import Config
from agent_desk.state import StateStore


@pytest.fixture
def broker(tmp_path):
    cfg = Config()
    cfg.slippage_bps = 10
    cfg.commission_per_share = 0.01
    state = StateStore(tmp_path / "state.json", 100_000)
    return cfg, state, PaperBroker(cfg, state)


def bars(sym, low, high, close):
    idx = pd.bdate_range("2026-01-05", periods=1)
    return {sym: pd.DataFrame({"open": close, "high": high, "low": low, "close": close, "volume": 1}, index=idx)}


def test_entry_waits_for_approval(broker):
    cfg, state, b = broker
    order = b.propose("AAPL", "BUY", 10, 100.0, "test", stop=95, target=110, today="2026-01-05")
    assert state.data["positions"] == {} and state.data["cash"] == 100_000
    assert b.pending()[0]["id"] == order["id"]
    fill = b.approve(order["id"])
    assert fill["price"] == pytest.approx(100.1)          # 10 bps slippage
    assert state.data["cash"] == pytest.approx(100_000 - 1001.0 - 0.10)
    assert state.data["positions"]["AAPL"]["qty"] == 10
    assert b.pending() == []


def test_reject_and_expire(broker):
    cfg, state, b = broker
    o1 = b.propose("AAPL", "BUY", 10, 100.0, "t", today="2026-01-05")
    o2 = b.propose("MSFT", "BUY", 10, 100.0, "t", today="2026-01-05")
    assert b.reject(o1["id"], "no")
    assert b.approve(o1["id"]) is None
    assert b.expire_pending("2026-01-06") == []
    expired = b.expire_pending("2026-01-08")
    assert [o["id"] for o in expired] == [o2["id"]]
    assert state.data["positions"] == {}


def test_stop_loss_auto_exit_and_cooldown(broker):
    cfg, state, b = broker
    o = b.propose("AAPL", "BUY", 10, 100.0, "t", stop=95.0, target=110.0, today="2026-01-05")
    b.approve(o["id"])
    events = b.check_exits(bars("AAPL", low=94.0, high=101.0, close=96.0), {}, "2026-01-06")
    assert events[0].type == "order.filled"
    assert "AAPL" not in state.data["positions"]
    trade = state.data["trades"][-1]
    assert trade["side"] == "SELL" and trade["pnl"] < 0 and "停損" in trade["reason"]
    assert state.data["cooldown"]["AAPL"] == "2026-01-09"


def test_take_profit_and_signal_exit(broker):
    cfg, state, b = broker
    o = b.propose("AAPL", "BUY", 10, 100.0, "t", stop=95.0, target=110.0, today="2026-01-05")
    b.approve(o["id"])
    b.check_exits(bars("AAPL", low=105.0, high=111.0, close=109.0), {}, "2026-01-06")
    assert state.data["trades"][-1]["pnl"] > 0
    o = b.propose("MSFT", "BUY", 10, 100.0, "t", stop=90.0, target=120.0, today="2026-01-06")
    b.approve(o["id"])
    b.check_exits(bars("MSFT", low=99.0, high=101.0, close=100.0), {"MSFT": {"side": "SELL", "reason": "跌破 SMA50"}}, "2026-01-07")
    assert "MSFT" not in state.data["positions"]


def test_exit_needs_approval_when_configured(broker):
    cfg, state, b = broker
    cfg.auto_execute_exits = False
    o = b.propose("AAPL", "BUY", 10, 100.0, "t", stop=95.0, target=110.0, today="2026-01-05")
    b.approve(o["id"])
    events = b.check_exits(bars("AAPL", low=90.0, high=100.0, close=92.0), {}, "2026-01-06")
    assert events[0].type == "order.proposed" and "AAPL" in state.data["positions"]
    # 不會重複排隊
    assert b.check_exits(bars("AAPL", low=90.0, high=100.0, close=92.0), {}, "2026-01-06") == []


def test_mark_to_market_curve_and_drawdown(broker):
    cfg, state, b = broker
    o = b.propose("AAPL", "BUY", 100, 100.0, "t", today="2026-01-05")
    b.approve(o["id"])
    s1 = b.mark_to_market({"AAPL": 110.0}, "2026-01-05")
    s2 = b.mark_to_market({"AAPL": 99.0}, "2026-01-06")
    assert s1["equity"] > s2["equity"]
    assert s2["daily_pnl"] == pytest.approx(-1100.0)
    assert s2["drawdown"] == pytest.approx((s1["equity"] - s2["equity"]) / s1["equity"], rel=1e-3)
    assert [c["date"] for c in state.data["equity_curve"]] == ["2026-01-05", "2026-01-06"]
    # 同一天再標記一次會覆蓋，不會多一筆
    b.mark_to_market({"AAPL": 100.0}, "2026-01-06")
    assert len(state.data["equity_curve"]) == 2
