#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line logger for the 4-channel K-type thermometer (USB Type-C = virtual COM port).

    pip install pyserial
    python3 ktherm_logger.py --port COM5 --rate 1000 --out log.csv       # Windows
    python3 ktherm_logger.py --port /dev/ttyACM0 --rate 1000 --out log.csv
    python3 ktherm_logger.py --demo --count 10                           # no hardware needed

Ctrl-C stops and closes the file.  CSV columns:
    pc_time_iso, device_epoch, seq, CH1_C, CH2_C, CH3_C, CH4_C, CJC_C, flags
"""
import argparse
import csv
import datetime
import math
import sys
import time

from ktherm_proto import parse_line, make_frame


def demo_lines(rate_ms, count=None):
    seq = 0
    while count is None or seq < count:
        t = seq * rate_ms / 1000.0
        temps = [25 + 10 * math.sin(t / 7), 100 + 40 * math.sin(t / 11 + 1), -20 + 5 * math.sin(t / 5),
                 "OPEN" if (seq // 8) % 3 == 2 else 300 + 150 * math.sin(t / 30)]
        yield make_frame("T", seq, int(time.time()), temps, 24.6 + 0.2 * math.sin(t / 50), 0)
        seq += 1
        time.sleep(rate_ms / 1000.0)


def serial_lines(port, baud, rate_ms):
    try:
        import serial
    except ImportError:
        sys.exit("pyserial missing:  pip install pyserial")
    with serial.Serial(port, baud, timeout=1) as s:
        s.write(("RATE %d\r\nTIME %d\r\nSTREAM 1\r\n" % (rate_ms, int(time.time()))).encode())
        try:
            while True:
                raw = s.readline()
                if raw:
                    yield raw.decode("ascii", "replace")
        finally:
            s.write(b"STREAM 0\r\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", help="serial port (COMx or /dev/tty...)")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--rate", type=int, default=1000, help="sample period in ms (500..60000)")
    ap.add_argument("--out", default="ktherm_log.csv")
    ap.add_argument("--demo", action="store_true", help="simulated device")
    ap.add_argument("--count", type=int, help="stop after N samples")
    a = ap.parse_args()
    if not a.demo and not a.port:
        ap.error("--port or --demo required")
    src = demo_lines(a.rate, a.count) if a.demo else serial_lines(a.port, a.baud, a.rate)
    n = bad = 0
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pc_time_iso", "device_epoch", "seq", "CH1_C", "CH2_C", "CH3_C", "CH4_C", "CJC_C", "flags"])
        try:
            for line in src:
                p = parse_line(line)
                if p is None:
                    continue
                if p["type"] == "sample":
                    n += 1
                    w.writerow([datetime.datetime.now().isoformat(timespec="milliseconds"), p["t"], p["seq"]]
                               + p["ch"] + ["%.2f" % p["cjc"], "%X" % p["flags"]])
                    f.flush()
                    print("%6d  " % p["seq"] + "  ".join("%8s" % ("%.1f" % v if not isinstance(v, str) else v)
                                                           for v in p["ch"]) + "   CJC %.2f" % p["cjc"])
                    if a.count and n >= a.count:
                        break
                elif p["type"] == "bad":
                    bad += 1
                elif p["type"] == "info":
                    print("#", p["text"])
        except KeyboardInterrupt:
            pass
    print("\n%d samples written to %s (%d bad frames dropped)" % (n, a.out, bad))


if __name__ == "__main__":
    main()
