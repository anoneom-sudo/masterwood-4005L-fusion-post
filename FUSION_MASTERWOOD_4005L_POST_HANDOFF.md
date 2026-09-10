# Masterwood Project 4005L — Fusion post handoff

**For:** Grok (terminal) continuing this project  
**Date:** 2026-09-10  
**Goal:** A Fusion 360 post that this MW310 control will run for **3+2 first**, simultaneous 5-axis later if needed.  
**Do not** patch Autodesk `masterwood.cps` and expect it to cut. That file is 3-axis Fanuc-in-`.prg`. This machine is native Masterwood.

Living scratchpad (older, broader): `artifacts/MASTERWOOD_4005L_PROJECT_MEMORY.md`.

---

## 0. Status

| Item | State |
|---|---|
| Dialect | **Proven** from live `.prg` (Test.PRG, test2.PRG, 116-file archive) |
| Generic Autodesk `masterwood.cps` | Wrong language. Rejects multi-axis machine and Tool Orientation. |
| Production post | **Not started.** Fork a new `masterwood_4005L.cps` (or write native from scratch). |
| Fusion machine definition | Not created. Numbers below are enough for a first draft. |
| First Fusion-posted air cut | Not done. |

**Next work:** implement native 3+2 post (header + G172/G173 + T41/n + Z flip + F/S units). Compare output to `test2.PRG`. Do not implement simultaneous 5-axis until 3+2 matches.

---

## 1. Control dialect (must emit this)

File starts and ends with `%`. No `G0`, no `M6`, no `M30`, no trailing `.`.

Archive stats (116 programs): G172 ×1320, G173 ×26, G101 ×13706, G100 ×2170, G0 ×0, M30 ×0, `T M6` ×0.

### Header (from Test.PRG / test2.PRG)

```
%
|1
|2 0
|3 1
|4 800          panel X (mm)   — Fusion stock / setup X
|5 18           panel thickness
|6 500          panel Y (mm)
|7 0 0 0 0
|8 0
|9 4000
|10
|11 1
|12
|13
|14
|44 0
:1
G120 K1
#910=DX
#911=DY
M61 K0 D1
```

`#910=DX` / `#911=DY` are panel size variables. Masterwood CAM often programs `Y=#911-(offset)` from the far edge. Fusion may post **absolute Y** if the WCS origin is set that way. Do not copy `#911-` until the user’s Fusion origin is known.

### Vertical route (3-axis / A=90)

```
G172 X144.50 Y=#902 Z0 S20 E2 T41/10 J90
G42
G101 X144.50 Y=#902 Z0 F3
G101 X100 Y=#902 Z0 F3
…
G40
G101 … F3
```

Source: `Test.PRG` — 100×100 mm square in air, tool 41/10.

### 3+2 / oriented route

```
G173 X141.09 Y=#902 Z-20 S20 E2 T41/10 A80 C-15 D0
G101 X144.50 Y=#902 Z0 F2
G101 … Z0 F3 …
G101 X141.09 Y=#902 Z-20 F2
```

Source: `test2.PRG`. Operator set A=80 and UI rotation 15° on “Horizontale vlak”. File wrote **`C-15`**, not C15.

Rules:

- Vertical → `G172 … T41/n S.. E.. J90` then `G101` / `G102` / `G103`
- Any A/C not “J90 vertical” → `G173 … T41/n S.. E.. A.. C.. D0` then `G101`…
- `D0` is on every G173 in the archive
- XYZ after G173 stay in **panel WCS** (same X/Y as a vertical square). Not a Fanuc tilted workplane. Control applies head / TCP (`RAGGIO 5 A` = 184.90 mm)
- C almost never appears on G101 (once, in an A-cal file). Set A/C on G173
- `G41`/`G42`/`G40` are used; test2 had none

### Units on motion words

| Word | Working rule | Example |
|---|---|---|
| `S` on G172/G173 | rpm / 1000 | `S20` = 20000 rpm |
| `F` on G101 | m/min | `F3` = 3000 mm/min |
| `E` on G172/G173 | plunge, same unit as F | `E2` |
| Negative S | reverse spindle | `S-18`, `S-20` exist |

Production S is usually 18–22; F 1–4. `S3` appears on a pocket-check program, not typical cutting.

### Z convention (critical)

**Z− = above the panel. Z0 = top surface. Z+ = into the wood.**

test2: approach/retract `Z-20`, cut `Z0`. Archive G173 often starts `Z-20` then cuts `Z30` (30 mm deep).

Fusion is Z+ up. **The post must negate Z** (or equivalent).

### Other codes (do not invent in v1)

| Code | Role |
|---|---|
| `G100 … Tn` | Vertical / single drill |
| `G184`/`G185` + T31/T33 | Horizontal boring |
| `T81` + `#T81=…` | Gang / line boring |
| `G92 U V W` | Work shift |
| `G192` | Local origin |
| `G120 Kn` | Field / zone |
| `M61 Kn` | Vacuum / zone |
| `M60 K41` | Spindle unit 41 |
| `G170` | Non-cut move / park |
| `M98` | Macro |

v1 post: routing + 3+2 only (G172/G173/G101–103/G40–42). Drills later.

---

## 2. Kinematics to put in Fusion + post

Head/head on the spindle. C first (about Z), then A.

| Pose | Machine |
|---|---|
| A = **90** | Tool **vertical** (down) |
| A = **0**, C = **0** | Tool **horizontal**, pointing **right** (+X, 3 o’clock) |
| +C | **Clockwise** as seen from above |
| C software limits | **−140.00 … +286.80°** (`Syncro.prm`) |
| A software limits | **−38.60 … +211.40°** |
| A in Masterwood ops | often **0 … 90** only |
| Pivot / TCP radius | **RAGGIO 5 A = 184.90 mm** (`pargen.prm`) |
| Head envelope | INGOMBRO 5A = 120 mm |
| OFF.ANG A / C | **0 / 0** (no software trim stored) |

Clock from C=0 at 3 o’clock, +C clockwise:

- C0 = right  
- C90 = operator (6 o’clock)  
- C180 = left  
- C270 = column / back (12 o’clock)  

Archive G173 C values: 0, 90, 180, 270, one −5, plus test2 **C−15**.

### Fusion Machine Builder (draft)

- Type: milling, 5-axis **head/head**
- C vector **`[0, 0, −1]`** so Fusion +C = clockwise from above (matches control numbers)
- At C=0, A swings in the **XZ** plane → A axis at C=0 is **Y**, not X  
  Direction `[0, 1, 0]` if +Y is toward the column; flip if a test tilt is mirrored
- A home / safe: **90**. C home (work zero): **0**  
  Do not put Syncro homing-switch C ≈ −139° in Fusion home
- **Do not** also add a +90 C home if A is already about Y at C=0
- TCP off in the post (`supportsTCP` false). XYZ in work coords; control handles G173

Generic Fusion template (C about +Z, A about +X) has C=0 with A tilting front/back (12/6). This machine’s C=0 is 3 o’clock. Rebuild A about Y; do not stack a C offset on top.

### Fusion CAM (3+2)

- One setup WCS on the panel. Do **not** make a new setup per face  
- Operation **Tool Orientation** (Multi-Axis tab): Z = tool axis, X along the slot  
- Face slot, tool vertical: leave orientation off, or Z = setup Z → post `G172 J90`  
- Edge slot, tool horizontal right: Z out of +X face → expect A0 C0 → `G173 A0 C0 D0`  
- Paths: **2D Slot**, or Pocket / Contour / Trace. Not Swarf / Multi-Axis Flow (simultaneous)

---

## 3. Linear envelope (for machine def / simulation)

MW310 linear params are **0.01 mm**. Rotary FCSW **0.01°**.

| Axis | Software limits | Rapid | Notes |
|---|---|---|---|
| X / U | −15 … +6021.5 mm | 60 m/min | Stops usable ≈ 482 … 5691 mm |
| Y / V | −6 … +2018 mm | 48 m/min | **Work Y max marked 1360 mm.** Extra stroke is for boring-head offset, not more table |
| Z / W | −1 … +616 mm | 19.2 m/min | Full ram, not work cube |
| Two X zones | zone1 X≤2760, zone2 X≥3380 | | `EN_CAMPO_INT=1` |

Pods: **8 bars**, bar 115×1300 mm, cup **115×140×100 mm** compressed (measured). Do not inflate pod height; Fusion will treat extra height as solid.

ATC: on the **carriage** (moves in X with the head). Does **not** follow Z. Pneumatic in/out toward spindle. 10 pockets on a 100 mm circle, 36° (`Offset.prm` C0–C9 type 7). `Q 7 4780` = 47.80 mm approach.

---

## 4. Tool mapping

Native spindle address is **unit 41**.

| Station | Native | Fusion T (proposed) |
|---|---|---|
| Boring 1–13, 31, 33, 35–38 | `T1` … | T1–T50 as-is |
| Electrospindle pockets | **`T41/1` … `T41/10`** | T101–T110 → post must emit `41/1` … `41/10` |
| Probe | `T49` | T49 |

All ten pockets appear in programs. `UteName.dat` lists 41/1–6 and 41/8–10 (41/7 unnamed; TAB01 C7 still exists).

**41/6** = “zaag als frees 180mm” (saw used as a cutter in the spindle). No saw on the boring block.

Post: `T101 M6` is wrong. Put `T41/10` on the G172/G173 line.

---

## 5. What to write in the post (order)

Fork away from `masterwood.cps`. Keep that file as reference only.

1. `.prg` header (`|1`…`|14`, `|4|5|6` from stock) + `%` / `:1` / `G120` / `#910` `#911`  
2. Map tool number → `41/n`  
3. Convert Fusion mm/min and rpm → `F` m/min, `S` thousands, `E` plunge  
4. **Negate Z**  
5. If tool axis = setup Z (A90) → one `G172 … J90` then G101/G102/G103  
6. Else → `G173 … A.. C.. D0` then G101…  
7. A/C from Fusion workplane; output **control** angles (A90 vertical, C0 = right). Account for UI-vs-file C sign only if Fusion’s C already matches the **file** (test2 file is C−15)  
8. Retract in Z−  
9. Close with `%`  
10. Error on simultaneous 5-axis (`isMultiAxis()` true with moving ABC during the cut) until later  

Do **not** output machine-solved XYZ for the head. Output work XYZ + A + C.

Golden files to diff against:

- `attachments/test2.PRG` and archive `Test.PRG`  
- Any new MW310 export of the same square  

---

## 6. Files in this project

| Path | Role |
|---|---|
| `attachments/masterwood.cps` | Generic Autodesk 3-axis post (wrong dialect) |
| `attachments/TAB01.DAT` | Tool tech table |
| `attachments/MW310 PARAM.zip` | Live `Param/` (60 files) |
| `Param/pargen.prm` | Parametri generali + **TESTA 5 ASSI** |
| `Param/Syncro.prm` | Live axis limits (2025-01-09) |
| `Param/Offset.prm` | Station XYZ, ATC `C`/`Q` |
| `attachments/PRG.zip` | 116 live programs |
| `attachments/test2.PRG` | G173 A80 C−15 proof |
| `artifacts/MASTERWOOD_4005L_PROJECT_MEMORY.md` | Broader project log |

There is **no** file named Parametri. The Parametri menu writes `pargen.prm`.

---

## 7. Machine function (reference)

### 5-axis head

Birotative electrospindle. C about Z, A tilts the tool. A90 = down. A0 C0 = tool to the right. Pivot 184.90 mm. Hood enabled, anticollision 75 mm.

`pargen.prm` TESTA 5 ASSI:

```
EN_ASSEA 6
RAGGIO 5 A  18490
INGOMBRO 5A 12000
OFF.ANG. A  0
OFF.ANG. C  0
Q_ANTIC_CUF 7500
```

### Boring block

On the **back** of the mill head (1360 / gantry-leg / +Y direction). Whole block drops as a unit; selected drills then extend. Multiple verticals can run together (line boring). Offset.prm verticals 0–12, type 1, **32 mm** pitch along X (50, 82, … 242 mm), second row in −Y from the corner.

Horizontals: six programmed stations, types 2–5 = four headings. Two bits on one pneumatic slide share the slide but have **separate XYZ**. Z on those rows is still **height** (~449 mm), not hole depth. Depth into an edge is X or Y.

Operator believes eight physical horizontals (two per side); file shows six live stations.

No grooving saw on the block.

Line 40 type 99 = spindle unit 41 (X109.75 Y281.40 Z623.00 — head reference, not tool length).  
Line 48 type 21 = probe T49.

### Table

8 vacuum bars, pods 115×140×100 mm compressed. Work Y marked **1360 mm**. Brochure 1380 mm is gantry-leg theory. Extra Y travel exists so the offset boring unit can reach the same panel as the spindle.

### ATC

Star/circle magazine on the carriage. Fixed Z. Pneumatic approach. Pockets C0–C9 type 7, r=100 mm.

---

## 8. Calibration and known accuracy issues

### What lives where

| Problem | File / field |
|---|---|
| A90 not mechanical vertical, constant lean | `pargen.prm` **OFF.ANG. A** (now 0) |
| C0 not 3 o’clock | **OFF.ANG. C** (now 0) |
| One drill tip high/low or shallow | that station’s XYZ in **Offset.prm** |
| Soft limits / speeds | **Syncro.prm** |
| Pod / origin / DY | WCS, `G92`, `#911=DY`, battute — not OFF.ANG |

Do not edit OFF.ANG and Offset.prm in the same session.

`CALIBREREN A AS.PRG` in the archive: G173 A90 C0 vs A90 C180.

### Operator-reported (2026-09-10)

1. **3+2 slots:** stepped walls; mouth **wider at the top** as depth increases.  
   Classic leaned tool: A not normal to the face, or G173 A≠90 used as a face slot. Check the `.prg` first (`J90` vs `A80`). Same flare everywhere → A zero. Flare changes along the bed → pods/rails.

2. **Left/right drilling wrong on both spindle and boring head.**  
   Boring block does **not** use spindle A/C. Shared miss (height or Y) → WCS / DY / Z datum. Spindle L vs R only → C 0/180. Boring L vs R only → Offset.prm types 2–5.

### Suggested order

1. Read the bad slot program: G172 J90 or G173 A≠90?  
2. Vertical face cut J90 at two places on the table  
3. Vertical drill height vs horizontal spindle hole height — if those disagree, A0 is not 90° from J90  
4. Small OFF.ANG. A only after that  
5. Boring offsets last  

### MW310 UI vs posted C

UI “15°” on Horizontale vlak → file **C−15**. Post the **file** number. Confirm lean direction of C−15 (column vs operator) before locking Fusion C sign.

---

## 9. Open questions

1. From A90, does tilting toward the operator increase or decrease A?  
2. Which way does C−15 point (column vs operator)?  
3. Fusion origin vs Masterwood `#911=DY` Y convention  
4. D-axis physical role (`EN_ASSED=4`)  
5. Pocket 41/7 in use?  
6. Safe park / tool-change Z (magazine does not follow W)  
7. Simultaneous 5-axis: not seen as interpolated A/C on G101 in production files — G173 is indexed  

---

## 10. Short post spec (copy into the new `.cps` header comment)

```
Masterwood MW310 Project 4005L
Native PRG: % header |1..|14 :1 G120 G172/G173 G101 G100 %
Spindle tools T41/1..T41/10 on the G172/G173 line
G172 … J90          vertical
G173 … A.. C.. D0   3+2
S = rpm/1000, F = m/min, E = plunge
Z+ into the panel (negate Fusion Z)
Work XYZ + A + C; no TWP; no TCP output
A90 = tool down; A0 C0 = tool right; +C clockwise from above
Pivot 184.90 mm is on the control
3+2 only in v1
```
