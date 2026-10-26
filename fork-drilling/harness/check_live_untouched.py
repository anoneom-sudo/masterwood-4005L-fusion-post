#!/usr/bin/env python3
"""Prove this branch did not change live mill output.

The Fusion post engine is not on this machine, so this does not repost a
routing .cnc. It checks the two things that determine mill NC:

1. masterwood_4005L.cps is byte-identical to git HEAD and to main.
2. Inside the drill fork, the functions that emit routing moves are
   byte-identical to main. Gang drilling only adds the boring-cycle path.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIVE = ROOT / "masterwood_4005L.cps"
FORK = ROOT / "fork-drilling" / "masterwood_4005L_drill.cps"

# Routing words. Gang work must not edit these.
UNTOUCHED = [
    "writeLinear",
    "onLinear",
    "onCircular",
    "onRapid",
    "startRoute",
    "formatX",
    "formatY",
    "formatZ",
    "toPanel",
    "mapSpindleTool",
    "toMPerMin",
    "onClose",
    "writeBlock",
]


def git_show(spec):
    return subprocess.check_output(["git", "show", spec], cwd=ROOT)


def functions(text):
    """Split top-level function bodies. Brace depth, not the first '}'."""
    lines = text.splitlines(keepends=True)
    found = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("function "):
            name = line.split()[1].split("(")[0]
            depth = line.count("{") - line.count("}")
            buf = [line]
            i += 1
            while i < len(lines) and depth > 0:
                buf.append(lines[i])
                depth += lines[i].count("{") - lines[i].count("}")
                i += 1
            found[name] = "".join(buf)
        else:
            i += 1
    return found


def main():
    diff = subprocess.run(
        ["git", "diff", "--exit-code", "HEAD", "--", "masterwood_4005L.cps"],
        cwd=ROOT,
    )
    if diff.returncode != 0:
        print("LIVE POST DIFFERS FROM HEAD")
        return 1
    base = subprocess.check_output(
        ["git", "merge-base", "HEAD", "main"], cwd=ROOT, text=True
    ).strip()
    disk = LIVE.read_bytes()
    for rev in ("HEAD", base):
        blob = git_show(rev + ":masterwood_4005L.cps")
        if blob != disk:
            print("live file bytes != " + rev)
            return 1
    print("live post sha256", hashlib.sha256(disk).hexdigest())

    old = functions(git_show(base + ":fork-drilling/masterwood_4005L_drill.cps").decode("utf-8"))
    new = functions(FORK.read_text(encoding="utf-8"))
    changed = []
    for name in UNTOUCHED:
        if name not in old or name not in new:
            changed.append(name + " missing")
        elif old[name] != new[name]:
            changed.append(name)
    if changed:
        print("fork routing functions changed:", ", ".join(changed))
        return 1
    print("fork routing functions unchanged vs main:", " ".join(UNTOUCHED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
