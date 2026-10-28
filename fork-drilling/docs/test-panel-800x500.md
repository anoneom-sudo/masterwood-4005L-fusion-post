# Test panel 800 × 500 × 18

One piece of 18 mm MDF. X is the 800 mm edge, Y is the 500 mm edge. That matches the station layout: the Ø5 gang runs along X, and a 12-hole row at 32 mm pitch needs the long side. The Y arm only needs 64 mm for its pair, so 500 mm is enough.

Expected NC: `fork-drilling/harness/expected/test-panel-800x500.prg`
Hole table: `fork-drilling/harness/expected/test-panel-800x500.csv`
Sketch: `fork-drilling/harness/expected/test-panel-800x500.dxf`

The program positions below are what the machine drills (`G100` after `#911` is resolved). The CSV and the DXF are in Fusion coordinates: Fusion Y = 500 − program Y, origin on the same corner as the routing setups, Z up, top of the board.

## Tools

New library. Do not edit the electrospindle tools.

| Fusion tool | Station | Draw this diameter | Why |
|---|---|---|---|
| T202 | 2 | 5.0 flat | every Ø5 hole, including the Y column |
| T208 | 8 | 4.5 | Y pair, the upper hole of each pair |
| T210 | 10 | 7.0 flat | Y pair, the lower hole. **MACHINE CHECK:** the utn name says 6 mm. Measure the bit before trusting Ø7. |
| T209 | 9 | 8.0 | three dowels along Y, plus one Ø8 on the shelf line |
| T201 | 1 | 3.0 | one through, one blind |
| T213 | 13 | 10.0 | one isolated hole |
| T101 | 41/1 | any small cutter | the two reference crosses, Trace, 2 mm deep |

Post properties on the fork: Gang boring on, gang stations `2,3,4,5,6`, pitch 32, **max gang groups 8**. The default of 3 is the archive limit. This panel needs 8 so the Y pair is emitted as `T84`. Check station diameter on.

## Hole pattern (program coordinates)

| Case | Where | What the NC must do |
|---|---|---|
| A long X run | Y36, X48 then every 32 mm through X400 (12 holes), Ø5, Z13, F2 | two `T81` strokes and `T82=2,3` at X368 |
| B gap | Y72, X100, X196, X228, Ø5, Z13 | one stroke `T83=2,5,6` (stations 3 and 4 stay up) |
| C off pitch | Y108, X48…176 step 32, plus X90 | `T81` plus a single `T2` at X90 |
| D two depths | Y144, X48…176 Z13 and X240…368 Z8, both Ø5 F2 | two `T81` strokes, not one |
| E two feeds | Y180, X48…176 at 2000 mm/min and X240…368 at 800 mm/min | two `T81` strokes, `F2` and `F0.8` |
| F Ø5 along Y | X620, Y220, 252, 284, 316, 348 | five single `T2`. No extra holes at X652 |
| G Ø8 along Y | X720, Y60, 160, 260 | three single `T9` |
| H Y-arm pair, twice | X540. Y260 Ø7 with Y324 Ø4.5, and Y400 Ø7 with Y464 Ø4.5 | two strokes `#T84=10,8`, `#Y84=8,10`, `#S84=8,10`. `G100` Y is 260 and 400 |
| I through and blind | X100 Y430 Z19 Ø3, and X180 Y430 Z10 Ø3 | two single `T1`, different Z |
| J isolated | X300 Y280 Ø10 Z13 | single `T13` |
| K mixed on a shelf line | X460 Y36 Ø8 | single `T9`, not part of the `T81` on Y36 |
| Crosses | program (24, 300) and (760, 250), arms 12 mm, 2 mm deep | `G173 … T41/1 A90 C0 D0` then `G101` |

`check_prg.py` expands this file to 57 holes, 0 errors. That is the drawing.

## Fusion setup

1. New manufacturing model. Stock 800 × 500 × 18, origin at the corner, Z on the top, the same way the routing setups are oriented. X along 800, Y along 500.
2. Insert `test-panel-800x500.dxf` as a sketch on the top face. Layers are the case names. Circles are the holes. `CROSS` and `OUTLINE` are the crosses and the board.
3. The DXF has no depth. Use the CSV. `fusion_x_mm` / `fusion_y_mm` are the sketch. `program_x_mm` / `program_y_mm` are what you measure on the control.
4. Drill ops, all of them before the traces. One tool per op is normal. The fork holds consecutive boring ops and plans them together, which is how the Ø4.5 and the Ø7 become one stroke. Do not put a trace between those two ops.
5. Drilling cycle, rapid out, flat bottom, "drill tip through bottom" off. Feed from the CSV (2000 mm/min, or 800 for the slow five).
6. Two Trace ops for the crosses, T101, 2 mm deep, after the drills.
7. Post with `fork-drilling/masterwood_4005L_drill.cps` from a file path. Do not install it over the live post. Compare the `#T` / `G100` lines with the expected program. The crosses will match only if the traces are the 12 mm arms in the DXF.

## Run order

1. Air run, board in place, Z zero set high so nothing touches. Watch which spindles drop on the `T81`, `T82`, `T83` and `T84` lines. Stations 3 and 4 must stay up on the `T83` line. On `T84`, stations 10 and 8 drop, and nothing else.
2. Scrap. 18 mm MDF. No pod under the through hole at program X100 Y430.
3. Then measure. Do not skip the air run.

## Measuring checklist

Measure from the two crosses, or read the program coordinates in the CSV. Distances are in the program frame.

| If you see this | It points to |
|---|---|
| Ø5 pitch along X is not 32.0 mm | X-arm offset sign or pitch. Stop. Do not run the rest as production. |
| The 12-hole row is 12 separate plunges | grouping did not run (gang off, or max groups left at 3 and something else consumed T81–T83). |
| Holes at X132 or X164 on Y72 | stations 3 and 4 dropped on the gap stroke. Subset mask is wrong. |
| A hole at X90 is missing, or the five around it moved | off-pitch fallback failed. |
| The Z8 row and the Z13 row on Y144 are the same depth | depth split failed. The block has one Z. |
| The slow row is F2, or it joined the fast row | feed split failed. |
| The X620 column has partners at X652 | an Ø5 Y line was treated as an X gang. |
| The X720 dowels are not 100 mm apart, or they became one stroke | Ø8 Y line was ganged. There is only one Ø8 spindle. |
| The Ø4.5 / Ø7 pair is 64 mm the wrong way along Y | **Y offset sign** is the opposite of X. See gang-logic.md. |
| Those two bits are swapped (Ø4.5 where Ø7 should be) | `#T` order, or which station is the `G100` point. |
| The pair is two plunges, and the control alarm mentions T84 | group number above 83 is refused. Holes can still be right as singles. |
| Station 10's hole measures 6 mm | TAB01 name was right and the diameter field was not. Change the tool to Ø6 after confirming. |
| The X100 hole does not exit the back, or the X180 hole does | through depth or `M112`. Z19 vs Z10 is all the post emits today. |
| The Ø8 at X460 Y36 is inside the Ø5 row | mixed diameter was pulled into `T81`. |
| A mirrored run (control symmetry) moves the gap or the Y pair wrongly | `#X` / `#Y` / a missing mirror line. Run the same file once normal, once mirrored, before using symmetry in production. |
