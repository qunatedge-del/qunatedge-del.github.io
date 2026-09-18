"""離線整合測試：多日模擬，確認事件觸發、審核閘門、LLM 預算閘門都照設計運作。"""
from datetime import datetime, timedelta, timezone

import pytest

from agent_desk.agents.data import synthetic_bars
from agent_desk.config import Config
from agent_desk.orchestrator import Desk
from agent_desk.state import StateStore


class FakeLLM:
    """模擬 LLM 客戶端，記錄被呼叫幾次。"""
    available = True

    def __init__(self):
        self.calls = 0

    def calls_left(self):
        return 99

    def structured(self, system, user, schema, effort="low", max_tokens=4096, agent="llm"):
        self.calls += 1
        syms = [line[3:].strip() for line in user.splitlines() if line.startswith("## ")]
        return {"items": [{"symbol": s, "score": 0.5, "confidence": 0.8, "event_type": "earnings",
                           "horizon_days": 3, "rationale": "測試"} for s in syms]}

    def text(self, system, user, effort="medium", max_tokens=4096, agent="llm"):
        self.calls += 1
        return "假日報"


@pytest.fixture
def desk(tmp_path):
    cfg = Config()
    cfg.data_dir = str(tmp_path)
    cfg.watchlist = ["AAA", "BBB", "CCC", "DDD"]
    state = StateStore(tmp_path / "state.json", cfg.initial_cash)
    d = Desk(cfg, state, offline=True, demo_news=True)
    fake = FakeLLM()
    d.llm = fake
    d.sentiment.llm = fake
    d.report.llm = fake
    d.monitor.llm = fake
    return d, fake


def simulate(desk, days, approve=True, start_offset=120):
    end0 = datetime.now(timezone.utc) - timedelta(days=start_offset)
    results = []
    for i in range(days):
        end = end0 + timedelta(days=i)
        if end.weekday() >= 5:
            continue
        desk.data.fetch_bars = lambda end=end: {
            s: synthetic_bars(s, desk.cfg.lookback_days, 7, end) for s in desk.cfg.watchlist
        }
        res = desk.run_cycle()
        if approve:
            for o in list(desk.broker.pending()):
                desk.approve(o["id"])
        results.append(res)
    return results


def test_llm_only_called_on_events(desk):
    d, fake = desk
    results = simulate(d, 10)
    # 假新聞只在第一輪是新的 → 情緒代理只呼叫 1 次；日報每個交易日 1 次
    trading_days = len(results)
    assert fake.calls == 1 + trading_days
    assert d.state.data["sentiment"]["AAA"]["source"] == "llm"
    assert all(r["report"] is not None for r in results)
    # 同一天再跑一次：沒有新 K 線、沒有新新聞 → 一次 LLM 都不會呼叫
    before = fake.calls
    d.run_cycle()
    assert fake.calls == before


def test_entries_require_approval(desk):
    d, fake = desk
    simulate(d, 60, approve=False)
    assert d.state.data["trades"] == [] or all(t["side"] == "SELL" for t in d.state.data["trades"])
    assert d.state.data["positions"] == {}
    proposed = [o for o in d.state.data["pending"] if o["side"] == "BUY"]
    assert proposed, "60 天內應該至少提出一張進場單"
    assert all(o["status"] in {"pending", "expired"} for o in proposed)


def test_full_loop_with_approvals_trades_and_exports(desk):
    d, fake = desk
    results = simulate(d, 120)
    s = d.state.data
    assert s["trades"], "有核准就應該有成交"
    assert all(t["how"] == "人工核准" for t in s["trades"] if t["side"] == "BUY")
    assert len(s["equity_curve"]) == len(results)
    for pos in s["positions"].values():
        assert pos["qty"] * pos["last_price"] <= d.cfg.risk.max_position_pct * s["peak_equity"] * 1.5
    out = d.cfg.data_path / "agent_desk.json"
    assert out.exists()
    import json

    payload = json.loads(out.read_text())
    assert payload["kpi"]["equity"] == pytest.approx(d.state.equity(), rel=1e-6)
    assert payload["watchlist"][0]["symbol"] == "AAA"


def test_kill_switch_blocks_new_entries(desk):
    d, fake = desk
    simulate(d, 5)
    d.set_kill_switch(True, "測試")
    before = len(d.state.data["trades"])
    simulate(d, 40, start_offset=115)
    buys = [t for t in d.state.data["trades"][before:] if t["side"] == "BUY"]
    assert buys == []
    assert d.state.data["pending"] == [] or all(o["side"] != "BUY" or o["status"] != "pending" for o in d.state.data["pending"])


def test_state_survives_reload(desk, tmp_path):
    d, fake = desk
    simulate(d, 30)
    equity = d.state.equity()
    state2 = StateStore(tmp_path / "state.json", d.cfg.initial_cash)
    assert state2.equity() == pytest.approx(equity)
    assert state2.data["next_id"] == d.state.data["next_id"]
