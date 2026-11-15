# -*- coding: utf-8 -*-
"""
5-CH K-type BLE logger: schematic (SVG / PDF / HTML), netlist (CSV/JSON/KiCad-style text) and BOM.
Run:  python3 gen5.py
"""
import csv
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sheet as sh
from sheet import Sheet, INK, RED, GND_C, BLUE, ORG, GREY
import design5 as D

sh.POWER_NETS |= {"SYS_PWR", "VCC_3V3"} | {"AVDDR%d" % k for k in range(1, 6)}
sh.ANALOG_NETS |= {"ACM%d" % k for k in range(1, 6)} | {"AI%d0" % k for k in range(1, 6)} | {"AI11", "AI17"}
wc = sh.netcol

W, H = 2000, 1560
S = Sheet(W, H)
COL = {"P": ("#ffebee", "#c62828"), "M": ("#e8eaf6", "#3949ab"), "A": ("#fff3e0", "#ef6c00"),
       "N": ("#fff8e1", "#f9a825")}


def section(key, x, y, w, h, title):
    f, b = COL[key]
    S.box(x, y, w, h, title, f, b)


# ---------------------------------------------------------------- header
S.text(24, 40, "%s  ·  五通道 K 型熱電偶 BLE 記錄器" % D.PROJECT, 26, INK, "start", True)
S.text(24, 60, "CH583 + 5 x SD6500 (SDIC) + CE8503 buck  ·  AFE = IC-factory SDH260018 V1.0-2 (renumbered)  ·  "
               "CH583 / Flash / LCD pin numbers TBD", 12.5, GREY)
for i, (name, c) in enumerate((("Power", RED), ("GND", GND_C), ("Signal", BLUE), ("Analog", ORG))):
    S.line(1340 + i * 150, 38, 1376 + i * 150, 38, c, 3.5)
    S.text(1384 + i * 150, 43, name, 12, INK)
S.text(1976, 62, "Rev %s  ·  %s" % (D.REV, D.DATE), 11, GREY, "end")


# ---------------------------------------------------------------- local symbols
def inductor(x, y, ref, val, L=70):
    S.reg(ref)
    n = 4
    r = (L - 20) / n / 2
    S.line(x, y, x + 10, y, BLUE)
    S.line(x + L - 10, y, x + L, y, BLUE)
    for i in range(n):
        cx = x + 10 + r + i * 2 * r
        S.poly([(cx - r, y), (cx - r * .7, y - r * 1.1), (cx, y - r * 1.4), (cx + r * .7, y - r * 1.1), (cx + r, y)],
               INK, None, 2)
    S.text(x + L / 2, y - 22, ref, 10.5, INK, "middle", True)
    S.text(x + L / 2, y + 16, val, 9, INK, "middle")


def tant_cap(x, y, ref, val, L=44):
    S.cap(x, y, ref, val, L, "r", RED)
    m = y + L / 2
    S.text(x - 10, m - 6, "+", 10, INK, "end", True)


def battery(x, y, ref):
    S.reg(ref)
    S.rect(x, y, 62, 90, INK, "#fffde7", 3, 1.6)
    S.text(x + 31, y + 28, ref, 11, INK, "middle", True)
    S.text(x + 31, y + 43, "4 x AA", 9, INK, "middle")
    S.text(x + 31, y + 56, "6.0→3.6 V", 8.5, INK, "middle")
    S.text(x + 6, y + 14, "+", 12, RED, "start", True)
    S.text(x + 6, y + 84, "-", 12, INK, "start", True)


def nc_mark(x, y):
    S.line(x - 2, y - 5, x - 12, y + 5, GREY, 1.4)
    S.line(x - 2, y + 5, x - 12, y - 5, GREY, 1.4)


# ================================================================ P  power
section("P", 24, 70, 1156, 330, "P  POWER  ·  4 x AA → CE8503AM buck → VCC_3V3   (user's schematic, unchanged)")
by = 150
battery(44, by - 20, "BT1")
S.line(106, by - 6, 200, by - 6, RED)
S.dot(150, by - 6, RED)
S.gnd(75, by + 70)
rail = by - 6                                           # y of SYS_PWR rail (BT1 + terminal)
S.line(200, rail, 372, rail, RED)
S.text(150, rail - 12, "SYS_PWR", 10, RED, "middle", True)
for x, ref, val in ((200, "C22", "10 µF"), (262, "C27", "1 µF")):
    S.dot(x, rail, RED)
    S.cap(x, rail, ref, val, 46, "r", RED)
    S.gnd(x, rail + 46)
# U3
u3 = S.ic(420, 110, 124, 130, "U3", "CE8503AM", left=[(4, "VIN", rail - 110), (1, "EN", 76)],
          right=[(3, "LX", 30), (5, "FB", 76)], bottom=[(2, "VSS", 62)], inside=True)
S.line(372, rail, u3[("l", 4)][0], u3[("l", 4)][1], RED)
S.dot(372, rail, RED)
# R31 EN pull-up (recommended) and PB1
enx, eny = u3[("l", 1)]
S.res(372, rail, "R31", "100 kΩ", "v", eny - rail, "l", RED)
S.line(372, eny, enx, eny, BLUE)
S.dot(372, eny, BLUE)
S.line(372, eny, 340, eny, BLUE)
S.flag(340, eny, "PB1", "l")
S.gnd(*u3[("b", 2)])
# LX -> L3 -> VCC_3V3
lx, ly = u3[("r", 3)]
S.line(lx, ly, lx + 24, ly, BLUE)
inductor(lx + 24, ly, "L3", "2.2 µH", 70)
vx = lx + 24 + 70 + 24                                   # VCC_3V3 node x
S.line(lx + 24 + 70, ly, 1100, ly, RED)
S.text(vx + 6, ly - 10, "VCC_3V3", 10, RED, "start", True)
# FB divider
fx, fy = u3[("r", 5)]
dx = vx + 40
S.line(fx, fy, dx, fy, BLUE)
S.dot(dx, fy, BLUE)
S.dot(dx, ly, RED)
S.res(dx, ly, "R29", "180 kΩ", "v", fy - ly, "r", RED)
S.res(dx, fy, "R30", "39 kΩ", "v", 56, "r", BLUE)
S.gnd(dx, fy + 56)
cfx = dx + 70
S.dot(cfx, ly, RED)
S.line(dx, fy, cfx, fy, BLUE)
S.dot(cfx, fy, BLUE)
S.cap(cfx, ly, "C38", "22 pF", fy - ly, "r", BLUE)
S.text(dx - 14, fy - 6, "FB", 9.5, BLUE, "end", True)
# output caps
ox0 = cfx + 120
for i, (ref, val) in enumerate((("C23", "10 µF"), ("C16", "100 nF"))):
    x = ox0 + i * 90
    S.dot(x, ly, RED)
    S.cap(x, ly, ref, val, 46, "r", RED)
    S.gnd(x, ly + 46)
x = ox0 + 180
S.dot(x, ly, RED)
S.reg("C39")
tant_cap(x, ly, "C39", "100 µF/10 V tant.")
S.gnd(x, ly + 44)
# notes
pn = ["Vout = 0.6 V × (1 + R29/R30) = 0.6 × (1 + 180k/39k) = 3.37 V (VFB 0.6 V ±2 %, CE8503 datasheet V0.6).",
      "VIN 2.0–6.5 V (abs.max 7.5 V): fresh alkaline 4×AA ≈ 6.0–6.4 V is OK with ~0.1 V margin; do NOT use 4×lithium AA (7.2 V).",
      "R31 is RECOMMENDED (not in the original drawing): EN must not float and needs > 1.5 V; PB1 is high-Z at power-up.",
      "Suggested: R29 = 453k, R30 = 100k (datasheet: R2 ≤ 100k) → 3.32 V and ~6 µA instead of ~15 µA divider current.",
      "Missing in the original: reverse-polarity protection and battery-voltage sense (to a CH583 ADC pin)."]
for i, t in enumerate(pn):
    S.text(40, 322 + i * 15, "• " + t, 10, "#444444")

# ================================================================ M  MCU / peripherals
section("M", 1200, 70, 776, 330, "M  MCU INTERFACE · SPI FLASH · SPI LCD   (pin numbers TBD — CH583 datasheet needed)")
left_sig = [("PB1", "PB1"), ("SCK", "SCK"), ("DATA1", "DATA1"), ("DATA2", "DATA2"), ("DATA3", "DATA3"),
            ("DATA4", "DATA4"), ("DATA5", "DATA5")]
right_sig = ["FLASH_SCK", "FLASH_MOSI", "FLASH_MISO", "FLASH_CS", "LCD_SCK", "LCD_MOSI", "LCD_DC", "LCD_CS", "LCD_RST"]
S.reg("U1")
ux, uy, uw, uh = 1330, 112, 190, 262
S.rect(ux, uy, uw, uh, INK, "#fffde7", 4, 1.8)
S.text(ux + uw / 2, uy + 20, "U1  CH583", 12, INK, "middle", True)
S.text(ux + uw / 2, uy + 34, "WCH RISC-V BLE 5.3  ·  pins TBD", 8.5, GREY, "middle")
for i, (pin, net) in enumerate(left_sig):
    y = uy + 50 + i * 22
    S.line(ux - 14, y, ux, y, INK, 1.4)
    S.text(ux + 6, y + 3.5, pin, 9.5)
    S.text(ux - 3, y - 3, "PA?", 7, GREY, "end")
    S.line(ux - 14, y, ux - 22, y, wc(net))
    S.flag(ux - 22, y, net, "l")
y = uy + 50 + 7 * 22 + 8
S.line(ux - 14, y, ux, y, INK, 1.4); S.text(ux + 6, y + 3.5, "VCC", 9.5)
S.line(ux - 14, y, ux - 22, y, RED); S.flag(ux - 22, y, "VCC_3V3", "l")
y += 24
S.line(ux - 14, y, ux, y, INK, 1.4); S.text(ux + 6, y + 3.5, "GND", 9.5)
S.gnd(ux - 14, y)
for i, net in enumerate(right_sig):
    y = uy + 50 + i * 22
    S.line(ux + uw, y, ux + uw + 14, y, INK, 1.4)
    S.text(ux + uw - 6, y + 3.5, net, 9, INK, "end")
    S.text(ux + uw + 3, y - 3, "P?", 7, GREY, "start")
    S.line(ux + uw + 14, y, ux + uw + 22, y, BLUE)
    S.flag(ux + uw + 22, y, net, "r")
# SPI flash U2
f = S.ic(1660, 128, 124, 126, "U2", "SPI Flash (TBD)",
         left=[(8, "VCC", 20), (3, "WP", 44), (7, "HOLD", 68)],
         right=[(1, "CS", 22), (2, "SO", 46), (5, "SI", 70), (6, "SCK", 94)],
         bottom=[(4, "GND", 62)], inside=True)
bx_ = 1634
ys = [f[("l", n)][1] for n in (8, 3, 7)]
for n in (8, 3, 7):
    x, y = f[("l", n)]
    S.line(x, y, bx_, y, RED)
S.line(bx_, ys[0], bx_, ys[-1], RED)
S.dot(bx_, ys[1], RED)
S.line(bx_, ys[0], bx_, ys[0] - 14, RED)
S.vcc(bx_, ys[0] - 14, "VCC_3V3")
S.gnd(*f[("b", 4)])
for pn_, net in ((1, "FLASH_CS"), (2, "FLASH_MISO"), (5, "FLASH_MOSI"), (6, "FLASH_SCK")):
    x, y = f[("r", pn_)]
    S.line(x, y, x + 8, y, BLUE)
    S.flag(x + 8, y, net, "r")
S.cap(1900, 150, "C801", "100 nF", 44, "r", RED)
S.vcc(1900, 150, "VCC_3V3")
S.gnd(1900, 194)

# LCD module
S.reg("LCD1")
lx0, ly0, lw, lh = 1660, 282, 140, 100
S.rect(lx0, ly0, lw, lh, INK, "#fffde7", 3, 1.8)
S.text(lx0 + 40, ly0 + 44, "LCD1", 11, INK, "middle", True)
S.text(lx0 + 40, ly0 + 58, "SPI LCD", 8.5, INK, "middle")
S.text(lx0 + 40, ly0 + 70, "(TBD)", 8.5, GREY, "middle")
for i, (net, lab) in enumerate((("LCD_SCK", "SCK"), ("LCD_MOSI", "MOSI"), ("LCD_RST", "RES"), ("LCD_DC", "DC"),
                                ("LCD_CS", "CS"))):
    y = ly0 + 14 + i * 18
    S.line(lx0 + lw, y, lx0 + lw + 8, y, BLUE)
    S.text(lx0 + lw - 5, y + 3.4, lab, 8.5, INK, "end")
    S.flag(lx0 + lw + 8, y, net, "r")
S.line(lx0, ly0 + 24, lx0 - 12, ly0 + 24, RED)
S.vcc(lx0 - 12, ly0 + 24, "VCC_3V3")
S.text(lx0 + 5, ly0 + 27, "VCC", 8.5)
S.line(lx0, ly0 + 74, lx0 - 12, ly0 + 74, GND_C)
S.gnd(lx0 - 12, ly0 + 74)
S.text(lx0 + 5, ly0 + 77, "GND", 8.5)


# ================================================================ A  AFE channels
def channel(k, cx, cy):
    section("A", cx, cy, 966, 330, "A%d  SD6500 #%d  ·  K-type channel %d  ·  U1%d / T%d" % (k, k, k, k, k))
    ref = "U1%d" % k
    ix, iy, iw, ih = cx + 150, cy + 74, 140, 160
    labels_l = [(1, "AI0", 26), (2, "AI1", 56), (3, "AI6 / ACM", 86), (4, "AI7 / OPA", 116), (5, "AVSS", 146)]
    labels_r = [(10, "DATA", 26), (9, "SCK", 56), (8, "DVSS", 86), (7, "VDD", 116), (6, "AVDDR", 146)]
    p = S.ic(ix, iy, iw, ih, ref, "SD6500  (MSOP-10)", left=labels_l, right=labels_r)
    # left side
    x, y = p[("l", 1)]
    S.line(x, y, x - 8, y, ORG); S.flag(x - 8, y, "AI%d0" % k, "l")
    x, y = p[("l", 2)]
    if k == 1:
        S.line(x, y, x - 8, y, ORG); S.flag(x - 8, y, "AI11", "l")
    else:
        nc_mark(x, y); S.text(x - 18, y + 3.5, "floating", 8.5, GREY, "end")
    x, y = p[("l", 3)]
    S.line(x, y, x - 8, y, ORG); S.flag(x - 8, y, "ACM%d" % k, "l")
    x, y = p[("l", 4)]
    if k == 1:
        S.line(x, y, x - 8, y, ORG); S.flag(x - 8, y, "AI17", "l")
    else:
        nc_mark(x, y); S.text(x - 18, y + 3.5, "floating", 8.5, GREY, "end")
    S.gnd(*p[("l", 5)])
    # right side
    x, y = p[("r", 10)]
    S.line(x, y, x + 18, y, BLUE)
    S.dot(x + 18, y, BLUE)
    S.line(x + 18, y, x + 40, y, BLUE)
    S.flag(x + 40, y, "DATA%d" % k, "r")
    S.vcc(x + 18, y - 44, "VCC_3V3")
    S.res(x + 18, y - 44, "R%d03" % k, "10 kΩ", "v", 44, "r", RED)
    x, y = p[("r", 9)]
    S.line(x, y, x + 8, y, BLUE); S.flag(x + 8, y, "SCK", "r")
    S.gnd(*p[("r", 8)])
    x, y = p[("r", 7)]
    S.line(x, y, x + 8, y, RED); S.flag(x + 8, y, "VCC_3V3", "r")
    x, y = p[("r", 6)]
    S.line(x, y, x + 8, y, RED); S.flag(x + 8, y, "AVDDR%d" % k, "r")
    # decoupling
    caps = [("C%d02" % k, "100 nF", "AVDDR%d" % k), ("C%d03" % k, "10 µF", "VCC_3V3"), ("C%d04" % k, "100 nF", "VCC_3V3")]
    for i, (r_, v_, net) in enumerate(caps):
        x = cx + 410 + i * 72
        S.text(x, cy + 100, net, 8.5, wc(net), "middle", True)
        S.line(x, cy + 104, x, cy + 114, wc(net))
        S.cap(x, cy + 114, r_, v_, 44, "r", wc(net))
        S.gnd(x, cy + 158)
    S.text(cx + 410, cy + 190, "decoupling (AVDDR 0.1 µF, VDD 10 µF + 0.1 µF)", 8.5, GREY)
    # thermocouple front end
    ny, ry = cy + 146, cy + 198
    jx = cx + 650
    S.reg("T%d" % k)
    S.rect(jx, ny - 12, 52, ry - ny + 24, INK, "#fffde7", 3, 1.6)
    S.text(jx + 26, ny + 14, "T%d" % k, 11, INK, "middle", True)
    S.text(jx + 26, ny + 27, "K-type", 8.5, INK, "middle")
    S.text(jx + 46, ny + 4, "+", 11, INK, "end", True)
    S.text(jx + 46, ry + 4, "-", 11, INK, "end", True)
    xa, xb, xc = cx + 730, cx + 790, cx + 850
    S.line(jx + 52, ny, cx + 890, ny, ORG)
    S.line(jx + 52, ry, xc, ry, ORG)
    S.vcc(xa, ny - 56, "AVDDR%d" % k)
    S.res(xa, ny - 56, "R%d01" % k, "22 MΩ", "v", 56, "r", RED)
    S.dot(xa, ny, ORG)
    S.res(xb, ny, "R%d02" % k, "5.1 MΩ", "v", ry - ny, "r", ORG)
    S.dot(xb, ny, ORG); S.dot(xb, ry, ORG)
    S.cap(xc, ny, "C%d01" % k, "100 nF", ry - ny, "r", ORG)
    S.dot(xc, ny, ORG); S.dot(xc, ry, ORG)
    S.line(xc, ry, xc + 14, ry, ORG)
    S.flag(xc + 14, ry, "ACM%d" % k, "r")
    S.line(cx + 890, ny, cx + 900, ny, ORG)
    S.flag(cx + 900, ny, "AI%d0" % k, "r")
    S.text(cx + 600, cy + 292, "Open TC: K+ node floats to ACM + (AVDDR-ACM) × 5.1/27.1", 9, GREY)
    S.text(cx + 600, cy + 307, "≈ +339 mV at AVDDR = 3.0 V → ADC over-range → open", 9, GREY)
    S.text(cx + 150, cy + 292, "AI1 (pin 2) and AI7 (pin 4) left floating" if k > 1 else
           "AI1 ← AI11, AI7 ← AI17: cold-junction NTC network (section N)", 9, GREY)
    S.text(cx + 150, cy + 307, "Single-ended read of AI0 vs ACM%d; K- tied to ACM%d (factory SDH260018 V1.0-2)" % (k, k), 9, GREY)


cells = {1: (24, 420), 2: (24, 770), 3: (1010, 770), 4: (24, 1120), 5: (1010, 1120)}
for k, (cx, cy) in cells.items():
    channel(k, cx, cy)

# ================================================================ N  NTC network
section("N", 1010, 420, 966, 330, "N  COLD-JUNCTION NTC NETWORK (shared)  ·  on SD6500 #1 only  ·  冷端補償")
nx, ny0 = 1290, 504
S.vcc(nx, ny0, "AVDDR1")
S.res(nx, ny0, "R901", "1 MΩ", "v", 62, "r", RED)
na = ny0 + 62
S.dot(nx, na, ORG); S.line(nx, na, nx + 70, na, ORG); S.flag(nx + 70, na, "AI17", "r")
S.res(nx, na, "R902", "100 kΩ 0.1%", "v", 62, "r", ORG)
nb = na + 62
S.dot(nx, nb, ORG); S.line(nx, nb, nx + 70, nb, ORG); S.flag(nx + 70, nb, "AI11", "r")
S.ntc(nx, nb, "NTC1", "NTC 10 kΩ", 62)
nc = nb + 62
S.dot(nx, nc, ORG); S.line(nx, nc, nx + 70, nc, ORG); S.flag(nx + 70, nc, "ACM1", "r")
xl = nx - 70
S.line(nx, na, xl, na, ORG); S.line(nx, nb, xl, nb, ORG); S.line(nx, nc, xl, nc, ORG)
S.cap(xl, na, "C901", "100 nF", 62, "l", ORG)
S.cap(xl, nb, "C902", "100 nF", 62, "l", ORG)
S.dot(xl, na, ORG); S.dot(xl, nb, ORG); S.dot(xl, nc, ORG)
nt = ["R_NTC = R902 × V(AI11-ACM1) / V(AI17-AI11)    (ratiometric; AVDDR cancels)",
      "Chain current ≈ (AVDDR-ACM)/1.11 MΩ ≈ 1.6 µA at AVDDR = 3.0 V (negligible self-heating).",
      "V(AI17-AI11) ≈ 160 mV; V(AI11-ACM1) ≈ 16 mV @25 °C, 45 mV @0 °C, 7 mV @50 °C → PGIA gain 32.",
      "Brief said 'midpoint to AI6 and AI7' — that reads 0 V differentially and uses up ACM; replaced by the",
      "factory topology above (AI1/AI7 pair, ACM1 stays available as the bias for T1).",
      "Factory file lists these resistors as 5 %: R902 must be 0.1 % (25 ppm) for CJC accuracy.",
      "V1.0 → V1.0-2 fix: NTC1 / C902 bottom was on a separate net 'ACM' (not tied to ACM1). Now merged into ACM1.",
      "Place NTC1 at the centre of the T1–T5 jack row, on the same copper island (see docs)."]
import textwrap
_yy = 520
for t in nt:
    for ln in textwrap.wrap(t, 86):
        S.text(1520, _yy, ln, 9.8, "#444444")
        _yy += 15
    _yy += 4

# ================================================================ notes + title block
S.rect(24, 1470, 1500, 76, "#9e9e9e", "#fafafa", 6, 1.4)
S.text(36, 1488, "NOTES  ·  備註", 11.5, INK, "start", True)
nts = ["AFE netlist is the IC factory's SDH260018 V1.0-2 verbatim (round-trip checked), only renumbered. Factory refdes ↔ ours: docs/FACTORY_V1_TO_V2.md.",
       "DEVIATIONS from factory: C304 / C404 / C504 are 0.1 µF here (factory file has 10 µF on the second VDD cap of U3/U4/U5 — to be confirmed); R902 = 0.1 %.",
       "OPEN: CH583 pins, SPI Flash / LCD part numbers, reverse-polarity protection, battery sense, EN pull-up R31, AI1/AI7 left floating (confirm with SDIC)."]
for i, t in enumerate(nts):
    S.text(36, 1506 + i * 15, t, 9.2, "#444444")
tbx, tby, tbw, tbh = 1540, 1470, 436, 76
S.rect(tbx, tby, tbw, tbh, INK, "#ffffff", 0, 2)
S.line(tbx, tby + 26, tbx + tbw, tby + 26, INK, 1)
S.line(tbx, tby + 48, tbx + tbw, tby + 48, INK, 1)
S.text(tbx + 10, tby + 19, D.PROJECT, 12.5, INK, "start", True)
S.text(tbx + 10, tby + 40, "SCHEMATIC  ·  線路圖", 11, INK, "start", True)
S.text(tbx + 10, tby + 65, "Rev %s   %s" % (D.REV, D.DATE), 10, INK)
S.text(tbx + tbw - 8, tby + 65, "Sheet 1 of 1", 10, INK, "end")

# ---------------------------------------------------------------- consistency
missing = sorted(set(D.PARTS) - S.refs)
extra = sorted(S.refs - set(D.PARTS))
if missing or extra:
    raise SystemExit("schematic/data mismatch: not drawn %s ; drawn but not in data %s" % (missing, extra))
errs = D.check()
if errs:
    raise SystemExit("netlist errors:\n" + "\n".join(errs))


# ================================================================ outputs
def refkey(r):
    m = re.match(r"([A-Za-z]+)(\d+)", r)
    return (m.group(1), int(m.group(2)))


def write_netlist():
    out = os.path.join(HERE, "..", "netlist")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "5ch_logger_netlist.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Net", "Pin count", "Pins (REF.PIN)"])
        for n in sorted(D.NETS):
            w.writerow([n, len(D.NETS[n]), " ".join(sorted(D.NETS[n], key=lambda p: (refkey(p.split(".")[0]), p)))])
    json.dump({"nets": D.NETS, "parts": D.PARTS, "no_connect": sorted(D.NO_CONNECT), "factory_map": D.FACTORY_MAP},
              open(os.path.join(out, "5ch_logger_netlist.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # simple pin table: one row per part pin
    with open(os.path.join(out, "5ch_logger_pin_table.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Ref", "Value", "Pin", "Net"])
        pin2net = {p: n for n, ps in D.NETS.items() for p in ps}
        for ref in sorted(D.PARTS, key=refkey):
            for pin in D.PARTS[ref]["pins"]:
                w.writerow([ref, D.PARTS[ref]["value"], pin, pin2net.get("%s.%s" % (ref, pin), "(no connect)")])
    return out


def write_bom():
    out = os.path.join(HERE, "..", "bom")
    os.makedirs(out, exist_ok=True)
    groups = {}
    for ref, p in D.PARTS.items():
        groups.setdefault((p["cat"], p["value"], p["pkg"], p["desc"], p["notes"]), []).append(ref)
    order = ["IC", "Passive", "Connector"]
    rows = []
    for key, refs in groups.items():
        refs.sort(key=refkey)
        rows.append((order.index(key[0]), refkey(refs[0]), key, refs))
    rows.sort(key=lambda t: (t[0], t[1]))
    head = ["Item", "Ref Des", "Qty", "Value", "Package", "Description", "Category", "Notes"]
    table = [[i, ", ".join(r), len(r), k[1], k[2], k[3], k[0], k[4]] for i, (_, _, k, r) in enumerate(rows, 1)]
    with open(os.path.join(out, "5ch_logger_BOM.csv"), "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows([head] + table)
    return table


def write_svg_pdf():
    open(os.path.join(HERE, "5ch_logger_schematic.svg"), "w", encoding="utf-8").write(S.to_svg())
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont("ZH", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", subfontIndex=0))
    fonts = dict(latin="Helvetica", latin_b="Helvetica-Bold", zh="ZH")
    pw = 1190.55
    ph = pw * H / W
    c = canvas.Canvas(os.path.join(HERE, "5ch_logger_schematic.pdf"), pagesize=(pw, ph))
    c.setTitle("5-CH K-type BLE logger - schematic Rev A")
    S.draw_pdf(c, pw, ph, fonts)
    c.showPage()
    c.save()


def write_html(bom):
    pin2net = {p: n for n, ps in D.NETS.items() for p in ps}
    nrows = "".join("<tr><td>%s</td><td>%d</td><td>%s</td></tr>" % (
        html.escape(n), len(D.NETS[n]), html.escape(" ".join(sorted(D.NETS[n], key=lambda p: (refkey(p.split('.')[0]), p)))))
        for n in sorted(D.NETS))
    brows = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % html.escape(str(c)) for c in r) for r in bom)
    mrows = "".join("<tr><td>%s</td><td>%s</td></tr>" % (html.escape(o), html.escape(n))
                    for o, n in sorted(D.FACTORY_MAP.items(), key=lambda kv: refkey(kv[0])))
    doc = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>5-CH K-Type BLE Logger Schematic</title><style>
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI","Noto Sans TC",sans-serif;background:#fff;color:#222}
header{padding:14px 20px;border-bottom:1px solid #ddd} h1{margin:0;font-size:21px} h2{margin:26px 20px 8px;font-size:17px}
.sch{overflow:auto;padding:8px} .sch svg{width:2000px;height:auto;max-width:none;display:block}
table{border-collapse:collapse;margin:0 20px 22px;font-size:13px;width:calc(100% - 40px)} th,td{border:1px solid #ddd;padding:4px 8px;text-align:left;vertical-align:top;word-break:break-word}
th{background:#eceff1} .wrap{overflow-x:auto} nav a{margin-right:14px;color:#1565c0;text-decoration:none;font-size:14px}
</style></head><body><header><h1>5-CH K-Type BLE Data Logger — Schematic · 線路圖</h1>
<nav><a href="#s">Schematic</a><a href="#n">Netlist</a><a href="#b">BOM</a><a href="#m">Refdes map</a></nav></header>
<div class="sch" id="s">@@SVG@@</div>
<h2 id="n">Netlist (@@NN@@ nets)</h2><div class="wrap"><table><tr><th>Net</th><th>Pins</th><th>REF.PIN</th></tr>@@NROWS@@</table></div>
<h2 id="b">BOM</h2><div class="wrap"><table><tr><th>#</th><th>Ref</th><th>Qty</th><th>Value</th><th>Package</th><th>Description</th><th>Category</th><th>Notes</th></tr>@@BROWS@@</table></div>
<h2 id="m">Factory refdes → ours</h2><div class="wrap"><table><tr><th>Factory (SDH260018)</th><th>This design</th></tr>@@MROWS@@</table></div>
</body></html>"""
    for k, v in (("@@SVG@@", S.to_svg(inline=True)), ("@@NROWS@@", nrows), ("@@BROWS@@", brows), ("@@MROWS@@", mrows),
                 ("@@NN@@", str(len(D.NETS)))):
        doc = doc.replace(k, v)
    open(os.path.join(HERE, "5ch_logger_schematic.html"), "w", encoding="utf-8").write(doc)


if __name__ == "__main__":
    write_svg_pdf()
    bom = write_bom()
    nd = write_netlist()
    write_html(bom)
    print("ok: parts", len(D.PARTS), "nets", len(D.NETS), "drawn refs", len(S.refs), "BOM lines", len(bom))
