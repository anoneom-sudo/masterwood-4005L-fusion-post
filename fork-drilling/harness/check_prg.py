#!/usr/bin/env python3
"""Static checker for MW310 .prg output from the drilling fork.

Usage: check_prg.py file.prg [more.prg ...]
Exit 1 if any rule fails. Rules come from AGENTS.md + docs/drilling-dialect.md.
Prints a hole list in program coordinates (Y resolved from #911 = |6 DY).
"""
import re, sys

NUM = r"-?\d+(?:\.\d+)?"
G100_RE = re.compile(r"^G100 X(?P<x>" + NUM + r") Y(?P<y>=#902|" + NUM + r") Z(?P<z>" + NUM +
                     r") F(?P<f>" + NUM + r") T(?P<t>\d+)$")

def check(path):
    errs, warns, holes = [], [], []
    lines = [l.rstrip("\r\n") for l in open(path, encoding="latin1")]
    body = [l for l in lines if l.strip() != ""]
    if not body or body[0] != "%" or body[-1] != "%":
        errs.append("file must start and end with %")
    hdr = {}
    for l in body:
        m = re.match(r"^\|(\d+) ?(.*)$", l)
        if m:
            hdr[int(m.group(1))] = m.group(2).strip()
    try:
        dx, dz, dy = float(hdr[4]), float(hdr[5]), float(hdr[6])
    except Exception:
        errs.append("header |4 |5 |6 missing or not numeric"); dx = dz = dy = 0.0
    tables = {}
    last902 = None
    for i, l in enumerate(body, 1):
        if re.search(r"(^|\s)(G0|G00|G1|G01|M6|M06|M30)(\s|$)", l):
            errs.append("line %d: forbidden Fanuc word: %s" % (i, l))
        if l.endswith(".") and not l.startswith("("):
            errs.append("line %d: trailing dot: %s" % (i, l))
        m = re.match(r"^#902=#911-\((" + NUM + r")\)$", l)
        if m:
            last902 = dy - float(m.group(1)); continue
        m = re.match(r"^#([TXYS])(8[1-9])=([\d,]+)$", l)
        if m:
            tables.setdefault(int(m.group(2)), {})[m.group(1)] = [int(s) for s in m.group(3).split(",")]
            continue
        if l.startswith("G100"):
            g = G100_RE.match(l)
            if not g:
                errs.append("line %d: G100 not in X Y Z F T form: %s" % (i, l)); continue
            y = g.group("y")
            if y == "=#902":
                if last902 is None:
                    errs.append("line %d: Y=#902 without a preceding #902=#911-(..)" % i); continue
                yv = last902; last902 = None
            else:
                yv = float(y)
            x, z, f, t = float(g.group("x")), float(g.group("z")), float(g.group("f")), int(g.group("t"))
            if not (0 < z <= dz + 1.0):
                errs.append("line %d: depth Z%s outside 0 < Z <= panel %s + 1" % (i, z, dz))
            if not (0 < f <= 5):
                warns.append("line %d: F%s m/min unusual for G100 (archive: 0.5..2)" % (i, f))
            if not (0 <= x <= dx and 0 <= yv <= dy):
                warns.append("line %d: hole X%s Y%s outside panel %sx%s" % (i, x, yv, dx, dy))
            if 81 <= t <= 89:
                if t not in tables or "T" not in tables[t]:
                    errs.append("line %d: T%d used but #T%d table not defined before" % (i, t, t)); continue
                # Y arm offsets from Offset.prm, in 0.01 mm. Used only when the
                # group has #Y and no #X (tablet.PRG shape).
                y_off = {1: -11063, 8: -17485, 9: -20675, 10: -23885, 12: -30285, 13: -33485}
                ts = tables[t]["T"]
                if "Y" in tables[t] and "X" not in tables[t]:
                    first = ts[0]
                    if first not in y_off:
                        errs.append("line %d: Y-gang station %s has no Offset.prm Y" % (i, first)); continue
                    for s in ts:
                        if s not in y_off:
                            errs.append("line %d: Y-gang station %s has no Offset.prm Y" % (i, s)); continue
                        hy = round(yv + (y_off[s] - y_off[first]) / 100.0, 2)
                        holes.append((x, hy, z, "T%d/s%d" % (t, s)))
                else:
                    for s in ts:
                        holes.append((x + 32 * (s - ts[0]), yv, z, "T%d/s%d" % (t, s)))
            elif 1 <= t <= 50:
                holes.append((x, yv, z, "T%d" % t))
            else:
                errs.append("line %d: T%d not a boring station (1..50) or group (81..89)" % (i, t))
    print("== %s: %d holes, %d errors, %d warnings" % (path, len(holes), len(errs), len(warns)))
    for e in errs: print("ERROR", e)
    for w in warns: print("WARN ", w)
    for h in sorted(holes, key=lambda h: (h[1], h[0])):
        print("  hole X%-8g Y%-8g Z%-6g %s" % h)
    return not errs

if __name__ == "__main__":
    ok = all([check(p) for p in sys.argv[1:]])
    sys.exit(0 if ok else 1)
