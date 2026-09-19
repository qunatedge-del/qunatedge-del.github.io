"""CLI：python -m agent_desk <command>

  run                跑一輪（抓資料 → 情緒 → 訊號 → 風控 → 紙上執行 → 監控 → 日報 → 匯出）
  status             看目前權益、持倉、待審核單
  pending            列出待審核單
  approve ORD-xxxxx  核准一張單（紙上成交）
  approve-all        核准全部待審核單
  reject ORD-xxxxx   駁回一張單
  report             印出最新日報
  killswitch on|off  手動啟動 / 解除 kill switch
  reset              清空狀態（會先要求輸入 yes）

常用參數：--offline（合成資料，不連網）、--demo-news（離線時塞幾則假新聞測試情緒代理）
"""
from __future__ import annotations

import argparse
import json
import sys

from .config import load_config
from .orchestrator import Desk
from .state import StateStore


def build(args) -> Desk:
    cfg = load_config()
    state = StateStore(cfg.data_path / "agent_desk_state.json", cfg.initial_cash)
    return Desk(cfg, state, offline=args.offline, seed=args.seed, demo_news=args.demo_news)


def cmd_run(args):
    desk = build(args)
    result = desk.run_cycle()
    snap = result["snapshot"]
    if not snap:
        print("本輪沒有資料。")
        return 1
    print(f"交易日 {result['today']}  權益 {snap['equity']:,.0f}  當日 {snap['daily_pnl']:+,.0f}  "
          f"回撤 {snap['drawdown']:.1%}  持倉 {snap['n_positions']}  現金 {snap['cash']:,.0f}")
    print("事件：", ", ".join(result["events"]) or "無")
    if result["alerts"]:
        print("告警：")
        for a in result["alerts"]:
            print("  -", a)
    if result["pending"]:
        print("待審核：")
        for o in result["pending"]:
            print(f"  {o['id']}  {o['side']} {o['qty']} {o['symbol']} @ {o['price_ref']:.2f}  "
                  f"名目 {o['notional']:,.0f}  停損 {o['stop']:.2f}  到期 {o['expires']}")
            print(f"      {o['reason']}")
    if result["report"]:
        print("\n" + result["report"]["text"])
    return 0


def cmd_status(args):
    desk = build(args)
    s = desk.state.data
    prices = {k: p["last_price"] for k, p in s["positions"].items()}
    print(f"權益 {desk.state.equity(prices):,.0f}  現金 {s['cash']:,.0f}  回撤 {desk.state.drawdown():.1%}  "
          f"kill switch {'ON' if s['kill_switch']['active'] else 'off'}")
    for sym, p in s["positions"].items():
        upl = (p["last_price"] - p["avg_price"]) * p["qty"]
        print(f"  {sym:6} {p['qty']:>6} @ {p['avg_price']:.2f}  現價 {p['last_price']:.2f}  未實現 {upl:+,.0f}  "
              f"停損 {p['stop']:.2f} 停利 {p['target']:.2f}")
    cmd_pending(args, desk)
    return 0


def cmd_pending(args, desk=None):
    desk = desk or build(args)
    pend = desk.broker.pending()
    print(f"待審核 {len(pend)} 張")
    for o in pend:
        print(f"  {o['id']}  {o['side']} {o['qty']} {o['symbol']} @ {o['price_ref']:.2f}  名目 {o['notional']:,.0f}  到期 {o['expires']}")
        print(f"      {o['reason']}")
    return 0


def cmd_approve(args):
    desk = build(args)
    ids = [o["id"] for o in desk.broker.pending()] if args.all else args.ids
    if not ids:
        print("沒有待審核單。")
        return 0
    for oid in ids:
        fill = desk.approve(oid)
        print(f"{oid}: " + (f"成交 {fill['side']} {fill['qty']} {fill['symbol']} @ {fill['price']:.2f}" if fill else "找不到或已處理"))
    return 0


def cmd_reject(args):
    desk = build(args)
    for oid in args.ids:
        print(f"{oid}: " + ("已駁回" if desk.reject(oid, args.note) else "找不到或已處理"))
    return 0


def cmd_report(args):
    desk = build(args)
    reports = desk.state.data["reports"]
    if not reports:
        print("還沒有日報。")
        return 0
    print(reports[-1]["text"])
    return 0


def cmd_killswitch(args):
    desk = build(args)
    desk.set_kill_switch(args.mode == "on", reason="人工啟動")
    print("kill switch", args.mode)
    return 0


def cmd_reset(args):
    desk = build(args)
    if not args.yes:
        ans = input("這會清空所有紙上交易狀態，輸入 yes 確認：")
        if ans.strip().lower() != "yes":
            print("取消。")
            return 1
    desk.state.reset()
    from .export import export_dashboard

    export_dashboard(desk.cfg, desk.state, {})
    print("已重設。")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="agent_desk", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--offline", action="store_true", help="用合成資料，不連網")
    p.add_argument("--demo-news", action="store_true", help="離線模式下塞幾則假新聞")
    p.add_argument("--seed", type=int, default=42)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run").set_defaults(fn=cmd_run)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("pending").set_defaults(fn=cmd_pending)
    a = sub.add_parser("approve"); a.add_argument("ids", nargs="*"); a.add_argument("--all", action="store_true"); a.set_defaults(fn=cmd_approve)
    sub.add_parser("approve-all").set_defaults(fn=cmd_approve, all=True, ids=[])
    r = sub.add_parser("reject"); r.add_argument("ids", nargs="+"); r.add_argument("--note", default=""); r.set_defaults(fn=cmd_reject)
    sub.add_parser("report").set_defaults(fn=cmd_report)
    k = sub.add_parser("killswitch"); k.add_argument("mode", choices=["on", "off"]); k.set_defaults(fn=cmd_killswitch)
    rs = sub.add_parser("reset"); rs.add_argument("--yes", action="store_true"); rs.set_defaults(fn=cmd_reset)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
