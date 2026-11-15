# 5-Channel K-Type BLE Data Logger (CH583 + 5×SD6500)

狀態：**線路圖草稿 Rev A 已完成**（AFE 採用 IC 工廠 SDH260018 V1.0-2）；CH583 / Flash / LCD 腳號 TBD。

| 路徑 | 內容 |
|---|---|
| `schematic/5ch_logger_schematic.pdf` / `.html` / `.svg` | **線路圖**（HTML 版含網路表、BOM、位號對照） |
| `netlist/5ch_logger_netlist.json` / `.csv`、`5ch_logger_pin_table.csv` | **網路表**（本機 KiCad 以此為準） |
| `bom/5ch_logger_BOM.csv` | 零件表 |
| `docs/FACTORY_V1_TO_V2.md` | 工廠 V1.0→V1.0-2 差異、與原需求對照、我們偏離工廠之處、位號對照表 |
| `docs/HANDOFF_LOCAL_CLAUDE.md` | 交給本機 Claude Code + KiCad MCP 的交接文件（先讀） |
| `docs/PROJECT_BRIEF.md` | 原始需求（原文） |
| `reference/` | SD6500、CE8503 規格書、使用者電源圖、工廠兩版檔案 |

重新產生：`cd schematic && python3 gen5.py`（會檢查網路表完整性、與工廠網路表一致、圖面與零件 66/66 一致）。

與 `../K TYPE THERMOMETER/`（SD93F115B 的 4 通道版本）是**不同的設計**。
