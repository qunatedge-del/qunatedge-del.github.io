# -*- coding: utf-8 -*-
"""
Data model for the 5-channel K-type BLE logger (CH583 + 5 x SD6500 + CE8503 buck).

The analog front end is derived mechanically from the IC factory's netlist
(reference/factory_SDH260018_V1.0-2/netlist_parsed.json) so it cannot drift from it.
Factory refdes clash with the user's existing power section (U3 = CE8503, C16, C22, C23),
therefore the AFE parts are renumbered; FACTORY_MAP records old -> new.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FACTORY_JSON = os.path.join(HERE, "..", "reference", "factory_SDH260018_V1.0-2", "netlist_parsed.json")
FACTORY = json.load(open(FACTORY_JSON, encoding="utf-8"))

PROJECT = "5-CH K-TYPE BLE DATA LOGGER"
REV = "A (draft)"
DATE = "2026-11-15"

# --------------------------------------------------------------------------
# refdes mapping factory -> ours  (per channel k = 1..5)
# --------------------------------------------------------------------------
#            U     R22M  R5.1M  Rpull  Ctc   Cavddr  Cvdd10  Cvdd2
_CH = {1: ("U1", "R1", "R2", "R11", "C3", "C8", "C6", "C7"),
       2: ("U2", "R4", "R6", "R9", "C13", "C10", "C9", "C15"),
       3: ("U3", "R7", "R8", "R15", "C1", "C17", "C16", "C22"),
       4: ("U4", "R10", "R12", "R20", "C2", "C24", "C23", "C29"),
       5: ("U5", "R13", "R14", "R25", "C11", "C31", "C30", "C36")}
FACTORY_MAP = {}
for k, (u, r1, r2, rp, ct, ca, cv1, cv2) in _CH.items():
    FACTORY_MAP.update({u: "U1%d" % k, r1: "R%d01" % k, r2: "R%d02" % k, rp: "R%d03" % k,
                        ct: "C%d01" % k, ca: "C%d02" % k, cv1: "C%d03" % k, cv2: "C%d04" % k,
                        "T%d" % k: "T%d" % k})
FACTORY_MAP.update({"R5": "R901", "R3": "R902", "C5": "C901", "C4": "C902", "NTC1": "NTC1"})
INV_MAP = {v: k for k, v in FACTORY_MAP.items()}

# --------------------------------------------------------------------------
# parts
# --------------------------------------------------------------------------
PARTS = {}


def add(ref, value, pkg, desc, cat, notes="", tbd=False, pins=None, src=""):
    assert ref not in PARTS, ref
    PARTS[ref] = dict(value=value, pkg=pkg, desc=desc, cat=cat, notes=notes, tbd=tbd, pins=pins, src=src)


# ---- AFE (from factory) ----
for k in range(1, 6):
    add("U1%d" % k, "SD6500", "MSOP-10", "24-bit Sigma-Delta ADC + PGIA, 2-wire interface (SDIC)", "IC",
        "Channel %d" % k, pins=[str(i) for i in range(1, 11)], src="factory U%d" % k)
    add("R%d01" % k, "22 MΩ", "0603", "K+ bias pull-up to AVDDR%d (open-TC detect)" % k, "Passive",
        "Factory file: 5 %%. Open-circuit node = ACM + (AVDDR-ACM) x 5.1/27.1", pins=["1", "2"], src="factory " + _CH[k][1])
    add("R%d02" % k, "5.1 MΩ", "0603", "K+ bias pull-down to ACM%d" % k, "Passive", "Factory file: 5 %",
        pins=["1", "2"], src="factory " + _CH[k][2])
    add("R%d03" % k, "10 kΩ", "0603", "DATA%d pull-up to VCC_3V3 (datasheet typical application)" % k, "Passive",
        "Factory footprint is R1/8W (axial) - replace by 0603", pins=["1", "2"], src="factory " + _CH[k][3])
    add("C%d01" % k, "100 nF X7R 50V", "0402", "Thermocouple input filter, K+ node to ACM%d" % k, "Passive",
        pins=["1", "2"], src="factory " + _CH[k][4])
    add("C%d02" % k, "100 nF X7R 50V", "0402", "AVDDR%d filter to AVSS (datasheet requires 0.1 uF)" % k, "Passive",
        pins=["1", "2"], src="factory " + _CH[k][5])
    add("C%d03" % k, "10 µF X7R", "0603", "VDD bulk decoupling (datasheet: 10 uF VDD-AVSS)", "Passive",
        "Factory file: 0402 10 uF 50 V", pins=["1", "2"], src="factory " + _CH[k][6])
    chg = "" if k in (1, 2) else "DEVIATION: factory file has 10 uF here (C%s); we use 0.1 uF to match the brief. Confirm with factory." % _CH[k][7][1:]
    add("C%d04" % k, "100 nF X7R 50V", "0402", "VDD HF decoupling", "Passive", chg, pins=["1", "2"], src="factory " + _CH[k][7])
    add("T%d" % k, "K-type mini jack", "TBD", "Thermocouple connector %d (pin 1 = K+, pin 2 = K-)" % k, "Connector",
        "Part not chosen yet", pins=["1", "2"], src="factory T%d" % k)
add("R901", "1 MΩ", "0603", "CJC chain: top resistor from AVDDR1", "Passive", "Factory file: 5 %", pins=["1", "2"], src="factory R5")
add("R902", "100 kΩ 0.1%", "0603", "CJC chain: ratiometric reference", "Passive",
    "DEVIATION: factory file 5 %; CJC accuracy depends on this resistor -> 0.1 % 25 ppm recommended",
    pins=["1", "2"], src="factory R3")
add("C901", "100 nF X7R", "0603", "CJC filter across R902", "Passive", pins=["1", "2"], src="factory C5")
add("C902", "100 nF X7R", "0603", "CJC filter across NTC1", "Passive", pins=["1", "2"], src="factory C4")
add("NTC1", "NTC 10 kΩ 1%", "0603", "Cold-junction sensor (shared by all 5 channels)", "Passive",
    "Factory footprint is LED-0603 (wrong). Place at the isothermal block centre.", pins=["1", "2"], src="factory NTC1")

# ---- power (user's own schematic, reference/power_section_user_schematic.png) ----
add("BT1", "4 x AA holder", "TBD", "Battery pack, 6.0 V fresh / 3.6 V empty (SYS_PWR)", "Connector",
    "No reverse-polarity protection in the user's schematic", pins=["1", "2"])
add("U3", "CE8503AM", "SOT-23-5", "800 mA 1.5 MHz synchronous buck, VIN 2-6.5 V (Chipower)", "IC",
    "'M' pinout: 1 EN, 2 VSS, 3 SW, 4 VIN, 5 FB. Vout = 0.6 x (1+R29/R30) = 3.37 V", pins=["1", "2", "3", "4", "5"])
add("C22", "10 µF", "TBD", "U3 VIN bulk", "Passive", "From user's schematic", pins=["1", "2"])
add("C27", "1 µF", "TBD", "U3 VIN HF", "Passive", "From user's schematic", pins=["1", "2"])
add("L3", "2.2 µH", "TBD", "Buck inductor (datasheet 1-4.7 uH)", "Passive", "From user's schematic", pins=["1", "2"])
add("R29", "180 kΩ 1%", "TBD", "FB divider, top", "Passive",
    "Recommended: 453 k (with R30 = 100 k) -> 3.32 V, 6 uA (datasheet: R2 <= 100 k)", pins=["1", "2"])
add("R30", "39 kΩ 1%", "TBD", "FB divider, bottom", "Passive", "Recommended: 100 k", pins=["1", "2"])
add("C38", "22 pF", "TBD", "FB feed-forward (datasheet: optional)", "Passive", "From user's schematic", pins=["1", "2"])
add("C23", "10 µF", "TBD", "VCC_3V3 output cap", "Passive", "From user's schematic", pins=["1", "2"])
add("C16", "100 nF", "TBD", "VCC_3V3 HF cap", "Passive", "From user's schematic", pins=["1", "2"])
add("C39", "100 µF / 10 V tantalum", "TBD", "VCC_3V3 bulk", "Passive",
    "Tantalum + battery inrush: consider polymer/ceramic", pins=["1", "2"])
add("R31", "100 kΩ", "TBD", "EN pull-up to SYS_PWR - RECOMMENDED, not in the user's schematic", "Passive",
    "CE8503 EN must not float and must be > 1.5 V to start; PB1 is high-Z at power-up. Confirm.", pins=["1", "2"])

# ---- MCU / peripherals (pin numbers NOT known yet) ----
add("U1", "CH583", "TBD (QFN48/QFN28)", "WCH RISC-V BLE 5.3 MCU", "IC",
    "PIN NUMBERS TBD - need WCH datasheet. Signals listed below are required connections.", tbd=True,
    pins=["VCC", "GND", "PB1", "SCK", "DATA1", "DATA2", "DATA3", "DATA4", "DATA5", "FLASH_SCK", "FLASH_MOSI",
          "FLASH_MISO", "FLASH_CS", "LCD_SCK", "LCD_MOSI", "LCD_DC", "LCD_CS", "LCD_RST"])
add("U2", "SPI Flash (TBD)", "SOIC-8 (typical)", "Data-logging flash on SPI0", "IC",
    "Typical 25-series SOIC-8 pinout assumed: 1 CS, 2 SO, 3 WP, 4 GND, 5 SI, 6 SCK, 7 HOLD, 8 VCC. Verify for the chosen part.",
    tbd=True, pins=[str(i) for i in range(1, 9)])
add("C801", "100 nF", "TBD", "U2 bypass", "Passive", "", pins=["1", "2"])
add("LCD1", "SPI LCD module (TBD)", "TBD", "LCD on SPI1", "Connector",
    "Module and pinout TBD; typical 7-wire interface assumed.", tbd=True,
    pins=["VCC", "GND", "SCK", "MOSI", "RES", "DC", "CS"])

# --------------------------------------------------------------------------
# nets
# --------------------------------------------------------------------------
NETS = {}


def conn(net, *pins):
    NETS.setdefault(net, [])
    for p in pins:
        assert p not in NETS[net], (net, p)
        NETS[net].append(p)


# AFE: mechanical translation of the factory v2 netlist
_net_rename = {"VDD": "VCC_3V3"}
for fnet, fpins in FACTORY["nets"].items():
    net = _net_rename.get(fnet, fnet)
    for fp in fpins:
        ref, pin = fp.split(".")
        if re.fullmatch(r"DATA\d", ref):                 # factory interface test points -> MCU pins
            conn(net, "U1.%s" % ref)
        else:
            conn(net, "%s.%s" % (FACTORY_MAP[ref], pin))
conn("SCK", "U1.SCK")                                     # shared SCK goes to ONE MCU GPIO
conn("VCC_3V3", "U1.VCC")
conn("GND", "U1.GND")

# power section (as drawn by the user)
conn("SYS_PWR", "BT1.1", "C22.1", "C27.1", "U3.4", "R31.1")
conn("GND", "BT1.2", "C22.2", "C27.2", "U3.2", "R30.2", "C23.2", "C16.2", "C39.2")
conn("PB1", "U3.1", "R31.2", "U1.PB1")
conn("LX", "U3.3", "L3.1")
conn("VCC_3V3", "L3.2", "R29.1", "C38.1", "C23.1", "C16.1", "C39.1")
conn("FB", "U3.5", "R29.2", "R30.1", "C38.2")

# SPI flash (SPI0) and LCD (SPI1)
conn("FLASH_CS", "U2.1", "U1.FLASH_CS")
conn("FLASH_MISO", "U2.2", "U1.FLASH_MISO")
conn("FLASH_MOSI", "U2.5", "U1.FLASH_MOSI")
conn("FLASH_SCK", "U2.6", "U1.FLASH_SCK")
conn("VCC_3V3", "U2.3", "U2.7", "U2.8", "C801.1", "LCD1.VCC")
conn("GND", "U2.4", "C801.2", "LCD1.GND")
conn("LCD_SCK", "LCD1.SCK", "U1.LCD_SCK")
conn("LCD_MOSI", "LCD1.MOSI", "U1.LCD_MOSI")
conn("LCD_RST", "LCD1.RES", "U1.LCD_RST")
conn("LCD_DC", "LCD1.DC", "U1.LCD_DC")
conn("LCD_CS", "LCD1.CS", "U1.LCD_CS")

# deliberately unconnected pins (floating, per factory v2)
NO_CONNECT = {"U12.2", "U12.4", "U13.2", "U13.4", "U14.2", "U14.4", "U15.2", "U15.4"}


def check():
    errs = []
    seen = {}
    for n, pins in NETS.items():
        for p in pins:
            if p in seen:
                errs.append("pin %s on two nets: %s and %s" % (p, seen[p], n))
            seen[p] = n
        if len(pins) < 2:
            errs.append("net %s has only one pin %s" % (n, pins))
    for ref, p in PARTS.items():
        for pin in p["pins"]:
            key = "%s.%s" % (ref, pin)
            if key not in seen and key not in NO_CONNECT:
                errs.append("pin %s is on no net" % key)
    for key in NO_CONNECT:
        if key in seen:
            errs.append("%s is declared NC but connected to %s" % (key, seen[key]))
    for p in seen:
        ref = p.split(".")[0]
        if ref not in PARTS:
            errs.append("pin %s refers to unknown part" % p)
        elif p.split(".")[1] not in PARTS[ref]["pins"]:
            errs.append("pin %s is not a pin of %s" % (p, ref))
    # round trip: our AFE nets mapped back to factory refdes must equal the factory netlist exactly
    back = {}
    inv_net = {"VCC_3V3": "VDD"}
    for n, pins in NETS.items():
        for p in pins:
            ref, pin = p.split(".")
            if ref in INV_MAP:
                back.setdefault(inv_net.get(n, n), set()).add("%s.%s" % (INV_MAP[ref], pin))
            elif ref == "U1" and re.fullmatch(r"DATA\d", pin):
                back.setdefault(n, set()).add("%s.1" % pin)
    for fnet, fpins in FACTORY["nets"].items():
        if set(fpins) != back.get(fnet, set()):
            errs.append("factory net %s differs: factory %s vs ours %s" % (fnet, sorted(fpins), sorted(back.get(fnet, []))))
    return errs


if __name__ == "__main__":
    e = check()
    print("\n".join(e) if e else "design5 checks passed: %d parts, %d nets, %d pins" % (
        len(PARTS), len(NETS), sum(len(v) for v in NETS.values())))
