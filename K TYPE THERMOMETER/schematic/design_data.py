# -*- coding: utf-8 -*-
"""
Single source of truth for the 4-channel K-type thermometer / logger.
Used by gen_schematic.py (drawing), gen_bom.py (BOM) and the docs.
"""

PROJECT = "4-CH K-TYPE THERMOMETER / LOGGER"
PROJECT_ZH = "四通道 K 型溫度計 / 溫度記錄器"
REV = "A (draft)"
DATE = "2026-10-09"

# --------------------------------------------------------------------------
# BOM  (ref -> part).  Passives are generic; ICs carry real MPNs.
# --------------------------------------------------------------------------
PARTS = {}


def _add(refs, value, pkg, desc, cat, mfr="Generic", mpn="-", notes=""):
    for r in refs:
        assert r not in PARTS, "duplicate refdes " + r
        PARTS[r] = dict(value=value, pkg=pkg, desc=desc, cat=cat,
                        mfr=mfr, mpn=mpn, notes=notes)


# ---- ICs ----
_add(["U1"], "SD93F115B-JQS", "LQFP100 14x14 0.5mm",
     "32-bit MCU SoC: 18/20-bit SD-ADC+PGIA, LCD driver 4COMx44SEG, RTC, UART/I2C/SPI",
     "IC", "SDIC (晶華微)", "SD93F115B-JQS",
     "LQFP100 chosen for 4COM x 39 usable SEG + charge pump (see docs)")
_add(["U2"], "TP4054", "SOT-23-5", "1S Li-ion linear charger, 500 mA (R18=2k)", "IC",
     "TOPPOWER / equiv. LTC4054", "TP4054", "Pinout = LTC4054: 1 CHRG,2 GND,3 BAT,4 VCC,5 PROG")
_add(["U3", "U4"], "XC6206P332MR", "SOT-23", "3.3 V 200 mA low-Iq LDO. U3 = system rail VDD (from battery); U4 = USB-UART bridge rail (from VBUS)", "IC",
     "Torex", "XC6206P332MR", "3-pin SOT-23: verify pin order against the vendor datasheet. Do not use a 40 uA-Iq LDO as U3 (sleep current)")
_add(["U5"], "CH340N", "SOP-8", "USB to UART bridge, no crystal, VCC=V3=3.3 V", "IC",
     "WCH (沁恆)", "CH340N", "Verify SOP-8 pin numbers against CH340N datasheet before layout")
_add(["U6"], "AT24CM01-SSHD-T", "SOIC-8", "1 Mbit (128 KB) I2C EEPROM - stand-alone log memory", "IC",
     "Microchip", "AT24CM01-SSHD-T", "A1,A2 and WP tied to GND, A0 NC; 24C512 is a drop-in if cost matters")
_add(["U7"], "USBLC6-2SC6", "SOT-23-6", "USB D+/D- ESD protection", "IC",
     "STMicroelectronics", "USBLC6-2SC6", "")
_add(["Q1"], "MMBT3904", "SOT-23", "NPN, LCD backlight switch (optional)", "Discrete", "onsemi", "MMBT3904")
_add(["F1"], "PTC 0.5 A hold", "1206", "Resettable fuse on VBUS", "Discrete", "Bourns", "MF-NSMF050-2")

# ---- connectors / electromechanical ----
_add(["J1", "J2", "J3", "J4"], "K-type mini socket", "PCB / panel",
     "Miniature thermocouple jack, ANSI yellow, flat-pin (K)", "Connector",
     "Omega / equiv.", "SMPW-K-F (or equivalent)",
     "Pin 1 = K+ (chromel, yellow-labelled +), pin 2 = K- (alumel). Metal body away from heat sources")
_add(["J5"], "USB Type-C 16P", "SMD", "USB 2.0 Type-C receptacle, 16-pin", "Connector",
     "HRO / equiv.", "TYPE-C-31-M-12", "CC1/CC2 5.1k pull-downs fitted")
_add(["J6"], "JST PH 2P", "THT/SMD", "Battery connector (1S Li-ion/LiPo with protection PCM)", "Connector",
     "JST", "B2B-PH-K-S", "Red = +, black = -. Pack MUST have a protection circuit")
_add(["J7"], "FPC 43P 0.5mm", "SMD", "LCD interface (4 COM + 39 SEG) - match to custom glass", "Connector",
     "Generic", "-", "Or zebra / pin header, depends on glass vendor")
_add(["J8"], "2P 1.25mm", "SMD", "LCD backlight LED connector (optional)", "Connector", "Generic", "-", "DNP if no backlight")
_add(["P2"], "1x5 pad/header", "2.54mm", "ISP UART: 3V3, BOOT, RXD1, TXD1, GND (vendor ref P2)", "Connector",
     "Generic", "-", "Not needed in normal use - firmware can be loaded through the Type-C bridge")
_add(["P3"], "1x5 pad/header", "2.54mm", "SWD debug: 3V3, TCK, TMS, BOOT, GND (vendor ref P3)", "Connector",
     "Generic", "-", "")
_add(["P4"], "1x4 header", "2.54mm", "UART0 expansion: 3V3, TXD0, RXD0, GND (BT/WiFi module etc.)", "Connector",
     "Generic", "-", "DNP / optional")
_add(["SW1", "SW2", "SW3", "SW4", "SW5"], "Tact switch", "SMD 6x6 / 3x4",
     "Front-panel keys: POWER/BL, MODE, HOLD, MAX/MIN, LOG", "Electromech", "Generic", "-", "")
_add(["SW6"], "Tact switch", "SMD 3x4", "Hardware reset", "Electromech", "Generic", "-", "")
_add(["SW7"], "SPDT slide switch", "SMD", "Battery on/off (isolates load, charger still works)", "Electromech",
     "Generic", "-", "")
_add(["SW8"], "Tact switch", "SMD 3x4", "BOOT select (ISP) - optional", "Electromech", "Generic", "-",
     "DNP until BOOT polarity is confirmed with SDIC")
_add(["BZ1"], "Piezo 4 kHz", "12 mm", "Passive piezo buzzer, driven differentially by BUZ0/BUZB0", "Electromech",
     "Generic", "-", "No driver transistor needed")
_add(["Y1"], "32.768 kHz 12.5 pF", "3215", "RTC crystal on XIN1/XOUT1 (P00/P01)", "Crystal",
     "Epson / equiv.", "FC-135 or equivalent", "+-20 ppm")

# ---- resistors ----
_add(["R1", "R4", "R7", "R10"], "22 MΩ 1%", "1206", "TC bias pull-up to AVDDR (open-TC detect)", "Passive",
     notes="High-value: clean flux, no leakage path. >= 200 V rated")
_add(["R2", "R5", "R8", "R11"], "5.1 MΩ 1%", "0805", "TC bias pull-down to ACM (open-TC detect)", "Passive",
     notes="Open-circuit node = ACM + 339 mV at AVDDR=3.0 V")
_add(["R3", "R6", "R9", "R12"], "1 kΩ 1%", "0603", "TC input series resistor (RC filter)", "Passive")
_add(["R13"], "300 kΩ 1%", "0603", "CJC NTC network: current-setting resistor", "Passive",
     notes="Value cancels out in the ratiometric calculation")
_add(["R14"], "10 kΩ 0.1% 25ppm", "0603", "CJC NTC network: ratiometric reference", "Passive",
     notes="Precision part: sets CJC accuracy")
_add(["R15", "R16"], "470 kΩ 1%", "0603", "VBAT sense divider (1/2)", "Passive",
     notes="4.5 uA drain at 4.2 V")
_add(["R17"], "10 kΩ", "0603", "RST_B pull-up", "Passive")
_add(["R18"], "2.0 kΩ 1%", "0603", "TP4054 PROG: sets 500 mA charge current", "Passive",
     notes="Use 4k for 250 mA if the cell is < 500 mAh")
_add(["R19"], "100 kΩ", "0603", "USB_DET divider (top)", "Passive")
_add(["R20"], "120 kΩ", "0603", "USB_DET divider (bottom)", "Passive", notes="VBUS 4.5 V -> 2.45 V (> VIH 2.31 V)")
_add(["R21", "R22"], "5.1 kΩ 1%", "0603", "USB-C CC1 / CC2 pull-downs", "Passive")
_add(["R23"], "10 kΩ", "0603", "UART1 TXD1 -> CH340N RXD series (limits back-power)", "Passive",
     notes="Firmware must tri-state TXD1 when USB_DET = 0")
_add(["R24"], "1 kΩ", "0603", "UART1 RXD1 <- CH340N TXD series", "Passive")
_add(["R25"], "10 kΩ", "0603", "BOOT pull-up (DNP until polarity confirmed)", "Passive", notes="DNP")
_add(["R26", "R27"], "4.7 kΩ", "0603", "I2C SDA / SCL pull-ups", "Passive")
_add(["R28"], "1 kΩ", "0603", "Backlight transistor base resistor", "Passive")
_add(["R29"], "per LED", "0603", "Backlight LED current-limit resistor", "Passive",
     notes="Calculate from LED Vf / If; fed from VBAT_SW")
_add(["R30"], "100 kΩ", "0603", "Backlight base pull-down", "Passive")
_add(["RT1"], "NTC 10 kΩ 1% B3380", "0603", "Cold-junction sensor", "Passive",
     "Murata", "NCP18XH103F03RB",
     "Place at the thermocouple jacks (isothermal with J1-J4), away from U3/U1")

# ---- capacitors ----
_add(["C1", "C2", "C3", "C4"], "100 nF X7R", "0603", "TC input filter (K+ node to ACM)", "Passive")
_add(["C5", "C6"], "100 nF X7R", "0603", "CJC network filter (across R14 / across RT1)", "Passive")
_add(["C7"], "100 nF X7R", "0603", "ACM to GND (vendor reference C9)", "Passive")
_add(["C8"], "100 nF X7R", "0603", "VBAT sense filter", "Passive")
_add(["C9"], "1 µF X7R", "0603", "VDD bulk at U1 pin 8", "Passive")
_add(["C10"], "100 nF X7R", "0603", "VDD HF decoupling at U1", "Passive")
_add(["C11"], "100 nF X7R", "0603", "AVDDR filter (pin 9) to AVSS", "Passive")
_add(["C12"], "100 nF X7R", "0603", "ACM 1.2 V reference filter (pin 10) to AVSS", "Passive")
_add(["C13"], "1 µF X7R", "0603", "DVDDR (pin 62) to DVSS", "Passive", notes="Vendor ref uses 1 uF; datasheet text says >= 0.1 uF")
_add(["C14"], "1 µF X7R", "0603", "VLCD (pin 3) to VDD", "Passive")
_add(["C15"], "100 nF X7R", "0603", "LCD charge pump flying cap, CN (pin 1) - CP (pin 2)", "Passive")
_add(["C16"], "100 nF X7R", "0603", "RST_B filter", "Passive")
_add(["C17"], "1 µF X7R 10V", "0603", "TP4054 VCC input", "Passive")
_add(["C18"], "4.7 µF X5R 10V", "0805", "TP4054 BAT output", "Passive")
_add(["C19"], "1 µF X7R 10V", "0603", "U3 input", "Passive")
_add(["C20"], "10 µF X5R 10V", "0805", "U3 output / VDD bulk", "Passive")
_add(["C21", "C22"], "1 µF X7R 10V", "0603", "U4 input / output", "Passive")
_add(["C23"], "100 nF X7R", "0603", "CH340N VCC decoupling", "Passive")
_add(["C24", "C25", "C26", "C27", "C28"], "100 nF X7R", "0603", "Key debounce / ESD", "Passive")
_add(["C29", "C30"], "18 pF C0G", "0603", "32.768 kHz crystal load capacitors", "Passive",
     notes="Re-tune for the layout: CL = C/2 + Cstray = 12.5 pF")
_add(["C31"], "100 nF X7R", "0603", "U6 decoupling", "Passive")

CATEGORY_ORDER = ["IC", "Discrete", "Passive", "Crystal", "Connector", "Electromech"]

# --------------------------------------------------------------------------
# SD93F115B-JQS (LQFP100) pin names, from datasheet table 2
# --------------------------------------------------------------------------
PIN_NAMES = {
    1: "CN", 2: "CP", 3: "VLCD", 4: "NC", 5: "VSS", 6: "AVSS", 7: "AVDD", 8: "VDD", 9: "AVDDR", 10: "ACM",
    11: "A0", 12: "A1", 13: "A2", 14: "A3", 15: "A4/P83", 16: "A5/P82", 17: "A6/P81", 18: "A7/P80",
    19: "P06/KEY6", 20: "P05/KEY5", 21: "P04/KEY4/ADC0", 22: "P03/KEY3/ADC1", 23: "P02/KEY2/ADC2",
    24: "NC", 25: "NC", 26: "NC", 27: "P01/KEY1/XOUT1", 28: "P00/KEY0/XIN1",
    29: "P17/PWM0/PDM0", 30: "P16/PWM1/PDM1", 31: "P15/BUZ0", 32: "P14/BUZB0", 33: "P13/TXD0", 34: "P12/RXD0",
    35: "NC", 36: "NC", 37: "P11/SEG43/SCL", 38: "P10/SEG42/SDA", 39: "P27/SEG41/CS", 40: "P26/SEG40/MOSI",
    41: "P25/SEG39/MISO", 42: "P24/SEG38/SCK", 43: "P23/SEG37/T0CK", 44: "P22/SEG36/PFD",
    45: "P21/SEG35/INT0", 46: "P20/SEG34/INT1", 47: "P37/SEG33/TXD1", 48: "P36/SEG32/RXD1",
    49: "NC", 50: "NC", 51: "NC", 52: "P35/SEG31/CLKout", 53: "P34/SEG30/CCP", 54: "P33/SEG29/BUZ1",
    55: "P32/SEG28/BUZB1", 56: "P31/SEG27/BOOT", 57: "P30/SEG26/LBTIN", 58: "P47/SEG25/AUD",
    59: "P46/SEG24/DAO", 60: "P45/SEG23", 61: "NC", 62: "DVDDR", 63: "DVSS", 64: "P44/SEG22",
    65: "P43/SEG21", 66: "P42/SEG20", 67: "P41/SEG19", 68: "P40/SEG18", 69: "P57/SEG17", 70: "P56/SEG16",
    71: "P55/SEG15", 72: "P54/SEG14", 73: "P53/SEG13", 74: "P52/SEG12", 75: "NC", 76: "NC", 77: "NC",
    78: "P51/SEG11", 79: "P50/SEG10", 80: "P67/SEG9", 81: "P66/SEG8", 82: "P65/SEG7", 83: "P64/SEG6",
    84: "P63/SEG5", 85: "P62/SEG4", 86: "P61/COM7/SEG3", 87: "P60/COM6/SEG2", 88: "P77/COM5/SEG1",
    89: "NC", 90: "P76/COM4/SEG0", 91: "P75/COM3", 92: "P74/COM2", 93: "P73/COM1", 94: "P72/COM0",
    95: "P71/XOUT2", 96: "P70/XIN2", 97: "TMS/TXD1", 98: "TCK/RXD1", 99: "RST_B", 100: "NC",
}
assert len(PIN_NAMES) == 100

# SEG number -> LQFP100 pin
SEG_PIN = {0: 90, 1: 88, 2: 87, 3: 86, 4: 85, 5: 84, 6: 83, 7: 82, 8: 81, 9: 80, 10: 79, 11: 78,
           12: 74, 13: 73, 14: 72, 15: 71, 16: 70, 17: 69, 18: 68, 19: 67, 20: 66, 21: 65, 22: 64,
           23: 60, 24: 59, 25: 58, 26: 57, 27: 56, 28: 55, 29: 54, 30: 53, 31: 52, 32: 48, 33: 47,
           34: 46, 35: 45, 36: 44, 37: 43, 38: 42, 39: 41, 40: 40, 41: 39, 42: 38, 43: 37}
COM_PIN = {0: 94, 1: 93, 2: 92, 3: 91}

# SEG lines given to the LCD (others are used by BOOT / UART1 / I2C)
RESERVED_SEG = {27: "BOOT (P31)", 32: "RXD1 (UART1)", 33: "TXD1 (UART1)", 42: "SDA (I2C)", 43: "SCL (I2C)"}
LCD_SEGS = [s for s in range(44) if s not in RESERVED_SEG]
assert len(LCD_SEGS) == 39

# J7 pin plan: 1-4 COM0-3, 5.. SEG lines in ascending order
J7 = []
for c in range(4):
    J7.append(("COM%d" % c, COM_PIN[c]))
for s in LCD_SEGS:
    J7.append(("SEG%d" % s, SEG_PIN[s]))
assert len(J7) == 43

# Net names of the non-LCD pins (what the schematic flags say)
PIN_NET = {
    1: "LCD_CN (C15)", 2: "LCD_CP (C15)", 3: "VLCD (C14 to VDD)", 5: "GND", 6: "GND", 7: "VDD",
    8: "VDD (C9, C10)", 9: "AVDDR (C11)", 10: "ACM (C12)",
    11: "TC1 (J1 via R3)", 12: "TC2 (J2 via R6)", 13: "TC3 (J3 via R9)", 14: "TC4 (J4 via R12)",
    15: "CJC_A (R13/R14 node)", 16: "CJC_B (R14/RT1 node)", 17: "VBAT_SENSE (R15/R16)",
    18: "CHRG_N (U2 pin 1)",
    19: "KEY6 - POWER/BL (SW1)", 20: "KEY5 - MODE (SW2)", 21: "KEY4 - HOLD (SW3)",
    22: "KEY3 - MAX/MIN (SW4)", 23: "KEY2 - LOG (SW5)",
    27: "XOUT1 (Y1)", 28: "XIN1 (Y1)", 29: "BL_PWM (Q1)", 30: "USB_DET (R19/R20)",
    31: "BUZ_P (BZ1)", 32: "BUZ_N (BZ1)", 33: "UART0_TXD (P4)", 34: "UART0_RXD (P4)",
    37: "-- unused SEG43 (I2C SCL) --", 38: "-- unused SEG42 (I2C SDA) --",
    47: "UART1_TXD -> U5 RXD (R23)", 48: "UART1_RXD <- U5 TXD (R24)",
    56: "BOOT (P2, P3, SW8)", 62: "DVDDR (C13)", 63: "GND", 97: "SWD_TMS (P3)", 98: "SWD_TCK (P3)",
    99: "RST_B (R17, C16, SW6)",
}
PIN_NET[37] = "I2C_SCL (U6, R27)"
PIN_NET[38] = "I2C_SDA (U6, R26)"
for _s in LCD_SEGS:
    _j = [i for i, (n, p) in enumerate(J7, 1) if n == "SEG%d" % _s][0]
    PIN_NET[SEG_PIN[_s]] = "LCD SEG%d -> J7.%d" % (_s, _j)
for _c in range(4):
    PIN_NET[COM_PIN[_c]] = "LCD COM%d -> J7.%d" % (_c, _c + 1)

# --------------------------------------------------------------------------
# LCD glass proposal: 4 COM x 39 SEG
#   per channel  9 SEG lines: [sign/label] + 4 digits x 2 lines
#   global       3 SEG lines: unit + status icons
#   digit mapping (2 lines, 4 COM):  line A: COM0=a COM1=f COM2=e COM3=d
#                                    line B: COM0=b COM1=g COM2=c COM3=DP
# --------------------------------------------------------------------------
LCD_PLAN = []   # (seg, J7 pin, mcu pin, owner, com0, com1, com2, com3)
_idx = 0
for _ch in range(4):
    LCD_PLAN.append((LCD_SEGS[_idx], 0, 0, "CH%d sign/label" % (_ch + 1),
                     "minus", "CH%d label" % (_ch + 1), "OPEN/ERR", "spare"))
    _idx += 1
    for _d in range(4):
        LCD_PLAN.append((LCD_SEGS[_idx], 0, 0, "CH%d digit %d (A)" % (_ch + 1, _d + 1), "a", "f", "e", "d"))
        _idx += 1
        LCD_PLAN.append((LCD_SEGS[_idx], 0, 0, "CH%d digit %d (B)" % (_ch + 1, _d + 1), "b", "g", "c", "DP"))
        _idx += 1
_glob = [("global 1", "°C", "°F", "HOLD", "MAX"),
         ("global 2", "MIN", "LOG/REC", "USB/PC", "BATT frame"),
         ("global 3", "BATT bar 1", "BATT bar 2", "BATT bar 3", "spare")]
for g in _glob:
    LCD_PLAN.append((LCD_SEGS[_idx], 0, 0, g[0], g[1], g[2], g[3], g[4]))
    _idx += 1
assert _idx == 39
LCD_PLAN = [(s, [i for i, (n, p) in enumerate(J7, 1) if n == "SEG%d" % s][0], SEG_PIN[s]) + tuple(rest)
            for (s, _a, _b, *rest) in LCD_PLAN]

# --------------------------------------------------------------------------
# Notes shown on the schematic / in the docs
# --------------------------------------------------------------------------
SCHEM_NOTES = [
    "1. TC front-end copied from SDIC ref. SDH260013 (SZ37 V1.0): 22M/5.1M open-detect bias, 1k + 100nF per channel. Read A0..A3 single-ended vs ACM, PGIA gain 32 (+/-75 mV @ Vref 2.4 V).",
    "2. Open thermocouple: K+ node floats to ACM + 339 mV (AVDDR = 3.0 V) -> ADC over-range -> firmware shows 'OPEn'. Use UNGROUNDED / insulated probes only (all K- share ACM).",
    "3. CJC: A4-A5 = current (R14), A5-ACM = NTC voltage; R_NTC = R14 x V(A5-ACM) / V(A4-A5). Ratiometric, use PGIA gain 4. Mount RT1 touching the J1-J4 terminals.",
    "4. USB-C bridge CH340N runs from its own 3.3 V LDO (U4, from VBUS) so it draws nothing from the battery. Firmware must set TXD1 (P37) to input when USB_DET = 0.",
    "5. BOOT polarity / ISP entry is not specified in datasheet v0.1 - confirm with SDIC before fitting R25 / SW8 (both DNP).",
    "6. LCD: custom glass 4 COM x 39 SEG, 1/3 bias, VLCD from internal charge pump (C14, C15). See page 3 for the segment plan. SEG27/32/33/42/43 are not available (BOOT, UART1, I2C).",
]
