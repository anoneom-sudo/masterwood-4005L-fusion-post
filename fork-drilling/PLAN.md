# PLAN: vertical boring (G100) in the Masterwood 4005L Fusion post

Fork: `fork-drilling/` · Started 2026-10-19 (Europe/Brussels) · Live post `../masterwood_4005L.cps` **untouched**.
Read first: `docs/drilling-dialect.md` (dialect, proven vs inferred) and `harness/README.md` (how to test).

## 0. Where we are

| Done | File |
|---|---|
| Dialect reference from ISO.TXT, goldens, the 2023 archive (135 G100 programs, 21,605 TLF line-borings), Offset.prm and TAB01 2026-10-19 | `docs/drilling-dialect.md` |
| Fork of the live post. Fusion T201–T250 → boring station. Gang rows on the 32 mm X pitch become `#T81` / `#T82` / `#T83`; every other hole stays one `G100`. | `masterwood_4005L_drill.cps`, `docs/GANG-DRILLING.md` |
| Headless gang test (no Fusion) plus the older post-engine harness | `harness/run_gang_test.sh`, `harness/run_post.sh`, `harness/check_prg.py` |
| Expected outputs in MW310 dialect | `docs/example-side-panel-*.prg`, `docs/example-B2-subset-target.prg`, `harness/expected/*.holes` |

The fork is **not** in Fusion's posts folder and must not be symlinked there until §7.

## 1. Key facts the design rests on (details in the dialect doc)

1. `G100 X Y Z F T` drills vertically. Z = depth below the top (+ into wood), F in m/min, **no S**, no head-down/up code.
2. The boring head has stations **1–7 on a 32.00 mm row along X** (Offset.prm X 50, 82 … 242). **Ø5 is on 2, 3, 4, 5, 6** (TAB01 2026-10-19). Stations 8–13 run along Y with mixed diameters (4.5 / 8 / 5 pilot / – / 35 cup / 10).
3. Multi-spindle stroke: `#T81=2,3,4,5,6` (+ mirrored `#X81=6,5,4,3,2`, `#S81=6,5,4,3,2`), then `G100 X<first spindle> Y Z F T81`. Spindle s drills at X + 32·(s−first). This reproduces the golden's 122 holes exactly. Subsets get new numbers (`T82=2,5,6`, `T83=2,3,4`).
4. Y must use the post's `#902=#911-(y)` transform (same as routing). The CAD's raw-Y style must **not** be copied, because Fusion Y is flipped vs mill Y.

## 2. Mapping Fusion drill cycles → G100

| Fusion `cycleType` | Boring head (T2xx) | Notes |
|---|---|---|
| `drilling` | `G100` | main case |
| `counter-boring` (drilling + dwell) | `G100`, dwell ignored + warning | the control has its own dwell for big drills (`DIA_FOR_TIM`) |
| `chip-breaking`, `deep-drilling` | `G100` single stroke + warning (skeleton). Later: property `peckPolicy` = `warn` / `error` | G100 can't peck. Wood doesn't need pecking at ≤ 30 mm |
| `break-through` | later: `M112 D<dist> F<slow>` before, `M112 D0 F0` after | through holes only (see §5) |
| tapping, reaming, boring, back-boring, circular/thread/bore milling | **error** | not boring-head work |
| any cycle with a T1–T10 / T101–T110 tool | `expandCyclePoint` → `G173 … T41/n` + `G101` | today's live behaviour; the live post defines no `onCyclePoint`, so I *infer* Fusion already expands |

Words:
- `X` = hole X (single) or the **first gang station's** hole X (gang).
- `Y` = `#902=#911-(yFusion)` then `Y=#902`, using the same `formatY` as routing.
- `Z` = −(Fusion hole-bottom z), with WCS Z0 = stock top. Fusion Drill must use **flat-bottom** tool geometry (tip angle 180°) or "depth = shoulder"; otherwise Fusion adds the tip length. The rijboren have TIPOPUNTA 0 (flat).
- `F` = `cycle.feedrate`/1000 (m/min). Optionally clamp to a per-station max (open question Q5).
- No `S`, no clearance/retract words (the control retracts), no `G173`, no A/C.

## 3. Tool mapping

- **Fusion T(200+n) = boring station n** (T201 … T250); property `boringToolBase`, default 200. Avoid T1–T10: the live post maps them to `T41/n`, and Johannes's Fusion library already uses 1–10 for the ATC (`tools/masterwood_4005L_tools_proposed.json`).
  - Note: AGENTS.md says "Do not use Fusion T1–T10 for C-pockets (collide with boring)", yet the library and `mapSpindleTool` use 1–10 → `41/n`. This doesn't break drilling (T2xx is separate), but AGENTS.md should be reconciled. Open question Q14.
- The user never picks T81/T82: **the post builds the groups**. Any Ø5 hole drilled with a gang-capable station (T202–T206) may be grouped.
- Station table inside the post (from TAB01 2026-10-19), used as a guard. Error if Fusion tool Ø ≠ station Ø ± 0.1 or depth > max depth:

  | station | Ø | max depth | role |
  |---|---|---|---|
  | 1 | 3 | 30 (utn text) | pilot / through |
  | 2–6 | 5 | 30 | system holes, gang |
  | 8 | 4.5 | 20 | dowel/screw |
  | 9 | 8 | (bit L 55.7) | dowel |
  | 10 | 5 (Puntboor) | 40 | pilot |
  | 12 | 35 | (cup) | hinge cup |
  | 13 | 10 | – | dowel |

  The table must be refreshed whenever TAB01 changes. Keep it in a single const block with the TAB01 date.

## 4. Grouping holes into 32 mm strokes (**cloud-agent task CA-1**)

Collect the cycle points of each drill operation in `onCyclePoint` (don't write yet), and emit them in `onCycleEnd`/`onSectionEnd` so op order relative to routing is kept. Optional property `mergeDrillOps`: merge consecutive Ø5 ops with the same depth/feed.

Algorithm (greedy leftmost, optimal for fixed-width windows):
1. Candidates: holes whose station is in `gangStations` (property, default `2,3,4,5,6`; must be consecutive on the X row), all with the same depth (±0.01) and the same feed.
2. Bucket by Y (±0.01 mm) → rows along X. Sort by X.
3. While the row has undrilled holes: x0 = leftmost; window = {x0 + 32·k, k = 0..4}; subset = stations whose window slot has an undrilled hole (±0.01); mark those drilled.
4. Subset = full gang → `T81`. Otherwise reuse or allocate the next group number (first-seen order: T82, T83, …). If more than `maxGroups` (default 3 = archive max, Q3) distinct subsets are needed, fall back to single-station G100 (`T<first station>`) for the rest, with a warning.
5. Emit all `#T8n/#X8n/#S8n` lines **once, before the first G100 of the batch** (golden places them right after the header). Mirror rule: `s → first + last − s`. Emit `#S` = `#X` for X rows (golden). Don't emit `#Y`.
6. Order: row by row, serpentine (row 1 ascending X, row 2 descending), like the golden.
7. Holes that are not gang-eligible, or rows along Y, → single `G100 … T<station>`.
- Unit tests (node, no Fusion): 15 holes → 3×T81; 17 → 3×T81 + T82=2,3; golden zijkant hole set → the same number of strokes as the golden (26) and the same hole set; two lines with a 224 gap merged across like X1197 `T82=2,5,6`; off-grid hole → single; mixed depths → separate.
- Acceptance: `check_prg.py` hole list == expected `.holes` for every fixture; zero errors.

## 5. Safety

1. **Depth guard** (in skeleton): 0 < Z ≤ thickness + `boringMaxOverThrough` (default 1 mm). CA-2 adds a per-station max depth.
2. **Through holes** (Z ≥ thickness) need an explicit opt-in property. Bits come out under the panel where the **pods/cups (115×140×100)** are, so a through hole over a cup damages it. When opted in, emit `M112 D3 F1 … M112 D0 F0` (archive pattern). Q7.
3. **Diameter/station mismatch → error** (wrong bit = wrong hole). T2xx in a non-drill op → error (in skeleton). T1–T10 never go to G100. T2xx never go to G173.
4. **Panel bounds**: every hole (every spindle of a stroke) inside 0..DX / 0..DY (warning now, error later). Subset strokes guarantee the up-spindles drill nothing.
5. **Tilted head before boring**: after a 3+2 section the head may stand at A≠90. Whether the control swings back before `G100` is UNKNOWN (Q8). Until answered, CA-2 adds an error if a boring section follows a non-vertical section in the same program. The user then orders boring ops first, which is also how the CAD orders them (zijkant: boring, then routing macros).
6. **Hinge cups** (station 12): wrap in `M111 D3 F0.5 … M111 D0 F0` (macro pattern) and default F0.5.
7. **Vertical only**: boring tool with a tilted tool orientation → error (in skeleton).
8. First mill runs follow §7 (single holes in scrap first). Nothing goes to the mill without a human air/scrap run.

## 6. Simulation / Machine Sim

- `masterwood_4005L.mch` models only the head with spindle 41. The **boring head is not modelled**, so Fusion simulates the T2xx drill at the spindle tip, at the programmed XY. That is fine for **hole position/depth vs stock**. It says nothing about collisions or about where the physical station sits (stations are 50–242 mm in X and 110–335 mm toward the back of the head, per Offset.prm).
- The post must not call `simRetractThenOrient`/A-C swings for boring sections, and should keep A90 C0 (later CA-2 check). The skeleton never starts a route in boring sections, so no swing is emitted.
- Optional later (Johannes, manual in Machine Builder): add the boring block as a second tool attachment with Offset.prm offsets. Not needed for v1 drilling.

## 7. Test steps

1. **Harness (now, headless):** `harness/run_post.sh` with sample `.cnc` (`forceMM` + `boringToolBase 0`) → G100 path works, unsupported cycles refused. Done 2026-10-19 11:49 (Europe/Brussels).
2. **Regression parity:** once an mm `.cnc` of a routing job exists (export the bath/slot with "export cnc file to vs code" **after** the bath job), post it with the live post and the fork headless, then diff. They must be identical apart from header comments.
3. **Fusion test part** (separate document, after the bath job; spec in `harness/README.md` Option B). Export the `.cnc`, then run the harness → `HOLES MATCH expected/side-panel-720x560x18.holes`.
4. **After CA-1:** the same `.cnc` → output equals `docs/example-side-panel-target.prg` (6 strokes of T81), plus the B2 fixture → `T82=2,3`.
5. **Mill, step 1 (operator):** a hand-made 2-hole program (T2 single, T9 single) on scrap 18 mm MDF. Check position against a routed reference cross (same program, `G173 … T41/n`) to prove routing and boring share the frame (#911, Singolo).
6. **Mill, step 2:** one T81 stroke row (5 holes) on scrap. Measure pitch 32.0 and start X.
7. **Mill, step 3:** the full test part.
8. Promote: merge the fork changes into the live post (one commit). Update AGENTS.md ("Codes not in v1" → G100/T81 now in scope) and STATUS.

## 8. Work split / budget routing

| ID | Task | Who |
|---|---|---|
| CA-1 | Grouping + table emit + node unit tests (§4) | **Cursor cloud agent** |
| CA-2 | Safety tables/guards (§5 items 1, 3, 4, 5, 6), `peckPolicy`, through-hole opt-in + M112, `maxGroups` fallback | **Cursor cloud agent** |
| CA-3 | Parity test script live-vs-fork on exported `.cnc` | cloud agent (small) |
| L-1 | Fusion test part + `.cnc` export | Johannes (after bath job) |
| L-2 | Mill scrap runs §7.5–7.7 | Johannes / operator |

Cloud-agent brief: work only in `fork-drilling/`, never edit `../masterwood_4005L.cps`, keep `harness/check_prg.py` green, and add fixtures under `harness/expected/`.

## 9. Open questions (only Johannes / the mill can answer)

1. **TAB01 now:** are stations 2–6 all Ø5 rijboren of the same length (TAB01 says L 55.00), and is 7 really empty? Do the bits alternate rotation, and does that limit which station can drill alone?
2. **Mirroring:** do you ever run a program mirrored (zijkant rechts from links, Singolo/UI symmetry)? That's when `#X/#S` matter.
3. **Group limit:** how many `#T8n` groups can one program define (only 81–83 seen)?
4. **Station 7 / `Q 7 4780` in Offset.prm:** what is it? Can 7 hold a 6th Ø5 (1–7 all on the 32 mm row)?
5. **Feeds:** is F2 (CAD standard) right for Ø5 in chipboard/MDF/solid, or should the post default to TAB01 (0.6–0.8 m/min)? Cup F0.5?
6. **Depth reference:** is G100 Z from the nominal top (|5 DZ)? Is there any panel-thickness probing?
7. **Through holes:** allowed? Which station (T1 Ø3 or T10 Ø5 pilot)? Always with M112?
8. **After a 3+2 routing op**, does the control bring A/C back before a `G100`, or must boring come first?
9. **Hood:** zijkant uses `M61 K0 D11`, the post uses `M61 K0 D1`. What does D11 mean, and does boring need another hood position?
10. **`G92 U2.50 V2.50 W0`** in CAD programs: does the Fusion routing need it too? (The post doesn't emit it. Holes and routing will agree as long as both skip it.)
11. **Panel orientation:** is it OK to always place side panels so the 32 mm rows run along X (needed for the Ø5 gang)?
12. **Y-row gang** (`tablet.PRG #T81=10,8`): still used? Which stations are on the Y row today?
13. **Cup station 12:** any dwell needed (`DIA_FOR_TIM 16 mm / 500 ms` in pargen)?
14. **Fusion numbering:** OK with T201–T250 for boring stations? And reconcile the AGENTS.md "no T1–T10" rule with the ATC library using 1–10.
15. OK to run the §7.5 two-hole scrap test as the first mill step?

## 10. Files to grab from the mill PC

- **Raw (zipped) copy of `C:\Mw310`**, or at least `Prog\`, `Param\`, `English\`, `Defs\`, `Utensili\`. The live Drive upload (`_reference/mill-files/Full MW310/`) is converting `.TXT/.LOG` to Google Docs (`*.TXT.gdoc`), so I can't read them. A `.zip` avoids that.
- **Recent side-panel programs** (2024–2026) with line boring: PRG **and** TLF pairs, ideally one "links" + its mirrored "rechts", and any with T82/T83. The archive here is the 2023 snapshot plus the one 2026 zijkant golden.
- Current `Param\Offset.prm`, `TESTINE.PRM`, `TAB01.DAT` (already have 2026-10-19), `Defs\Testa.dis` (head drawing) and `Defs\Macchina.dis`.
- `Errors_*.Log` for 2025–2026 (look for 4003 / 4012 / 4031 / 4033).
- Any Masterwood manual chapter on multiple tools ("utensili multipli" / foratrice). `MW Support\` is empty in the zip.
- A photo of the boring head from below with the station numbers.
