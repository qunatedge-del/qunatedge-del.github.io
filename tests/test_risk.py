import pytest

from agent_desk.agents.risk import RiskAgent
from agent_desk.config import Config
from agent_desk.state import StateStore


@pytest.fixture
def desk(tmp_path):
    cfg = Config()
    state = StateStore(tmp_path / "state.json", cfg.initial_cash)
    return cfg, state, RiskAgent(cfg, state)


def test_sizing_respects_risk_per_trade(desk):
    cfg, state, risk = desk
    d = risk.evaluate_entry("AAPL", price=100.0, atr_value=2.0, equity=100_000, today_pnl=0, today="2026-01-05")
    assert d.approved
    # 1% of 100k = 1000 risk / (2 ATR * 2.0) = 250 shares, but 10% position cap = 100 shares
    assert d.qty == 100
    assert d.stop == pytest.approx(96.0) and d.target == pytest.approx(108.0)


def test_position_cap_binds_before_risk(desk):
    cfg, state, risk = desk
    d = risk.evaluate_entry("AAPL", price=10.0, atr_value=0.05, equity=100_000, today_pnl=0, today="2026-01-05")
    assert d.approved and d.qty * 10.0 <= cfg.risk.max_position_pct * 100_000 + 1e-6


def test_blocked_when_kill_switch(desk):
    cfg, state, risk = desk
    state.data["kill_switch"]["active"] = True
    d = risk.evaluate_entry("AAPL", 100.0, 2.0, 100_000, 0, "2026-01-05")
    assert not d.approved and any("kill switch" in r for r in d.reasons)


def test_blocked_on_daily_loss(desk):
    cfg, state, risk = desk
    d = risk.evaluate_entry("AAPL", 100.0, 2.0, 100_000, today_pnl=-2_500, today="2026-01-05")
    assert not d.approved and any("當日虧損" in r for r in d.reasons)


def test_blocked_when_max_positions(desk):
    cfg, state, risk = desk
    for i in range(cfg.risk.max_positions):
        state.data["positions"][f"S{i}"] = {"qty": 1, "avg_price": 1.0, "last_price": 1.0}
    d = risk.evaluate_entry("AAPL", 100.0, 2.0, 100_000, 0, "2026-01-05")
    assert not d.approved and any("持倉數" in r for r in d.reasons)


def test_blocked_in_cooldown_and_no_pyramiding(desk):
    cfg, state, risk = desk
    state.data["cooldown"]["AAPL"] = "2026-01-10"
    assert not risk.evaluate_entry("AAPL", 100.0, 2.0, 100_000, 0, "2026-01-05").approved
    state.data["positions"]["MSFT"] = {"qty": 1, "avg_price": 1.0, "last_price": 1.0}
    assert not risk.evaluate_entry("MSFT", 100.0, 2.0, 100_000, 0, "2026-01-05").approved


def test_gross_exposure_cap(desk):
    cfg, state, risk = desk
    state.data["positions"]["BIG"] = {"qty": 600, "avg_price": 100.0, "last_price": 100.0}  # 60% exposure
    d = risk.evaluate_entry("AAPL", 100.0, 2.0, 100_000, 0, "2026-01-05")
    assert not d.approved and any("太小" in r for r in d.reasons)


def test_kill_switch_trips_on_drawdown(desk):
    cfg, state, risk = desk
    state.data["peak_equity"] = 100_000
    assert not risk.check_kill_switch(95_000)
    assert risk.check_kill_switch(89_000)
    assert state.data["kill_switch"]["active"]
    assert state.data["alerts"][-1]["level"] == "critical"
