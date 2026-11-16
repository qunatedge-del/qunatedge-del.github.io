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

sh.POWER_NETS |= {"SYS_PWR", "VCC_3V3", "BAT_IN"} | {"AVDDR%d" % k for k in range(1, 6)}
sh.ANALOG_NETS |= {"VBAT_SENSE"} | {"ACM%d" % k for k in range(1, 6)} | {"AI%d0" % k for k in range(1, 6)} | {"AI11", "AI17"}
wc = sh.netcol

W, H = 2000, 2000
S = Sheet(W, H)
COL = {"P": ("#ffebee", "#c62828"), "M": ("#e8eaf6", "#3949ab"), "A": ("#fff3e0", "#ef6c00"),
       "N": ("#fff8e1", "#f9a825"), "C": ("#e0f2f1", "#00796b")}


def section(key, x, y, w, h, title):
    f, b = COL[key]
    S.box(x, y, w, h, title, f, b)


# ---------------------------------------------------------------- header
S.text(24, 40, "%s  ·  五通道 K 型熱電偶 BLE 記錄器" % D.PROJECT, 26, INK, "start", True)
S.text(24, 60, "CH583M + 5 x SD6500 (SDIC) + CE8503 buck  ·  AFE = IC-factory SDH260018 V1.0-2 (renumbered)  ·  "
               "CH583M QFN48 pins per WCH datasheet V1.9  ·  Flash / LCD parts TBD", 12.5, GREY)
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
section("P", 24, 70, 1156, 330, "P  POWER  ·  4 x AA → reverse-polarity P-MOS → CE8503AM buck → VCC_3V3   (user's schematic + recommended changes)")
rail = 144                                              # y of the battery / SYS_PWR rail
battery(44, rail - 14, "BT1")
S.gnd(75, rail + 84)
S.line(106, rail, 130, rail, RED)
S.text(118, rail - 14, "BAT_IN", 9.5, RED, "middle", True)


def pmos_series(cx, y, ref, val):
    """P-MOSFET in series with the positive rail: drain (left) = battery, source (right) = load, gate lead down."""
    S.reg(ref)
    S.line(cx - 40, y, cx - 14, y, RED)
    S.line(cx + 14, y, cx + 40, y, RED)
    for a_, b_ in ((-14, -6), (-3, 3), (6, 14)):
        S.line(cx + a_, y, cx + b_, y, INK, 2.6)
    S.line(cx - 14, y + 8, cx + 14, y + 8, INK, 2.6)
    S.line(cx, y + 8, cx, y + 28, BLUE)
    S.text(cx - 22, y - 5, "D", 8.5, GREY, "end")
    S.text(cx + 22, y - 5, "S", 8.5, GREY, "start")
    S.text(cx + 6, y + 22, "G", 8.5, GREY, "start")
    S.text(cx, y - 24, ref, 10.5, INK, "middle", True)
    S.text(cx, y - 12, val, 8.5, INK, "middle")


qx = 170
pmos_series(qx, rail, "Q1", "P-MOS")
S.line(qx + 40, rail, 420 + 0, rail, RED)
S.res(qx, rail + 28, "R32", "100 kΩ", "v", 40, "r", BLUE)
S.gnd(qx, rail + 68)
S.text(qx, rail + 100, "gate to GND via R32:", 8.5, GREY, "middle")
S.text(qx, rail + 111, "off on reverse battery,", 8.5, GREY, "middle")
S.text(qx, rail + 122, "~0 V drop when correct", 8.5, GREY, "middle")
S.text(236, rail - 12, "SYS_PWR", 10, RED, "middle", True)
for x, ref, val in ((270, "C22", "10 µF"), (330, "C27", "1 µF")):
    S.dot(x, rail, RED)
    S.cap(x, rail, ref, val, 46, "r", RED)
    S.gnd(x, rail + 46)
# U3
u3 = S.ic(460, 110, 124, 130, "U3", "CE8503AM", left=[(4, "VIN", rail - 110), (1, "EN", 76)],
          right=[(3, "LX", 30), (5, "FB", 76)], bottom=[(2, "VSS", 62)], inside=True)
S.line(420, rail, u3[("l", 4)][0], u3[("l", 4)][1], RED)
S.dot(420, rail, RED)
# R31 EN pull-up and PB1
enx, eny = u3[("l", 1)]
S.res(420, rail, "R31", "100 kΩ", "v", eny - rail, "l", RED)
S.line(420, eny, enx, eny, BLUE)
S.dot(420, eny, BLUE)
S.line(420, eny, 392, eny, BLUE)
S.flag(392, eny, "PB1", "l")
S.gnd(*u3[("b", 2)])
# LX -> L3 -> VCC_3V3
lx, ly = u3[("r", 3)]
S.line(lx, ly, lx + 24, ly, BLUE)
inductor(lx + 24, ly, "L3", "2.2 µH", 70)
vx = lx + 24 + 70 + 24                                   # VCC_3V3 node x
S.line(lx + 24 + 70, ly, 1090, ly, RED)
S.text(vx + 6, ly - 10, "VCC_3V3", 10, RED, "start", True)
# FB divider
fx, fy = u3[("r", 5)]
dx = vx + 40
S.line(fx, fy, dx, fy, BLUE)
S.dot(dx, fy, BLUE)
S.dot(dx, ly, RED)
S.res(dx, ly, "R29", "453 kΩ", "v", fy - ly, "r", RED)
S.res(dx, fy, "R30", "100 kΩ", "v", 56, "r", BLUE)
S.gnd(dx, fy + 56)
cfx = dx + 70
S.dot(cfx, ly, RED)
S.line(dx, fy, cfx, fy, BLUE)
S.dot(cfx, fy, BLUE)
S.cap(cfx, ly, "C38", "10 pF", fy - ly, "r", BLUE)
S.text(dx - 14, fy - 6, "FB", 9.5, BLUE, "end", True)
# output caps
ox0 = cfx + 90
for i, (ref, val) in enumerate((("C23", "10 µF"), ("C16", "100 nF"))):
    x = ox0 + i * 80
    S.dot(x, ly, RED)
    S.cap(x, ly, ref, val, 46, "r", RED)
    S.gnd(x, ly + 46)
x = ox0 + 160
S.dot(x, ly, RED)
tant_cap(x, ly, "C39", "100 µF polymer")
S.gnd(x, ly + 44)
# battery voltage sense (net-label style)
bx, by0 = 940, 246
S.text(bx - 60, by0 - 18, "Battery voltage sense", 10.5, INK, "start", True)
S.flag(bx, by0, "SYS_PWR", "l")
S.line(bx, by0, bx, by0 + 8, RED)
S.res(bx, by0 + 8, "R33", "2.4 MΩ", "v", 40, "r", RED)
nodey = by0 + 48
S.dot(bx, nodey, ORG)
S.res(bx, nodey, "R34", "1.0 MΩ", "v", 40, "r", ORG)
S.gnd(bx, nodey + 40)
S.line(bx, nodey, bx + 60, nodey, ORG)
S.dot(bx + 60, nodey, ORG)
S.cap(bx + 60, nodey, "C40", "100 nF", 40, "r", ORG)
S.gnd(bx + 60, nodey + 40)
S.line(bx + 60, nodey, bx + 90, nodey, ORG)
S.flag(bx + 90, nodey, "VBAT_SENSE", "r")
# notes
pn = ["Vout = 0.6 V × (1 + R29/R30) = 0.6 × (1 + 453k/100k) = 3.32 V (VFB 0.6 V ±2 %); divider current ≈ 6 µA (was 15 µA with 180k/39k).",
      "VIN 2.0–6.5 V (abs.max 7.5 V): fresh alkaline 4×AA ≈ 6.0–6.4 V is OK with ~0.1 V margin; do NOT use 4×lithium AA (7.2 V).",
      "CHANGES vs the original drawing: R29/R30 453k/100k, C38 22→10 pF (keeps the datasheet's feed-forward zero, computed not tested),",
      "C39 tantalum→polymer, + R31 EN pull-up, + Q1/R32 reverse-polarity protection, + R33/R34/C40 battery sense to a CH583 ADC pin.",
      "VBAT_SENSE = 0.294 × VBAT (6.4 V → 1.88 V, 3.6 V → 1.06 V): inside the CH583 ADC 0 dB range (recommended 0–2 V, Vref 1.05 V). Check buck stability with the polymer C39."]
for i, t in enumerate(pn):
    S.text(40, 322 + i * 15, "• " + t, 10, "#444444")

# ================================================================ M  MCU / peripherals
section("M", 1200, 70, 776, 330, "M  MCU GPIO (U1A) · SPI FLASH · SPI LCD   (CH583M QFN48 pins: WCH datasheet V1.9; Flash / LCD parts TBD)")
S.reg("U1")
ux, uy, uw, uh = 1340, 112, 180, 272
ua_left = [("24", "PB0", "SCK"), ("23", "PB1", "PB1"), ("22", "PB2", "DATA1"), ("21", "PB3", "DATA2"),
           ("20", "PB4", "DATA3"), ("19", "PB5", "DATA4"), ("18", "PB6", "DATA5"), ("36", "PA4", "VBAT_SENSE")]
ua_right = [("46", "PA12", "FLASH_CS"), ("45", "PA13", "FLASH_SCK"), ("44", "PA14", "FLASH_MOSI"), ("43", "PA15", "FLASH_MISO"),
            ("39", "PA0", "LCD_SCK"), ("40", "PA1", "LCD_MOSI"), ("41", "PA2", "LCD_DC"), ("42", "PA3", "LCD_CS"),
            ("8", "PB8", "LCD_RST")]
pa = S.ic(ux, uy, uw, uh, "U1", "CH583M  (QFN48)  ·  unit A: GPIO",
          left=[(n, lab, 44 + i * 28) for i, (n, lab, _) in enumerate(ua_left)],
          right=[(n, lab, 44 + i * 25) for i, (n, lab, _) in enumerate(ua_right)], inside=True)
for n, lab, net in ua_left:
    x, y = pa[("l", n)]
    S.line(x, y, x - 8, y, wc(net)); S.flag(x - 8, y, net, "l")
for n, lab, net in ua_right:
    x, y = pa[("r", n)]
    S.line(x, y, x + 8, y, BLUE); S.flag(x + 8, y, net, "r")
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

# ================================================================ C  CH583M support (unit B)
section("C", 24, 1470, 1952, 420, "C  CH583M SUPPORT (U1B)  ·  power pins, DC-DC, crystals, antenna, reset / boot, SWD, UART1   (per WCH datasheet V1.9 + EVT schematic)")
bx0, by1, bw, bh = 870, 1512, 170, 340
lb = [("3", "VDD33/VIO33", 40, "VCC_3V3"), ("1", "VDCID", 72, "VDCID"), ("35", "VDCIA", 104, "VDCID"),
      ("2", "VSW", 136, "VSW"), ("33", "VINTA", 168, "VINTA"), ("0", "EPAD (GND)", 220, None)]
rb = [("34", "ANT", 40, "ANT"), ("32", "X32MI", 66, "X32MI"), ("31", "X32MO", 92, "X32MO"), ("48", "PA10/X32KI", 124, "X32KI"),
      ("47", "PA11/X32KO", 150, "X32KO"), ("25", "PB23/RST#", 186, "RST_N"), ("26", "PB22/BOOT", 212, "BOOT"),
      ("12", "PB14/SWDIO", 248, "SWDIO"), ("11", "PB15/SWDCK", 274, "SWDCK"), ("5", "PA8/RXD1", 306, "UART1_RX"),
      ("6", "PA9/TXD1", 330, "UART1_TX")]
pb = S.ic(bx0, by1, bw, bh, "U1", "CH583M  (QFN48)  ·  unit B: power / RF / debug",
          left=[(n, lab, o) for n, lab, o, _ in lb], right=[(n, lab, o) for n, lab, o, _ in rb])
for n, lab, o, net in lb:
    x, y = pb[("l", n)]
    if net is None:
        S.gnd(x, y)
    else:
        S.line(x, y, x - 8, y, wc(net)); S.flag(x - 8, y, net, "l")
for n, lab, o, net in rb:
    x, y = pb[("r", n)]
    S.line(x, y, x + 8, y, wc(net)); S.flag(x + 8, y, net, "r")
# decoupling (net-label style)
S.text(60, 1530, "Decoupling at the pins (no vias between cap and pin)", 10.5, INK, "start", True)
for i, (ref, val, net) in enumerate((("C41", "2.2 µF", "VCC_3V3"), ("C42", "2.2 µF", "VDCID"), ("C43", "100 nF", "VDCID"), ("C44", "1 µF", "VINTA"))):
    x = 100 + i * 100
    S.text(x, 1566, net, 8.5, wc(net), "middle", True)
    S.line(x, 1570, x, 1580, wc(net))
    S.cap(x, 1580, ref, val, 46, "r", wc(net))
    S.gnd(x, 1626)
S.text(60, 1660, "VDDx pins: C41 on VDD33/VIO33 (pin 3); C42 on VDCID; C43 on VDCIA (tied to VDCID); C44 on VINTA.", 9, GREY)
# DC-DC inductor
S.text(60, 1700, "On-chip DC-DC inductor (VSW → VDCID)", 10.5, INK, "start", True)
S.flag(70, 1740, "VSW", "r")
S.line(101, 1740, 140, 1740, BLUE)
inductor(140, 1740, "L1", "10 µH", 70)
S.line(210, 1740, 240, 1740, RED)
S.flag(240, 1740, "VDCID", "r")
S.text(60, 1768, "L1 fitted so the DC-DC can be enabled in software; with DC-DC off it is just a DC path VSW → VDCID.", 9, GREY)
# crystals
cx1 = 1330
S.text(1250, 1530, "Clocks", 10.5, INK, "start", True)
S.flag(cx1 - 14, 1560, "X32MI", "l"); S.line(cx1 - 14, 1560, cx1, 1560, BLUE)
S.xtal(cx1, 1560, "Y1", "32 MHz", 60, BLUE, "r")
S.line(cx1, 1620, cx1 - 14, 1620, BLUE); S.flag(cx1 - 14, 1620, "X32MO", "l")
cx2 = 1500
S.flag(cx2 - 14, 1560, "X32KI", "l"); S.line(cx2 - 14, 1560, cx2, 1560, BLUE)
S.xtal(cx2, 1560, "Y2", "32.768 kHz", 60, BLUE, "r")
S.line(cx2, 1620, cx2 - 14, 1620, BLUE); S.flag(cx2 - 14, 1620, "X32KO", "l")
S.text(1250, 1650, "32 MHz: internal load caps (10–24 pF), none external (as the WCH EVT).", 9, GREY)
S.text(1250, 1664, "32.768 kHz: optional, for an accurate RTC / BLE sleep clock.", 9, GREY)
# antenna
S.reg("E1")
S.text(1700, 1530, "Antenna", 10.5, INK, "start", True)
S.flag(1690, 1565, "ANT", "l"); S.line(1690, 1565, 1706, 1565, BLUE)
S.rect(1706, 1545, 150, 76, INK, "#fffde7", 3, 1.6)
S.text(1781, 1578, "E1  2.4 GHz", 10.5, INK, "middle", True)
S.text(1781, 1592, "PCB trace antenna", 9, INK, "middle")
S.text(1781, 1606, "(WCH ANT-F-2.4G-FR4)", 8.5, GREY, "middle")
S.line(1781, 1621, 1781, 1631, GND_C); S.gnd(1781, 1631)
S.text(1714, 1561, "1", 8, GREY)
# reset / boot
S.text(1250, 1700, "Reset / download", 10.5, INK, "start", True)
for x, ref, net, lab in ((1290, "SW1", "RST_N", "RESET (PB23)"), (1440, "SW2", "BOOT", "BOOT (PB22)")):
    S.flag(x, 1730, net, "r"); S.line(x, 1730, x, 1750, BLUE)
    S.sw(x, 1750, ref, 56)
    S.gnd(x, 1806)
    S.text(x + 14, 1792, lab, 8.5, INK)
# SWD and UART1 headers
for hx, ref, ttl, pins4 in ((1560, "P1", "P1  SWD", [("1", "3V3", "VCC_3V3"), ("2", "SWDIO", "SWDIO"), ("3", "SWDCK", "SWDCK"), ("4", "GND", None)]),
                            (1790, "P2", "P2  UART1", [("1", "3V3", "VCC_3V3"), ("2", "RX", "UART1_RX"), ("3", "TX", "UART1_TX"), ("4", "GND", None)])):
    S.reg(ref)
    S.rect(hx, 1710, 84, 92, INK, "#fffde7", 3, 1.6)
    S.text(hx + 42, 1728, ttl, 10.5, INK, "middle", True)
    for i, (n, lab, net) in enumerate(pins4):
        yy = 1746 + i * 16
        S.line(hx + 84, yy, hx + 98, yy, wc(net) if net else GND_C)
        S.text(hx + 8, yy + 3.4, "%s %s" % (n, lab), 9, INK)
        if net:
            S.flag(hx + 98, yy, net, "r")
        else:
            S.gnd(hx + 98, yy)
S.text(60, 1812, "Unused GPIO (no connect, free for expansion): PA5, PA6, PA7, PB7, PB9–PB13, PB16–PB21.", 9, GREY)
S.text(60, 1826, "ADC: PA4 = AIN0, 12-bit, Vref 1.05 V, 0 dB, input buffer ON (3.4 MΩ source). DATA1–5 = PB2–PB6 (one port read samples all five).", 9, GREY)
S.text(60, 1840, "VIO ≤ VIO33 + 0.4 V (abs. max): VBAT_SENSE may precede VCC_3V3 for ~ms at battery insertion; current is < 1 µA through 2.4 MΩ.", 9, GREY)

# ================================================================ notes + title block
S.rect(24, 1910, 1500, 76, "#9e9e9e", "#fafafa", 6, 1.4)
S.text(36, 1928, "NOTES  ·  備註", 11.5, INK, "start", True)
nts = ["AFE netlist is the IC factory's SDH260018 V1.0-2 verbatim (round-trip checked), only renumbered. Factory refdes ↔ ours: docs/FACTORY_V1_TO_V2.md.",
       "DEVIATIONS from factory: C304 / C404 / C504 are 0.1 µF here (factory file has 10 µF on the second VDD cap of U3/U4/U5 — to be confirmed); R902 = 0.1 %.",
       "OPEN: SPI Flash / LCD part numbers, Y1/Y2 crystal specs and antenna tuning (WCH EVT BOM / PCB notes), AI1/AI7 of U12–U15 left floating (confirm with SDIC)."]
for i, t in enumerate(nts):
    S.text(36, 1946 + i * 15, t, 9.2, "#444444")
tbx, tby, tbw, tbh = 1540, 1910, 436, 76
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
    order = ["IC", "Discrete", "Passive", "Crystal", "Connector", "Electromech"]
    order += sorted({v["cat"] for v in D.PARTS.values()} - set(order))
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
