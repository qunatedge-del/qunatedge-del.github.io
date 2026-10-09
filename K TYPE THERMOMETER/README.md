# 四通道 K 型溫度計 / 溫度記錄器（SD93F115B）

**狀態：Rev A 草稿（設計階段，尚未打樣）** · 日期 2026-10-09

用 SDIC（晶華微）**SD93F115B**（18/20-bit Σ-Δ ADC + LCD 驅動 + 32-bit MCU）做 4 通道 K 型熱電偶溫度計，
有 LCD 顯示，Type-C 接電腦當 **溫度記錄器（logger）**，也可脫機記錄。
熱電偶前端直接採用 SDIC 官方參考設計 SDH260013（SZ37 V1.0）的做法，不需要外加運放或 ADC。

## 檔案

| 路徑 | 內容 |
|---|---|
| `schematic/ktherm…schematic.pdf` | **線路圖**（A3，3 頁：圖面 / 100 腳腳位分配 / LCD 玻璃規劃） |
| `schematic/ktherm…schematic.html` | 同一份線路圖的網頁版（可縮放）＋腳位表＋LCD 表＋BOM |
| `schematic/ktherm…schematic.svg` | 向量圖 |
| `bom/ktherm_thermometer_BOM.xlsx` / `.csv` | 零件表（92 件，按類別小計） |
| `pc-logger/ktherm_logger.html` | **電腦端記錄器**：雙擊用 Chrome/Edge 開啟即可，免安裝（Web Serial）。加 `?demo=1` 或按「示範模式」可無硬體預覽 |
| `pc-logger/ktherm_logger.py` | 命令列記錄器（`pip install pyserial`），輸出 CSV |
| `firmware/ktype.c/.h` | K 型 mV↔°C 轉換（NIST ITS-90），含主機端自我測試 |
| `docs/PROTOCOL.md` | USB 序列通訊協定 |
| `docs/FIRMWARE_PLAN.md` | 韌體架構、ADC 掃描流程、校正方法 |
| `docs/BRINGUP_AND_LAYOUT.md` | 打樣前確認事項、PCB 佈局要點、上電測試步驟 |
| `reference/` | 兩份原廠文件與參考產品照片 |

重新產生圖面/BOM：`python3 schematic/gen_schematic.py && python3 schematic/gen_bom.py`
（腳本會檢查圖上每個位號都在 BOM 裡、BOM 每個位號都有畫在圖上，目前 92 / 92）。

## 系統方塊

```
 K 型插座 ×4 ──22M/5.1M 偏壓 + 1k/100nF──► A0..A3 ─┐
 NTC 冷端(CJC) ─► A4,A5                              ├─► SD93F115B-JQS ──► LCD（4COM×39SEG）
 電池分壓 ──────► A6                                 │   (Σ-Δ ADC+PGIA、RTC、    ► 蜂鳴器、背光
                                                     │    LCD 驅動、32-bit MCU)  ◄ 5 顆按鍵
 USB-C ─► CH340N ─► UART1 ◄──────────────────────────┘                           ► I²C EEPROM(脫機記錄)
 USB-C VBUS ─► TP4054 充電 ─► 1S 鋰電池 ─► XC6206 3.3 V ─► VDD
```

## 主要設計決定與理由

| 項目 | 決定 | 理由 |
|---|---|---|
| MCU 封裝 | **LQFP100**（SD93F115B-JQS） | 4COM 可用 SEG 最多、有電荷泵（VLCD 最高 5.2 V）；64 腳版沒有 CN/CP，也只剩 33 SEG，放不下 4 通道×4 位數 |
| 熱電偶前端 | 官方參考做法：AVDDR─22 MΩ─K+─5.1 MΩ─ACM、1 kΩ + 100 nF，單端讀 A0..A3（對 ACM） | 官方已驗證；不用外部運放，PGIA 增益 32（±75 mV）涵蓋 K 型 −5.9…+54.9 mV |
| 開路偵測 | 未接熱電偶時 K+ 浮到 ACM + 339 mV（AVDDR=3.0 V）→ ADC 超量程 → LCD 顯示 `OPEn` | 同上，不需額外元件 |
| 冷端補償 | NTC 10 kΩ（Murata NCP18XH103F03RB, B=3380）+ R14 10 kΩ 0.1 %，**比例式**量測 | 結果只取決於 R14 與 NTC，與電流/Vref 無關；R_NTC = R14·V(A5−ACM)/V(A4−A5) |
| USB | USB-C ＋ **CH340N**（USB→UART，免晶振），接 UART1 | 晶片沒有 USB；UART1 同時是官方 ISP 燒錄口，所以**也能經 Type-C 更新韌體** |
| CH340N 供電 | 自己的 3.3 V LDO（U4，取自 VBUS） | 拔掉 USB 時完全不耗電池；TXD1 串 10 kΩ 限制倒灌，韌體在 USB 未接時把 TXD1 設為輸入 |
| 電源 | 1S 鋰電池（需帶保護板）＋ TP4054 充電（500 mA）＋ 低靜態電流 3.3 V LDO（XC6206，Iq 約 1 µA） | **這是我的假設**（使用者未指定），照片中的參考產品也是 2 pin 電池接頭。要改乾電池只需換 D 區 |
| 時鐘 | 內部 24 MHz RC（±1 %）；外加 32.768 kHz 晶振給 RTC | 記錄需要時間戳；不需要高頻晶振 |
| 脫機記錄 | I²C EEPROM AT24CM01（128 KB）＝ 8192 筆 | 1 s/筆約 2.3 小時，60 s/筆約 5.7 天；要更長可改 SPI Flash（代價：SEG 線不夠，見「待確認」） |
| 蜂鳴器 | 無源壓電片，BUZ0/BUZB0 差動直驅 | 省一顆驅動電晶體 |

## 腳位使用摘要（完整 100 腳表見 PDF 第 2 頁）

| 功能 | 腳位 | 說明 |
|---|---|---|
| TC1–TC4 | 11–14（A0–A3） | 單端，對 ACM |
| CJC | 15、16（A4、A5） | 比例式 NTC |
| VBAT 偵測 | 17（A6） | 電池 ½ 分壓；A6−ACM = 0.30…0.90 V，PGIA 增益 1 |
| CHRG_N | 18（P80） | TP4054 充電中＝低 |
| 按鍵 KEY2–KEY6 | 23…19（P02–P06） | 內部上拉；可從 STOP 喚醒 |
| 32.768 kHz | 28/27（P00/P01） | RTC |
| 背光 PWM／USB_DET | 29／30（P17／P16） | USB_DET = VBUS 分壓 100k/120k（4.5 V → 2.45 V > VIH） |
| 蜂鳴器 | 31、32（BUZ0/BUZB0） | 差動 |
| UART1（USB 橋 + ISP） | 47、48（P37/P36） | 115200 8N1 |
| UART0（擴充排針 P4） | 33、34 | 預留藍牙/WiFi 模組 |
| I²C（EEPROM） | 37、38（P11/P10） | 佔用 SEG43/42 |
| LCD | COM0–3：94–91；39 條 SEG | 見 PDF 第 3 頁 |
| BOOT／SWD／RST | 56／97、98／99 | 官方參考相同 |

## LCD（需要訂製玻璃）

4COM × 39SEG、1/3 bias。每通道 9 條 SEG 線（符號/標籤 1 條 + 4 位數 × 2 條），共 36 條，
另 3 條放 °C/°F、HOLD、MAX/MIN、LOG、USB、電池格。**SEG27（BOOT）、SEG32/33（UART1）、SEG42/43（I²C）不能給 LCD。**
完整 J7 腳位與每個 COM/SEG 的段定義在 PDF 第 3 頁，可直接交給玻璃廠。

## 精度（估算，非保證）

| 誤差來源 | 量級 | 說明 |
|---|---|---|
| ADC 雜訊 | < 0.01 °C rms | 原廠規格書：增益 256、OSR 4096 時 ENOB 18.06 bit（68.6 nV rms）；增益 32 的數據原廠未給，需實測 |
| ADC 解析度 | 0.57 µV/LSB ≈ 0.015 °C | ±75 mV、18 bit |
| 冷端補償 | ±0.5 … 1 °C | NTC 1 % ≈ ±0.26 °C @25 °C；主要取決於 NTC 與端子溫度是否一致（佈局） |
| 偏壓電流 | ≤ 0.05 °C | 66 nA × 30 Ω 迴路電阻 ≈ 2 µV |
| 熱電偶本身 | Class 1：±1.5 °C 或 0.4 %；Class 2：±2.5 °C 或 0.75 % | 儀器無法改善 |

目標：做過 2 點校正後 **±(0.3 % 讀值 + 1 °C)**（設計目標，需打樣後驗證）。

## 掃描時間與電池

ADC 250 kHz、OSR 4096 ≈ 61 sps，每通道丟 2 筆、平均 4 筆 ≈ 98 ms；4 個熱電偶 + 2 次 CJC 量測 ≈ **0.6 s**。
所以預設取樣週期 1 s；0.5 s 需把平均降為 2 筆（≈ 0.4 s）。
以平均 1–2 mA（顯示 + 1 Hz 記錄）估，800 mAh 電池約 14–28 天（**粗估**，需實測）；休眠（STOP）規格 ≤ 25 µA；加上 LDO、VBAT 分壓（4.5 µA）與 TP4054 漏電，整機預估約 35–45 µA，800 mAh 可待機一年以上（估算）。

## 重要使用限制

1. **只能用絕緣（ungrounded）探頭。** 4 個通道的 K− 全部接到同一個 ACM；接地型探頭碰到同一塊金屬或接地物體，
   會互相短路甚至把 ACM（1.2 V 基準）拉到地。USB 連接電腦時地線與電腦相通，風險更高。
   需要量接地型探頭請改用隔離 USB（如 ADuM3160）加隔離電源，這會是下一版。
2. 22 MΩ / 5.1 MΩ 是高阻抗節點：焊接後務必清洗助焊劑、板面不可有漏電路徑。
3. RT1（NTC）必須貼近 K 型插座的金屬端子，遠離 U3、MCU、背光等熱源，否則冷端補償會有梯度誤差。

## 待你確認（我先用預設值往下做）

| # | 問題 | 目前預設 | 影響 |
|---|---|---|---|
| 1 | 電池/供電 | 1S 鋰電池 + USB-C 充電 | 改乾電池/只用 USB 供電要改 D 區 |
| 2 | LCD | 訂製玻璃 4COM×39SEG | 要用現成玻璃的話需要先選玻璃，再回頭改 SEG 分配 |
| 3 | 脫機記錄 | 128 KB EEPROM（1 s/筆 ≈ 2.3 h） | 要更長：改 SPI Flash，但 SEG 線只剩 35 條，LCD 需縮減 |
| 4 | BOOT 腳極性 | 規格書 v0.1 沒寫，R25/SW8 先 DNP | 請向 SDIC 索取燒錄說明，或用 SWD |
| 5 | 探頭類型 | 絕緣型 | 若有接地型探頭需求要加隔離 |
| 6 | 韌體 | 先交付設計與轉換函式庫，ADC/LCD 暫存器驅動需要 SDIC SDK | 請提供 SDK/範例碼，或告訴我要不要先做 PC 端 |

## 已驗證 / 未驗證

已驗證（在本環境實際跑過）：
- `firmware/ktype.c` 對 18 個 NIST ITS-90 K 型參考點：正向誤差 < 0.0005 mV，反向 < 0.07 °C（全範圍來回最大 0.067 °C，出現在 −200 °C）。
  `cd firmware && gcc -o t test_ktype.c ktype.c -lm && ./t`
- 通訊協定：Python 實作單元測試通過；網頁版的解析/組包與 Python 逐行比對一致；
  網頁記錄器在無頭 Chromium 示範模式下跑 6 秒：無 console 錯誤、即時曲線與 CSV 匯出正常。
- 線路圖：位號與 BOM 92/92 一致；腳位表由規格書第 5–7 頁抄錄並檢查 100 腳無重複使用。

**未驗證：** 沒有實體硬體，所以 Web Serial 實際連線、CH340N 腳位編號、PGIA/AVDDR/Vref 暫存器設定、
BOOT 極性、LCD 實際顯示與所有電氣數字（電池壽命、精度）都需要打樣後確認。
圖中 CH340N（SOP-8）與 XC6206（SOT-23）的腳位編號是依我的記憶標示，**佈局前請對照廠商 datasheet**。
