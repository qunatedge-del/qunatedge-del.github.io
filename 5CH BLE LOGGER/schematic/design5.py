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
# CH583M (QFN48 5x5) pin numbers - from WCH CH583 datasheet V1.9, section 1.2
# --------------------------------------------------------------------------
U1P = {"GND": "0", "VDCID": "1", "VSW": "2", "VCC": "3", "PA7": "4", "RXD1": "5", "TXD1": "6", "PB9": "7",
       "LCD_RST": "8", "PB17": "9", "PB16": "10", "SWDCK": "11", "SWDIO": "12", "PB13": "13", "PB12": "14",
       "PB11": "15", "PB10": "16", "PB7": "17", "DATA5": "18", "DATA4": "19", "DATA3": "20", "DATA2": "21",
       "DATA1": "22", "PB1": "23", "SCK": "24", "RST": "25", "BOOT": "26", "PB21": "27", "PB20": "28",
       "PB19": "29", "PB18": "30", "X32MO": "31", "X32MI": "32", "VINTA": "33", "ANT": "34", "VDCIA": "35",
       "VBAT_ADC": "36", "PA5": "37", "PA6": "38", "LCD_SCK": "39", "LCD_MOSI": "40", "LCD_DC": "41",
       "LCD_CS": "42", "FLASH_MISO": "43", "FLASH_MOSI": "44", "FLASH_SCK": "45", "FLASH_CS": "46",
       "X32KO": "47", "X32KI": "48"}
U1_PORT = {"0": "EPAD GND", "1": "VDCID", "2": "VSW", "3": "VDD33/VIO33", "4": "PA7", "5": "PA8", "6": "PA9", "7": "PB9",
           "8": "PB8", "9": "PB17", "10": "PB16", "11": "PB15", "12": "PB14", "13": "PB13", "14": "PB12", "15": "PB11",
           "16": "PB10", "17": "PB7", "18": "PB6", "19": "PB5", "20": "PB4", "21": "PB3", "22": "PB2", "23": "PB1",
           "24": "PB0", "25": "PB23", "26": "PB22", "27": "PB21", "28": "PB20", "29": "PB19", "30": "PB18",
           "31": "X32MO", "32": "X32MI", "33": "VINTA", "34": "ANT", "35": "VDCIA", "36": "PA4", "37": "PA5",
           "38": "PA6", "39": "PA0", "40": "PA1", "41": "PA2", "42": "PA3", "43": "PA15", "44": "PA14", "45": "PA13",
           "46": "PA12", "47": "PA11", "48": "PA10"}
U1_UNUSED = ["PA7", "PB9", "PB17", "PB16", "PB13", "PB12", "PB11", "PB10", "PB7", "PB21", "PB20", "PB19", "PB18",
             "PA5", "PA6"]


def u1(name):
    return "U1.%s" % U1P[name]


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
add("BT1", "4 x AA holder", "TBD", "Battery pack, 6.0 V fresh / 3.6 V empty (net BAT_IN, before Q1)", "Connector",
    "Alkaline only: 4 x lithium AA = 7.2 V exceeds the CE8503 6.5 V limit", pins=["1", "2"])
add("Q1", "P-MOSFET (e.g. AO3401A)", "SOT-23", "Reverse-polarity protection, series high-side switch", "Discrete",
    "Drain = battery side, source = load side, gate to GND via R32. Need Vds >= 20 V, Vgs(max) >= 12 V, Rds(on) < 100 mOhm "
    "@ -4.5 V. SOT-23 pinout assumed 1 G / 2 S / 3 D (AO3401A): verify for the chosen part.", pins=["1", "2", "3"])
add("R32", "100 kΩ", "0603", "Q1 gate pull-down to GND", "Passive", "Vgs = -(battery voltage) when conducting (max -6.4 V)", pins=["1", "2"])
add("R33", "2.4 MΩ 1%", "0603", "Battery sense divider, top", "Passive",
    "Ratio 1/3.4 = 0.294: 6.4 V -> 1.88 V (CH583 ADC 0 dB: recommended 0-2 V, Vref 1.05 V); 3.6 V -> 1.06 V. ADC input buffer ON.", pins=["1", "2"])
add("R34", "1.0 MΩ 1%", "0603", "Battery sense divider, bottom", "Passive", "Divider drain 6.4 V / 3.4 MΩ = 1.9 uA", pins=["1", "2"])
add("C40", "100 nF", "0603", "Battery sense filter / ADC sample reservoir", "Passive", "", pins=["1", "2"])
add("U3", "CE8503AM", "SOT-23-5", "800 mA 1.5 MHz synchronous buck, VIN 2-6.5 V (Chipower)", "IC",
    "'M' pinout: 1 EN, 2 VSS, 3 SW, 4 VIN, 5 FB. Vout = 0.6 x (1+R29/R30) = 3.32 V", pins=["1", "2", "3", "4", "5"])
add("C22", "10 µF", "TBD", "U3 VIN bulk", "Passive", "From user's schematic", pins=["1", "2"])
add("C27", "1 µF", "TBD", "U3 VIN HF", "Passive", "From user's schematic", pins=["1", "2"])
add("L3", "2.2 µH", "TBD", "Buck inductor (datasheet 1-4.7 uH)", "Passive", "From user's schematic", pins=["1", "2"])
add("R29", "453 kΩ 1%", "0603", "FB divider, top", "Passive",
    "Changed from 180 k: Vout = 0.6 x (1 + 453/100) = 3.32 V, divider current 6 uA (was 15 uA). Datasheet: R2 <= 100 k", pins=["1", "2"])
add("R30", "100 kΩ 1%", "0603", "FB divider, bottom", "Passive", "Changed from 39 k", pins=["1", "2"])
add("C38", "10 pF", "0603", "FB feed-forward (datasheet: optional)", "Passive",
    "Changed from 22 pF to keep the datasheet example's feed-forward zero (200 k x 22 pF = 4.4 us; 453 k x 10 pF = 4.5 us). "
    "Computed, not tested: check load-step/ripple on the prototype.", pins=["1", "2"])
add("C23", "10 µF", "TBD", "VCC_3V3 output cap", "Passive", "From user's schematic", pins=["1", "2"])
add("C16", "100 nF", "TBD", "VCC_3V3 HF cap", "Passive", "From user's schematic", pins=["1", "2"])
add("C39", "100 µF / 10 V polymer", "TBD", "VCC_3V3 bulk (low-ESR polymer aluminium)", "Passive",
    "Changed from tantalum (failure mode with battery inrush). Check that the buck stays stable with the lower ESR.", pins=["1", "2"])
add("R31", "100 kΩ", "0603", "U3 EN pull-up to SYS_PWR (added)", "Passive",
    "CE8503 EN must not float and must be > 1.5 V to start; PB1 is high-Z at power-up. MCU pulls PB1 low to shut the buck down.", pins=["1", "2"])

# ---- MCU / peripherals (pin numbers NOT known yet) ----
add("U1", "CH583M", "QFN48 5x5", "WCH RISC-V BLE 5.3 MCU (448 KB flash, 30 KB RAM, 2 SPI, 14-ch 12-bit ADC)", "IC",
    "Pin numbers from the WCH CH583 datasheet V1.9 section 1.2. PB1 exists only on QFN48 (not QFN28). EPAD = GND.",
    pins=[str(i) for i in range(0, 49)])
add("U2", "SPI Flash (TBD)", "SOIC-8 (typical)", "Data-logging flash on SPI0", "IC",
    "Typical 25-series SOIC-8 pinout assumed: 1 CS, 2 SO, 3 WP, 4 GND, 5 SI, 6 SCK, 7 HOLD, 8 VCC. Verify for the chosen part.",
    tbd=True, pins=[str(i) for i in range(1, 9)])
add("C801", "100 nF", "TBD", "U2 bypass", "Passive", "", pins=["1", "2"])
add("LCD1", "SPI LCD module (TBD)", "TBD", "LCD on SPI1", "Connector",
    "Module and pinout TBD; typical 7-wire interface assumed.", tbd=True,
    pins=["VCC", "GND", "SCK", "MOSI", "RES", "DC", "CS"])


# ---- CH583M support circuit (WCH EVT schematic CH583SCH + datasheet section 1.2) ----
add("C41", "2.2 µF", "0603", "U1 VDD33/VIO33 decoupling (pin 3)", "Passive", "EVT: 2.2 uF; datasheet: 2.2 uF with DC-DC, 0.1 uF without", pins=["1", "2"])
add("C42", "2.2 µF", "0603", "U1 VDCID decoupling (pin 1)", "Passive", "Datasheet: 2.2 uF recommended with DC-DC enabled", pins=["1", "2"])
add("C43", "100 nF", "0402", "U1 VDCIA decoupling (pin 35)", "Passive", "VDCIA is tied to VDCID (datasheet recommendation)", pins=["1", "2"])
add("C44", "1 µF", "0603", "U1 VINTA decoupling (pin 33)", "Passive", "Datasheet: 1 uF with DC-DC enabled (0.47-2.2 uF)", pins=["1", "2"])
add("L1", "10 µH", "TBD", "U1 on-chip DC-DC inductor, VSW (pin 2) to VDCID (pin 1)", "Passive",
    "Datasheet: 10 uH recommended (3.3-33 uH supported); EVT uses 22 uH. Also works as a DC short when DC-DC is disabled.", pins=["1", "2"])
add("Y1", "32 MHz crystal", "SMD 3225/2016", "BLE high-frequency crystal (HSE) on X32MI/X32MO", "Crystal",
    "No external load caps (internal 10-24 pF selectable). Crystal specs TBD from WCH EVT BOM. 4-pad package: other pads to GND.", pins=["1", "2"])
add("Y2", "32.768 kHz crystal", "SMD 3215", "RTC / BLE sleep-clock crystal on PA10/PA11 (optional)", "Crystal",
    "Internal load caps selectable (12-27 pF); EVT fits it without external caps.", pins=["1", "2"])
add("E1", "2.4 GHz PCB antenna", "PCB trace", "BLE antenna fed directly from ANT (pin 34)", "Connector",
    "Use WCH template ANT-F-2.4G-FR4.PcbDoc; antenna needs a ground end; keep ground clear around it.", pins=["1", "2"])
add("SW1", "Tact switch", "SMD", "Reset (RST# = PB23, active low, internal pull-up)", "Electromech", "", pins=["1", "2"])
add("SW2", "Tact switch", "SMD", "BOOT / download (PB22)", "Electromech", "EVT: PB22 'Download BOOT'", pins=["1", "2"])
add("P1", "1x4 header", "2.54 mm", "SWD debug: 3V3, SWDIO (PB14), SWDCK (PB15), GND", "Connector",
    "While the debug interface is enabled PB14/PB15 are used only as TIO/TCK", pins=["1", "2", "3", "4"])
add("P2", "1x4 header", "2.54 mm", "UART1 debug: 3V3, RXD1 (PA8), TXD1 (PA9), GND", "Connector", "", pins=["1", "2", "3", "4"])

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
            conn(net, u1(ref))
        else:
            conn(net, "%s.%s" % (FACTORY_MAP[ref], pin))
conn("SCK", u1("SCK"))                                     # shared SCK goes to ONE MCU GPIO
conn("VCC_3V3", u1("VCC"))
conn("GND", u1("GND"))

# power section (as drawn by the user)
conn("BAT_IN", "BT1.1", "Q1.3")
conn("SYS_PWR", "Q1.2", "C22.1", "C27.1", "U3.4", "R31.1", "R33.1")
conn("PG", "Q1.1", "R32.1")
conn("VBAT_SENSE", "R33.2", "R34.1", "C40.1", u1("VBAT_ADC"))
conn("GND", "BT1.2", "C22.2", "C27.2", "U3.2", "R30.2", "C23.2", "C16.2", "C39.2", "R32.2", "R34.2", "C40.2")
conn("PB1", "U3.1", "R31.2", u1("PB1"))
conn("LX", "U3.3", "L3.1")
conn("VCC_3V3", "L3.2", "R29.1", "C38.1", "C23.1", "C16.1", "C39.1")
conn("FB", "U3.5", "R29.2", "R30.1", "C38.2")

# SPI flash (SPI0) and LCD (SPI1)
conn("FLASH_CS", "U2.1", u1("FLASH_CS"))
conn("FLASH_MISO", "U2.2", u1("FLASH_MISO"))
conn("FLASH_MOSI", "U2.5", u1("FLASH_MOSI"))
conn("FLASH_SCK", "U2.6", u1("FLASH_SCK"))
conn("VCC_3V3", "U2.3", "U2.7", "U2.8", "C801.1", "LCD1.VCC")
conn("GND", "U2.4", "C801.2", "LCD1.GND")
conn("LCD_SCK", "LCD1.SCK", u1("LCD_SCK"))
conn("LCD_MOSI", "LCD1.MOSI", u1("LCD_MOSI"))
conn("LCD_RST", "LCD1.RES", u1("LCD_RST"))
conn("LCD_DC", "LCD1.DC", u1("LCD_DC"))
conn("LCD_CS", "LCD1.CS", u1("LCD_CS"))

# CH583M support circuit
conn("VCC_3V3", "C41.1", "P1.1", "P2.1")
conn("GND", "C41.2", "C42.2", "C43.2", "C44.2", "E1.2", "SW1.2", "SW2.2", "P1.4", "P2.4")
conn("VDCID", u1("VDCID"), u1("VDCIA"), "L1.2", "C42.1", "C43.1")
conn("VSW", u1("VSW"), "L1.1")
conn("VINTA", u1("VINTA"), "C44.1")
conn("ANT", u1("ANT"), "E1.1")
conn("X32MI", u1("X32MI"), "Y1.1")
conn("X32MO", u1("X32MO"), "Y1.2")
conn("X32KI", u1("X32KI"), "Y2.1")
conn("X32KO", u1("X32KO"), "Y2.2")
conn("RST_N", u1("RST"), "SW1.1")
conn("BOOT", u1("BOOT"), "SW2.1")
conn("SWDIO", u1("SWDIO"), "P1.2")
conn("SWDCK", u1("SWDCK"), "P1.3")
conn("UART1_RX", u1("RXD1"), "P2.2")
conn("UART1_TX", u1("TXD1"), "P2.3")

# deliberately unconnected pins (floating, per factory v2; unused GPIO on U1)
NO_CONNECT = {"U12.2", "U12.4", "U13.2", "U13.4", "U14.2", "U14.4", "U15.2", "U15.4"} | {u1(n) for n in U1_UNUSED}


_DATA_BY_PIN = {U1P["DATA%d" % k]: "DATA%d" % k for k in range(1, 6)}


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
            elif ref == "U1" and pin in _DATA_BY_PIN:
                back.setdefault(n, set()).add("%s.1" % _DATA_BY_PIN[pin])
    for fnet, fpins in FACTORY["nets"].items():
        if set(fpins) != back.get(fnet, set()):
            errs.append("factory net %s differs: factory %s vs ours %s" % (fnet, sorted(fpins), sorted(back.get(fnet, []))))
    return errs


if __name__ == "__main__":
    e = check()
    print("\n".join(e) if e else "design5 checks passed: %d parts, %d nets, %d pins" % (
        len(PARTS), len(NETS), sum(len(v) for v in NETS.values())))
