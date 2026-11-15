# -*- coding: utf-8 -*-
"""Tiny 2-backend (SVG + ReportLab PDF) drawing layer plus circuit symbols."""
import html

INK = "#2b2b2b"
RED = "#d32f2f"
GND_C = "#333333"
BLUE = "#1565c0"
ORG = "#e65100"
GREY = "#777777"

POWER_NETS = {"VDD", "VBAT", "VBAT_SW", "VBUS", "VBUS_F", "VUSB3V3", "AVDDR", "DVDDR", "VLCD"}
ANALOG_NETS = {"TC1", "TC2", "TC3", "TC4", "CJC_A", "CJC_B", "ACM", "VBAT_SENSE"}


def netcol(name):
    if name in POWER_NETS:
        return RED
    if name == "GND":
        return GND_C
    if name in ANALOG_NETS:
        return ORG
    return BLUE


def _is_ascii(t):
    return all(ord(c) < 128 for c in t)


def text_w(t, size):
    return len(t) * size * 0.56


class Sheet:
    def __init__(self, w, h):
        self.W, self.H = w, h
        self.items = []
        self.refs = set()

    # ------------------------------------------------------------ primitives
    def reg(self, ref):
        self.refs.add(ref)

    def line(self, x1, y1, x2, y2, col=BLUE, w=1.6):
        self.items.append(("line", x1, y1, x2, y2, col, w))

    def rect(self, x, y, w, h, stroke=INK, fill=None, rx=0, sw=1.4, dash=False):
        self.items.append(("rect", x, y, w, h, stroke, fill, rx, sw, dash))

    def circ(self, cx, cy, r, stroke=INK, fill=None, sw=1.4):
        self.items.append(("circ", cx, cy, r, stroke, fill, sw))

    def poly(self, pts, stroke=INK, fill=None, sw=1.4):
        self.items.append(("poly", pts, stroke, fill, sw))

    def text(self, x, y, t, size=10.5, col=INK, anchor="start", bold=False, italic=False):
        self.items.append(("text", x, y, t, size, col, anchor, bold, italic))

    def dot(self, x, y, col=BLUE):
        self.circ(x, y, 2.6, col, col, 1)

    # ------------------------------------------------------------ symbols
    def vcc(self, x, y, name="VDD"):
        """supply bar with the pin point at (x, y); label above"""
        c = netcol(name)
        self.line(x, y, x, y - 8, c)
        self.line(x - 9, y - 8, x + 9, y - 8, c, 2.2)
        self.text(x, y - 13, name, 9.5, c, "middle", True)

    def gnd(self, x, y):
        self.line(x, y, x, y + 7, GND_C)
        self.line(x - 10, y + 7, x + 10, y + 7, GND_C, 2.2)
        self.line(x - 6.5, y + 11, x + 6.5, y + 11, GND_C, 2.2)
        self.line(x - 3, y + 15, x + 3, y + 15, GND_C, 2.2)

    def flag(self, x, y, name, d="r", col=None, size=9.5):
        col = col or netcol(name)
        tw = text_w(name, size) + 8
        if d == "r":
            pts = [(x, y), (x + 7, y - 8), (x + 7 + tw, y - 8), (x + 7 + tw, y + 8), (x + 7, y + 8)]
            tx, anc = x + 7 + tw / 2, "middle"
        else:
            pts = [(x, y), (x - 7, y - 8), (x - 7 - tw, y - 8), (x - 7 - tw, y + 8), (x - 7, y + 8)]
            tx, anc = x - 7 - tw / 2, "middle"
        self.poly(pts, col, "#ffffff", 1.4)
        self.text(tx, y + 3.4, name, size, col, anc, True)

    def res(self, x, y, ref, val, o="v", L=60, lab="r", wc=BLUE, note=None, valpos="below"):
        """resistor, first terminal at (x,y), second at (x,y+L) or (x+L,y)"""
        self.reg(ref)
        if o == "v":
            m = y + L / 2
            self.line(x, y, x, m - 13, wc)
            self.line(x, m + 13, x, y + L, wc)
            self.rect(x - 6, m - 13, 12, 26, INK, "#ffffff")
            ax, anc = (x + 11, "start") if lab == "r" else (x - 11, "end")
            self.text(ax, m - 1, ref, 10.5, INK, anc, True)
            self.text(ax, m + 11, val, 9, INK, anc)
        else:
            m = x + L / 2
            self.line(x, y, m - 13, y, wc)
            self.line(m + 13, y, x + L, y, wc)
            self.rect(m - 13, y - 6, 26, 12, INK, "#ffffff")
            if valpos == "above":
                self.text(m, y - 21, val, 9, INK, "middle")
                self.text(m, y - 10, ref, 10.5, INK, "middle", True)
            else:
                self.text(m, y - 10, ref, 10.5, INK, "middle", True)
                self.text(m, y + 21, val, 9, INK, "middle")

    def ntc(self, x, y, ref, val, L=60, wc=ORG):
        self.res(x, y, ref, val, "v", L, "r", wc)
        m = y + L / 2
        self.line(x - 12, m + 17, x + 12, m - 17, INK, 1.6)
        self.text(x - 16, m - 2, "t°", 10, INK, "end", True)

    def cap(self, x, y, ref, val, L=50, lab="r", wc=BLUE):
        self.reg(ref)
        m = y + L / 2
        self.line(x, y, x, m - 3.5, wc)
        self.line(x, m + 3.5, x, y + L, wc)
        self.line(x - 12, m - 3.5, x + 12, m - 3.5, INK, 2.4)
        self.line(x - 12, m + 3.5, x + 12, m + 3.5, INK, 2.4)
        ax, anc = (x + 16, "start") if lab == "r" else (x - 16, "end")
        self.text(ax, m - 1, ref, 10.5, INK, anc, True)
        self.text(ax, m + 11, val, 9, INK, anc)

    def sw(self, x, y, ref, L=56, wc=BLUE):
        """vertical push switch, contacts at (x,y) and (x,y+L)"""
        self.reg(ref)
        m = y + L / 2
        self.line(x, y, x, m - 10, wc)
        self.line(x, m + 10, x, y + L, wc)
        self.circ(x, m - 10, 2.4, INK, INK)
        self.circ(x, m + 10, 2.4, INK, INK)
        self.line(x - 9, m - 15, x + 9, m - 15, INK, 1.6)
        self.line(x, m - 15, x, m - 11, INK, 1.4)

    def diode_led(self, x, y, ref, L=44, wc=BLUE):
        self.reg(ref)
        m = y + L / 2
        self.line(x, y, x, m - 8, wc)
        self.line(x, m + 8, x, y + L, wc)
        self.poly([(x - 8, m - 8), (x + 8, m - 8), (x, m + 8)], INK, "#ffffff")
        self.line(x - 8, m + 8, x + 8, m + 8, INK, 2)

    def xtal(self, x, y, ref, val, L=60, wc=BLUE, lab="r"):
        self.reg(ref)
        m = y + L / 2
        self.line(x, y, x, m - 14, wc)
        self.line(x, m + 14, x, y + L, wc)
        self.line(x - 10, m - 14, x + 10, m - 14, INK, 2.4)
        self.line(x - 10, m + 14, x + 10, m + 14, INK, 2.4)
        self.rect(x - 5, m - 10, 10, 20, INK, "#ffffff")
        ax, anc = (x + 16, "start") if lab == "r" else (x - 16, "end")
        self.text(ax, m - 1, ref, 10.5, INK, anc, True)
        self.text(ax, m + 11, val, 9, INK, anc)

    def npn(self, x, y, ref, val):
        """NPN with base wire coming from the left at (x,y); collector up, emitter down"""
        self.reg(ref)
        r = 17
        cx = x + 24
        self.circ(cx + 2, y, r, INK, "#ffffff", 1.4)
        self.line(x, y, cx - 8, y, BLUE)
        self.line(cx - 8, y - 10, cx - 8, y + 10, INK, 2.4)
        self.line(cx - 8, y - 5, cx + 8, y - 16, INK, 1.6)
        self.line(cx - 8, y + 5, cx + 8, y + 16, INK, 1.6)
        self.line(cx + 8, y - 16, cx + 8, y - 30, BLUE)
        self.line(cx + 8, y + 16, cx + 8, y + 30, BLUE)
        self.poly([(cx + 8, y + 16), (cx + 1, y + 14), (cx + 5, y + 8)], INK, INK, 1)
        self.text(cx + 24, y - 2, ref, 10.5, INK, "start", True)
        self.text(cx + 24, y + 10, val, 9, INK)
        return (cx + 8, y - 30), (cx + 8, y + 30)      # collector, emitter

    def box(self, x, y, w, h, title, fill, border, tsize=13):
        self.rect(x, y, w, h, border, fill, 10, 2.2)
        self.rect(x, y, w, 28, border, border, 10, 2.2)
        self.rect(x, y + 14, w, 14, border, border, 0, 0.1)
        self.text(x + 12, y + 19.5, title, tsize, "#ffffff", "start", True)

    def ic(self, x, y, w, h, ref, part, left=(), right=(), top=(), bottom=(), fs=9.5, pn=True, sub=None, inside=False):
        """
        Generic IC. Pin tuples: (pinno, label, pos) with pos = y-offset (left/right) or x-offset (top/bottom).
        Returns {(side, pinno): (px, py)} = outer end of each pin stub.
        """
        self.reg(ref)
        self.rect(x, y, w, h, INK, "#fffde7", 3, 1.8)
        if inside:
            self.text(x + w / 2, y + h / 2 - 2, ref, 11, INK, "middle", True)
            self.text(x + w / 2, y + h / 2 + 10, part, 8.5, INK, "middle")
            if sub:
                self.text(x + w / 2, y + h + 12, sub, 8, GREY, "middle")
        else:
            self.text(x + w / 2, y + h + 14, ref, 10.5, INK, "middle", True)
            self.text(x + w / 2, y + h + 26, part, 9, INK, "middle")
            if sub:
                self.text(x + w / 2, y + h + 38, sub, 8.5, GREY, "middle")
        out = {}
        S = 14
        for no, lab, o in left:
            py = y + o
            self.line(x - S, py, x, py, INK, 1.4)
            self.text(x + 5, py + 3.5, lab, fs)
            if pn:
                self.text(x - 3, py - 3, str(no), 7.5, GREY, "end")
            out[("l", no)] = (x - S, py)
        for no, lab, o in right:
            py = y + o
            self.line(x + w, py, x + w + S, py, INK, 1.4)
            self.text(x + w - 5, py + 3.5, lab, fs, INK, "end")
            if pn:
                self.text(x + w + 3, py - 3, str(no), 7.5, GREY, "start")
            out[("r", no)] = (x + w + S, py)
        for no, lab, o in top:
            px = x + o
            self.line(px, y - S, px, y, INK, 1.4)
            self.text(px, y + 13, lab, fs, INK, "middle")
            if pn:
                self.text(px + 3, y - S + 6, str(no), 7.5, GREY, "start")
            out[("t", no)] = (px, y - S)
        for no, lab, o in bottom:
            px = x + o
            self.line(px, y + h, px, y + h + S, INK, 1.4)
            self.text(px, y + h - 6, lab, fs, INK, "middle")
            if pn:
                self.text(px + 3, y + h + S - 2, str(no), 7.5, GREY, "start")
            out[("b", no)] = (px, y + h + S)
        return out

    # ------------------------------------------------------------ SVG
    def to_svg(self, inline=False):
        o = []
        if not inline:
            o.append('<?xml version="1.0" encoding="UTF-8"?>')
        o.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
                 'font-family="Helvetica, Arial, \'WenQuanYi Zen Hei\', \'Noto Sans CJK TC\', sans-serif">'
                 % (self.W, self.H, self.W, self.H))
        o.append('<rect width="%d" height="%d" fill="#ffffff"/>' % (self.W, self.H))
        for it in self.items:
            k = it[0]
            if k == "line":
                _, x1, y1, x2, y2, c, w = it
                o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f" '
                         'stroke-linecap="round"/>' % (x1, y1, x2, y2, c, w))
            elif k == "rect":
                _, x, y, w, h, s, f, rx, sw, dash = it
                o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%s" fill="%s" stroke="%s" '
                         'stroke-width="%.1f"%s/>' % (x, y, w, h, rx, f or "none", s if sw > 0.2 else "none", sw,
                                                      ' stroke-dasharray="6 4"' if dash else ""))
            elif k == "circ":
                _, cx, cy, r, s, f, sw = it
                o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" stroke-width="%.1f"/>'
                         % (cx, cy, r, f or "none", s, sw))
            elif k == "poly":
                _, pts, s, f, sw = it
                o.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%.1f" stroke-linejoin="round"/>'
                         % (" ".join("%.1f,%.1f" % p for p in pts), f or "none", s, sw))
            elif k == "text":
                _, x, y, t, size, c, anc, bold, ital = it
                o.append('<text x="%.1f" y="%.1f" font-size="%.1f" fill="%s" text-anchor="%s"%s%s>%s</text>'
                         % (x, y, size, c, anc, ' font-weight="bold"' if bold else "",
                            ' font-style="italic"' if ital else "", html.escape(t)))
        o.append("</svg>")
        return "\n".join(o)

    # ------------------------------------------------------------ PDF
    def draw_pdf(self, c, pw, ph, fonts):
        """c: reportlab canvas, (pw,ph) page size in pt, fonts: dict(latin, latin_b, zh)"""
        from reportlab.lib.colors import HexColor
        s = pw / self.W

        def X(v):
            return v * s

        def Y(v):
            return ph - v * s

        def col(h):
            return HexColor(h)

        for it in self.items:
            k = it[0]
            if k == "line":
                _, x1, y1, x2, y2, cl, w = it
                c.setStrokeColor(col(cl)); c.setLineWidth(w * s); c.setLineCap(1)
                c.line(X(x1), Y(y1), X(x2), Y(y2))
            elif k == "rect":
                _, x, y, w, h, st, f, rx, sw, dash = it
                c.setLineWidth(max(sw * s, 0.01))
                c.setDash([6 * s, 4 * s], 0) if dash else c.setDash()
                if f: c.setFillColor(col(f))
                c.setStrokeColor(col(st))
                do_stroke = 1 if sw > 0.2 else 0
                if rx:
                    c.roundRect(X(x), Y(y + h), w * s, h * s, rx * s, stroke=do_stroke, fill=1 if f else 0)
                else:
                    c.rect(X(x), Y(y + h), w * s, h * s, stroke=do_stroke, fill=1 if f else 0)
                c.setDash()
            elif k == "circ":
                _, cx, cy, r, st, f, sw = it
                c.setLineWidth(sw * s); c.setStrokeColor(col(st))
                if f: c.setFillColor(col(f))
                c.circle(X(cx), Y(cy), r * s, stroke=1, fill=1 if f else 0)
            elif k == "poly":
                _, pts, st, f, sw = it
                c.setLineWidth(sw * s); c.setStrokeColor(col(st)); c.setLineJoin(1)
                if f: c.setFillColor(col(f))
                p = c.beginPath()
                p.moveTo(X(pts[0][0]), Y(pts[0][1]))
                for q in pts[1:]:
                    p.lineTo(X(q[0]), Y(q[1]))
                p.close()
                c.drawPath(p, stroke=1, fill=1 if f else 0)
            elif k == "text":
                _, x, y, t, size, cl, anc, bold, ital = it
                fn = fonts["zh"] if not _is_ascii(t) else (fonts["latin_b"] if bold else fonts["latin"])
                c.setFillColor(col(cl)); c.setFont(fn, size * s)
                if anc == "start":
                    c.drawString(X(x), Y(y), t)
                elif anc == "middle":
                    c.drawCentredString(X(x), Y(y), t)
                else:
                    c.drawRightString(X(x), Y(y), t)
