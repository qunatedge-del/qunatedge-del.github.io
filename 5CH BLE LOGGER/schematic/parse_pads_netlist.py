import re, sys, json
src, out = sys.argv[1], sys.argv[2]
txt = open(src, encoding="utf-8", errors="replace").read().splitlines()
i = next(k for k,l in enumerate(txt) if l.startswith("*PART*")) + 1
parts = {}; cur = None
for ln in txt[i:]:
    if ln.startswith("*NET*") or ln.startswith("*SIGNAL*") or ln.startswith("*CONNECTION*"): break
    m = re.match(r"^([A-Za-z]+\d+)\s+(\S+)\s+\d+\s+\d+\s+\d+", ln)
    if m and not ln.startswith('"'):
        cur = m.group(1); parts[cur] = {"type": m.group(2)}; continue
    m = re.match(r'^"(Value|PCB_DECAL|Value2|PCB DECAL)"\s+(.*)$', ln)
    if m and cur: parts[cur][m.group(1)] = m.group(2).strip()
start = next(k for k,l in enumerate(txt) if l.startswith("*CONNECTION*"))
nets = {}; cur = None
for l in txt[start:]:
    m = re.match(r"^\*SIGNAL\*\s+(\S+)", l)
    if m: cur = m.group(1); nets[cur] = []; continue
    if l.startswith("*END*"): break
    if "@@@" in l and cur:
        m = re.search(r"(?:^|\s)([A-Za-z]+\d+)\.(\d+)(?:\s|$)", l)
        if m: nets[cur].append(m.group(1)+"."+m.group(2))
nets = {k: sorted(set(v)) for k, v in nets.items()}
json.dump({"parts": parts, "nets": nets}, open(out, "w"), ensure_ascii=False, indent=1)
print(src, len(parts), "parts", len(nets), "nets")
