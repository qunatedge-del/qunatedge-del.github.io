# -*- coding: utf-8 -*-
"""
K-therm serial protocol helpers (reference implementation, shared by the CLI logger,
the fake device and the tests).  See ../docs/PROTOCOL.md.

Frame:  $<body>*<CS>\n     CS = XOR of every character of <body>, two upper-case hex digits
Sample: $T,<seq>,<epoch>,<t1>,<t2>,<t3>,<t4>,<cjc>,<flags>*CS
Log:    $L,<idx>,<epoch>,<t1>,<t2>,<t3>,<t4>,<cjc>,<flags>*CS   ...   $L,END,<count>*CS
tN = temperature in degC with 1 decimal, or OPEN (no thermocouple) / OVR (out of range)
flags (hex): bit0 low battery, bit1 charging, bit2 logging, bit3 hold
"""
import re

FLAG_LOWBAT, FLAG_CHARGING, FLAG_LOGGING, FLAG_HOLD = 1, 2, 4, 8
_NUM = re.compile(r"^-?\d+(\.\d+)?$")


def checksum(body: str) -> str:
    c = 0
    for ch in body:
        c ^= ord(ch)
    return "%02X" % c


def _fmt_t(v):
    if isinstance(v, str):
        return v
    return "%.1f" % v


def make_frame(kind, seq, epoch, temps, cjc, flags):
    body = "%s,%d,%d,%s,%.2f,%X" % (kind, seq, epoch, ",".join(_fmt_t(t) for t in temps), cjc, flags)
    return "$%s*%s" % (body, checksum(body))


def make_log_end(count):
    body = "L,END,%d" % count
    return "$%s*%s" % (body, checksum(body))


def parse_line(line: str):
    """Returns a dict with key 'type': info | sample | logrec | logend | resp | bad"""
    line = line.strip()
    if not line:
        return None
    if line[0] == "#":
        return {"type": "info", "text": line[1:].strip()}
    if line[0] != "$":
        return {"type": "resp", "text": line}
    star = line.rfind("*")
    if star < 0:
        return {"type": "bad", "text": line, "reason": "no checksum"}
    body, cs = line[1:star], line[star + 1:].upper()
    if checksum(body) != cs:
        return {"type": "bad", "text": line, "reason": "checksum"}
    f = body.split(",")
    if f[0] == "L" and len(f) >= 3 and f[1] == "END":
        return {"type": "logend", "count": int(f[2])}
    if f[0] in ("T", "L") and len(f) == 9:
        def num(v):
            if _NUM.match(v):
                return float(v)
            if v in ("OPEN", "OVR"):
                return v
            raise ValueError(v)
        try:
            return {"type": "sample" if f[0] == "T" else "logrec", "seq": int(f[1]), "t": int(f[2]),
                    "ch": [num(v) for v in f[3:7]], "cjc": float(f[7]), "flags": int(f[8], 16)}
        except ValueError:
            return {"type": "bad", "text": line, "reason": "field"}
    return {"type": "bad", "text": line, "reason": "unknown frame"}
