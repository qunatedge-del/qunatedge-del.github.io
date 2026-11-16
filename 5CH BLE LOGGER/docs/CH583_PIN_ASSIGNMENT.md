# CH583M（QFN48）腳位分配與周邊電路

資料來源（都在 `reference/`）：WCH 官方 `CH583_datasheet_V1.9_en.pdf`（第 1.2 節腳位表、第 15 章 ADC、第 20 章參數）、
`CH583_EVT_schematic.pdf`（官方評估板線路圖）、`WCH_BLE_circuit_and_PCB_notes_zh.pdf`。
官方 repo：https://github.com/openwch/ch583 。**選 QFN48（CH583M）**：你的需求用到 `PB1`，而 PB1 只存在於 QFN48，QFN28 沒有。

## 1. 腳位分配（全部腳號來自規格書 1.2 節）

| 功能 | 網路 | 腳位 | 腳號 | 理由 |
|---|---|---|---|---|
| 5 片 SD6500 共用 SCK | `SCK` | PB0 | 24 | 單一 GPIO（你的需求） |
| CE8503 EN | `PB1` | PB1 | 23 | 你的原圖就叫 PB1 |
| SD6500 #1–#5 DATA | `DATA1`–`DATA5` | PB2–PB6 | 22,21,20,19,18 | **同一個 GPIO 埠的連續 5 位元**：一次讀埠暫存器就同時取樣 5 條，符合「平行取樣」 |
| 電池電壓偵測 | `VBAT_SENSE` | PA4（AIN0） | 36 | ADC 通道 |
| SPI0 → Flash：CS / SCK / MOSI / MISO | `FLASH_*` | PA12 / PA13 / PA14 / PA15 | 46 / 45 / 44 / 43 | SPI0 預設腳；PA12 的 SCS 是從機輸入，主機模式當 GPIO 做 CS |
| SPI1 → LCD：SCK / MOSI | `LCD_SCK`、`LCD_MOSI` | PA0 / PA1 | 39 / 40 | SPI1 只能做主機（LCD 剛好） |
| LCD DC / CS / RST | `LCD_DC`、`LCD_CS`、`LCD_RST` | PA2 / PA3 / PB8 | 41 / 42 / 8 | 一般 GPIO |
| 重設 | `RST_N` | PB23（RST#） | 25 | 低有效，內建上拉 |
| 下載 BOOT | `BOOT` | PB22 | 26 | EVT 做法 |
| SWD 除錯 | `SWDIO`、`SWDCK` | PB14 / PB15 | 12 / 11 | 啟用除錯介面後只當 TIO/TCK |
| UART1 除錯 | `UART1_RX`、`UART1_TX` | PA8 / PA9 | 5 / 6 | |
| 32.768 kHz（選用） | `X32KI`、`X32KO` | PA10 / PA11 | 48 / 47 | RTC / 睡眠時鐘 |
| 未使用（不接） | — | PA7→腳4, PB9→腳7, PB17→腳9, PB16→腳10, PB13→腳13, PB12→腳14, PB11→腳15, PB10→腳16, PB7→腳17, PB21→腳27, PB20→腳28, PB19→腳29, PB18→腳30, PA5→腳37, PA6→腳38（共 15 腳；腳號 = 規格書 QFN48） | 保留擴充，圖上標示為不接 |

DATA 與 SCK 的 GPIO 準位：CH583 VOH ≥ VIO33−0.4 V，SD6500 VIH = 0.7×VDD ≈ 2.3 V，相容。

## 2. 電源腳與周邊（依規格書 1.2 節與 EVT）

| 腳 | 名稱 | 做法 |
|---|---|---|
| 3 | VDD33 / VIO33（同一腳） | `VCC_3V3`；C41 2.2 µF |
| 1 / 35 | VDCID / VDCIA | 接在一起（規格書建議）；C42 2.2 µF、C43 0.1 µF |
| 2 | VSW | L1 10 µH 到 VDCID（規格書建議 10 µH，可用 3.3–33 µH；EVT 用 22 µH）。裝著電感，軟體可啟用晶片內 DC-DC；不啟用時它只是直流通路 |
| 33 | VINTA | C44 1 µF（規格書：啟用 DC-DC 時 1 µF） |
| 0 | EPAD | GND，底部鋪銅並多個過孔到背面地（WCH PCB 注意事項） |
| 31 / 32 | X32MO / X32MI | Y1 32 MHz；**不加外部負載電容**（內部可選 10–24 pF，EVT 同樣做法） |
| 34 | ANT | 直接接 PCB 天線 E1（WCH 範本 `ANT-F-2.4G-FR4.PcbDoc`）；天線必須有接地端 |

## 3. 電池偵測分壓的修正（CH583 ADC 實際規格）

規格書第 15 章：12 位元、內部參考 Vref = VINTA ≈ 1.05 V、輸入 0–VIO33；PGA 0 dB 時建議輸入 0–2 V（量程 2×Vref = 2.1 V）；
輸入緩衝建議開啟（高阻抗訊號源）。我上一版用的比例 0.4（6.4 V → 2.56 V）超出 0 dB 建議範圍。

改為 **R33 2.4 MΩ / R34 1.0 MΩ**（比例 1/3.4 = 0.294）：6.4 V → 1.88 V、3.6 V → 1.06 V，都在 0–2 V 內；耗電 6.4 V/3.4 MΩ = 1.9 µA；
每 LSB 約 0.5 mV × 3.4 ≈ 1.7 mV（電池端）。軟體設定：PGA 0 dB、緩衝開啟。

**注意：** 規格書絕對最大值 VIO ≤ VIO33 + 0.4 V。電池剛插入、VCC_3V3 還沒建立的幾毫秒內，`VBAT_SENSE`（約 1.9 V）會比 MCU 電源先到；
經 2.4 MΩ 限流後小於 1 µA，實務上可接受，但嚴格說超過額定，打樣時留意。

## 4. 對照使用者原需求的發現

- 規格書概述寫「supports at least 75V power voltage」是**筆誤**（參數表是 VDD33 最小 1.75 V，最大 3.6 V，絕對最大 4.2 V）。
  我們的 3.32 V（FB 容差下最大約 3.44 V）在範圍內。
- 「內建電池電壓偵測」只監測 VDD33（3.3 V 軌），**不能量 4 顆 AA 的電壓**，所以仍需要外部分壓。

## 5. 仍待確認

1. **SPI Flash 與 LCD 的型號**（目前只畫介面與典型腳位）。
2. Y1、Y2 的晶振規格（頻率容差、等效負載電容）：規格書文字沒有明確要求，請對照 WCH EVT 的 BOM。
3. 天線匹配與調校；天線附近的佈局（WCH PCB 注意事項）。
4. DC-DC 是否在軟體啟用（功耗取捨）；L1 取 10 µH 還是 EVT 的 22 µH。
5. 未使用 GPIO 是否要預留給背光、UART0 等。
