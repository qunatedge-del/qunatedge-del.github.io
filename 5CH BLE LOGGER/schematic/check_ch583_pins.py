# -*- coding: utf-8 -*-
"""Verifies design5.U1_PORT (QFN48 pin -> port) against the WCH CH583 datasheet V1.9 pin table.
Needs poppler's pdftotext on PATH.   python3 check_ch583_pins.py"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design5 as D

pdf = os.path.join(HERE, "..", "reference", "CH583_datasheet_V1.9_en.pdf")
txt = subprocess.run(["pdftotext", "-layout", "-f", "1", "-l", "12", pdf, "-"], capture_output=True, text=True, check=True).stdout.splitlines()
ds = {"0": "EPAD GND", "1": "VDCID", "2": "VSW", "3": "VDD33/VIO33"}
for l in txt:
    m = re.match(r"^\s+(\d+)\s+(\d+|None)\s+(P[AB]\d+|X32MO|X32MI|VINTA|ANT|VDCIA)(\s|$)", l)
    if m:
        ds[m.group(1)] = m.group(3)
bad = [(k, D.U1_PORT[k], ds.get(k)) for k in D.U1_PORT if D.U1_PORT[k] != ds.get(k)]
print("datasheet pins parsed: %d, mismatches: %s" % (len(ds), bad or "none"))
sys.exit(1 if bad else 0)
