# -*- coding: utf-8 -*-
"""Consistency checks between the drawn schematic, design_data and the datasheet pin table."""
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_schematic as g
from design_data import PIN_NAMES, PIN_NET, SEG_PIN, COM_PIN, LCD_SEGS, J7, PARTS

errors = []
drawn = {}                                        # pin -> (label, net)
for e in g.left:
    if e:
        drawn[e[0]] = (e[1], e[2])
for gname, pins in g.lcd_groups:
    for lab, pin, full in pins:
        drawn[pin] = (full, gname)
for pin, lab, net in g.dig:
    drawn[pin] = (lab, net)

# 1. every pin drawn once, label tokens are a subset of the datasheet pin name
seen = {}
for pin, (lab, net) in drawn.items():
    toks = {t for t in re.split(r"[\s/]+", lab) if t}
    name_toks = set(PIN_NAMES[pin].split("/"))
    if not toks <= name_toks:
        errors.append("pin %d label %r not in datasheet name %r" % (pin, lab, PIN_NAMES[pin]))
# 2. drawn pins that are not in PIN_NET and vice versa
for pin in drawn:
    if pin not in PIN_NET:
        errors.append("pin %d drawn but missing in PIN_NET" % pin)
for pin, net in PIN_NET.items():
    if pin not in drawn:
        if not net.startswith("--") and pin not in (37, 38):
            errors.append("pin %d in PIN_NET (%s) but not drawn" % (pin, net))
# 3. nothing drawn on an NC pin
for pin in drawn:
    if PIN_NAMES[pin] == "NC":
        errors.append("pin %d is NC in datasheet but is used" % pin)
# 4. SEG numbers vs pin names
for s in LCD_SEGS:
    if "SEG%d" % s not in PIN_NAMES[SEG_PIN[s]].split("/"):
        errors.append("SEG%d -> pin %d name %s" % (s, SEG_PIN[s], PIN_NAMES[SEG_PIN[s]]))
for c, p in COM_PIN.items():
    if "COM%d" % c not in PIN_NAMES[p]:
        errors.append("COM%d -> pin %d name %s" % (c, p, PIN_NAMES[p]))
# 5. J7 pins unique mcu pins
if len({p for _, p in J7}) != len(J7):
    errors.append("duplicate MCU pin on J7")
# 6. a flag net used on U1 appears somewhere else on the sheet (otherwise it is a dangling net label)
flags = {}
for it in g.S.items:
    if it[0] == "text":
        flags.setdefault(it[3], 0)
        flags[it[3]] += 1
u1_nets = {net for (_, net) in drawn.values() if net not in ("GND",)}
for n in sorted(u1_nets):
    if flags.get(n, 0) < 2:
        errors.append("net label %s appears only once on the sheet (dangling?)" % n)
print("U1 pins drawn:", len(drawn), "  NC pins:", sum(1 for v in PIN_NAMES.values() if v == "NC"),
      "  power/ground drawn:", sum(1 for p in drawn if PIN_NAMES[p] in ("VDD", "AVDD", "AVDDR", "ACM", "DVDDR", "VSS", "AVSS", "DVSS", "VLCD", "CN", "CP")))
rest = [p for p in range(1, 101) if p not in drawn and PIN_NAMES[p] != "NC"]
print("pins neither drawn nor NC (deliberately unused):", [(p, PIN_NAMES[p]) for p in rest])
if errors:
    print("\n".join("ERROR: " + e for e in errors))
    sys.exit(1)
print("design checks passed; parts", len(PARTS), "refs drawn", len(g.S.refs))
