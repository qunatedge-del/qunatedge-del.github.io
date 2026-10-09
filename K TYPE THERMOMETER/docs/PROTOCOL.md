# USB 序列通訊協定（草案 v0.1）

Type-C 接上電腦後，CH340N 在電腦端出現一個虛擬 COM 埠（Windows 需裝 WCH 驅動；macOS/Linux 多半內建）。
**115200 baud, 8N1, 無流控；以 LF（`\n`）結尾的 ASCII 文字行。** 這是設計草案，韌體尚未實作；
`pc-logger/ktherm_proto.py` 與 `pc-logger/ktherm_logger.html` 已按本文件實作並互相驗證。

## 裝置 → 電腦

| 類型 | 格式 | 說明 |
|---|---|---|
| 資訊 | `# <文字>` | 開機訊息，如 `# KTHERM 4CH FW1.0` |
| 即時取樣 | `$T,<seq>,<epoch>,<t1>,<t2>,<t3>,<t4>,<cjc>,<flags>*<CS>` | `STREAM 1` 時每個取樣週期一行 |
| 機內記錄 | `$L,<idx>,<epoch>,<t1>,<t2>,<t3>,<t4>,<cjc>,<flags>*<CS>` | `LOG DUMP` 的回應 |
| 記錄結束 | `$L,END,<count>*<CS>` | |
| 回應 | `OK` ／ `ERR <code>` ／ 其他文字 | 對指令的回覆 |

- `seq`：取樣序號（十進位，開機歸零）；`epoch`：RTC 的 Unix 秒（未設時間為 0 起算）。
- `t1..t4`：°C、**固定 1 位小數**（`23.4`、`-200.0`、`1372.0`）；或 `OPEN`（沒接熱電偶）／`OVR`（超出 −200…1372 °C）。
- `cjc`：冷端（NTC）溫度，°C、2 位小數。
- `flags`：十六進位位元欄：bit0 電池低、bit1 充電中、bit2 機內記錄中、bit3 HOLD。
- `CS`：`$` 與 `*` 之間所有字元的 **XOR**，兩位大寫十六進位。例：本體 `ABC` → `40`。
- 電腦端遇到校驗錯誤的行應丟棄並計數，不可中斷記錄。

範例：
```
$T,12,1760000000,23.4,-200.0,OPEN,1372.0,24.57,5*<CS>
```

## 電腦 → 裝置（以 CR/LF 結尾，不分大小寫）

| 指令 | 回應 | 說明 |
|---|---|---|
| `*IDN?` | `KTHERM,4CH,FW<ver>,SN<hex>` | 識別 |
| `STREAM 0` / `STREAM 1` | `OK` | 關/開即時串流（開機預設 0） |
| `RATE <ms>` | `OK` ／ `ERR 2` | 取樣週期 500…60000 ms（預設 1000）；LCD、串流、機內記錄共用 |
| `TIME <epoch>` | `OK` | 設定 RTC（Unix 秒，UTC） |
| `TIME?` | `TIME <epoch>` | 讀 RTC |
| `UNIT C` / `UNIT F` | `OK` | 只影響 LCD 顯示；串流與記錄一律 °C |
| `LOG START` / `LOG STOP` | `OK` | 脫機記錄開關（按鍵 LOG 同效） |
| `LOG?` | `LOG <on\|off>,<count>,<capacity>` | 狀態 |
| `LOG DUMP` | 多行 `$L,…` + `$L,END,<n>*CS` | 傳出全部機內記錄（傳輸期間暫停串流） |
| `LOG ERASE` | `OK` | 清除機內記錄 |
| `CAL?` | `CAL <ch>,<offset_uV>,<gain>…` | 讀校正係數（工廠用） |

錯誤碼：`ERR 1` 指令不認得、`ERR 2` 參數錯誤、`ERR 3` 忙碌（例如正在 DUMP）。

## 機內記錄格式（EEPROM，16 byte/筆，little-endian）

| offset | 型別 | 內容 |
|---|---|---|
| 0 | u32 | epoch（秒） |
| 4 | i16 ×4 | CH1…CH4，單位 0.1 °C；`0x7FFF`＝OPEN，`0x7FFE`＝OVR |
| 12 | i16 | CJC，單位 0.01 °C |
| 14 | u16 | flags |

AT24CM01 = 131072 byte → 8192 筆，環狀覆寫或寫滿即停（韌體選項）。標頭頁放寫入指標與筆數。
EEPROM 頁寫入 256 byte、約 5 ms，記錄時一筆一筆寫即可。
