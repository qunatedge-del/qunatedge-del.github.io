# 韌體規劃（未實作）

SD93F115B 的 ADC/PGIA/LCD 暫存器細節在原廠規格書 v0.1 裡沒有（只有概要與電氣特性），
**實際驅動需要 SDIC 的 SDK 或暫存器手冊**。以下是不依賴暫存器細節的架構與演算法；
已實作並驗證的只有 `firmware/ktype.c`（K 型轉換）。

## 模組

| 模組 | 內容 |
|---|---|
| `adc_scan` | 依序切換 A0…A3、A4/A5 並讀 Σ-Δ ADC |
| `ktype` | mV↔°C（已完成，NIST ITS-90） |
| `cjc` | NTC 比例式量測 → 冷端溫度 |
| `lcd` | 依 `schematic/design_data.py` 的 LCD_PLAN 建立段碼表、寫顯示 RAM |
| `keys` | KEY2…KEY6 中斷（去彈跳 20 ms、長按） |
| `rtc` / `log` | RTC 時間戳；I²C EEPROM 記錄 |
| `usb_proto` | UART1 指令解析與 `$T/$L` 組包（見 PROTOCOL.md） |
| `power` | STOP/DOZE 休眠、USB_DET、電池電量 |

## 取樣掃描（每個取樣週期一次）

1. 開 AVDDR（3.0 V）與 ACM（1.2 V），等穩定。
2. **熱電偶**：A0…A3 各自對 ACM 單端量測；PGIA 增益 32、OSR 4096、ADC 250 kHz（≈ 61 sps）；
   切換通道後丟 2 筆（SINC3 建立時間）、再平均 4 筆 ≈ 98 ms/通道。
   Vref×增益要涵蓋 ±55 mV：Vref = 2.4 V 用增益 32（±75 mV）；若 Vref 只能用 1.2 V（ACM）則用增益 16（±75 mV）。
3. **冷端**：增益 4（±600 mV）量 V_R14 = A4−A5 與 V_NTC = A5−ACM；R_NTC = 10 kΩ × V_NTC / V_R14。
   用 NTC 的 B 值或 3 點 Steinhart–Hart 轉成 °C。
   NTC 電壓範圍（AVDDR=3.0 V）：−10 °C 229 mV、0 °C 150 mV、25 °C 56 mV、50 °C 24 mV、85 °C 8.6 mV。
4. **開路判斷**：未接熱電偶時 A0…A3 ≈ ACM + 339 mV，遠超過 ±75 mV 量程 → ADC 飽和 → 該通道標 `OPEN`。
   另判斷 mV 超出 −5.891…54.886 → `OVR`。
5. 計算：`T = ktype_compensate(V_mV_校正後, T_cjc)`。
6. 更新 LCD、送 `$T` 串流、需要時寫入 EEPROM，然後關閉類比電路並休眠到下次。

全部掃描約 0.6 s（4 熱電偶 + 2 次冷端量測），所以最短取樣週期 1 s；0.5 s 需把平均降為 2 筆（≈ 0.4 s）。

## 校正

- 每通道：**偏移**（輸入短路或接 ACM 讀值）＋**增益**（以精密 mV 源如 K 型校正器，在 ≈ 40 mV 一點）。係數存 Flash。
- 冷端：在 25 °C 與另一個溫度（如 50 °C）對照參考溫度計，修正 NTC 偏移（單點）或 B 值（兩點）。
- 驗證：冰水點（0 °C）與沸水（依海拔修正）或乾井爐。

## 電源狀態

- 顯示中：LCD 持續，掃描間隔以 DOZE（約 25 µA 等級）等待。
- POWER 鍵長按或 5 分鐘無操作：關 LCD 進 STOP（規格書 ≤ 25 µA）；任一 KEY 或 UART RXD1 下降緣喚醒。
- **USB_DET = 0 時把 TXD1（P37）設為輸入**：CH340N 無電時，TXD1 經 10 kΩ 會倒灌約 0.27 mA。
- 電池格數由 A6 讀值換算（VBAT = 2×(V_A6−ACM + 1.2 V)），低於約 3.3 V 顯示低電並旗標 bit0。

## 韌體更新

UART1 同時是 ISP 口。正常做法：按住 BOOT（SW8）再按 RESET，用 SDIC 的燒錄工具經 Type-C 橋接更新。
**BOOT 極性規格書 v0.1 沒有寫**，R25/SW8 先不焊；也可以用 P3 的 SWD。

## 下一步（需要你提供）

1. SDIC SDK / 暫存器手冊 / 範例碼（ADC、PGIA、LCD、RTC、KEY、UART）。
2. 開發環境（IDE/編譯器、燒錄器型號）。
3. LCD 玻璃定案後，用 LCD_PLAN 產生段碼表。
