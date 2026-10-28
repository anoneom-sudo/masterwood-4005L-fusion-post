# Gang drilling from Fusion (foratura multipla)

Prototype in the drill fork only. The live post `masterwood_4005L.cps` is unchanged. Nothing here has been run on the mill.

## Recommendation

Let the post group the holes. The CAM user drills ordinary holes with one boring tool. The post looks for holes that sit on a 32 mm line along X, at the same depth and the same feed, and writes one multi-spindle hit (`G100 … T81`, or `T82` / `T83` for a shorter set).

That is how the shop programs already work. In `1 2 Zijkant Links.tlf` every shelf line is `FOR_LINEA` with `NUMUTENSILE 0`, `DIAMETRO 5`, `PASSO 32`, `PROFLAVORAZIONE 13`. The CAD does not name spindles. The NC names them. The matching program, `1 2 Zijkant Links.PRG`, is 26 `G100` strokes. Expanding each stroke with "spindle s drills at X + 32 mm × (s − first spindle)" gives the 122 TLF holes, none missing and none extra. Checked against the TLF in this repo (it matches the private copy).

Keep one `G100` per hole as the fallback. Turn grouping off with the operation property **Gang boring**.

Rows along Y are not a second Ø5 gang. Stations 8–13 share one X and each holds a different bit. The only Y-row gang in the program archive is `tablet.PRG` (`#T81=10,8`, 64 mm). Rules, the station table, and the machine checks are in `gang-logic.md`. The 800 × 500 × 18 test panel is in `test-panel-800x500.md`.

## What the machine files actually show

Sources used for this, and not committed (they are shop and manufacturer files):

| File | What it settled |
|---|---|
| `1 2 Zijkant Links.PRG` + `.tlf` | Panel 2445 × 561 × 18. Tables below. Rows at program Y36 and Y525. Second row runs back along X. |
| `MW310 PARAM.zip` → `Param/Offset.prm` | Per-station offsets, 0.01 mm. Station number is field index 14. |
| `TAB01.DAT` (same bytes as `Param/TAB01.DAT` in that zip) | Which station holds which bit. |
| `drill-2026-10-20.zip` → `Mw310/Prog` | Older gang programs, plus `tablet.PRG`. |
| `Mw310/English/ISO.TXT` (inside that zip) | `G100` words. |
| `Sv.zip` → `MW310.PLC` | Boring-head outputs. It does not document `#T81`. |
| `docs/2026-09-18 Line drilling zijkant.md` | Early notes. Its reading of `#X` / `#S` does not match the programs. |
| `pargen.prm` | `EN_FORATRICE 0`, `DIA_FOR_TIM 1600`, `TIM_DIA_FOR 500`. |

Not in this git repo at all: `MACHINE-SPECS.md`, `docs/COORDINATES.md`, `docs/HORIZONTAL-DRILLING.md`, `docs/MW310-CODES.md`, and `reference/` (no `Offset.prm` there). `docs/example-side-panel-*.prg` from `PLAN.md` was never committed. The shop `.PRG` is not in git. The `.tlf` is, at `samples/zijkant-links/`.

### Head geometry (testa a forare)

`Offset.prm` rows for the vertical drills (type 1), X and Y in 0.01 mm:

| Station | X mm | Y mm | `TAB01.DAT` |
|---|---|---|---|
| 1 | 50.00 | −110.63 | Puntboor 3 mm |
| 2 | 82.00 | −110.63 | rijboren 5 mm |
| 3 | 114.00 | −110.63 | rijboren 5 mm |
| 4 | 146.00 | −110.63 | rijboren 5 mm |
| 5 | 178.00 | −110.63 | rijboren 5 mm |
| 6 | 210.00 | −110.63 | rijboren 5 mm |
| 7 | 242.00 | −110.63 | empty |
| 8–13 | 50.00 | about −175 to −335 | other diameters, along Y |

Stations 1–7 are 32.00 mm apart along X. Stations 2–6 are the only equal Ø5 gang. Stations 8–13 share X with station 1 and step along Y, and those Y steps are not all exactly 32 mm (8→9 is 31.90, 9→10 is 32.10, then 32.00). The prototype does not gang a Y column.

`drilling-dialect.md` says a 2026-10-19 tool table put a 5 mm pilot on station 10. The `TAB01.DAT` in hand does not. Station 10 is named `Drevelboor 57x6mm.utn` and the diameter field is 700 (7.00 mm if that column is 0.01 mm). The name and the field disagree, so the post does not hard-check station 10.

Horizontal drills (foratura orizzontale, `G182`–`G185`) are separate stations (31, 33, 35–38). Not in this prototype.

### How a gang hit is written

From `1 2 Zijkant Links.PRG`:

```
#T81=2,3,4,5,6
#X81=6,5,4,3,2
#S81=6,5,4,3,2
#T82=2,5,6
#X82=6,3,2
#S82=6,3,2
#T83=2,3,4
#X83=6,5,4
#S83=6,5,4
G100 X173 Y36 Z13 F2 T81
…
G100 X1197 Y36 Z13 F2 T82
…
G100 X1677 Y36 Z13 F2 T83
G100 X2157 Y525 Z13 F2 T81
…
G100 X173 Y525 Z13 F2 T81
```

`#T8n` is the list of stations that drop together (utensili multipli). `G100` X and Y are the hole of the **first station in that list**. The next station is one pitch further along X. `T82=2,5,6` at X1197 drills 1197, 1293 and 1325: the 96 mm gap between two shelf lines, bridged in one stroke. `ISO.TXT` lists `G100` words as X, Y, Z, F, T. There is no S word. Z is depth below the top, positive into the wood. F is the boring feed. Shop programs use `F2`.

`#X` and `#S` are not millimetre offsets and not a spindle-direction flag. The 2026-09-18 note guessed that. Every table found since is a **mirrored station list**:

- X row, mirror about the ends of the full row. For stations 2…6 the map is `s → 8 − s`, so 2↔6, 3↔5, 4 stays 4. `#S` is the same list as `#X`. There is no `#Y` line.
- Older head, `Diependaele/…/zijkant rechts.PRG`: `#T81=3,4,5,6,7` mirrors about 3 and 7 (`#X81=7,6,5,4,3`). Subset `#T83=3,4,7` becomes `#X83=7,6,3`. Same rule, different row ends, because Ø5 lived on 3–7 then.
- Y row, `tablet.PRG`: `#T81=10,8`, `#Y81=8,10`, `#S81=8,10`, and no `#X`. Mirror along Y reverses the list. Mirror along X would not, so `#X` is omitted.

So: `#T` is the set for a normal run, `#X` when the program is mirrored in X, `#Y` when mirrored in Y, `#S` when mirrored in both. A missing mirror line shows up only when that mirror would not change the order. This fits every table in the Prog tree (three programs) and the 2026 zijkant. It is still an inference until someone runs a mirrored program on this mill. See the open questions.

`MW310.PLC` job "PUNTE TESTA A FORARE SU/GIU" maps one output per vertical drill (`OF_PUNTA_VERT1` from `RFOROV1`, and on up). If the vertical tool type is `AGGR_MULTIPLO` ("aggregato multiplo su testa a forare") the PLC waits an extra launch time. That matches "the selected drills pop out, then the shared Z bores them all to the same depth." The PLC source does not mention `#T81`. The NC programs are the evidence for the word.

Group numbers in the Prog tree and in the 2026 zijkant are only 81, 82 and 83. Inline lists also exist (`G100 … T1,2,3,4,5` in `verticali.prg`). Production line-boring uses the `#T8n` form. The prototype uses that form.

`rug.PRG` is single-spindle `G100 … T1` only. `zitvlak.PRG` is routing, no `G100`.

## The four ways to drive this from Fusion

| Approach | What the CAM user does | Reliability | Machine Simulation |
|---|---|---|---|
| **1. Post groups 32 mm holes** | One Drill op. Tool T202 (station 2, Ø5) on every shelf hole. Same depth, same feed. | The post uses the same rule as the shop NC. A hole that is not on the pitch, a different depth, or another station stays a single `G100`. | Fusion still has one point per hole, so the sim shows every hole at the programmed XY and depth. |
| **2. A virtual "gang" tool** | The user picks a 5-spindle tool, or a 2+3 tool, per stroke. | The user has to know the subset. The zijkant uses three different subsets in one panel (`T81`, `T82=2,5,6`, `T83=2,3,4`). A tool cannot see the neighbouring holes. | A gang tool that represents only the first hole hides the other holes from the sim. |
| **3. Operation property or comment** | The user types the station list, or writes `T81` in a comment. | Fine as an override. Poor as the main method: 122 holes, and the subset changes along the row. | Same as 1 if the holes are still real hole features. |
| **4. Always one G100 per hole** | Nothing special. | Each hole is explicit. The head repositions and drops one spindle every time. The shop does not do this for shelf rows. | Same as 1. |

Use **1**, and keep **4** as the fallback. Property **Gang boring** (per operation) turns grouping off. There is no gang tool to put in the library.

Machine Simulation limit, either way: `masterwood_4005L.mch` has spindle 41 only. The boring block is not in the model. Stations sit 50–242 mm along X and about 111 mm toward the back of the head (`Offset.prm` Y −110.63). The sim is a check of hole position and depth against the stock. It does not show which physical spindle is down, and it does not show a collision between the boring block and a clamp.

## What the fork posts

Tool map, unchanged: Fusion `T(200+n)` is boring station n. Shelf pins are **T202**. Dowels Ø8 are **T209**. Hinge cups Ø35 are **T212**. Tools T1–T10 and T101–T110 stay on the electrospindle (`T41/n`), expanded to `G173` / `G101` as before.

For each drilling operation the post stores the holes, then at the end of the cycle:

1. Holes whose station is in `gangStations` (default `2,3,4,5,6`) are candidates. Others are single `G100 … T<station>`.
2. Candidates are split by Y, depth and feed (0.01 mm, 0.001 m/min).
3. On each row, take the leftmost remaining hole as station 2. Look 32, 64, 96 and 128 mm further for the other stations. Mark those holes done. Repeat.
4. The full row `2,3,4,5,6` is `T81`. Any other set reuses a previous group or takes the next number, `T82` then `T83`. A fourth distinct set is posted as single holes, with a warning. One station alone is always a single `G100`, using the tool the user picked.
5. `#X` and `#S` are the mirror of `#T` about stations 2 and 6. `#Y` is not written for this X row.
6. Rows are ordered by program Y. The first row runs +X, the next −X, as in the zijkant program.
7. Y uses the routing convention. With **Y as #911-(…)** on (the default, and what the bath programs use), the post writes `#902=#911-(Fusion Y)` and `Y=#902`. Program Y is `DY − Fusion Y`.

The shop program writes plain `Y36` / `Y525` because Masterwood CAD's Y is already program Y. Fusion's setup Y is the one the routing post flips. Drilling uses that same flip, so a hole and a contour at the same sketch Y stay together. The prototype therefore does **not** copy the shop program's Y numbers literally. It copies the hole positions in program coordinates.

It also does not copy `G92 U2.50 V2.50 W0` or `M61 K0 D11`. Routing does not emit that `G92`, and the post's hood word is `M61 K0 D1`. Adding them only on drill programs would move the holes relative to the contours. Both are open questions for the mill, not something to invent here.

Worked example, 2445 × 561 × 18, holes taken from the TLF, Fusion Y = `561 − program Y`. Full file: `harness/expected/zijkant-links-2445x561x18.prg`.

```
#T81=2,3,4,5,6
#X81=6,5,4,3,2
#S81=6,5,4,3,2
#T82=2,5,6
#X82=6,3,2
#S82=6,3,2
#T83=2,3,4
#X83=6,5,4
#S83=6,5,4
#902=#911-(525)
G100 X173 Y=#902 Z13 F2 T81
…
#902=#911-(36)
G100 X173 Y=#902 Z13 F2 T81
```

`#911-(525)` with DY 561 is program Y36. `#911-(36)` is program Y525. 26 strokes, 122 holes, same X and same T numbers as the shop program. `check_prg.py` reports 122 holes, 0 errors.

Also checked, without Fusion:

| Fixture | Result |
|---|---|
| Gang off, same 122 holes | 122 × `G100 … T2`, no `#T81`, same holes |
| 15 holes on one row | 3 × `T81` |
| 17 holes (720-panel subset) | 3 × `T81` + `#T82=2,3` / `#X82=6,5` |
| One hole 18 mm off the pitch | that hole is `T2`, the rest stay `T81` |
| Two depths | two strokes |
| Five holes in a Y column | five single `G100`s |
| A T209 hole beside a shelf row | `T9` single, shelf still `T81` |
| A fourth distinct subset | warning, those holes posted as `T2` |
| README side panel 720 × 560 × 18 | 6 × `T81`, six `T9`, one `T12` at `F0.5`. Hole list matches `expected/side-panel-720x560x18.holes` |

Run `fork-drilling/harness/run_gang_test.sh`. The Fusion `post` CLI is not on this machine, so this test calls the grouping functions directly. It does not execute the rest of the `.cps`.

CAM setup when someone posts from Fusion later: one setup, stock = panel, origin the same as the routing setups, tool orientation top-down. One Drill operation for the shelf holes, tool T202, cycle Drilling, flat bottom (the rijboren are flat; a pointed tool makes Fusion add tip length). Feed is written as m/min (`2000` mm/min → `F2`). Put Ø8 and Ø35 in their own operations with T209 and T212. Keep the 32 mm rows along machine X. The fork is not installed in Fusion's Posts folder.

## Open questions for the mill

These are the points the files do not settle. The prototype does not guess past them.

1. **Mirrored run.** Does a symmetry run actually swap in `#X` / `#S` / `#Y`? Every table matches the mirror-station rule, and no links/rechts pair of the 2026 program was in the zip to compare. A scrap panel run mirrored, and the same program run normal, would settle it.
2. **Omitted mirror line.** When `#Y` is absent on an X-row, does the control treat it as "same as `#T`"? `tablet.PRG` omits `#X` the same way. Confirm before relying on a mirrored Y row.
3. **Which stations may fire together.** Programs do fire non-adjacent sets (`2,5,6` and, on the old head, `3,4,7`). Confirm a subset drops only the listed spindles and does not drop the neighbours. The PLC has one output per drill, which supports that, and it is still worth one scrap stroke.
4. **Station 7.** Empty in this `TAB01.DAT`, and absent from the 2026 `#T81`. The X offset is real (242 mm). Can it take a sixth Ø5? The prototype will not call it unless `gangStations` is edited.
5. **Station 10.** Name says 6 mm, diameter field says 7.00. Which bit is in the station?
6. **`G100` X is the first listed station.** The TLF reconstruction uses that and matches 122/122. A two-hole scrap (measure both holes against a routed cross in the same program) is still the right first mill check.
7. **Group numbers above 83.** Only 81–83 appear. The post stops at three groups and falls back to single holes. If the control accepts `T84`, the property `maxGangGroups` can be raised after a trial.
8. **Y-row gang.** `tablet.PRG` gangs stations 10 and 8, which are 64 mm apart in `Offset.prm`, not the Ø5 row. Is that program still used? The prototype leaves Y columns as single holes.
9. **Feed.** Shelf programs use `F2`. `TAB01` feed field for the rijboren is 60, which is 0.60 m/min if the column is 0.01 m/min. The post writes the Fusion feed. Which value should the shop use in chipboard and MDF?
10. **`G92 U2.50 V2.50 W0`.** Present in the CAD programs (`OFFSET_DIMA` 2.5 in the TLF). Absent from the routing post. Confirm the Fusion origin and Singolo already share one zero, so drilling must not add this shift on its own.
11. **Hood `M61 K0 D11` vs `D1`.** The zijkant uses D11. The post uses D1. What does D11 select, and does boring need it?
12. **Head pose before `G100`.** After a 3+2 route the head may sit at A ≠ 90. The PLC knows how to rotate spindles for the boring head in manual jobs. It is not clear that the interpreter does that before `G100`. Until that is tried, put boring operations before tilted routing.
13. **`EN_FORATRICE 0`** in `pargen.prm`. The flag is 0 and the shop still has a library of `G100` programs, so this prototype does not treat 0 as "head disabled". Worth knowing what the flag actually gates.
14. **Large-drill dwell.** `DIA_FOR_TIM 1600` and `TIM_DIA_FOR 500` look like 16 mm and 500 ms. The post does not emit a dwell. Confirm the control still applies that on a `G100` for the Ø35 cup.
15. **Through holes.** A through hole comes out where the pods are (cup 115 × 140 × 100). Not enabled here.
16. **Fusion tool numbers T201–T250.** They stay clear of the electrospindle tools T1–T10. Confirm that numbering is acceptable in the library.
17. **Panel orientation.** The Ø5 gang only helps when the shelf rows run along machine X. Confirm side panels are placed that way.
18. **First scrap test.** One single `T2`, one single `T9`, then one `T81` row of five holes, measured against a routed reference in the same program. Then the zijkant pattern.
