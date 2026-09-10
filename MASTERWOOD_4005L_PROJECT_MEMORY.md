# Masterwood Project 4005L × Fusion 360 — Project Memory

Last updated: 2026-09-10 (test2.PRG A80 C-15, Z- above surface)
Conversation role: living record of confirmed machine data, setup decisions, and progress.
How to use: re-attach this file at the start of a new chat. When a new variable is given, add it here and mark the source (operator / plate / Master AT / measured / MW310 file).

Unit convention in MW310 `.prm` linear values: **0.01 mm** (100 = 1 mm).
Unit convention for A/C in `Syncro.prm` FCSW: treated as **0.01 degree** (100 = 1°). This matches the operator’s ~426° C span.

---

## 1. Status

| Item | State | Notes |
|---|---|---|
| Generic Autodesk `masterwood.cps` | Installed / available | 3-axis ISO-in-PRG only. Rejects multi-axis machine and any non-Z tool axis. |
| 5-axis production post | Not started | Must emit native `41/n` spindle calls, A/C, boring-head offsets from `Offset.prm`. |
| Fusion machine definition | Not created | Enough axis numbers now exist to build a first kinematics draft. |
| Fusion tool library from TAB01.DAT | Inventory parsed | Native IDs confirmed in `UteName.dat` as `41/1`…`41/10`. |
| Control dialect proven | **Native Masterwood**, not Fanuc-in-PRG | — | `Test.PRG` + archive | 2026-09-10 | G172 / G173 / G101 / G100. Generic Autodesk G0/G1/T101 M6 will not run. |
| MW310 parameter pack | Parsed 2026-09-08 | Source zip `MW310 PARAM.zip` (60 files). Live axis file = `Param/Syncro.prm` (dated 2025-01-09). Live general = `Param/pargen.prm`. |
| First air-cut | `Test.PRG` + `test2.PRG` captured | Vertical G172 and tilted G173 squares from MW310. Not yet run as Fusion output. |

---

## 2. Confirmed machine variables

Only values the operator or a file from this machine has given. Brochure guesses stay in section 3.

| Variable | Value | Unit | Source | Date | Notes |
|---|---|---|---|---|---|
| Y work limit on machine | **1360** | mm | Operator, text on the machine | 2026-09-08 | Plate says “max 1360 mm”. Brochure 1380 is theoretical/gantry-leg figure — do not use 1380 as programmed work Y. |
| Extra Y axis travel | carriage travel past the work cube so the **offset boring unit** can cover the same panel as the spindle | — | Operator explanation | 2026-09-08 | Live V-axis −6 … +2018 mm is not extra table. Boring block is on the **back / 1380-direction** of the 5-axis head; drills need the spindle to run past the 1360 mm field. |
| Boring block location | Back side of the 5-axis head, toward the 1360/1380 / gantry-leg direction | — | Operator | 2026-09-08 | Not left/right of the spindle as the primary offset. Rear-of-head in Y. |
| Boring block Z | Block extends **as a unit**; selected drills then extend further | — | Operator (belief) | 2026-09-08 | Whole block drops. Drills in the cycle also stroke down. Several drills can be down together for **line boring**. Independent of 5-axis W still “I believe,” not proven by a jog test. |
| Line boring | Yes, multiple drills at once | — | Operator | 2026-09-08 | Confirms a gang boring head, not single-spindle only. Pitch not measured (typical 32 mm — unconfirmed). |
| Grooving saw on boring block | **None** | — | Operator + TAB01/Offset | 2026-09-08 | Confirmed: no saw on the drill block. Brochure Ø125 block saw does not apply. |
| Saw in spindle magazine | C6 / **41/6** = “zaag als frees 180mm” — **confirmed on the machine** | — | TAB01 + operator | 2026-09-08 | 180 mm blade in the electrospindle magazine, used as a cutter. Not a gang-head groover. Table rpm 14051. |
| Horizontal drills (file) | 6 stations programmed: 31,33,35–38 | — | TAB01 + Offset | 2026-09-08 | 31/33/35/37 named “Hor Drevelboor 8mm”; 36/38 “Drevelboor 57x6.35mm” but Offset types 4–5 = horizontal. Operator still believes 8 physical (2 per side). |
| ATC location | On the **carriage** (travels in X with the head) | — | Operator | 2026-09-08 | Circular/star rack from Offset.prm C0–C9. Not a bed-mounted linear rack. |
| ATC Z motion | **Does not lift with Z / W** | — | Operator | 2026-09-08 | Magazine height is fixed on the carriage. Tool change only at a matching spindle Z. Simulation: magazine body is a carriage child, not a Z-ram child. |
| ATC approach axis | Extra **pneumatic** in/out toward the spindle for tool change | — | Operator | 2026-09-08 | Not the W axis. Direction (X vs Y) and stroke not yet measured. Offset.prm `Q 7 4780` (47.80 mm) may be related — unconfirmed. |
| Reported: L/R drilling | Spindle **and** boring-head holes from left/right are regularly wrong | — | Operator | 2026-09-10 | Shared WCS/origin more likely than A offset alone (boring block does not use spindle A/C). |
| Reported: 3+2 slots | Stepped walls; mouth **wider at the top** as depth increases | — | Operator | 2026-09-10 | Classic leaned tool: A not normal to the cut face, or G173 A≠90 used on a face slot. Not the first place to put OFF.ANG. |
| Z sense (working) | **Z− is above the panel, Z0 = surface, Z+ into the panel** | mm | test2 vs archive G173 | 2026-09-10 | Matches classic Masterwood. Fusion post must negate Z or set a Z-up machine with inverted output. |
| Pose C=0 A=0 | Spindle **horizontal**, tool pointing **right** | — | Operator | 2026-09-08 | Completes the head frame: A=90 down; A=0 at C=0 points to 3 o’clock / right. Fusion A offset 90°; C=0 is that same right-hand heading. |
| A at tool-horizontal | **0** (at least when C=0) | degrees | Operator | 2026-09-08 | Matches the Masterwood 0–90 working band (edge ↔ face). |
| C-axis travel (operator) | ±213 | degrees | Operator | 2026-09-08 | Half-span. Control zero is **not** in the middle. Software −140 … +286.8. |
| C-axis software limits | −140.00 … +286.80 | degrees | `Syncro.prm` FCSW C −14000 / 28680 | 2026-09-08 | Span 426.80°, matches ±213. **Use these limits in Fusion**, not ±213 about zero. |
| C-axis max vel | 5000 | control units | `Syncro.prm` | 2026-09-08 | Jog max in pargen: 300 |
| A at tool-vertical | **90** | degrees | Operator (jog, spindle straight down) | 2026-09-08 | Do not treat A=0 as vertical. Fusion kinematics need a 90° A offset. |
| A working range in Masterwood | **0 … 90** for several operations | degrees | Operator | 2026-09-08 | Tighter than Syncro FCSW (−38.6 … +211.4). Treat 0–90 as the **CAM / cycle limit**, not yet as the hard stop. A=0 is expected to be horizontal if 90 is vertical — unconfirmed by a jog. |
| A-axis software limits | −38.60 … +211.40 | degrees | `Syncro.prm` FCSW A −3860 / 21140 | 2026-09-08 | Span 250.00°. Vertical is at 90°, not mid-travel. |
| A-axis max vel | 4500 | control units | `Syncro.prm` | 2026-09-08 | Jog max in pargen: 300 |
| A-axis enabled | yes (`EN_ASSEA` = 6) | — | `pargen.prm` 5-axis head section | 2026-09-08 | Confirms birotative head |
| C-axis enabled | yes (`EN_ASSEC` = 1) | — | `pargen.prm` | 2026-09-08 | |
| 5-axis head radius (RAGGIO 5 A) | 184.90 | mm | `pargen.prm` 18490 | 2026-09-08 | Pivot / TCP reference radius. Critical for 5-axis post. |
| 5-axis head envelope (INGOMBRO 5A) | 120.00 | mm | `pargen.prm` 12000 | 2026-09-08 | Collision envelope around head |
| A/C angular offset | 0 / 0 | deg | `pargen.prm` OFF.ANG. A/C | 2026-09-08 | No extra software angle offset stored |
| X / U software limits | −15.00 … +6021.50 | mm | `Syncro.prm` FCSW U −1500 / 602150 | 2026-09-08 | Full axis stroke ≈ 6036 mm. Usable table is smaller (stops / zones). |
| Y / V software limits | −6.00 … +2018.00 | mm | `Syncro.prm` FCSW V −600 / 201800 | 2026-09-08 | Full **carriage** stroke ≈ 2024 mm. **Work Y = 1360 mm** (marked). Extra travel is for boring-head offset, not more table. |
| Z / W software limits | −1.00 … +616.00 | mm | `Syncro.prm` FCSW W −100 / 61600 | 2026-09-08 | Full Z stroke ≈ 617 mm including tool-change lift. **Not** the old brochure “200 mm on pods”. |
| X max rapid | 60000 | mm/min | `Syncro.prm` VEL max U | 2026-09-08 | 60 m/min |
| Y max rapid | 48000 | mm/min | `Syncro.prm` VEL max V | 2026-09-08 | 48 m/min |
| Z max rapid | 19200 | mm/min | `Syncro.prm` VEL max W | 2026-09-08 | 19.2 m/min |
| D-axis | same stroke as U | mm | `Syncro.prm` + `EN_ASSED` = 4 | 2026-09-08 | Present in software. Role TBD (slave / second X / changer). `EN_2GAMBI` = 0. |
| Two work zones | yes | — | `pargen.prm` EN_CAMPO_INT = 1 | 2026-09-08 | X max zone 1 = 2760 mm; X min zone 2 = 3380 mm |
| Max panel length zone 1 / 2 | 1200 / 1200 | mm | `pargen.prm` L.MAX.PAN.Z1/Z2 120000 | 2026-09-08 | Software cap per zone; physical bed is longer |
| Rails / bars (pianetti) | 8 | — | `ventose.prm` NUM_PIANETTI=8 | 2026-09-08 | |
| Bar size | 115 × 1300 | mm | `ventose.prm` Dim_X/Y Pianetto 11500 / 130000 | 2026-09-08 | |
| Pod (supporto) footprint | 115 × 140 | mm | `ventose.prm` 11500 × 14000 | 2026-09-08 | Matches classic 114×140 Masterwood cup. |
| Pod Y travel on bar | 45 … 1255 | mm | `ventose.prm` YMin/YMax Supporto | 2026-09-08 | |
| Pod height (working) | **100** | mm | Operator measured | 2026-09-08 | Height with vacuum on and rubber **fully compressed**, top face treated as flat. Uncompressed rubber looked ~100–105 mm; that free height is not the machining datum. Fusion fixture Z = 100 mm. |
| Vacuum / pods enabled | EN_VENTOSE = 5 | — | `pargen.prm` | 2026-09-08 | |
| Dust hood | enabled (`EN_CUFFIA` = 1) | — | `pargen.prm` | 2026-09-08 | Anticollision hood distance `Q_ANTIC_CUF` = 75 mm |
| Probe | Tastatore, tool 49, type enabled (`TIPO_TASTA` = 1) | — | TAB01 + pargen | 2026-09-08 | Max probe W `MAX Q.TAST.W` = 420 mm |
| Software family | MW310 parameter set | — | zip folder `Param/` | 2026-09-08 | Files named MW310, not Master 3D. |
| Native spindle tool IDs | **41/1 … 41/10** | — | `UteName.dat` | 2026-09-08 | C1 in TAB01 = 41/1 on the control. Generic post `T101 M6` will not match this. |

### Stops (`BATTUTE.PRM`, 0.01 mm)

| Stop | X mm | Y mm | Flag |
|---|---|---|---|
| A | 481.92 | 678.90 | 0 |
| B | 481.92 | 678.90 | 1 |
| C | 5691.30 | 678.90 | 0 |
| D | 5691.30 | 678.90 | 1 |
| E | 481.95 | 1139.32 | 0 |
| F | 481.95 | 1139.32 | 1 |
| G | 5691.30 | 1139.40 | 0 |
| H | 5691.30 | 1139.40 | 1 |
| I | 482.55 | 1889.20 | 10 |
| J | 482.55 | 1889.20 | 11 |
| K | 5691.30 | 1889.10 | 10 |
| L | 5691.30 | 1889.10 | 11 |
| R (Y ref) | — | 678.90 | — |

Usable X between side stops ≈ **481.9 … 5691.3 mm** (span ≈ 5209 mm). That matches an “L” long bed much better than raw U-axis 0–6021.

### Native tool names (`UteName.dat`)

| Control ID | Label in file |
|---|---|
| 1–9, 11, 12, 31, 33, 35–38, 49 | Gereedschap / Tool (boring + probe) |
| **41/1, 41/2, 41/3, 41/4, 41/5, 41/6, 41/8, 41/9, 41/10** | Utensile / Gereedschap (electrospindle / ATC) |

Missing 41/7 in the name list (TAB01 C7 still exists as diamantfrees 80×26). Pocket 7 may be unnamed, empty in the name file, or unused.

### Native program dialect (`Test.PRG` 2026-09-10 + archive)

`Test.PRG` = 100×100 mm square in air, tool **41/10**.

```
%
|1 … |14     header / stock (this file: |4=800 |5=18 |6=500)
:1
G120 K1
#910=DX
#911=DY
M61 K0 D1
G172 X.. Y=#902 Z0 S20 E2 T41/10 J90
G42
G101 … F3
G40
%
```

| Token | Meaning (from use) |
|---|---|
| File start/end | `%` … `%` (not `M30` + `.`) |
| `G172` | Start 3-axis / vertical route. Tool + S + E + **J** (J90 = tool vertical). |
| `G173` | Start oriented route: `A.. C.. D0` on the same line. |
| `G101` / `G103` | Linear / arc (G1 / G3). C can also appear on `G101`. |
| `G100` | Drill. `T1`… or gang `T81`. |
| `T41/10` | Spindle pocket 10. Never `T110 M6`. |
| `S20` | Spindle word on G172/G173. Treat as **rpm/1000** until proven (20 → 20000). |
| `F3` | Feed on G101. Treat as **m/min** until proven (3 → 3000 mm/min). |
| `E2` | Plunge / entry feed on G172/G173. |
| `J90` | Vertical tool on G172 (same idea as A90). `J0` also seen. |
| `A90 C0 D0` | Explicit 3+2 on G173. D0 always present in samples. |
| `#911=DY` then `Y=#911-(…)` | Y often from panel depth DY, not raw machine Y. |
| `M61 Kn` | Zone / vacuum field. |
| `G120 Kn` | Work field / offset select. |
| `M60 K41` | Spindle unit 41 (tool-change related). |
| `G170` | Move without cutting (park). |

`test2.PRG` (2026-09-10) = same 100×100 idea, tool **41/10**, tilted.

```
G173 X141.09 Y=#902 Z-20 S20 E2 T41/10 A80 C-15 D0
G101 X144.50 Y=#902 Z0 F2
G101 … square at Z0 F3 …
G101 X141.09 Y=#902 Z-20 F2
```

- MW310 fields: A **80**, rotation **15**, tool 41/10, X1 144.50, Y1 100, F 2 / 3, S 20.
- Posted C is **−15**, not +15.
- No G41/G42. XY stays in panel WCS (not a tilted workplane).
- Approach/retract **Z−20**, cut **Z0** → Z− above surface, Z+ into panel.
- `D0` present. Control expected to apply head/TCP (`RAGGIO 5 A` = 184.90).

Post rules from these two files:
- Vertical → `G172 … T41/n J90` then `G101`
- Any A/C ≠ vertical J90 → `G173 … T41/n A.. C.. D0` then `G101`
- Output work XYZ (panel), not pre-rotated machine XYZ
- Flip Fusion Z (Z+ up) to Masterwood Z (Z+ down)

### Offset.prm layout (this machine)

Linear values **0.01 mm**. Station line:

`index  type  X  Y  Z  p5  p6  …  enable  seq  toolId  …`

| type | Meaning here |
|---|---|
| 0 | empty |
| 1 | vertical drill (stations 0–12) |
| 2–5 | horizontal directions (30,32,34–37) |
| 21 | probe → tool 49 |
| 99 | electrospindle unit **41** (line 40) |

`C n type X Y 41` = ATC pocket. Type 7 = circle r=100 mm, 36°. `Q 7 4780` = 47.80 mm approach.

---

## 3. Assumed / unverified (do not treat as fact)

| Variable | Working assumption | Unit | Confidence | Confirm how |
|---|---|---|---|---|
| Model | Project 4005L | — | High (user) | Nameplate |
| Kinematics | Head/head: C about Z, A about X, both on the spindle | — | High | Jog and watch |
| A = 0 meaning | **Not vertical.** Vertical = A 90° | deg | High | Operator jog |
| Usable machining Z above pod | far less than 616 mm | mm | Medium | Measure spindle nose at pod top vs W max |
| Spindle power / taper | 12 kW liquid, HSK-F63 | — | Medium | Nameplate / tool cone |
| Max spindle rpm | ~24000 | rpm | Medium | Inverter; TAB01 C tools run 10–19k |
| ATC mechanical pockets | 10 on circle in Offset.prm, brochure often says 16 | — | Medium from file | Count pockets on the machine |
| ATC approach direction | pneumatic toward spindle; axis unknown | — | Low | Look at change: in/out in X or Y |
| Boring head | Verticals 0–12 in Offset.prm + horizontals 30–37 + probe 48; **rear of 5-axis head**, can drop below it | — | High | Visual + operator |
| Grooving saw | brochure Ø125 on block: **not in this config**. Spindle C6 is a 180 mm “zaag als frees” | — | High from files | Glance at pocket 41/6 |
| Brochure overall L version | length 8790 × widths 3280 / 4070 / 3590 × height 2280 | mm | 2009 PROJECT 4000/4005 brochure | 2026-09-08 | External envelope only. **Not measured on this machine.** Work strokes in same brochure: X 6000 / Y 1380 / Z 250 for 4005 L. Live Syncro strokes are larger (axis travel, not work cube). |
| Brochure work strokes 4005 L | X 6000, Y 1380, Z 250 | mm | same brochure | 2026-09-08 | Aligns with stops span ~5209 and bar length 1300. Z 250 is usable work, not W 616. |
| Brochure rapids 4005 | 90 / 70 / 25 | m/min | same brochure | 2026-09-08 | Live Syncro is 60 / 48 / 19.2 — use live file. |
| Public 3D machine model | none found | — | web search 2026-09-08 | 2026-09-08 | No GrabCAD/STEP for Project 4005. Closest sisters: Project 385 L 5-axis, Project 455 L. Simulation will start from a Fusion kinematic model we build, not a downloaded assembly. |

---

## 4. Files in play

| File | Role |
|---|---|
| `masterwood.cps` | Generic Autodesk 3-axis post. Will not speak `41/n` or A/C. |
| `TAB01.DAT` | Tool technology table (rpm/feeds/names). Also inside the MW310 zip (dated 2026-08-27). |
| `MW310 PARAM.zip` | Live MW310 parameter dump. Keep with the project. |
| `Param/pargen.prm` | General machine options, 5-axis head radius, zones, jog. |
| `Param/Syncro.prm` | **Live axis limits and speeds** (newest axis file, 2025-01-09). |
| `Param/Offset.prm` | Per-tool XYZ offsets and ATC pocket XY. |
| `Param/ventose.prm` | 8 bars, pod 115×140, Y 45–1255. |
| `Param/BATTUTE.PRM` | Fence / stop coordinates. |
| `Param/UteName.dat` | Native tool IDs including **41/n**. |
| `Param/TESTINE.PRM` | Aggregates: only T0 occupied (`1 22000 5000 0 0 9000 9000`). |
| `PRG.zip` | Live program archive from the machine (116 `.prg`). Dialect evidence. |
| `Test.PRG` | 100×100 air square, T41/10, `G172 … J90`. |
| `test2.PRG` | Same square, T41/10, `G173 A80 C-15 D0`, Z−20 / Z0. |

---

## 5. Tool numbering scheme

Boring head and spindle both use “1” on the machine. Native spindle address is **unit 41**.

| Station | Machine ID | Native call | Fusion T (proposed) |
|---|---|---|---|
| Boring head | 1–50 | 1–50 | T1–T50 |
| Electrospindle | C1–C10 | **41/1–41/10** | T101–T110 until the post maps them |
| Probe | 49 | 49 | T49 Probe |

A production post must convert Fusion T101 → `41/1`, T102 → `41/2`, … not `T101 M6`.

---

## 6. Post / control facts that matter

- Generic Autodesk post cannot output A or C and must not be used for 5-axis production.
- This control’s tool table talks **Masterwood unit/tool** (`41/1`), which is the native dialect family (`G172 … T41/8`), not Fanuc.
- Linear parameters in MW310 are 0.01 mm. Rotary FCSW treated as 0.01°.
- 5-axis TCP needs `RAGGIO 5 A` = 184.90 mm plus the electrospindle offset in `Offset.prm` line 40 (`type 99`, X109.75 Y281.40 Z623.00 — interpret with care; may be machine coords not tool length).
- Next proof was `Test.PRG` / `test2.PRG` — dialect is native G172/G173, not ISO.

---

## 7. Fusion machine definition — type this

- Type: Milling, 5-axis **head / head**
- X: min −15 mm, max 6021.5 mm (optionally restrict work envelope to stops 482–5691 mm)
- Y: axis −6 … 2018 mm; **programmed work field Y max = 1360 mm**
- Do not set Fusion stock/table Y to 2018. Table/bars ≈ 1300 mm long; work mark 1360 mm.
- Z: min −1 mm, max 616 mm
- C on head, vector `[0, 0, 1]`, **min −140°, max +286.8°**
- A on head, vector `[1, 0, 0]` (confirm sign later), **min −38.6°, max +211.4°**, **vertical at 90°**
- Head radius / pivot: **184.90 mm**
- Fixture: 8 rails, pods **115 × 140 × 100 mm** (true-ish size; do not add extra height “for safety”)
- Fixture rule: model what is there. Inflated pods become obstacles the toolpath will skirt. Clearance belongs in operation heights, not in a fatter fixture.
- Two X zones: zone1 X≤2760, zone2 X≥3380
- TCP: simulation only until a 5-axis post exists
- Linked post: generic Masterwood only on 3-axis test setups

---

## 8. Open questions

1. A direction: from 90°, does tilting toward the operator increase or decrease A?
2. What is D-axis physically?
3. Max panel thickness / passage with 100 mm compressed pods?
4. ~~ISO vs G172~~ **Settled 2026-09-10:** native `G172`/`G173`/`G101` only. Generic Fusion ISO will not run.
5. Confirm A/C direction signs vs Fusion right-hand rule. UI 15° posted as C−15 — watch the head on test2.
9. Which way does C−15 lean (column vs operator)?
6. Home / reference positions and safe retract plane (W park)?
7. Is pocket 41/7 in use?
8. Meaning of Offset.prm columns for type 99 tool 40 (spindle) and type 21 tool 48 (probe).

---

## 9. Decision log

| Date | Decision |
|---|---|
| 2026-09-08 | Treat attached `masterwood.cps` as 3-axis test post only. |
| 2026-09-08 | C-axis travel confirmed ±213° by operator; **software limits −140.00° … +286.80°** from Syncro.prm. |
| 2026-09-08 | Pod height observed ~100–105 mm, replacing brochure 125 mm. Footprint 115×140 mm from ventose.prm. |
| 2026-09-08 | **Do not pad pod height.** Operator: being conservative by adding height makes Fusion avoid them extra; avoidance is already standard. |
| 2026-09-08 | Pod working height **measured 100 mm** with vacuum pulled and rubber fully compressed (flat). Use 100 mm in Fusion. Matches brochure ventose 114×140×100. |
| 2026-09-08 | **C=0, A=0:** tool horizontal, pointing **right** (3 o’clock). A=90 vertical. |
| 2026-09-08 | Brochure X/Y/Z 5200/1345/200 replaced by Syncro.prm strokes 6021.5 / 2018 / 616 mm (full axis, not all usable). |
| 2026-09-08 | Brochure A ±108° replaced by Syncro.prm −38.60° … +211.40°. |
| 2026-09-08 | Spindle tools on this machine are **41/n**, not Fanuc T numbers. |
| 2026-09-10 | `test2.PRG`: MW310 A=80 and UI 15° → **`G173 A80 C-15 D0`**. Z−20 above, Z0 surface. XYZ stay in panel WCS. |

---

## 10. Raw notes

- Operator will call out specific variables as they are known; each must land in section 2 with date and source.
- Do not overwrite a confirmed value with a brochure value.
- Do not add extra fixture height as a safety margin. That only makes CAM treat air as solid.
- `Sy420ac.prm`, `Sy420cc.prm`, `sy621.prm`, `Syncro16.prm` look like older or alternate machine templates. **Do not use them for this machine** unless proven; `Syncro.prm` is the live file.
- `PARGEN.DFL` is a default template; live general params are `pargen.prm`.
