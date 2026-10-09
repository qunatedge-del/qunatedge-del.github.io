# -*- coding: utf-8 -*-
"""
Generates the schematic for the 4-ch K-type thermometer:
    ktype_thermometer_schematic.svg / .pdf (A3, 3 pages) / .html (self-contained)
Run:  python3 gen_schematic.py
"""
import os
import sys
import html

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from design_data import (PARTS, PIN_NAMES, PIN_NET, SEG_PIN, COM_PIN, LCD_SEGS, J7, LCD_PLAN, RESERVED_SEG,
                         SCHEM_NOTES, PROJECT, PROJECT_ZH, REV, DATE, CATEGORY_ORDER)
from sheet import (Sheet, INK, RED, GND_C, BLUE, ORG, GREY, netcol)

W, H = 2000, 1414
S = Sheet(W, H)

# section colours (pastel fill, saturated border)
COL = {
    "A": ("#fff3e0", "#ef6c00"),
    "B": ("#fff8e1", "#f9a825"),
    "C": ("#e8eaf6", "#3949ab"),
    "D": ("#ffebee", "#c62828"),
    "E": ("#e3f2fd", "#1565c0"),
    "F": ("#f3e5f5", "#8e24aa"),
    "G": ("#e8f5e9", "#2e7d32"),
}


def section(key, x, y, w, h, title):
    f, b = COL[key]
    S.box(x, y, w, h, title, f, b)


def wc(net):
    return netcol(net)


# =========================================================================
# header
# =========================================================================
S.text(24, 40, "%s  ·  %s" % (PROJECT, PROJECT_ZH), 26, INK, "start", True)
S.text(24, 60, "MCU SD93F115B-JQS (LQFP100)  ·  4 x K-type thermocouple, SD-ADC + PGIA  ·  USB Type-C UART logger  ·  "
               "1S Li-ion + charger", 12.5, GREY)
lx = 1340
for i, (name, c) in enumerate((("Power", RED), ("GND", GND_C), ("Signal", BLUE), ("Analog", ORG))):
    S.line(lx + i * 150, 38, lx + i * 150 + 36, 38, c, 3.5)
    S.text(lx + i * 150 + 44, 43, name, 12, INK)
S.text(1976, 62, "Rev %s  ·  %s  ·  Sheet 1/3" % (REV, DATE), 11, GREY, "end")

# =========================================================================
# A  thermocouple inputs
# =========================================================================
section("A", 24, 70, 600, 636, "A  THERMOCOUPLE INPUTS x4  ·  熱電偶輸入  (22M/5.1M open-detect, 1k+100nF)")
tc_refs = [("J1", "R1", "R2", "R3", "C1"), ("J2", "R4", "R5", "R6", "C2"),
           ("J3", "R7", "R8", "R9", "C3"), ("J4", "R10", "R11", "R12", "C4")]
tc_pin = [11, 12, 13, 14]
for k, (j, rup, rdn, rs, cc) in enumerate(tc_refs):
    yb = 112 + k * 146
    nx, nrail = yb + 70, yb + 122
    S.text(36, yb + 14, "CH%d" % (k + 1), 15, ORG, "start", True)
    S.text(36, yb + 30, "→ U1 pin %d (A%d)" % (tc_pin[k], k), 9.5, GREY)
    # jack
    S.reg(j)
    S.rect(62, yb + 54, 58, 86, INK, "#fffde7", 3, 1.6)
    S.text(91, yb + 82, j, 11, INK, "middle", True)
    S.text(91, yb + 97, "K-type", 9, INK, "middle")
    S.text(91, yb + 109, "mini jack", 9, INK, "middle")
    S.text(112, nx + 4, "+", 12, INK, "end", True)
    S.text(112, nrail + 4, "-", 12, INK, "end", True)
    S.line(120, nx, 436, nx, ORG)
    S.line(120, nrail, 330, nrail, ORG)
    # 22M pull-up
    S.vcc(180, yb + 18, "AVDDR")
    S.res(180, yb + 18, rup, "22 MΩ", "v", 52, "r", RED)
    S.dot(180, nx, ORG)
    # 5.1M pull-down
    S.res(260, nx, rdn, "5.1 MΩ", "v", 52, "r", ORG)
    S.dot(260, nx, ORG); S.dot(260, nrail, ORG)
    # filter cap
    S.cap(332, nx, cc, "100 nF", 52, "r", ORG)
    S.dot(332, nx, ORG); S.dot(332, nrail, ORG)
    S.line(332, nrail, 346, nrail, ORG)
    S.flag(346, nrail, "ACM", "r")
    # series resistor
    S.res(350, nx, rs, "1 kΩ", "h", 60, "r", ORG)
    S.line(410, nx, 436, nx, ORG)
    S.flag(436, nx, "TC%d" % (k + 1), "r")
S.text(150, 701, "Open TC: K+ node floats to ACM + 339 mV → ADC over-range → 'OPEn'", 9, GREY)

# =========================================================================
# B  CJC + battery sense
# =========================================================================
section("B", 24, 716, 600, 300, "B  COLD-JUNCTION NTC + BATTERY SENSE  ·  冷端補償 / 電池偵測")
b = 770
cx = 160
S.vcc(cx, b, "AVDDR")
S.res(cx, b, "R13", "300 kΩ", "v", 60, "r", RED)
S.res(cx, b + 60, "R14", "10 kΩ 0.1%", "v", 60, "r", ORG)
S.ntc(cx, b + 120, "RT1", "NTC 10 kΩ 1%", 60)
n1, n2, n3 = b + 60, b + 120, b + 180
S.dot(cx, n1, ORG); S.dot(cx, n2, ORG); S.dot(cx, n3, ORG)
S.line(cx, n1, 262, n1, ORG); S.flag(262, n1, "CJC_A", "r")
S.line(cx, n2, 262, n2, ORG); S.flag(262, n2, "CJC_B", "r")
S.line(cx, n3, 250, n3, ORG); S.flag(250, n3, "ACM", "r")
# C5 across R14, C6 across RT1 on the left
xc = 96
S.line(cx, n1, xc, n1, ORG); S.line(cx, n2, xc, n2, ORG); S.line(cx, n3, xc, n3, ORG)
S.cap(xc, n1, "C5", "100 nF", 60, "l", ORG)
S.cap(xc, n2, "C6", "100 nF", 60, "l", ORG)
S.dot(xc, n1, ORG); S.dot(xc, n2, ORG); S.dot(xc, n3, ORG)
# C7 ACM to GND
S.cap(cx, n3, "C7", "100 nF", 34, "r", ORG)
S.gnd(cx, n3 + 34)
S.text(300, b + 204, "R_NTC = R14 × V(A5-ACM) / V(A4-A5)  ·  PGIA gain 4", 9.5, GREY)
S.text(300, b + 218, "RT1 must touch the J1-J4 terminals (isothermal block)", 9.5, GREY)
# battery sense
vx = 460
S.flag(vx - 8, b + 2, "VBAT_SW", "l")
S.line(vx - 8, b + 2, vx, b + 2, RED)
S.res(vx, b + 2, "R15", "470 kΩ", "v", 60, "r", RED)
S.res(vx, b + 62, "R16", "470 kΩ", "v", 60, "r", BLUE)
S.dot(vx, b + 62, ORG)
S.line(vx, b + 62, vx + 56, b + 62, ORG)
S.flag(vx + 56, b + 62, "VBAT_SENSE", "r")
S.gnd(vx, b + 122)
S.line(vx - 44, b + 122, vx, b + 122, GND_C)
S.cap(vx - 44, b + 62, "C8", "100 nF", 60, "l", ORG)
S.line(vx - 44, b + 62, vx, b + 62, ORG)
S.dot(vx - 44, b + 62, ORG)
S.text(vx - 40, b + 150, "A6 - ACM = VBAT/2 - 1.2 V", 9.5, GREY)
S.text(vx - 40, b + 164, "0.30 ... 0.90 V  →  PGIA gain 1", 9.5, GREY)

# =========================================================================
# C  MCU
# =========================================================================
section("C", 644, 70, 600, 1220, "C  MCU  U1  SD93F115B-JQS  ·  LQFP100  ·  單晶片 MCU")
UX, UY, UW, UH = 790, 112, 330, 1054
S.reg("U1")
S.rect(UX, UY, UW, UH, INK, "#fffde7", 4, 2.2)
S.text(UX + UW / 2, UY + 22, "U1  SD93F115B-JQS", 14, INK, "middle", True)
S.text(UX + UW / 2, UY + 38, "SDIC 32-bit MCU · 20-bit ADC · LCD driver · LQFP100", 10, GREY, "middle")

# left pins ------------------------------------------------------------
left = [
    (8, "VDD", "VDD"), (7, "AVDD", "VDD"), (9, "AVDDR", "AVDDR"), (10, "ACM", "ACM"), (62, "DVDDR", "DVDDR"),
    (3, "VLCD", "VLCD"), (1, "CN", "LCD_CN"), (2, "CP", "LCD_CP"),
    (5, "VSS", "GND"), (6, "AVSS", "GND"), (63, "DVSS", "GND"), None,
    (11, "A0", "TC1"), (12, "A1", "TC2"), (13, "A2", "TC3"), (14, "A3", "TC4"),
    (15, "A4 / P83", "CJC_A"), (16, "A5 / P82", "CJC_B"), (17, "A6 / P81", "VBAT_SENSE"),
    (18, "A7 / P80", "CHRG_N"), None,
    (99, "RST_B", "RST_B"), (56, "P31 / BOOT", "BOOT"), (98, "TCK / RXD1", "SWD_TCK"),
    (97, "TMS / TXD1", "SWD_TMS"), (28, "P00 / XIN1", "XIN1_32K"), (27, "P01 / XOUT1", "XOUT1_32K"),
]
y = UY + 70
step = 31
for e in left:
    if e is None:
        y += 14
        continue
    pin, lab, net = e
    S.line(UX - 16, y, UX, y, INK, 1.4)
    S.text(UX + 6, y + 3.6, lab, 10)
    S.text(UX - 4, y - 3, str(pin), 7.5, GREY, "end")
    S.line(UX - 16, y, UX - 26, y, wc(net))
    S.flag(UX - 26, y, net, "l")
    y += step

# right pins -----------------------------------------------------------
lcd_groups = [
    ("LCD_COM0-3", [("COM%d" % c, COM_PIN[c], "COM%d / P7%d" % (c, 2 + c)) for c in range(4)]),
    ("LCD_SEG0-3", [("SEG%d" % s, SEG_PIN[s], "SEG%d" % s) for s in range(0, 4)]),
    ("LCD_SEG4-26", [("SEG%d" % s, SEG_PIN[s], "SEG%d" % s) for s in range(4, 27)]),
    ("LCD_SEG28-31", [("SEG%d" % s, SEG_PIN[s], "SEG%d" % s) for s in range(28, 32)]),
    ("LCD_SEG34-41", [("SEG%d" % s, SEG_PIN[s], "SEG%d" % s) for s in range(34, 42)]),
]
dig = [
    (19, "P06 / KEY6", "KEY6"), (20, "P05 / KEY5", "KEY5"), (21, "P04 / KEY4", "KEY4"), (22, "P03 / KEY3", "KEY3"),
    (23, "P02 / KEY2", "KEY2"), (31, "P15 / BUZ0", "BUZ_P"), (32, "P14 / BUZB0", "BUZ_N"),
    (30, "P16", "USB_DET"), (29, "P17 / PWM0", "BL_PWM"), (37, "P11 / SCL", "I2C_SCL"), (38, "P10 / SDA", "I2C_SDA"),
    (47, "P37 / TXD1", "UART1_TXD"), (48, "P36 / RXD1", "UART1_RXD"), (33, "P13 / TXD0", "UART0_TXD"),
    (34, "P12 / RXD0", "UART0_RXD"),
]
npins = sum(len(g[1]) for g in lcd_groups) + len(dig)
ngaps = len(lcd_groups) + 1
rstep = (UH - 70 - 24 - ngaps * 9) / (npins - 1)
y = UY + 70
BX = UX + UW + 16
for gname, pins in lcd_groups:
    y0 = y
    for lab, pin, _ in pins:
        S.line(UX + UW, y, UX + UW + 16, y, INK, 1.4)
        S.text(UX + UW - 6, y + 3.4, lab if not lab.startswith("COM") else lab, 8.8, INK, "end")
        S.text(UX + UW + 3, y - 2.5, str(pin), 7, GREY, "start")
        S.line(UX + UW + 16, y, BX + 12, y, BLUE, 1.2)
        y += rstep
    ya, yb_ = y0, y - rstep
    S.line(BX + 12, ya, BX + 12, yb_, BLUE, 1.8)
    ym = (ya + yb_) / 2
    S.line(BX + 12, ym, BX + 20, ym, BLUE)
    S.flag(BX + 20, ym, gname, "r")
    y += 9
for pin, lab, net in dig:
    S.line(UX + UW, y, UX + UW + 16, y, INK, 1.4)
    S.text(UX + UW - 6, y + 3.4, lab, 9.5, INK, "end")
    S.text(UX + UW + 3, y - 2.5, str(pin), 7, GREY, "start")
    S.line(UX + UW + 16, y, UX + UW + 26, y, wc(net))
    S.flag(UX + UW + 26, y, net, "r")
    y += rstep

# decoupling strip -------------------------------------------------------
S.text(660, 1188, "U1 decoupling — place at the pins (analog caps against AVSS)", 10, GREY)
S.line(660, 1194, 1230, 1194, "#9fa8da", 1)
caps = [("C9", "1 µF", "VDD", None), ("C10", "100 nF", "VDD", None), ("C11", "100 nF", "AVDDR", None),
        ("C12", "100 nF", "ACM", None), ("C13", "1 µF", "DVDDR", None), ("C14", "1 µF", "VLCD", "VDD"),
        ("C15", "100 nF", "LCD_CN", "LCD_CP")]
for i, (ref, val, top, bot) in enumerate(caps):
    x = 700 + i * 78
    S.line(x, 1212, x, 1222, wc(top))
    S.text(x, 1209, top, 9, wc(top), "middle", True)
    S.cap(x, 1222, ref, val, 44, "r", wc(top))
    if bot is None:
        S.gnd(x, 1266)
    else:
        S.text(x, 1283, bot, 9, wc(bot), "middle", True)

# =========================================================================
# D  power
# =========================================================================
section("D", 1264, 70, 712, 310, "D  POWER  ·  USB VBUS → TP4054 CHARGER → Li-ion → 3.3 V LDO (U3)  ·  電源")
# row 1
r1 = 160
S.flag(1286, r1, "VBUS", "r")
S.line(1286 + 7 + 34 + 8, r1, 1352, r1, RED)
S.res(1352, r1, "F1", "PTC 0.5 A", "h", 64, "r", RED)
S.line(1416, r1, 1440, r1, RED)
S.dot(1440, r1, RED)
S.cap(1440, r1, "C17", "1 µF", 44, "r", RED)
S.gnd(1440, r1 + 44)
S.line(1440, r1, 1480, r1, RED)
u2 = S.ic(1494, 120, 130, 104, "U2", "TP4054  (SOT-23-5)",
          left=[(4, "VCC", 40), (2, "GND", 84)],
          right=[(3, "BAT", 40), (1, "CHRG", 62), (5, "PROG", 84)])
S.line(1480, r1, 1480, 120 + 40, RED)
S.line(1480, 120 + 40, 1494 - 14, 120 + 40, RED)
S.gnd(1494 - 14, 120 + 84)
bx, by_ = u2[("r", 3)]
S.line(bx, by_, 1728, by_, RED)
S.dot(1690, by_, RED)
S.cap(1690, by_, "C18", "4.7 µF", 44, "r", RED)
S.gnd(1690, by_ + 44)
S.text(1736, by_ - 8, "VBAT", 10, RED, "middle", True)
cx_, cy_ = u2[("r", 1)]
S.line(cx_, cy_, cx_ + 8, cy_, BLUE)
S.flag(cx_ + 8, cy_, "CHRG_N", "r")
px_, py_ = u2[("r", 5)]
S.line(px_, py_, 1660, py_, BLUE)
S.res(1660, py_, "R18", "2.0 kΩ", "v", 52, "r", BLUE)
S.gnd(1660, py_ + 52)
# J6 battery
S.reg("J6")
S.line(1728, by_, 1892, by_, RED)
S.rect(1892, 138, 70, 78, INK, "#fffde7", 3, 1.6)
S.text(1927, 160, "J6", 11, INK, "middle", True)
S.text(1927, 174, "JST-PH 2P", 9, INK, "middle")
S.text(1927, 186, "Li-ion + PCM", 9, INK, "middle")
S.text(1898, by_ + 4, "+", 12, INK, "start", True)
S.line(1892, 200, 1880, 200, GND_C)
S.text(1898, 204, "-", 12, INK, "start", True)
S.line(1880, 200, 1880, 204, GND_C)
S.gnd(1880, 204)
S.text(1812, 238, "1S cell, protected pack", 9, GREY, "middle")
# row 2
r2 = 294
S.flag(1286, r2, "VBAT", "r")
S.line(1286 + 7 + 38 + 8, r2, 1330, r2, RED)
S.reg("SW7")
S.line(1330, r2, 1352, r2, RED)
S.line(1388, r2, 1440, r2, RED)
S.circ(1352, r2, 2.6, INK, INK); S.circ(1388, r2, 2.6, INK, INK)
S.line(1352, r2, 1384, r2 - 14, INK, 1.8)
S.text(1370, r2 - 22, "SW7", 10.5, INK, "middle", True)
S.text(1370, r2 + 42, "slide, battery on/off", 8.5, INK, "middle")
S.dot(1440, r2, RED)
S.line(1440, r2, 1440, r2 - 42, RED)
S.flag(1440, r2 - 42, "VBAT_SW", "l")
S.cap(1440, r2, "C19", "1 µF", 40, "l", RED)
S.gnd(1440, r2 + 40)
S.reg("U3")
S.line(1440, r2, 1486, r2, RED)
S.rect(1486, r2 - 20, 100, 56, INK, "#fffde7", 3, 1.6)
S.text(1536, r2 - 2, "U3", 10.5, INK, "middle", True)
S.text(1536, r2 + 10, "XC6206P332", 8.5, INK, "middle")
S.text(1536, r2 + 22, "3.3 V LDO, Iq ~1 uA", 8.5, INK, "middle")
S.text(1491, r2 - 5, "IN", 8, GREY)
S.text(1581, r2 - 5, "OUT", 8, GREY, "end")
S.line(1536, r2 + 36, 1536, r2 + 44, GND_C)
S.gnd(1536, r2 + 44)
ox, oy = 1586, r2
S.line(ox, oy, 1720, oy, RED)
S.dot(1690, oy, RED)
S.cap(1690, oy, "C20", "10 µF", 44, "r", RED)
S.gnd(1690, oy + 44)
S.line(1720, oy, 1740, oy, RED)
S.flag(1740, oy, "VDD", "r")
# USB detect divider
S.flag(1862, 258, "VBUS", "l")
S.line(1862, 258, 1862, 270, RED)
S.res(1862, 270, "R19", "100 kΩ", "v", 44, "r", RED)
S.dot(1862, 314, BLUE)
S.line(1862, 314, 1884, 314, BLUE)
S.flag(1884, 314, "USB_DET", "r")
S.res(1862, 314, "R20", "120 kΩ", "v", 44, "r", BLUE)
S.gnd(1862, 358)

# =========================================================================
# E  USB-C + bridge
# =========================================================================
section("E", 1264, 396, 712, 440, "E  USB TYPE-C · CH340N UART BRIDGE · PROGRAMMING  ·  USB 連接 / 韌體燒錄")
ey = 40
# J5 USB-C
S.reg("J5")
jx, jy, jw, jh = 1286, 470 + ey - 40, 116, 214
S.rect(jx, jy, jw, jh, INK, "#fffde7", 3, 1.8)
S.text(jx + jw / 2, jy + 20, "J5  USB Type-C", 11, INK, "middle", True)
S.text(jx + jw / 2, jy + 34, "16P receptacle (USB 2.0)", 8.5, INK, "middle")
rows = {"VBUS": 62, "D+": 94, "D-": 142, "CC2": 172, "CC1": 198}
for nm, o in rows.items():
    S.line(jx + jw, jy + o, jx + jw + 14, jy + o, INK, 1.4)
    S.text(jx + jw - 6, jy + o + 3.4, nm, 9.5, INK, "end")
S.text(jx + 8, jy + 62 + 3, "A4 B4 A9 B9", 7.5, GREY)
S.text(jx + 8, jy + 94 + 3, "A6 B6", 7.5, GREY)
S.text(jx + 8, jy + 142 + 3, "A7 B7", 7.5, GREY)
S.text(jx + 8, jy + 172 + 3, "B5", 7.5, GREY)
S.text(jx + 8, jy + 198 + 3, "A5", 7.5, GREY)
S.line(jx + 40, jy + jh, jx + 40, jy + jh + 14, GND_C)
S.text(jx + 40, jy + jh - 6, "GND", 9.5, INK, "middle")
S.gnd(jx + 40, jy + jh + 14)
S.text(jx + 40, jy + jh + 40, "+ shell (A1/A12/B1/B12)", 8, GREY, "middle")
# VBUS flag
S.line(jx + jw + 14, jy + 62, jx + jw + 24, jy + 62, RED)
S.flag(jx + jw + 24, jy + 62, "VBUS", "r")
# D+ / D- straight to U7
u7 = S.ic(1530, jy + 78, 100, 80, "U7", "USBLC6-2SC6",
          left=[(1, "I/O1", 16), (3, "I/O2", 64)],
          right=[(6, "I/O1", 16), (4, "I/O2", 64)],
          top=[(5, "VBUS", 50)], bottom=[(2, "GND", 50)], inside=True)
S.line(jx + jw + 14, jy + 94, 1530 - 14, jy + 94, BLUE)
S.line(jx + jw + 14, jy + 142, 1530 - 14, jy + 142, BLUE)
S.text(1470, jy + 90, "USB_DP", 8.5, BLUE, "middle", True)
S.text(1470, jy + 138, "USB_DM", 8.5, BLUE, "middle", True)
tx_, ty_ = u7[("t", 5)]
S.line(tx_, ty_, tx_, ty_ - 14, RED)
S.flag(tx_, ty_ - 14, "VBUS", "r")
bx_, by2 = u7[("b", 2)]
S.gnd(bx_, by2)
# CC resistors
S.line(jx + jw + 14, jy + 172, 1494, jy + 172, BLUE)
S.res(1494, jy + 172, "R22", "5.1 kΩ", "v", 44, "r", BLUE)
S.gnd(1494, jy + 216)
# CC1 below: route to resistor at x=1420
S.line(jx + jw + 14, jy + 198, 1428, jy + 198, BLUE)
S.res(1428, jy + 198, "R21", "5.1 kΩ", "v", 40, "r", BLUE)
S.gnd(1428, jy + 238)
# U5 CH340N
u5 = S.ic(1670, jy + 78, 130, 100, "U5", "CH340N  (SOP-8)",
          left=[(5, "UD+", 16), (6, "UD-", 64)],
          right=[(2, "TXD", 16), (3, "RXD", 64)],
          top=[(8, "VCC", 38), (4, "V3", 88)], bottom=[(1, "GND", 62)], inside=True)
S.line(1630 + 14, jy + 94, 1670 - 14, jy + 94, BLUE)
S.line(1630 + 14, jy + 142, 1670 - 14, jy + 142, BLUE)
v1x, v1y = u5[("t", 8)]
v3x, v3y = u5[("t", 4)]
S.line(v1x, v1y, v1x, v1y - 12, RED)
S.line(v3x, v3y, v3x, v3y - 12, RED)
S.line(v1x, v1y - 12, v3x, v3y - 12, RED)
S.dot(v1x + 20, v1y - 12, RED)
S.line(v1x + 20, v1y - 12, v1x + 20, v1y - 24, RED)
S.flag(v1x + 20, v1y - 24, "VUSB3V3", "r")
gx, gy = u5[("b", 1)]
S.gnd(gx, gy)
# UART lines to MCU
txp = u5[("r", 2)]
rxp = u5[("r", 3)]
S.line(txp[0], txp[1], 1830, txp[1], BLUE)
S.res(1830, txp[1], "R24", "1 kΩ", "h", 54, "r", BLUE)
S.line(1884, txp[1], 1894, txp[1], BLUE)
S.flag(1894, txp[1], "UART1_RXD", "r")
S.line(rxp[0], rxp[1], 1830, rxp[1], BLUE)
S.res(1830, rxp[1], "R23", "10 kΩ", "h", 54, "r", BLUE)
S.line(1884, rxp[1], 1894, rxp[1], BLUE)
S.flag(1894, rxp[1], "UART1_TXD", "r")
# row 2: U4 3.3V LDO
r4 = 730 + 30
S.reg("U4")
S.flag(1316, r4 - 22, "VBUS", "l")
S.line(1316, r4 - 22, 1316, r4, RED)
S.dot(1316, r4, RED)
S.cap(1316, r4, "C21", "1 µF", 40, "r", RED)
S.gnd(1316, r4 + 40)
S.line(1316, r4, 1356, r4, RED)
S.rect(1356, r4 - 20, 84, 56, INK, "#fffde7", 3, 1.6)
S.text(1398, r4 - 2, "U4", 10.5, INK, "middle", True)
S.text(1398, r4 + 10, "XC6206P332", 8.5, INK, "middle")
S.text(1398, r4 + 22, "3.3 V LDO", 8.5, INK, "middle")
S.text(1361, r4 - 5, "IN", 8, GREY)
S.text(1435, r4 - 5, "OUT", 8, GREY, "end")
S.line(1398, r4 + 36, 1398, r4 + 44, GND_C)
S.gnd(1398, r4 + 44)
S.line(1440, r4, 1486, r4, RED)
S.dot(1486, r4, RED)
S.cap(1486, r4, "C22", "1 µF", 40, "r", RED)
S.gnd(1486, r4 + 40)
S.line(1486, r4, 1520, r4, RED)
S.flag(1520, r4, "VUSB3V3", "r")
S.flag(1640, r4 - 22, "VUSB3V3", "r")
S.line(1640, r4 - 22, 1640, r4 + 6, RED)
S.cap(1640, r4 + 6, "C23", "100 nF", 40, "r", RED)
S.gnd(1640, r4 + 46)
# P2 ISP header
S.reg("P2")
S.rect(1760, 706, 84, 104, INK, "#fffde7", 3, 1.6)
S.text(1802, 724, "P2  ISP", 10.5, INK, "middle", True)
p2 = [("1", "3V3", "VDD"), ("2", "BOOT", "BOOT"), ("3", "RXD1", "UART1_RXD"), ("4", "TXD1", "UART1_TXD"),
      ("5", "GND", None)]
for i, (n, lab, net) in enumerate(p2):
    yy = 738 + i * 16
    S.line(1844, yy, 1858, yy, wc(net) if net else GND_C)
    S.text(1768, yy + 3.4, "%s %s" % (n, lab), 9, INK)
    if net:
        S.flag(1858, yy, net, "r")
    else:
        S.gnd(1858, yy)
S.text(1802, 826, "(not needed: flash via Type-C bridge)", 8, GREY, "middle")

# =========================================================================
# F  keys + LCD connector
# =========================================================================
section("F", 24, 1026, 600, 264, "F  KEYS + LCD CONNECTOR  ·  按鍵 / LCD 介面")
keys = [("SW1", "POWER/BL", "KEY6", "C24"), ("SW2", "MODE", "KEY5", "C25"), ("SW3", "HOLD", "KEY4", "C26"),
        ("SW4", "MAX/MIN", "KEY3", "C27"), ("SW5", "LOG", "KEY2", "C28")]
for i, (sw, fn, net, cc) in enumerate(keys):
    x = 36 + i * 64
    S.flag(x, 1082, net, "r")
    S.line(x, 1082, x, 1112, BLUE)
    S.dot(x, 1112, BLUE)
    S.sw(x, 1112, sw, 56)
    S.gnd(x, 1168)
    S.line(x, 1112, x + 22, 1112, BLUE)
    S.cap(x + 22, 1112, cc, "100n", 44, "r", BLUE)
    S.line(x + 22, 1156, x + 22, 1168, GND_C)
    S.line(x, 1168, x + 22, 1168, GND_C)
    S.text(x + 10, 1200, sw, 10.5, INK, "middle", True)
    S.text(x + 10, 1213, fn, 8.5, INK, "middle")
S.text(36, 1250, "Internal 50k pull-ups enabled; any KEYx press wakes the MCU from STOP.", 9.5, GREY)
S.text(36, 1264, "Keys: POWER/BL (sleep + backlight), MODE (°C/°F), HOLD, MAX/MIN, LOG start/stop.", 9.5, GREY)
# J7
S.reg("J7")
jx7, jy7, jw7, jh7 = 474, 1060, 142, 200
S.rect(jx7, jy7, jw7, jh7, INK, "#fffde7", 3, 1.8)
S.text(jx7 + jw7 / 2, jy7 + 20, "J7  LCD 43P", 11, INK, "middle", True)
S.text(jx7 + jw7 / 2, jy7 + 33, "4COM x 39SEG glass", 8.5, INK, "middle")
grp = [("1–4", "COM0–3", "LCD_COM0-3"), ("5–8", "SEG0–3", "LCD_SEG0-3"), ("9–31", "SEG4–26", "LCD_SEG4-26"),
       ("32–35", "SEG28–31", "LCD_SEG28-31"), ("36–43", "SEG34–41", "LCD_SEG34-41")]
for i, (pn, sg, net) in enumerate(grp):
    yy = jy7 + 58 + i * 28
    S.line(jx7 - 14, yy, jx7, yy, BLUE)
    S.text(jx7 + 8, yy + 3.4, "%s   %s" % (pn, sg), 9.5)
    S.flag(jx7 - 14, yy, net, "l")
S.text(jx7 + jw7 / 2, jy7 + jh7 - 8, "VLCD: charge pump", 8, GREY, "middle")

# =========================================================================
# G  misc
# =========================================================================
section("G", 1264, 852, 712, 438, "G  RTC · EEPROM LOG · RESET · BUZZER · BACKLIGHT · DEBUG  ·  周邊")
# --- G1 RTC crystal (col 1)
gx0, gy0 = 1284, 902
S.text(gx0, gy0 - 8, "RTC 32.768 kHz", 10.5, INK, "start", True)
S.flag(gx0 + 100, gy0 + 40, "XIN1_32K", "l")
S.line(gx0 + 100, gy0 + 40, gx0 + 110, gy0 + 40, BLUE)
S.line(gx0 + 110, gy0 + 40, gx0 + 110, gy0 + 52, BLUE)
S.xtal(gx0 + 110, gy0 + 52, "Y1", "32.768k", 60, lab="l")
S.line(gx0 + 110, gy0 + 112, gx0 + 110, gy0 + 124, BLUE)
S.line(gx0 + 110, gy0 + 124, gx0 + 100, gy0 + 124, BLUE)
S.flag(gx0 + 100, gy0 + 124, "XOUT1_32K", "l")
S.dot(gx0 + 110, gy0 + 40, BLUE); S.dot(gx0 + 110, gy0 + 124, BLUE)
S.line(gx0 + 110, gy0 + 40, gx0 + 158, gy0 + 40, BLUE)
S.cap(gx0 + 158, gy0 + 40, "C29", "18p", 36, "r", BLUE)
S.gnd(gx0 + 158, gy0 + 76)
S.line(gx0 + 110, gy0 + 124, gx0 + 158, gy0 + 124, BLUE)
S.cap(gx0 + 158, gy0 + 124, "C30", "18p", 36, "r", BLUE)
S.gnd(gx0 + 158, gy0 + 160)

# --- G2 EEPROM (col 2)
ex, ey2 = 1500, 902
S.text(ex, ey2 - 8, "Log memory (stand-alone)", 10.5, INK, "start", True)
u6 = S.ic(ex + 20, ey2 + 6, 92, 100, "U6", "AT24CM01  128 KB",
          left=[(1, "A0", 20), (2, "A1", 38), (3, "A2", 56), (4, "VSS", 84)],
          right=[(8, "VCC", 20), (5, "SDA", 38), (6, "SCL", 56), (7, "WP", 84)])
nx_, ny_ = u6[("l", 1)]
S.line(nx_ - 2, ny_ - 5, nx_ - 12, ny_ + 5, GREY, 1.4)
S.line(nx_ - 2, ny_ + 5, nx_ - 12, ny_ - 5, GREY, 1.4)
for pn in (2, 3, 4):
    gx_, gy_ = u6[("l", pn)]
    S.gnd(gx_, gy_)
gx_, gy_ = u6[("r", 7)]
S.gnd(gx_, gy_)
vx_, vy_ = u6[("r", 8)]
S.line(vx_, vy_, vx_ + 6, vy_, RED); S.flag(vx_ + 6, vy_, "VDD", "r")
sx_, sy_ = u6[("r", 5)]
S.line(sx_, sy_, sx_ + 6, sy_, BLUE); S.flag(sx_ + 6, sy_, "I2C_SDA", "r")
cx2, cy2 = u6[("r", 6)]
S.line(cx2, cy2, cx2 + 6, cy2, BLUE); S.flag(cx2 + 6, cy2, "I2C_SCL", "r")
S.text(ex + 20, ey2 + 142, "pull-ups / bypass", 9, GREY)
for i, (ref, net) in enumerate((("R26", "I2C_SDA"), ("R27", "I2C_SCL"))):
    x = ex + 30 + i * 74
    S.flag(x, ey2 + 158, "VDD", "r")
    S.line(x, ey2 + 158, x, ey2 + 168, RED)
    S.res(x, ey2 + 168, ref, "4.7 kΩ", "v", 36, "r", BLUE)
    S.line(x, ey2 + 204, x, ey2 + 212, BLUE)
    S.flag(x, ey2 + 212, net, "r")
S.flag(ex + 178, ey2 + 158, "VDD", "r")
S.line(ex + 178, ey2 + 158, ex + 178, ey2 + 168, RED)
S.cap(ex + 178, ey2 + 168, "C31", "100 nF", 34, "r", RED)
S.gnd(ex + 178, ey2 + 202)

# --- G3 reset (col 3)
rx0, ry0 = 1770, 902
S.text(rx0 - 10, ry0 - 8, "Reset", 10.5, INK, "start", True)
S.vcc(rx0 + 20, ry0 + 20, "VDD")
S.res(rx0 + 20, ry0 + 20, "R17", "10 kΩ", "v", 52, "r", RED)
S.dot(rx0 + 20, ry0 + 72, BLUE)
S.line(rx0 + 20, ry0 + 72, rx0 + 70, ry0 + 72, BLUE)
S.flag(rx0 + 70, ry0 + 72, "RST_B", "r")
S.line(rx0 + 20, ry0 + 72, rx0 + 20, ry0 + 84, BLUE)
S.line(rx0 - 12, ry0 + 84, rx0 + 52, ry0 + 84, BLUE)
S.dot(rx0 + 20, ry0 + 84, BLUE)
S.cap(rx0 - 12, ry0 + 84, "C16", "100 nF", 44, "l", BLUE)
S.sw(rx0 + 52, ry0 + 84, "SW6", 52)
S.text(rx0 + 66, ry0 + 114, "SW6 reset", 9, INK)
S.gnd(rx0 - 12, ry0 + 128)
S.gnd(rx0 + 52, ry0 + 136)

# --- G4 buzzer + BOOT (col 1, lower)
bz_x, bz_y = 1284, 1090
S.text(bz_x, bz_y - 8, "Buzzer (differential drive)", 10.5, INK, "start", True)
S.reg("BZ1")
S.flag(bz_x, bz_y + 20, "BUZ_P", "r")
S.line(bz_x + 62, bz_y + 20, bz_x + 100, bz_y + 20, BLUE)
S.line(bz_x + 100, bz_y + 20, bz_x + 100, bz_y + 29, BLUE)
S.circ(bz_x + 120, bz_y + 38, 20, INK, "#ffffff", 1.6)
S.text(bz_x + 120, bz_y + 35, "BZ1", 10.5, INK, "middle", True)
S.text(bz_x + 120, bz_y + 47, "piezo", 8.5, INK, "middle")
S.flag(bz_x, bz_y + 56, "BUZ_N", "r")
S.line(bz_x + 62, bz_y + 56, bz_x + 100, bz_y + 56, BLUE)
S.line(bz_x + 100, bz_y + 56, bz_x + 100, bz_y + 47, BLUE)
S.text(bz_x, bz_y + 92, "BOOT select (DNP, polarity TBC)", 10.5, INK, "start", True)
S.vcc(bz_x + 30, bz_y + 120, "VDD")
S.res(bz_x + 30, bz_y + 120, "R25", "10 kΩ DNP", "v", 38, "r", RED)
S.dot(bz_x + 30, bz_y + 158, BLUE)
S.line(bz_x + 30, bz_y + 158, bz_x + 110, bz_y + 158, BLUE)
S.flag(bz_x + 110, bz_y + 158, "BOOT", "r")
S.sw(bz_x + 30, bz_y + 158, "SW8", 34)
S.text(bz_x + 44, bz_y + 180, "SW8 DNP", 9, INK)
S.gnd(bz_x + 30, bz_y + 192)

# --- G5 backlight (col 2, lower)
bl_x, bl_y = 1500, 1156
S.text(bl_x, bl_y - 10, "LCD backlight (optional)", 10.5, INK, "start", True)
S.flag(bl_x + 4, bl_y + 24, "VBAT_SW", "r")
S.line(bl_x + 78, bl_y + 24, bl_x + 90, bl_y + 24, RED)
S.res(bl_x + 90, bl_y + 24, "R29", "per LED", "h", 44, "r", RED)
S.line(bl_x + 134, bl_y + 24, bl_x + 146, bl_y + 24, RED)
S.reg("J8")
S.rect(bl_x + 146, bl_y + 8, 78, 34, INK, "#fffde7", 3, 1.6)
S.text(bl_x + 185, bl_y + 22, "J8 LED", 9.5, INK, "middle", True)
S.text(bl_x + 185, bl_y + 34, "A+      K-", 8, INK, "middle")
yb_ = bl_y + 88
S.flag(bl_x + 4, yb_, "BL_PWM", "r")
S.res(bl_x + 78, yb_, "R28", "1 kΩ", "h", 40, "r", BLUE, valpos="above")
S.line(bl_x + 118, yb_, bl_x + 140, yb_, BLUE)
S.dot(bl_x + 128, yb_, BLUE)
S.line(bl_x + 128, yb_, bl_x + 128, yb_ + 6, BLUE)
S.res(bl_x + 128, yb_ + 6, "R30", "100 kΩ", "v", 30, "l", BLUE)
S.gnd(bl_x + 128, yb_ + 36)
col_, em_ = S.npn(bl_x + 140, yb_, "Q1", "MMBT3904")
S.line(bl_x + 205, bl_y + 42, bl_x + 205, col_[1], BLUE)
S.line(bl_x + 205, col_[1], col_[0], col_[1], BLUE)
S.gnd(em_[0], em_[1])

# --- G6 debug headers (col 3, lower)
hx, hy = 1770, 1076
S.reg("P3")
S.rect(hx, hy, 84, 104, INK, "#fffde7", 3, 1.6)
S.text(hx + 42, hy + 18, "P3  SWD", 10.5, INK, "middle", True)
p3 = [("1", "3V3", "VDD"), ("2", "TCK", "SWD_TCK"), ("3", "TMS", "SWD_TMS"), ("4", "BOOT", "BOOT"), ("5", "GND", None)]
for i, (n, lab, net) in enumerate(p3):
    yy = hy + 34 + i * 16
    S.line(hx + 84, yy, hx + 98, yy, wc(net) if net else GND_C)
    S.text(hx + 8, yy + 3.4, "%s %s" % (n, lab), 9, INK)
    if net:
        S.flag(hx + 98, yy, net, "r")
    else:
        S.gnd(hx + 98, yy)
hy2 = 1196
S.reg("P4")
S.rect(hx, hy2, 84, 70, INK, "#fffde7", 3, 1.6)
S.text(hx + 42, hy2 + 16, "P4  UART0", 10.5, INK, "middle", True)
p4 = [("1", "3V3", "VDD"), ("2", "TXD0", "UART0_TXD"), ("3", "RXD0", "UART0_RXD"), ("4", "GND", None)]
for i, (n, lab, net) in enumerate(p4):
    yy = hy2 + 30 + i * 12
    S.line(hx + 84, yy, hx + 98, yy, wc(net) if net else GND_C)
    S.text(hx + 8, yy + 3.4, "%s %s" % (n, lab), 8.5, INK)
    if net:
        S.flag(hx + 98, yy, net, "r")
    else:
        S.gnd(hx + 98, yy)

# =========================================================================
# bottom: notes + title block
# =========================================================================
S.rect(24, 1304, 1500, 92, "#9e9e9e", "#fafafa", 6, 1.4)
S.text(36, 1322, "DESIGN NOTES  ·  設計備註", 11.5, INK, "start", True)
import textwrap
_ny = 1338
for n in SCHEM_NOTES:
    for j, ln in enumerate(textwrap.wrap(n, 235, subsequent_indent="    ")):
        S.text(36, _ny, ln, 8.6, "#444444")
        _ny += 10.5
tbx, tby, tbw, tbh = 1540, 1304, 436, 92
S.rect(tbx, tby, tbw, tbh, INK, "#ffffff", 0, 2)
S.line(tbx, tby + 28, tbx + tbw, tby + 28, INK, 1)
S.line(tbx, tby + 50, tbx + tbw, tby + 50, INK, 1)
S.line(tbx, tby + 71, tbx + tbw, tby + 71, INK, 1)
S.line(tbx + 250, tby + 50, tbx + 250, tby + tbh, INK, 1)
S.text(tbx + 10, tby + 21, "%s" % PROJECT, 12.5, INK, "start", True)
S.text(tbx + 10, tby + 43, "SCHEMATIC  ·  線路圖", 11, INK, "start", True)
S.text(tbx + 10, tby + 64, "MCU: SD93F115B-JQS (LQFP100)", 10, INK)
S.text(tbx + 10, tby + 85, "Power: USB-C 5 V / 1S Li-ion", 10, INK)
S.text(tbx + 260, tby + 64, "Rev: %s" % REV, 10, INK)
S.text(tbx + 260, tby + 85, "Date: %s" % DATE, 10, INK)
S.text(tbx + tbw - 8, tby + 43, "Sheet 1 of 3", 10, INK, "end")

# ---------------------------------------------------------------------------
# consistency check: every part in the BOM drawn exactly once, nothing extra
# ---------------------------------------------------------------------------
missing = sorted(set(PARTS) - S.refs)
extra = sorted(S.refs - set(PARTS))
if missing or extra:
    raise SystemExit("BOM/schematic mismatch  missing on sheet: %s   not in BOM: %s" % (missing, extra))


# =========================================================================
# outputs
# =========================================================================
def pin_rows():
    rows = []
    for p in range(1, 101):
        net = PIN_NET.get(p)
        if net is None:
            net = "NC - leave floating" if PIN_NAMES[p] == "NC" else "(unused)"
        rows.append((p, PIN_NAMES[p], net))
    return rows


def write_svg():
    path = os.path.join(HERE, "ktype_thermometer_schematic.svg")
    open(path, "w", encoding="utf-8").write(S.to_svg())
    return path


def write_pdf():
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.colors import HexColor

    zh_path = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
    pdfmetrics.registerFont(TTFont("ZH", zh_path, subfontIndex=0))
    fonts = dict(latin="Helvetica", latin_b="Helvetica-Bold", zh="ZH")
    pw, ph = 1190.55, 841.89
    path = os.path.join(HERE, "ktype_thermometer_schematic.pdf")
    c = canvas.Canvas(path, pagesize=(pw, ph))
    c.setTitle("4-CH K-type thermometer / logger - schematic (Rev %s)" % REV)
    c.setAuthor("Claude Code")
    S.draw_pdf(c, pw, ph, fonts)
    c.showPage()

    # ---- page 2: pin assignment
    T = Sheet(W, H)
    T.text(24, 40, "U1 SD93F115B-JQS (LQFP100) — PIN ASSIGNMENT  ·  腳位分配", 24, INK, "start", True)
    T.text(24, 60, "Datasheet v0.1 pin names  →  net / function in this design. NC pins must stay floating.", 12.5, GREY)
    rows = pin_rows()
    colw = 480
    for i, (p, nm, net) in enumerate(rows):
        col, r = divmod(i, 25)
        x = 24 + col * (colw + 12)
        y = 96 + r * 49
        used = net not in ("(unused)",) and not net.startswith("NC")
        bgc = "#f1f8e9" if used else ("#eeeeee" if net.startswith("NC") else "#fff8e1")
        T.rect(x, y, colw, 44, "#bdbdbd", bgc, 4, 1)
        T.text(x + 10, y + 28, str(p), 17, INK, "start", True)
        T.text(x + 56, y + 19, nm, 12.5, INK, "start", True)
        T.text(x + 56, y + 35, net, 11, "#37474f")
    T.text(24, 1340, "Green = used · Grey = NC (leave floating) · Amber = available GPIO/SEG not used in this design.", 12, GREY)
    T.text(24, 1362, "SEG27 (BOOT), SEG32/33 (UART1 ↔ USB bridge) and SEG42/43 (I2C EEPROM) are reserved, leaving 39 SEG lines for the LCD.",
           12, GREY)
    T.text(1976, 1390, "Sheet 2 of 3", 11, GREY, "end")
    T.draw_pdf(c, pw, ph, fonts)
    c.showPage()

    # ---- page 3: LCD plan
    L = Sheet(W, H)
    L.text(24, 40, "LCD GLASS PROPOSAL — 4 COM × 39 SEG  ·  LCD 玻璃規劃", 24, INK, "start", True)
    L.text(24, 60, "1/3 bias, 4-COM multiplex, VLCD from internal charge pump. Share this table with the LCD glass maker.", 12.5, GREY)
    hdr = ["J7", "MCU pin", "SEG", "Function", "COM0", "COM1", "COM2", "COM3"]
    xs = [24, 100, 190, 260, 560, 760, 960, 1160]
    for xh, ht in zip(xs, hdr):
        L.text(xh, 94, ht, 12, INK, "start", True)
    L.line(24, 100, 1400, 100, INK, 1.4)
    for i, (seg, jp, mp, owner, a, b_, c_, d_) in enumerate(LCD_PLAN):
        yy = 122 + i * 29
        if i % 2 == 0:
            L.rect(20, yy - 17, 1380, 26, "#f5f5f5", "#f5f5f5", 0, 0.1)
        for xv, tv in zip(xs, [str(jp), str(mp), "SEG%d" % seg, owner, a, b_, c_, d_]):
            L.text(xv, yy, tv, 11.5, INK)
    L.text(1420, 122, "COM pins on J7:", 12, INK, "start", True)
    for c_i in range(4):
        L.text(1420, 146 + c_i * 20, "J7.%d = COM%d  (MCU pin %d)" % (c_i + 1, c_i, COM_PIN[c_i]), 11.5, INK)
    L.text(1420, 250, "Digit (2 SEG lines × 4 COM):", 12, INK, "start", True)
    L.text(1420, 272, "line A: COM0=a COM1=f COM2=e COM3=d", 11.5, INK)
    L.text(1420, 292, "line B: COM0=b COM1=g COM2=c COM3=DP", 11.5, INK)
    L.text(1420, 330, "Reserved (not on LCD):", 12, INK, "start", True)
    for i, (s_, why) in enumerate(sorted(RESERVED_SEG.items())):
        L.text(1420, 352 + i * 20, "SEG%d  →  %s" % (s_, why), 11.5, INK)
    L.text(1976, 1390, "Sheet 3 of 3", 11, GREY, "end")
    L.draw_pdf(c, pw, ph, fonts)
    c.showPage()
    c.save()
    return path


def write_html(svg_text):
    # BOM grouped
    groups = {}
    for ref, p in PARTS.items():
        key = (p["cat"], p["value"], p["pkg"], p["desc"], p["mfr"], p["mpn"], p["notes"])
        groups.setdefault(key, []).append(ref)

    def refkey(r):
        import re
        m = re.match(r"([A-Za-z]+)(\d+)", r)
        return (m.group(1), int(m.group(2)))

    brows = []
    for key, refs in groups.items():
        refs = sorted(refs, key=refkey)
        brows.append((CATEGORY_ORDER.index(key[0]), refkey(refs[0]), key, refs))
    brows.sort(key=lambda t: (t[0], t[1]))
    bom_html = []
    for n, (_, _, key, refs) in enumerate(brows, 1):
        cat, val, pkg, desc, mfr, mpn, notes = key
        bom_html.append("<tr><td>%d</td><td>%s</td><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                        % (n, html.escape(", ".join(refs)), len(refs), html.escape(val), html.escape(pkg),
                           html.escape(desc), html.escape(mfr), html.escape(mpn), html.escape(notes)))
    pin_html = []
    for p, nm, net in pin_rows():
        cls = "nc" if net.startswith("NC") else ("un" if net == "(unused)" else "used")
        pin_html.append('<tr class="%s"><td>%d</td><td>%s</td><td>%s</td></tr>' % (cls, p, html.escape(nm), html.escape(net)))
    lcd_html = []
    for seg, jp, mp, owner, a, b_, c_, d_ in LCD_PLAN:
        lcd_html.append("<tr><td>%d</td><td>%d</td><td>SEG%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                        % (jp, mp, seg, html.escape(owner), a, b_, c_, d_))
    notes_html = "".join("<li>%s</li>" % html.escape(n[3:] if n[1] == "." else n) for n in SCHEM_NOTES)
    doc = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>4-CH K-Type Thermometer Schematic</title>
<style>
:root{--bg:#fff;--fg:#222;--mut:#666;--line:#ddd;--acc:#1565c0;--row:#f7f7f7}
@media (prefers-color-scheme:dark){:root{--bg:#fff;--fg:#222}}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI","Noto Sans TC","PingFang TC",sans-serif;background:var(--bg);color:var(--fg)}
header{padding:16px 20px;border-bottom:1px solid var(--line)}
h1{margin:0;font-size:22px} h2{margin:28px 20px 8px;font-size:18px} p.sub{margin:4px 0 0;color:var(--mut)}
nav a{margin-right:14px;color:var(--acc);text-decoration:none;font-size:14px}
.sch{overflow:auto;border-bottom:1px solid var(--line);padding:8px}
.sch svg{width:2000px;height:auto;max-width:none;display:block}
.tools{padding:8px 20px;font-size:13px;color:var(--mut)} .tools button{margin-right:6px;padding:4px 10px}
table{border-collapse:collapse;margin:0 20px 24px;font-size:13px;width:calc(100% - 40px)}
th,td{border:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}
th{background:#eceff1;position:sticky;top:0}
tr.nc td{background:#eee;color:#888} tr.un td{background:#fff8e1} tr.used td{background:#f1f8e9}
ul{margin:0 20px 20px 40px;line-height:1.6}
.wrap{overflow-x:auto}
</style></head><body>
<header><h1>4-CH K-Type Thermometer / Logger — Schematic · 線路圖</h1>
<p class="sub">SD93F115B-JQS · Rev @@REV@@ · @@DATE@@ · PDF (A3, 3 sheets) and BOM are in the same folder</p>
<nav><a href="#sch">Schematic</a><a href="#notes">Notes</a><a href="#pins">Pin map</a><a href="#lcd">LCD plan</a><a href="#bom">BOM</a></nav></header>
<div class="tools">Zoom: <button onclick="z(0.5)">50%</button><button onclick="z(0.75)">75%</button><button onclick="z(1)">100%</button><button onclick="z(1.5)">150%</button></div>
<div class="sch" id="sch">@@SVG@@</div>
<h2 id="notes">Design notes</h2><ul>@@NOTES@@</ul>
<h2 id="pins">U1 pin map (LQFP100)</h2><div class="wrap"><table><tr><th>Pin</th><th>Datasheet name</th><th>Net / function</th></tr>@@PINS@@</table></div>
<h2 id="lcd">LCD glass plan (4 COM × 39 SEG)</h2><div class="wrap"><table><tr><th>J7</th><th>MCU pin</th><th>SEG</th><th>Function</th><th>COM0</th><th>COM1</th><th>COM2</th><th>COM3</th></tr>@@LCD@@</table></div>
<h2 id="bom">Bill of materials</h2><div class="wrap"><table><tr><th>#</th><th>Ref</th><th>Qty</th><th>Value</th><th>Package</th><th>Description</th><th>Manufacturer</th><th>MPN</th><th>Notes</th></tr>@@BOM@@</table></div>
<script>function z(f){var s=document.querySelector('.sch svg');s.style.width=(2000*f)+'px'}
z(Math.min(1,(window.innerWidth-24)/2000)>0.5?Math.min(1,(window.innerWidth-24)/2000):0.5)</script>
</body></html>"""
    for k, v in (("@@REV@@", REV), ("@@DATE@@", DATE), ("@@SVG@@", svg_text), ("@@NOTES@@", notes_html),
                 ("@@PINS@@", "\n".join(pin_html)), ("@@LCD@@", "\n".join(lcd_html)), ("@@BOM@@", "\n".join(bom_html))):
        doc = doc.replace(k, v)
    path = os.path.join(HERE, "ktype_thermometer_schematic.html")
    open(path, "w", encoding="utf-8").write(doc)
    return path


if __name__ == "__main__":
    print(write_svg())
    print(write_pdf())
    print(write_html(S.to_svg(inline=True)))
    print("refs drawn:", len(S.refs), "BOM refs:", len(PARTS))
