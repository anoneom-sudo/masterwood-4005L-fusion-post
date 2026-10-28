# Drill-fork test harness

Checks the post output **without Fusion running, posting, or being touched**. It never writes to Fusion's Posts folder, the post symlink, `~/Documents/Fusion 360/NC Programs/`, the tool library, or the live `masterwood_4005L.cps`.

## Gang test (no Fusion installed)

```
./run_gang_test.sh
```

Reads the shelf-pin lines out of `samples/zijkant-links/1 2 Zijkant Links.tlf` (2445 × 561 × 18), runs the grouping code inside `masterwood_4005L_drill.cps`, and checks the NC against the 26-stroke pattern of the shop program. Also posts the 800 × 500 × 18 gang test panel (X and Y cases), the 720 × 560 shelf part, a 17-hole subset (`T82=2,3`), and a gang-off single-hole program. `check_live_untouched.py` fails if `masterwood_4005L.cps` differs from git HEAD, and if the fork's routing functions changed. The shop `.PRG` itself is not in this git tree. The `.tlf` is.

## Option A: headless Fusion post engine (works today)

- Engine: **Autodesk CAM Post Processor 5.413.5**, a universal (arm64 + x86_64) CLI that ships inside Fusion:
  `~/Library/Application Support/Autodesk/webdeploy/production/Autodesk Fusion.app/Contents/Libraries/Applications/CAM360/post`
  The `Autodesk Fusion.app` symlink points to the current build, `4fcc3ec853a7fe76514fe04cc5fd7741e6b2c4ff` (Fusion 2705.1.15). Older builds in `production/` have their own `post`.
- Usage: `post [--property NAME VALUE]… [--log PATH] --noeditor --nointeraction --nobackup <post.cps> <intermediate.cnc> <output.prg>`. It runs **headless** against a saved intermediate. Verified 2026-10-19 11:49 (Europe/Brussels).
- Intermediates (`.cnc`, binary "compact-nci"):
  - Fusion does **not** leave its own intermediates on disk. None were found in `$TMPDIR`, Application Support or `~/Documents`. `$TMPDIR/AutodeskPostUtility/OutputFiles/` is empty.
  - Sample intermediates ship with the VS Code extension: `~/.vscode/extensions/autodesk.hsm-post-processor-5.0.2/res/CNC files/Milling/Drilling/*.cnc` (drilling, deep drilling, chip breaking, tapping, boring, …) and `…/Milling/2D/*.cnc`. They are **inch** parts with tools T1–T10. Four of them are copied into `harness/cnc/`.
  - To capture a real one from Fusion later, post the operation with **"export cnc file to vs code"** (Fusion post library; cached at `~/Library/Application Support/Autodesk/Autodesk Fusion 360/CAM/cache/posts/export cnc file to vs code.cps`). It saves the `.cnc`. Put it in `harness/cnc/`.
- Run:
  ```
  cd "~/Documents/Vonque/Fusion Post processor/fork-drilling/harness"
  ./run_post.sh                                      # all cnc/*.cnc
  PROPS="--property forceMM true" ./run_post.sh      # inch samples -> mm, electrospindle (expand) path
  PROPS="--property forceMM true --property boringToolBase 0" ./run_post.sh   # sample T1..T50 -> boring stations (G100 path)
  ```
  Output goes to `harness/out/<name>.prg|.log|.check|.holes|.diff`.
- `check_prg.py` checks these rules: `%` at both ends, no `G0/G1/M6/M30`, no trailing dot, `G100 X Y Z F T` form, every `Y=#902` has a `#902=#911-(…)` before it, 0 < Z ≤ panel + 1, T is a station 1–50 or a group 81–89 with its `#T8n` defined. It prints the **expanded hole list** (gang strokes resolved per spindle) in program coordinates. If `expected/<name>.holes` exists, the run diffs the hole list against it, so the test doesn't depend on hole order or grouping.
- The checker reproduces the golden `samples/zijkant-links/1 2 Zijkant Links.PRG` exactly: 122 holes, the same as its `.tlf` line definitions.

Smoke results 2026-10-19 (Europe/Brussels):

| Run | Result |
|---|---|
| default | all 4 fail in `onOpen` "millimetres only" (inch samples), which is expected |
| `forceMM` | `deep drilling` posts through the electrospindle expand path (`G173 … T41/3` + `G101` pecks) |
| `forceMM` + `boringToolBase 0` | `deep drilling` / `chip breaking` → `#902=#911-(10)` + `G100 X-25 Y=#902 Z17.26 F0.4 T3`, with a peck warning. `bore` (helical milling) and `tapping` are **refused** as designed. |

## Option B: test part in a separate Fusion document (after the bath job)

Do this only when the bath job is finished and Johannes opens a **new** document. No agent drives Fusion.

- Part: **side panel 720 (X) × 560 (Y) × 18 (Z)**, chipboard. Setup: stock = part, WCS origin **bottom-left = left + front edge**, Z0 = stock top, Z up (same as bath/slot setups). NC program post = **the fork**, picked from a file path, *not* installed in Fusion's posts folder. Or post with "export cnc file to vs code" and run Option A.
- Tools (new local library "MW boring (fork)"; don't edit the existing library):
  - **T202** drill Ø5, flat, L 55 (station 2, rijboren 5 mm)
  - **T209** drill Ø8 (station 9, Drevelboor 8 mm)
  - **T212** drill Ø35 (station 12, Potboor 35 mm)
- Features and Fusion operations (all **Drill** operations, top-down tool orientation):
  1. Shelf pins: two rows of Ø5 × 13 deep at **Y = 37 and Y = 523** (37 mm from front and back edges), **X = 136 … 584 step 32** (15 holes per row, 30 total). Drill op, cycle **Drilling – rapid out**, select by diameter, Bottom = hole depth 13 (flat, not tip; set "Drill tip through bottom" off), Feed 2000 mm/min.
  2. Dowels: Ø8 × 13 at X = 9 and X = 711, Y = 37 / 280 / 523 (6 holes). Drill op, T209, feed 2000.
  3. Hinge cup test: Ø35 × 13 at X = 360, Y = 280. Drill op, T212, feed 500 (archive cups use F0.5).
  4. Variant B2 (subset test), in a **second setup**: one row X = 136 … 648 (17 holes) at Y = 37. Expect 3 × `T81` + `T82=2,3`.
- Avoid for now: Circular/Bore/Thread ops (refused on boring tools), Chip breaking / Deep drilling (G100 can't peck; warned), and drilling from the side.
- Expected hole list: `expected/side-panel-720x560x18.holes` (37 holes, program coordinates).
- Expected PRG in the machine's dialect:
  - what the **skeleton** writes today: `../docs/example-side-panel-skeleton.prg` (one G100 per hole, `T2`/`T9`/`T12`)
  - the **target** after PLAN steps 3–5: `../docs/example-side-panel-target.prg` (`#T81` tables, 6 gang strokes, `M111` around the cup)
  - subset case: `../docs/example-B2-subset-target.prg`
- Machine Sim: the `.mch` has only spindle 41, so holes simulate at the spindle tip, not at the real station offset. Use it for **hole position/depth vs stock only**, not for collisions.
