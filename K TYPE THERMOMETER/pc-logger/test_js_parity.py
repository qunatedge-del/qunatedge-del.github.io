"""Runs the PROTO block of ktherm_logger.html under node and compares with ktherm_proto.py"""
import json, os, re, subprocess, sys, tempfile
from ktherm_proto import parse_line, make_frame, make_log_end, checksum

here = os.path.dirname(os.path.abspath(__file__))
html = open(os.path.join(here, "ktherm_logger.html"), encoding="utf-8").read()
proto = re.search(r"// ==PROTO==.*?\n(.*?)// ==/PROTO==", html, re.S).group(1)

lines = [
    make_frame("T", 5, 1760000000, [23.4, -200.0, "OPEN", 1372.0], 24.57, 5),
    make_frame("L", 9, 1760000100, [0.0, 99.9, "OVR", -5.5], 21.0, 0),
    make_log_end(42), "# KTHERM 4CH FW1.0", "OK", "ERR 3", "",
    "$T,1,2,3,4,5,6,7,8*00", "$T,1,2*" + checksum("T,1,2"), "no frame",
    "$T,1,1,x,2,3,4,20.00,0*" + checksum("T,1,1,x,2,3,4,20.00,0"),
    "$T,1,1,2,3,4,5,20.00,0", "$X,1*" + checksum("X,1"),
]
frames = [
    ("T", 3, 1760000000, [23.4, 100.0, "OPEN", -0.1], 24.56, 10),
    ("L", 0, 5, [1372.0, -200.0, 0.0, 12.3], 0.0, 15),
]
js = proto + "\nvar lines=%s;var out=lines.map(parseLine);var fr=%s.map(function(a){return makeFrame(a[0],a[1],a[2],a[3],a[4],a[5])});console.log(JSON.stringify({out:out,fr:fr}));" % (
    json.dumps(lines), json.dumps(frames))
with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
    f.write(js)
res = json.loads(subprocess.run(["node", f.name], capture_output=True, text=True, check=True).stdout)
os.unlink(f.name)

def norm(p):
    return None if p is None else {k: v for k, v in p.items() if k != "text"}

ok = True
for ln, jsout in zip(lines, res["out"]):
    py = norm(parse_line(ln)); jo = norm(jsout)
    if json.dumps(py, sort_keys=True) != json.dumps(jo, sort_keys=True):
        # allow 1372.0 vs 1372 differences
        if json.loads(json.dumps(py)) != jo:
            ok = False; print("MISMATCH", repr(ln), py, jo)
for fr, jf in zip(frames, res["fr"]):
    py = make_frame(*fr)
    if py != jf:
        ok = False; print("FRAME MISMATCH", py, jf)
print("JS/Python parity:", "OK (%d lines, %d frames)" % (len(lines), len(frames)) if ok else "FAILED")
sys.exit(0 if ok else 1)
