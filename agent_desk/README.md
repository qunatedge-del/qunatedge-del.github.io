# Agent Desk：一人交易桌的多代理紙上交易系統

這是把「350 個 AI 接管交易桌」那支影片裡真正可行的部分做出來的版本：
**6 到 7 個角色、規則優先、LLM 只在有事件時才醒來、所有進場都要人審核、全程紙上交易。**

```
DataAgent ──(news.new)──▶ SentimentAgent(LLM) ─┐
    │                                          ▼
    └──(bar.updated)──▶ SignalAgent(規則) ──▶ RiskAgent(硬上限) ──▶ PaperBroker
                                                                     │  進場 → 待審核佇列（人）
                                                                     │  出場 → 停損/停利自動
                                                                     ▼
                                     MonitorAgent(規則) ──▶ ReportAgent(LLM, 每日一次) ──▶ data/agent_desk.json ──▶ agent_desk.html
```

| 角色 | 檔案 | 用 LLM？ | 觸發條件 |
|---|---|---|---|
| 資料層 | `agents/data.py` | 否 | 每輪；只對「新 K 線」「沒看過的標題」發事件 |
| 新聞情緒 | `agents/sentiment.py` | **是** | 只有 `news.new` 事件才呼叫，所有標的打包成 1 次 |
| 訊號層 | `agents/signal.py` | 否 | 每輪；SMA20/50 趨勢 + 20 日突破 / 回檔 + RSI，情緒只做加減分 |
| 風控 | `agents/risk.py` | 否 | 每張進場單；單筆風險、部位上限、總曝險、持倉數、日虧損、回撤 kill switch |
| 執行層 | `agents/execution.py` | 否 | 進場單進待審核佇列；停損 / 停利 / 訊號翻空自動出場 |
| 監控 | `agents/reporter.py` | 否 | 每輪；回撤接近門檻、待審核單隔夜、資料過期、LLM 額度 |
| 日報 | `agents/reporter.py` | **是** | 只在「有新 K 線」且「今天還沒寫過」時呼叫 |

## 安裝（Mac）

```bash
git clone https://github.com/qunatedge-del/qunatedge-del.github.io.git
cd qunatedge-del.github.io
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # 可選；沒有的話情緒為中性、日報用模板
```

## 每天怎麼用

```bash
python -m agent_desk run          # 收盤後跑一輪：抓資料 → 情緒 → 訊號 → 風控 → 紙上執行 → 日報
python -m agent_desk pending      # 看有哪些進場單在等你
python -m agent_desk approve ORD-00012
python -m agent_desk reject ORD-00013 --note "財報前不進"
python -m agent_desk status       # 權益、持倉、待審核
python -m agent_desk report       # 印最新日報
python -m agent_desk killswitch on|off
open agent_desk.html              # 監控頁（或推上 GitHub Pages 後直接開網址）
```

離線試跑（不連網、合成行情）：`python -m agent_desk --offline --demo-news run`

> 監控頁用 `fetch` 讀 `data/agent_desk.json`。直接雙擊 HTML 有些瀏覽器會擋 `file://` 的 fetch，
> 用 `python3 -m http.server` 再開 `http://localhost:8000/agent_desk.html` 就好。

## 資料放哪裡

| 檔案 | 內容 | 要不要 commit |
|---|---|---|
| `agent_desk/config.json` | 觀察清單、風控參數、LLM 設定 | 要 |
| `data/agent_desk_state.json` | 現金、部位、成交、權益曲線、待審核單、看過的新聞、LLM 用量 | 要（這是你的帳本） |
| `data/agent_desk.json` | 監控頁讀的匯出檔 | 要（GitHub Pages 才看得到） |

沒有任何資料送到 Anthropic 以外的服務。送給模型的只有新聞標題和你的紙上部位摘要。

## 用 GitHub Actions 自動跑、用手機審核

`.github/workflows/agent_desk.yml` 會在每個交易日收盤後自動 `run` 並把結果 commit 回 repo。
在 repo 的 Settings → Secrets 加 `ANTHROPIC_API_KEY` 就會啟用 LLM。

審核可以不用開電腦：GitHub App → Actions → Agent Desk → Run workflow，
選 `approve` 並填單號。結果一樣會 commit，監控頁跟著更新。

注意：如果你同時在本機和 Actions 上操作，先 `git pull` 再動，不然狀態檔會衝突。

## 風控硬上限（`config.json` 的 `risk`）

- `risk_per_trade_pct` 0.01：一筆最多虧 1% 權益，用 2 ATR 停損反推股數
- `max_position_pct` 0.10、`max_gross_exposure_pct` 0.60、`max_positions` 6
- `max_daily_loss_pct` 0.02：當日虧 2% 就不開新倉
- `max_drawdown_pct` 0.10：回撤 10% 觸發 kill switch，只有人能解除
- `cooldown_days` 3：出場後同一檔 3 天內不再進

這一層永遠不呼叫 LLM，其他代理也繞不過它。

## LLM 成本

- 每天最多 `max_calls_per_day` 次（預設 20），超過就退回規則式行為並告警
- 實際用量：情緒 1 次（只在有新標題時）+ 日報 1 次。一天大約 2 到 3 次呼叫，成本以美分計
- 模型預設 `claude-opus-5`；用環境變數 `AGENT_DESK_MODEL` 或 `config.json` 換

## 換交易標的

改 `config.json` 的 `watchlist`，任何 yfinance 支援的代碼都可以：`2330.TW`、`0050.TW`、`BTC-USD`、`GC=F`。
目前只做多、日線。選擇權不在範圍內。

## 測試

```bash
python -m pytest -q tests
```

26 個測試涵蓋：訊號規則、風控每一條上限、紙上成交與滑價、停損停利、審核閘門、
多日整合流程（LLM 只在事件時被呼叫、同一天重跑零呼叫、kill switch 擋新倉、狀態可重載）。

## 接下來可以加的

1. 回測模式：把 `DataAgent` 換成歷史切片，跑同一套規則看幾年績效
2. 情緒代理的事件粒度：財報日前後自動改 `horizon_days`
3. 真實券商 API（IBKR、Alpaca）：只換 `PaperBroker.execute`，其他都不用動。但那是幾個月後的事
