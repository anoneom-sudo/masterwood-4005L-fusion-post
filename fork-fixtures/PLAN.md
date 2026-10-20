# fork-fixtures — pod/rail table for Machine Sim + suggested pod layout

> [!important] REQUIREMENT (2026-10-19, Johannes 15:24): standalone, no AI agent needed
> Everything we build for the sim and the post must work WITHOUT an AI agent. It is not just for Johannes; others must be able to use it without a Grok Bot subscription or any skilled AI. That means: the post (.cps) with documented properties; pod placement done by hand in Fusion; the machine (.mch + rails model) installable from a README; no steps that only an agent can do (no osascript, no headless harness required for normal use).
>
> **Primary pod method (15:26): drag the joints.** Rails and pods in "Mockup Masterwood - rails" are components with **slider joints** (rails along machine X within the ventose X limits, pods along the rail Y). A person drags them into place in Fusion. The Python placer (`fork-fixtures/pods/place_pods.py`) is an **optional helper** that suggests a layout (PNG/txt); it is not needed for normal use.
>
> **TODO (standalone):**
> - [ ] Slider joints on the rails and pods in the rails model, **documented in the README** (joint names, limits, how to drag, how to park).
> - [ ] Installer README: post (.cps) + machine (.mch + rails model link) + how to use the pods in Machine Sim.
> - [ ] Post properties documented in plain language.
> - [ ] Plain-language user docs (setup position = stock point bottom centre, Z0 = pod top = panel bottom; front = I stop = −Y).
> - [ ] Placer stays optional: core plain Python (no Fusion), outputs layout PNG/txt. A Fusion add-in is no longer the main deliverable (dropped 15:26).


Status: **research + plan only** (2026-10-19, Europe/Brussels; rail port map added 14:45; Z model / 3b + pod inventory 14:50). Nothing in Fusion docs, the machine definition or the live post was changed.
Tags: **[S]** = sourced (file/url/Johannes), **[E]** = estimate from photo, **[G]** = guess, needs Johannes.

Goal (Johannes): (1) see real crashes in Fusion Machine Simulation (pods, rails, lifts, not a flat table), and
(2) get pod placement **suggested** from the model for any panel / any toolpath, then show it to the operator.

---

## 1. How Machine Sim is set up today

| Item | Finding | Source |
|---|---|---|
| Machine definition | `~/Library/Application Support/Autodesk/CAM360/machines/masterwood_4005L.mch` (only file there), model "4005L mockup", vendor Masterwood | [S] file |
| Geometry | Not in the .mch. `general/model_urn` → Fusion design **"Mockup Masterwood"** (project *MasterWood Project 4005L*), `urn:adsk.wipprod:fs.file:vf.S5-qoboBTROaVc4QYjaGHA?version=5`. The design is at **version 6** now, so the .mch points to an older version | [S] .mch + Fusion data API |
| Kinematics | static_0 → X(±2000) → Y(±725) → Z(−750…0) → C ("U", ±213, home 90, axis [0,0,−1]) → A ("V", 0…120, axis [−1,0,0], TCP offset 184.9) → head. Separate **table** part, `attach_frame` at (0,0,0), no own axis | [S] .mch |
| Collisions | interaction pairs X/Y/Z/… vs `table` machine_part, `table` stock, `table` fixture: all `check_collisions` | [S] .mch |
| Sim envelope vs mill | Sim X ±2000 / Y ±725 / Z 750 vs Syncro U −15…6021.5, V −6…2018, W −1…616 mm (0.01 mm units). Not a blocker here, but Sim travel limits are not real | [S] Syncro.prm (`/workspace/drill/Mw310/Param/Syncro.prm`) |
| Table body height | Unknown from files (geometry is in the Mockup design, which I did not open: 2 docs were already open). Assumed: flat table body with top at the table attach point Z0 | [G] |
| Setup in "Bath - foot end" (read-only) | 1 setup "Foot end - machined face up", machine = this .mch. **No fixtures** (`fixtures []`, `job_fixture=false`). Stock = model box + X 5 / Y 3 mm, top/bottom 0 → stock 538.4 × 429.7 × **39** mm, Z −39…0 | [S] Fusion read-only script |
| Part placement on table | `job_positionReference_origin_mode = fixturePoint`, box point **bottom center**, offsets 0/0/0 → the **stock bottom sits on the table attach point** = on the flat table. That is why every cut that goes below the panel bottom is a table crash | [S] same |
| WCS | stock point `top 1` (corner, Z top) — matches program zero rule | [S] same |
| Ops in bath doc | 20 × 2D contour, T5 Ø19.38 (Brutfrees), 4.5° draft and 31.7° undercut edges; bottom offset −0.5 mm on most | [S] same |
| Doc type | Bath docs are **direct modelling** (`designType 0`): no user parameters possible in that doc | [S] API error "not a parametric design" |

## 2. Real dimensions found

### 2a. Pods (Schmalz VCBL-K2, height 100) — all share the **same base / bottom plate 140 × 115** (VCSP-U 10.01.12.00798)
Design data from Schmalz datasheets (saved in `cad/`): L = top plate length, B = top plate width, H = total height, H2 = height of the upper body (top face down to the step), L1 = base length incl. guide/handle, L2 = distance from the base end to the top plate. Bottom plate 140 × 115 for all.

| # | Type | Art.-Nr. | Top plate | Arrangement | H | H2 | L1 | L2 | Status |
|---|---|---|---|---|---|---|---|---|---|
| P1 | VCBL-K2 140x115x100 | 10.01.12.00445 | 140 × 115 | full | 100 | 74.8 (family table 75) | 166 | 26 | [S] label + schmalz.com/10.01.12.00445 |
| P2 | VCBL-K2 125x75x100 **Q** | 10.01.12.00447 | 125 × 75 | crossways (125 across rail) | 100 | 63 | 145 | 67.8 | [S] label + schmalz.com/10.01.12.00447 |
| P3 | VCBL-K2 120x50x100 **Q** | 10.01.12.00126 | 120 × 50 | crossways | 100 | 63 | 145 | 67.8 | [S] label + schmalz.com/10.01.12.00126 |
| P4 | VCBL-K2 125x75x100 **L** (likely) | 10.01.12.00506 | 125 × 75 | longways (125 along rail) | 100 | 63 | 145 | 20.5 | [G] label bleached; Johannes: "like 125x75 but top turned 90°". 00447 is already the Q (crossways) one, so the 90° variant is the L. The molded 10.01.12.00798 is the bottom suction plate common to all types, not the block |

Notes
- The L-shape in the photos = top plate cantilevered toward one end of the base; the base end without top plate is only H−H2 high (25 mm for P1, 37 mm for P2–P4). [S] datasheet drawing + photos
- Cross-rail position of the 125/120/75 plates on the 115 base: assumed centred (125 plate overhangs ~5 mm each side). [G]
- Orientation: **0° / 180° only** (flips the L2 end). [S] Johannes 2026-10-19
- Top plate rubber thickness 15.5–16.5 (VCSP-O); compressed height under vacuum: AGENTS.md says "115×140×100 compressed" → use H = 100 at the panel. [S] AGENTS.md
- Schmalz CAD (STEP) **needs a schmalz.com login**; the page reports no CADENAS/Traceparts files. Not downloaded. Datasheets + family sheet + drawing PNG are in `cad/`. [S] product page JSON (`hasCadenasFiles:false`, "CAD data is available to our logged-in users")
- Other families exist (VCBL-K2-PRO base 160×115; heights 50/75/125). Not on this machine as far as we know.


**Pod inventory (Johannes, 2026-10-19): 14 pods** [S]

| Type | Art.-Nr. | Count |
|---|---|---|
| P1 VCBL-K2 140x115x100 | 10.01.12.00445 | **4** |
| P2 VCBL-K2 125x75x100 Q | 10.01.12.00447 | **4** |
| P3 VCBL-K2 120x50x100 Q | 10.01.12.00126 | **4** |
| P4 VCBL-K2 125x75x100 L ("90°-twisted medium") | 10.01.12.00506 [G art.-nr.] | **2** |
| **Total** | | **14** |

The placer must respect these counts (14 pods over at most 8 rails, both fields together).

### 2b. Rails / consoles ("pianetti"), stops, lifts, envelope

| Item | Value | Status / source |
|---|---|---|
| Rail width | **115 mm** | [S] Johannes; also `Param/ventose.prm` `Dim_XPianetto=11500` (0.01 mm) |
| Rail length (pod field along Y) | 1300 mm; tape shows rail top ≈ 0…1285 mm | [S] ventose.prm `Dim_YPianetto=130000`; [E] photo |
| Pod on rail (control model) | Supporto 115 (X) × 140 (Y); pod Y min 45, max 1255 mm on the rail | [S] ventose.prm `[Supporto]` |
| Number of rails | **8**, 2 fields of 4 (each field has its own set of Y stops); ventose.prm bar X ranges 1:105–1950, 2:243–2090, 3:418–2270, 4:595–2445, 5:2705–4615, 6:2883–4790, 7:3058–4965, 8:3196–5105 (see 3b) | [S] Johannes 2026-10-19 + ventose.prm `NUM_PIANETTI=8` |
| Min rail spacing | **135 (1–2), 175 (2–3, 3–4)**, measured first edge to first edge (same-side edges), because the panel lifts on rails 2–4 shift the rail centres; rail 1 has no lift. Matches ventose.prm X-min steps 138/175/177. Control also has `QMin_Anticol_Pianetti` 130 and `Distanze` 245 (meaning unclear) | [S] Johannes + ventose.prm |
| Second (root) pod config | `ventose.ini` (Mw310 root): pianetto 185 × 1600, ventosa 185 × 185, ingombro 275 × 200, tol 5 | [S] file, probably a template/other layout — not used |
| Vacuum ports along rail | **Regular 150 mm pitch**, 8 pairs + 1 extra pair near the front stop — see **2d** | [E] folding-rule photos 2026-10-19 |
| Y stops on rail | 2 per rail, see **2d** (≈ 458 and ≈ 1227 mm from the back rail end) | [E] photos |
| Y stops in control | A/B Y 678.90, E/F Y 1139.32, I/J Y 1889.20 (C/D, G/H, K/L same Y at the other X) | [S] `Param/BATTUTE.PRM` (0.01 mm) |
| Cross-check | 1225 − 455 = 770 on tape vs I − E = 750 in control; rail end at V ≈ 670–685, close to stop A/B Y 678.9 | [E] |
| Stop height / collision | Pop up ~10 mm above pod top, **retract before the program runs** → reference only, **no collision body** | [S] Johannes |
| X stops | **Right edge of the machining envelope**; park / tool change further to X−. Control X 481.92 (A,B,E,F,I,J) and 5691.30 (C,D,G,H,K,L) — which is which field still to map | [S] Johannes + BATTUTE.PRM |
| Panel lifts ("alza pannelli") | On rails 2–4, beam beside the rail (photo "PISTON"); M207 per field | [S] Johannes, Documentazione Pianetti (Drive), [E] photo; size/height unknown |
| Work envelope (brochure) | Usable X 3200 (option 5200), Y 1340 with front stops, Z 200 workpiece passage; travel X 4120 Y 2045 Z 700 | [S] yumpu brochure (Project 4005), hoechsmann.com (4005 L, 5200 × 1340, 8 consoles) |
| Axis soft limits | U −15…6021.5, V −6…2018, W −1…616 mm | [S] Syncro.prm |
| Park / tool change | Park DRO X0 Y0 Z0 A0 C0 (column end); tool change program ends `G170 X0 Y1920 Z0` | [S] AGENTS.md, `Prog/a_gereedschapswissel.prg` |
| Heights | **No bed.** Pod top = Z0 (programs treat it as the bed), rail top = **Z−100**, rail body depth unknown | [S] Johannes 2026-10-19 |

### 2c. How Masterwood stored pod layouts (important for the operator output)
- **PRG header**: `|30 0 01` then `|31`…`|38` = one line per rail: `X_rail  Y1 t1  Y2 t2  Y3 t3 …` (t = flag, always 0 seen). 93 old PRGs carry it. Examples: `|31 177.00 70.00 0 720.00 0` (door, 2 pods), `aaa_parking.prg`: rails 105/350/595/840… pods 45/186/327. [S] `/workspace/drill/Mw310/Prog/*.PRG`
- **TLF**: `VENTOSE / ROTAIA X <x> I / VENTOSA Y <y> F ANG 0 …` (`ANG` = pod angle, so the control has a pod rotation field). Only 12 of 4692 TLFs have it, mostly defaults (rails 105/350/595/840, pods −25/116/257 = 141 mm pitch). Real one: GMatrix balie 1165 × 910 → rails 110/410/700/1020, pods Y 40 and 740 (third parked at 1138+). [S] TLF parse (`/workspace/tlf_pods.txt`)
- Pod Y in both looks like the pod **start edge**, X like the rail **centre**, both measured from the reference stop of the zone. [G — confirm on the mill]
- `pargen EN_VENTOSE=5` (table manager on); `VEN01–04.DAT` = 8 rails × 3 pod-type codes (13/14/2); MW310 errors 2833 "suction cups in collision", 2836 "off limit" → the control checks layouts. [S] Param files + help rtf
- The Fusion post today writes **no** `|30`–`|38` lines (`1013.prg` header ends with `|44 0`). [S]

### 2d. Rail port / stop map (from Johannes' folding-rule photos, 2026-10-19) — all **[E]**

Photos (box, `…/attachments/`): `e7ad3a08` (rule 0–12 + stop 1), `cb584ac3` (stop 1, rule flush with the rail end), `58029399` (21–41), `ed63b539` (51–70), `1771b88b` + `2ce8f9e2` (69–89, stop 2), `bfb4762a` (96–117), `2ae8e493` (109–122, back rail end), overview `05662bd6`.
Read with PIL zoom crops. Port position = the **far-row ring** (sits right at the rule edge, least parallax). Near-row rings read about ±1 cm off in opposite directions on the left/right half of each photo. That is perspective, so both rings of a pair are at the **same** position along the rail (pairs straight across, not staggered).

**Three frames (all mm):**
- **R** = folding-rule reading in the photo series. Rule zero was ~89 mm in from the front rail end (in `cb584ac3` the rule was pushed flush to the end: stop ring at 79 there vs ≈ −10 in the series).
- **D** = from the **front (operator) rail end** = R + 89 (±8).
- **M** = the rail's own side scale (white cm + yellow inch, both zero at the **back / park end**) = 1217 − R. Checked in 6 photos: rule + side scale ≈ 1217 everywhere (±5). Inch scale = M / 25.4 (e.g. 18" at M 457).
- **V (machine Y)** ≈ 679 + M. Anchor: stop A/B Y 678.90 in BATTUTE.PRM sits at the back rail end, and stop 2 then lands at V ≈ 1137 vs E/F 1139.32. Guess, to confirm.

| # | What | R | D (front end) | **M (rail scale)** | V ≈ | Fit to 84 + 150·k | Read quality |
|---|---|---|---|---|---|---|---|
| — | Front rail end (operator side) | −89 | 0 | 1306 | 1985 | | ±8 (from `cb584ac3` offset) |
| S1 | **Y stop 1** (front), ring centre, pins ±26 mm along the rail | −10 | 79 | 1227 | 1906 | | ±8. Control I/J = 1889.2 → M 1210, so it may be 17 mm further back |
| P9 | port pair (extra, 44 mm from P8) | 40 | 129 | 1177 | 1856 | off-pitch | ±6 (`e7ad3a08`, steep angle) |
| P8 | port pair | 84 | 173 | 1133 | 1812 | k=7: 1134 | ±5 |
| P7 | port pair | 236 | 325 | 981 | 1660 | k=6: 984 | ±4 |
| P6 | port pair | 383 | 472 | 834 | 1513 | k=5: 834 | ±4 |
| S2 | **Y stop 2** (back), ring centre (pins at 733 / 786 R) | 759 | 848 | 458 | 1137 | midway between P5/P4 | ±3 |
| P5 | port pair | 538 | 627 | 679 | 1358 | k=4: 684 | ±4 |
| P4 | port pair | 682 | 771 | 535 | 1214 | k=3: 534 | ±4 |
| P3 | port pair | 832 | 921 | 385 | 1064 | k=2: 384 | ±4 |
| P2 | port pair | 986 | 1075 | 231 | 910 | k=1: 234 | ±4 |
| P1 | port pair | 1133 | 1222 | 84 | 763 | k=0: 84 | ±3 |
| — | Back rail end (park side) | 1217 | 1306 | 0 | 679 | | ±5 |

- **Pattern:** P1…P8 at **M = 84 + 150·k** (k = 0…7, residuals ≤ 4 mm), plus P9 at M ≈ 1177, just behind the front stop. Stop 2 sits halfway between P4 and P5 (M 460). No ports between P1 and the back end (84 mm) or between P9 and the front end (≈ 129 mm).
- **Rail length** ≈ 1306 ± 10 measured → take **1300** (ventose.prm `Dim_YPianetto`).
- **Across the rail (115 wide, confirmed):** two rings per pair, ≈ 39 and ≈ 67 mm from the **far** edge (the edge away from the camera, i.e. away from where Johannes stood) → ~28 mm apart, pair centre ≈ 53 mm (rail centre 57.5). ±8 mm (foreshortening). Ring OD ≈ 17 mm (brass), mesh ≈ 12 mm. Which ring is circuit 1 (block) / circuit 2 (workpiece) is unknown.
- **Stop plates:** outlined rectangle ≈ 61–68 mm along the rail, large ring Ø ≈ 30 mm, 2 locating discs ≈ 52 mm apart along the rail on the near side. Reference only (they retract), not collision bodies. Assumed flush with the rail top, so a pod may stand on a stop plate when the stop is down (ask).
- **Cross-check with the old control data:** stop spacing measured ≈ 769 (S1–S2) vs E/F → I/J 749.9 in BATTUTE.PRM. S2 matches E/F within 2 mm. S1 is the less certain reading.
- **Sanity check 14:50 (zero = I stop, per Johannes):** re-read far-row rings in `58029399` (≈ 23.6 / 38.2 cm), `ed63b539` (≈ 53.8 / 68.1), `bfb4762a` (≈ 98.6 / 113.3), stop-2 ring in `1771b88b` (≈ 75.7) and the overview (pairs at tape ≈ 112 / 117 = P8/P9, 150 pitch elsewhere): all within ±5 mm of the table above, pairs straight across. In `e7ad3a08` the rule end touches the **field-side edge of the I-stop ring**, so R 0 = stop face, ring centre ≈ R −10…−15. If the control's I/J Y is the stop face, I stop ≈ M 1217 → V ≈ 1896 vs 1889.2 in BATTUTE.PRM (7 mm), better than the 17 mm from the ring centre.
- (Partly explained 14:41: pods only need a port under the suction area, so off-grid Y like 140 pitch is possible — see 2e.) Old MW310 programs place pods at **140–141 mm** pitch (e.g. Y 70/210/350/490) and ventose.prm models the pod Y as continuous (45…1255). That does not match a 150 mm port grid. Either the old header Y is only a display, or pods can sit between ports (ask, Q2).

### 2e. Which pods fit which ports
All four types share the **same base and bottom plate** (VCSP-U 140×115, 10.01.12.00798). So **every type fits every port pair**, provided the bottom-plate inlets line up with the ring pair. The type and orientation only change where the **top plate** (the part that holds the panel) ends up relative to the port.

Model (assumptions **[G]**: bottom plate centred on the port pair; L1 = base incl. guide/handle with the extra length at the "lug" end; plate offset along the rail = centre of top plate − port):

| Pod | Art.-Nr. | Top plate along × across rail | Base length L1 | Top-plate centre vs port (rot 0 / rot 180) | Across-rail overhang | Min. pitch to the next pod on the same rail |
|---|---|---|---|---|---|---|
| P1 140x115x100 | 10.01.12.00445 | 140 × 115 | 166 | 0 / 0 (centred) | 0 | 166 if a lug sits between them, else 140 (base-to-base, continuous Y) |
| P2 125x75x100 **Q** | 10.01.12.00447 | 75 × 125 | 145 | **+30 / −30** | 5 mm each side | 145 (base-to-base, continuous Y) |
| P3 120x50x100 **Q** | 10.01.12.00126 | 50 × 120 | 145 | **+18 / −18** | 2.5 mm each side | 145 (base-to-base, continuous Y) |
| P4 125x75x100 **L** (likely 4th) | 10.01.12.00506 [G] | 125 × 75 | 145 | **+8 / −8** | inside (20 mm each side) | 145 (base-to-base, continuous Y) |

What this means for placement
- **Pods must sit above a vacuum port** (Johannes 14:41, corrects 14:40): the port is a **hard constraint**, but the ports are meant to let a pod sit *almost anywhere*. Rule used in the model: a pod is valid when a port ring lies **under its bottom-plate suction area** (not necessarily centred). With a 140 base, ring OD 17 and a seal margin of ~5 mm per side, a port allows base starts over a window of ≈ 140 − 17 − 10 ≈ **110 mm** per port, i.e. ≈ 73 % of the rail on a 150 mm grid, with ~40 mm dead bands between windows (P8/P9 overlap). Top-plate offsets (P2 ±30, P3 ±18, P4 ±8 by 180° turn) widen the top-plate positions further. If instead the pod must be **centred** on the port (snap), the grid gives only 9 positions per rail — too sparse for "almost anywhere" → **flagged, Q2**. [S] Johannes, window [G]
- **0° / 180° only.** The guide strip runs along the console; a 90° turn would not seat on the 115 rail, so no 90° option in the model (to confirm, Q3). The "top rotated 90°" of type 4 is the L vs Q **variant**, not a placement choice.
- **Hard constraints per rail:** (1) a port under the suction area (window rule above; switchable to 'snap to port centre'); (2) pod bases (incl. lug, L1) must not overlap / touch the neighbour pods on the same rail (min gap g, default 2 mm); (3) base within the rail (ventose.prm pod Y 45…1255 [G]). **Caution zones:** the stop plates S1 (I stop, front end, ≈ M 1190…1306) and S2 (≈ M 425…490) — a pod base there is problematic (stop pin / plate): keep-out by default, 'caution' override = penalty. [S] Johannes, zone sizes [E] from 2d (plate ≈ 61–68 mm + margin).
- **Below-panel clearance per type:** top plate at H 100; the rest of the base outside the top plate is only H − H2 high (P1: 25, P2–P4: 37). A tilted tool that dips 1 mm below the panel only meets the top plate, so the clearance test uses the top-plate rectangle. The lower base only matters for deep tools or saw blades.
- **Seal rule:** the whole top plate (VCSP-O lip) must be under solid panel, outside every through-cut sweep + clearance, otherwise that pod leaks and drops the vacuum for the panel.
- The placer uses (rail X) × (base Y on a 5 mm grid, **filtered to the port windows**) × (type) × (rot 0/180) → base rectangle + top-plate rectangle in table coordinates. In 'snap' mode the Y candidates are just the 9 port centres.

---

## 3. Plan

### 3a. Fixture model (pods + rails + lifts + stops) for Machine Sim
Bath docs are direct-modelling, so not user-parameter driven inside the job doc. Two pieces:

1. **Master design "MW4005L table" (parametric, own doc in project *MasterWood Project 4005L*)**, for looking at / checking a layout by hand. User parameters:
   `railW=115`, `railLen=1300`, `railTopZ=-100`, `railH=?`, `railX1..8` (2 fields), `podBaseL=140`, `podBaseW=115`, `podH=100`, per pod: `type`, `y`, `rot(0|180)`, `liftW/liftH/liftOffset`, `minGap12=135`, `minGap23=175`, `minGap34=175` (same-side edges; field 2 mirrored), per-rail `xMin/xMax` from ventose.prm, `podTopZ=0`.
   Pod types as 4 small components built from the Schmalz table (top plate L×B at H, upper body to H−H2, base 140×115 + lug to L1). Spacing rules as checks (a text warning from a script), not as constraints.
2. **Script `fixtures_build.py` (Fusion add-in / MCP script)** that reads a layout JSON and creates a component **"Fixture – MW table"** in the job doc: the pods of the layout (rails are machine parts, see 3b), panel-lift beams (retracted height), Y stops as **construction / non-solid reference only** (not in the fixture selection). Then sets the setup fixture to the rail+pod+lift bodies. Write test on a copy of a bath doc first, never on the original.
   - Coordinates: build in **machine table coordinates** (rail X from the reference stop, pod Y from the rail end / stop A), place the panel by the program-zero offset (DX/DY via Singolo) so Sim sees the real XY reach as well.

### 3b. Z model: rails + pods as the "table", pod top = Z0 (replaces "lower a solid table")
Confirmed by Johannes (2026-10-19): there is **no machine bed** under the panel. The rails (consoles) are the bed, the pods stand on the rails, and the programs treat the **pod top as the machine bed (Z0)**. So:

| Level | Z (sim / machine table frame) | Status |
|---|---|---|
| Panel bottom = pod top plate (compressed) | **0** (= table `attach_frame`) | [S] Johannes |
| Pod body | −100 … 0 (top plate at −H2…0, lower base at −100…−(100−H2+?) per type, see 2a) | [S] Schmalz H = 100 |
| Rail top | **−100** | [S] Johannes |
| Rail body | −100 − railH … −100 (railH unknown, use 120 as placeholder) | [G] |
| Panel lift beam (down) | top somewhere below Z0, beside rails 2–4 | [G] ask |
| Y stops (up) | ~+10 (pop up above pod top) but retracted before the program → reference only | [S] Johannes |
| X stops | right edge of the machining envelope; park / tool change further to X− | [S] Johannes |

**What to change in the "Mockup Masterwood" design (when Johannes OKs the edit — Q14)**
1. Backup `masterwood_4005L.mch` to `machines/backups/` first; work on a **copy** of "Mockup Masterwood" (or a new version), never overwrite v5/v6 blindly.
2. **Delete the solid table body.** Keep the `table` component and its attach point at the **pod-top plane, Z0**, so the stock bottom (setup box point "bottom center", offset 0) still lands at Z0. No setup change and no per-setup Z offset needed.
3. In the `table` machine part put **8 rail bodies** (115 wide × 1300 long along Y, top at Z−100, depth railH placeholder), 2 fields of 4, at a default X (e.g. the parked/min X from ventose.prm, see below). These are fixed machine parts → collision with tool/head is a real crash (e.g. a saw or long tool going 100 mm below the panel).
4. **Pods are not machine parts** (they move per job): model them as **fixtures** from the layout script (3a.2): 4 type components (top plate L×B, upper body to −H2, base 140×115 from −100, lug to L1), rot 0/180 only, placed at a Y inside a port window (2e; port under the suction area, stop plates as caution zones). Until the script exists, a default layout (e.g. 1–2 P1 pods per rail clear of S1/S2) is enough to see crashes.
5. Optional: panel-lift beams on rails 2–4 (and mirrored 5–7) as table bodies at their **down** height, once the size is known (Q9). Y stops / X stops as **non-solid reference sketches** (no collision).
6. Re-save the .mch from the machine library so `model_urn` points to the new version (today v5 of 6), then re-check kinematics zero (table attach = Z0 = pod top; head Z range unchanged).
7. Sim envelope: optional later — X/Y limits in the .mch are not the real ones (Syncro U −15…6021.5, V −6…2018).

**Rail X from the control (reconciles Johannes' spacing)** — ventose.prm `Dati_PianettoN = Xmin Xmax` (0.01 mm):

| Rail | Field | X min | X max | Δ to previous (min / max) | Lift |
|---|---|---|---|---|---|
| 1 | 1 | 105 | 1950 | — | none (Johannes) |
| 2 | 1 | 243 | 2090 | 138 / 140 | yes |
| 3 | 1 | 418 | 2270 | 175 / 180 | yes |
| 4 | 1 | 595 | 2445 | 177 / 175 | yes |
| 5 | 2 | 2705 | 4615 | — | yes [G mirror] |
| 6 | 2 | 2883 | 4790 | 178 / 175 | yes [G] |
| 7 | 2 | 3058 | 4965 | 175 / 175 | yes [G] |
| 8 | 2 | 3196 | 5105 | 138 / 140 | none [G mirror] |

The X-min steps 138 / 175 / 177 match Johannes' **135 / 175 / 175 same-side-edge spacing** (packed rails), and field 2 is the mirror (138 at the outer rail 8). So `Xmin/Xmax` = rail edge (or reference) position, packed together at min. With 115 wide rails: gap 1–2 ≈ 20 mm, gap 2–3 / 3–4 ≈ 60 mm = room for the lift beam. `QMin_Anticol_Pianetti` 130 = the control's anti-collision minimum (≈ 115 + 15), `Distanze` 245 not explained (maybe minimum for lifted lifts, or unused) [G]. Whether X in ventose.prm is the rail centre or an edge, and in which frame (X stop A 481.92?) is still open (Q6/Q10).

- **With fixtures (3a):** pods come from the layout JSON; rails stay in the machine. Stock still referenced to Z0.
- **Check:** Machine Sim on a **copy** of "Bath - foot end": the 31.7° and −0.5 mm cuts must give **no** collision (nothing exists at Z −0.5 except pods), a pod placed under an edge on purpose must give a **fixture** collision, and a deliberate Z −105 cut over a rail must give a **table** collision.

**Built 2026-10-19 ~14:55 (Johannes approved 14:43)** [S]
- Backups: `CAM360/machines/masterwood_4005L.mch.bak-20261019-144424-before-rails` (+ same file in `fork-fixtures/_backup/`). Note: the CAM360 sibling copy breaks the `machines/backups/README.md` policy (it was explicitly requested; extension `.mch.bak-…` so Fusion does not list it).
- Copy of the Mockup: **"Mockup Masterwood - rails"** (MasterWood Project 4005L, `urn:adsk.wipprod:dm.lineage:LvbHA3nZTaOtIsfOssrRzg`, **v3**). Original "Mockup Masterwood" (v6) untouched.
- In the copy, component `Table`: solid body (4000 × 1509 × 181, top Z0) **deleted**; **8 box bodies Rail1…Rail8** 115 (X) × 1300 (Y) × 90 deep, top **Z−100**, bottom Z−190 (depth 90 not 120: the mockup Static base top is at Z−191.4, 120 would collide permanently). Table attach point unchanged (0,0,0) = pod top = panel bottom. Sketch "REF Y stops (no collision)" = points at S2 (M 458) and I-stop face (M 1217) on each rail centre, Z0. No X stops, no lifts (TODO).
- Layout (default = ventose.prm X min, packed): sim X = machine X − 407.5 (field 1 centred on the sim origin where the setup puts the stock) → rail X− edges −302.5 / −164.5 / 10.5 / 187.5 (field 1), 2297.5 / 2475.5 / 2650.5 / 2788.5 (field 2, outside the sim X travel ±2000). Y: rail M 0 (back) = −650, M 1300 (front) = +650. **To change:** edit `rails_layout.json`, rerun `build_rails.py` via Fusion MCP (opens the copy invisibly, rebuilds, saves a new version) and bump `model_urn` version in the .mch.
- `.mch`: only `fusion.default.model_urn` → `…vf.LvbHA3nZTaOtIsfOssrRzg?version=3` and a dated line in `general.description`. Kinematics / controller / interactions byte-identical to the backup. Sim travel unchanged: X ±2000, Y ±725, Z −750…0, C(U) ±213 home 90, A(V) 0…120, TCP 184.9 (real: U −15…6021.5, V −6…2018, W −1…616 — not changed).
- Check so far: `Machine.createFromFile` loads it (hasSimulationModel true, kinematics tree intact). Throwaway **"ZZ throwaway - foot end rails test"** (copy of Bath - foot end v9, in MasterWood Project 4005L) has its setup machine set to the new .mch and saved; toolpaths are not valid in the copy (must be regenerated). Stock is placed by fixture point, Z offset 0 → stock bottom on Z0, no setup change needed. Lowest cut = −1.2 mm below panel bottom (31.7° ops), rails start at −100 → geometrically no table collision possible. **Interactive Machine Sim not run** (no API; another worker was using Fusion) → TODO for Johannes: open the throwaway, Generate all, Simulate with machine.
- Pods are not in the machine (they move per job) → no pod collisions yet: next step = pod boxes as setup fixtures (low fidelity per Johannes 14:47: plain boxes, top-plate footprint Z−100…0).

**Frame convention (Johannes 15:02; fixed 15:00)** [S unless marked]
- Program / setup WCS origin = panel **front-left corner, Z at stock top**. Front = operator side = **I stops** = sim **−Y** = the side with the Autodesk logo on the mockup gantry (black lettering at Y ≈ −1078). Left = −X.
- With the **I stop** the panel sits against I on its front edge and fills toward the park side (+Y in Fusion/sim). With the **E stop** (back) the control offsets by the panel Y size so 0 stays front-left.
- **Right field (rails 5–8): assumed** the same trick offsets X0 by the panel X size so 0 keeps its place relative to the operator. **Unverified** [G].
- Checks: all 4 bath programs (back rest, bottom, foot end, right side) have X 0…DX and Y 0…DY around the WCS → WCS at the stock (xmin, ymin) corner = front-left ✓. Post: mill Y = #911 − y, and the 2026-09-18 DRO (V = 969.3 + DY − y) shows V growing as Fusion y falls → Fusion ymin edge is toward the operator ✓. Open: in that DRO the front edge landed at V ≈ 1594 (DY 625), not at I ≈ 1889 — the fixed point was the back edge (V ≈ 969), consistent with **E stop** use in that run (E/F 1139 − ~170 unexplained). Not blocking for the sim.
- Rails v4: rail scale M → sim Y = 650 − M (back end +650, I-stop face −567, stop 2 +192). v3 had the stop reference points the wrong way round (rail boxes are symmetric, only the REF points moved). `.mch` now → `…LvbHA3nZTaOtIsfOssrRzg?version=4`; v3 `.mch` copy in `_backup/`.
- Placement (`pods/place_cfg.json` `placement_mode`): **istop** (default) = panel front edge on the I-stop face (sim Y −567), panel X centred on sim 0 (field-1 rails centred there by `sim_x0`; real X vs the X stop unknown). **setup** = as the bath setups today (stock bottom-centre on the table origin, front edge at sim Y ≈ −215, not on a stop).

**Pods v1 (2026-10-19 15:05)** — `pods/` (see `pods/README.md`): `podscan.cps` dump post → `scan_setup.py` → `place_pods.py` → `insert_pods.py`. Low fidelity: pods = top-plate footprint boxes, sim Z −100…0, no lugs. Tested on **"ZZ throwaway - foot end rails test"**: 9 pods on rails 1–3 (rail 4 parked), keep-outs from 16/20 ops, layout in `pods/out_footend/`, inserted as setup fixtures (component `PODS fork-fixtures`) with Position Y offset −352.144 so the front edge sits on I. **To check in Sim:** the panel bottom must stay at Z0 with fixtures on (Position reference = box point "bottom center"; if Fusion now uses the fixture box, the panel will float 100 mm up → then set the reference to stock), pods on the rail tops, no fixture collisions.

**Pods v2 (2026-10-19 15:11, Johannes 15:07)** — `pods/place_pods.py` v2 (v1 kept as `place_pods_v1.py`), `place_cfg.json`:
- Through cuts (tool tip below the panel bottom): pod top plates keep **`through_clearance` = 20 mm** from the tool envelope (disc R + 20). Other cuts that come within 5 mm of the pod-top plane: R + 5 (+ assumed holder R40 beyond body length) as before.
- **Fewest pods:** target = clamp(ceil(panel area / `area_per_pod_m2` 0.06), `min_pods` 4, `max_pods` 8). Search over 2–4 rails × 2–3 pods per rail (pods at the front-most / back-most valid positions, + middle for 3). Accept only if the convex hull of the top plates covers ≥ `hull_min_fraction` 0.45 of the panel area and spans ≥ `span_min_fraction` 0.6 in X and Y. Rank: fewest pods, fewest rails, hull (5 % bins), then larger top plates. Unused rails parked: before the first used rail packed at min X, after the last pushed past the panel edge if the range allows; a rail **between** two used rails cannot leave (rails do not pass) and stays under the panel at Z−100 without pods.
- PNG now 2 px/mm with labels (RAIL 1–4 + machine X / PARKED, FRONT – I STOP / OPERATOR, +X arrow, legend, pod type + rot); tiny bitmap font in `pods/font5x7.py`.
- Foot end result: **4 pods on rails 1 + 2** (each: 125x75 Q rot 0 at the back, 140x115 rot 0 at the front), rails 3/4 parked; hull 70 %, span X 74 % / Y 87 %.
- **Z bug found (15:09):** the pod boxes were built correctly in the model (Z −139…−39 = sim −100…0 under the panel), but with fixtures on, the setup Position mode `fixturePoint` + box point "bottom center" puts the **fixture box** bottom on the table attach point → pods 0…+100, panel on top. Fix (in `insert_pods.py`, **not yet applied**): `job_positionReference_origin_mode = 'stockPoint'`, box point bottom center, Z offset 0 (+ X/Y offsets for the I stop). The throwaway is still at **v4** (9 v1 pods, fixturePoint) → re-run `insert_pods.py` after Fusion is back and Johannes OKs.
- **Fusion crash 15:11:51**: `insert_pods.py` had just opened the throwaway v4 **invisibly** (log: Open … `End: Open the Document` 15:11:50, `CAM Create Iron Document`, then "program got crashed" 1 s later, before any script edit). Active doc at the crash: "Mockup Masterwood - rails" v4 (open in the UI, ChangeType Smudge). Nothing saved by that run. Likely trigger: hidden open of a CAM doc whose machine simulation model is the rails doc that was open at the same time (machine/sim-model assets still "migrating") — not proven. Rule from now: close the rails doc in the UI before scripts open a throwaway that uses the machine, and prefer one doc at a time.

### 3c. Smart step: suggested pod layout
**Input per job**
- Toolpath geometry: Fusion API gives no clean CL points, so use a **post fork `podscan.cps`** (like `fork-linkhome/test/cncdump.cps`) that writes JSON per move: tool tip XYZ, tool axis, tool Ø/flute length/holder Ø, op name, through/not. Run via the existing headless harness (`test/runpost.sh`) or `CAM.postProcess` with that post. Read-only for the doc.
- Panel outline (stock box or model outline at Z bottom), panel thickness, outer profile depth (now **~1 mm below bottom**).
- Machine: pod types (2a/2e), rails (width 115, X 50…2700, spacing 135/175/175), port grid per rail (2d: M = 84 + 150·k, k 0…7, + extra at 1177; to confirm on all 4 rails), lift beams. Saved as `rail_map.json`.

**Forbidden zone** (top view, Python + shapely):
- For every move whose tool reaches below `zBottom + 0.5`: sweep the tool cylinder (tip → tip + axis·(flute + holder)) and cut it with the slab `zBottom−Hpod … zBottom+ε`; take the XY outline. Union all.
- Buffer by `clearance` (user, e.g. 5 mm). For the outer profile at −1 mm this gives at least `R + clearance` from the cut line; tilted tools add `≈ depth·tanθ + R(1−cosθ)` on the lean side automatically.
- Lower parts of the pod (base end at H−H2, lug L1) are tested against the part of the sweep that goes that deep (normally nothing: tool tip only 1 mm below).
- Drilling through / through-pockets: same rule. Blind ops that stay above `zBottom` add nothing.
- Through-cuts that free inner pieces: list the pieces; each kept piece needs ≥ 2 pods (≥ 1 for small parts, option), scrap pieces: option "may fall".

**Search (simple and exact enough)**
1. For one rail at position x: candidate pods = base Y on a **5 mm grid restricted to the port windows** (a ring under the suction area; 'snap' mode = port centres only), minus stop-plate keep-out zones (or penalty in caution mode) × every type × rot 0/180 (top-plate offset from 2e), whose **top plate lies fully on the panel** (inside outline minus forbidden zone, seal margin m) and whose base/lug does not hit a deep sweep. Pick the best non-overlapping set along Y (bases incl. lug + gap g) with a 1-D weighted interval DP (weight = sealed area, bonus near panel edges/corners and near big cuts, penalty in stop caution zones). Inventory limit (4/4/4/2) is global over all rails: per-rail DP per type-count state, or greedy + repair across rails.
2. Rail X: grid 5 mm in 50…2700; best total over 4 rails with the spacing rules via DP over sorted x (score of rail = step 1). Rails with nothing useful go parked out of the panel footprint (and outside the forbidden zone).
3. Report: rails X, pods (type, Y, rot), sealed area, worst clearance, warnings (piece unsupported, < 4 pods, lift under a cut, layout outside 50…2700).

**Show it to the operator**
- The placer writes `layout.json` and a text block into the **setup notes** (`PODS: R1 X=… P2@Y… rot0; …`). The post reads it with `getGlobalParameter("job-notes")` (no file I/O) and writes:
  - human comments right after the header: `( PODS R1 X177 : 125x75Q Y70 R0, 140x115 Y720 R180 )`;
  - later, once tested on the mill with a dummy program: native `|30 0 01` + `|31…|34` lines so the MW310 table screen shows the same layout (frame and units to confirm first; the control may reject a bad layout with error 2833/2836, which is also a free check).
- Plus a top-view PNG/SVG (panel, cuts, rails, pods, stop refs) next to the .prg for the setup sheet.
- Fusion: rebuild "Fixture – MW table" from the same JSON (3a.2) and run Machine Sim as the final check.

**Order of work**
1. Johannes answers §4 → fill `machine_table.json` (rails, ports, pods, lifts). 
2. 3b Z model (rails at Z−100, no table body, attach Z0) on a copy of the Mockup + check on a bath doc copy.
3. `podscan.cps` + placer on the bath foot end (known 4.5° / 31.7° edges) → compare with what Johannes would place.
4. Fixture build script + Machine Sim check.
5. Post comments; then `|31` header test on the mill.

---

## 4. Questions only Johannes can answer
Answered 2026-10-19 (moved into 2a/2b/3b): 8 rails / 4 per field, rails 115 wide, spacing 135/175/175 same-side edges, pods turn 0/180 only, no bed (pod top Z0, rail top Z−100), Y stops retract (reference only), X stops at the right envelope edge, pod inventory 4/4/4/2 = 14, pods must sit over a port but almost anywhere along Y (port windows, see 2e); stop plates = caution zones.
1. Port map (2d): please check 2–3 positions on the rail **side scale**; are all 8 rails the same (incl. rails 1/8 without lift)? Which ring of a pair is circuit 1 / 2, and is the "far" edge X+ or X−?
2. **Port rule (flag):** pods must sit over a port, but the map from the photos has only **9 port positions per rail (150 mm grid + P9)**. Is that all, or are there more ports (e.g. hidden under dirt / other rails differ)? Is it enough that a ring is **anywhere under the pod's bottom plate** (→ ≈ 73 % of the rail usable, ~40 mm dead bands), or must the pod be **centred** on the pair? Can the two rings of a pair be used separately (one per circuit, or a pod needs both)? Where are the inlets on the pod bottom (distance from the lug end)? Exact keep-out length around S1 / S2 / I-stop end (only over the pin, or the whole plate)?
3. Is the 125/120 top plate **centred** across the 115 base, and where along the base (L2 values from the datasheet drawing)? Confirm art.-nr. 00506 for the 2 "twisted" pods.
4. Rail **X ranges per field**: are ventose.prm X min/max (105–1950 … 3196–5105) the real travel, measured to the rail centre or an edge, and from which zero (X stop)? Which side is rail 1?
5. **Panel lift**: width, length, height when down (how far below Z0), which side of rails 2–4 (and 5–7?), does it ever stay up while cutting?
6. **X stops**: machine X of each field's stop, size; confirm they retract too.
7. Rail body depth below its top (only matters for deep tools / saw) — default 120.
8. Header layout frame (`|31` X/Y from which stop, X = rail centre, Y = pod start edge?) and OK to test with a dummy `.prg` with only `|30`–`|38`.
9. Clearance pod top plate ↔ cut (default 5 mm) and seal margin to the panel edge (default 0).
10. Small loose pieces after through-cuts: hold or may fall?
11. OK to edit (a copy of) "Mockup Masterwood": delete the table body, add 8 rails at Z−100, keep attach at Z0, re-save the .mch (with backup)?

---

## Files
- `cad/` — `VCBL-K2_<size>_<artnr>_datasheet.pdf` for 00445, 00447, 00126, 00506; `VCBL-K2_family_datasheet.pdf` (all sizes, design data p.5, drawings p.4 → `fam-4.png`); `VCBL_operating_instructions_BAL_30.30.01.04961_en.pdf`. No STEP (Schmalz login needed).
- `rail_map.json` — port/stop map of section 2d (estimates).
- Photos (box): `/home/box/agent-data/agents/1e2d3807-…/attachments/` (labels, L-profile, bottom plate 00798, rail with tape `05662bd6…jpg`).
- Mill data (box): `/workspace/drill/Mw310/Param/{ventose.prm,BATTUTE.PRM,VEN0x.DAT,pargen.prm,Syncro.prm}`, `/workspace/drill/Mw310/ventose.ini`, TLF parse `/workspace/tlf_pods.txt`.
- Drive: "Documentazione Pianetti" (Masterwood DC-0005 rev.04, M200–M208 pod/stop/vacuum/lift ISO commands, motorised table; ours is manual but M207 = panel lifts).

**2026-10-19 15:35: slider joints (primary method, Johannes 15:26), BLOCKED.** `build_joints.py` + `joints_cfg.json` are ready. They make a body-less grounded root 'Table frame' anchor; Rail 1–8 components with as-built slider joints along X (zero = ventose X min, limits 0..max−min); 14 pod components (top-plate boxes Z−100..0) with Y sliders on rails (top-plate centre M45..1255). Default pose: rails 1/2 at X 195/508, rails 3/4 at 2270/2445. Fusion refuses: "AsBuiltJointInput is only supported in parametric". The rails doc is direct-modelling (designType 0), and switching it to parametric from a script on a hidden doc fails ("InternalValidationError : pAssetSession"). Needed: Johannes opens "Mockup Masterwood - rails" once and turns on Capture Design History (right-click the root > Capture Design History), saves, closes. Then the script can build the joints. Nothing saved; the rails doc is still v5 (Johannes's 15:19 crash-recovery save), and the .mch still points to v4.
Placer v3 (optional helper): balance objective (min support reach / panel reach over 16 directions from the centroid) + park unused rails at max travel → foot end: rails 1 (X 195) + 3 (X 508), 2 pods each (125x75 Q back, 125x75 L front), rail 2 idle under the panel between them, rail 4 parked 2445; balance 0.82, hull 75 %, span X 83 % / Y 86 %. The throwaway Z0 fix (stockPoint) is NOT applied (plan changed 15:26 before that run).

**2026-10-19 15:40: rail X travel corrected (Johannes 15:37).**
- The ventose.prm X max values (1950/2090/2270/2445) are believed to be the **crossover point** between the two table halves, not the end of travel. That's a belief, not confirmed.
- Rail 4 reaches **2700 (measured: Johannes moved it there)**. Rails 3/2/1 max = 2700 − 175 / −175 / −135 stacked = **2525 / 2350 / 2215** (derived).
- Field 2 is an **assumption** (mirrored): mins lowered by the same 255 mm → 2450 / 2628 / 2803 / 2941; maxes = ventose. Real field-2 limits are unconfirmed.
- The fields **overlap** around X 2450..2815. Rails of different fields must not collide; that's the operator's responsibility (like no passing within a field; the joints don't enforce either).
- Stored as `x_travel_min_max` in rail_map.json + rails_layout.json. The placer and `build_joints.py` use it.
- Joint zero = as-modelled position (`rail_x_machine`), limits relative to it.
- Default pose: rails 1/2 at 195/508, rail 3 at 2525, rail 4 at 2700. Field 2 parked at its far max (4615/4790/4965/5105) so it clears field 1 [assumption].
- The placer result is unchanged except parked rail 4 → 2700 (sim 2292.5, outside the sim's ±2000 X travel and view).

**2026-10-19 15:48: slider joints BUILT, "Mockup Masterwood - rails" v7** (built on Johannes's v6 = Capture Design History; the .mch now points to v7, backup `_backup/masterwood_4005L.mch.bak-20261019-154729-before-v7`). **Primary standalone method = drag the joints** (see README "How to place pods"). The placer is an optional helper only.
- Table now holds Rail 1–8 components (X sliders, root level, anchored to the grounded body-less top-level 'Table frame') and Pod 01–14 components (Y sliders on their rail, inside Table). 22 as-built joints.
- Joint zero = default pose (the API can't drive joints on a hidden doc, so rails were moved first and the position captured), limits = x_travel_min_max relative to it.
- Verified by bounding boxes: rails Z−190..−100 at X− edges 195/508/2525/2700/4615/4790/4965/5105; pods Z−100..0 centred on their rails; limits read back.
- Driving joints via the API on a hidden doc is ignored, so the drag test is for Johannes in the UI.
- The Machine Sim impact of nested components + joints in the Table part is untested; check that the pods collide as table geometry.

**2026-10-19 16:05: rails model v8 = pod sets per rail (Johannes 15:57).**
- Every rail (1–8) has its own 8 pods: `Rn 140x115 a/b`, `Rn 125x75Q a/b`, `Rn 120x50Q a/b`, `Rn 125x75L a/b`. 64 pods; 8 rail + 64 pod as-built slider joints. The old 14-pod set is removed.
- Default = all pods parked in a row behind the rail back end at sim Y 1160..2010 (10 mm gaps). This is beyond the X-gantry legs, which occupy |Y| 960..1120 at Z−100..0 over the whole X sweep (probed), and above the static base (top Z−191). Outside the tool Y travel ±725, so no false collisions; outside the sim view at default zoom.
- Pod joint value 0 = parked; limit = top-plate centre M1255. Johannes wrote "front limit M45", but M45 is the back of the rail scale, so the full rail is reachable.
- Rot 180 is not modelled. README: slide forward 60/36/16 mm (Q75/Q50/L; 2× the guessed top-plate offsets 30/18/8).
- Verified: rails unchanged (same bboxes), all 64 pods Z−100..0, Y 1160..2010, centred on their rails; limits read back. Open time v8 0.9–1.2 s vs v7 0.8 s.
- The .mch now points to v8; backup `_backup/masterwood_4005L.mch.bak-20261019-160014-before-v8`.
- Reproducible: `build_joints.py` + `joints_cfg.json` (`pod_sets`). On v7+ it rebuilds only the pods; on a v6-like doc it builds the rails too.
- **Per-job workflow (from the Fusion docs, not yet tested here):** Machine Library → My Machines → machine → Edit in Machine Builder (opens the rails design), drag, Finish (saves). Then in the job doc, right-click the machine → Update Machine Model. Fallback: save the design and re-pick the model or edit `model_urn`.

**2026-10-19 16:50: rails v9 (stop marks per rail) + bath machine swap (partial), second Fusion crash.**
- v9: deleted Table/'REF Y stops (no collision)'. Each Rail k component has two sketches on its top face (Z−100, centreline): 'Rk stop 2' (M458 → sim Y 192) and 'Rk I stop' (M1217 → sim Y −567). Each is a centre point + 20 mm cross, no bodies, so they move with the rail joint. Verified world positions in Table:1+Rail k:1. `build_stops.py`. The .mch → v9 (backup before-v9).
- Bath job (`/tmp/fxr/s_bathjob.py`: re-select local masterwood_4005L, position stockPoint/bottom centre, regenerate invalid, post to /tmp, diff, save only if identical):
  - Bath - foot end → **v10**: NC byte-identical (463362 B). All 20 ops were invalidated by the machine swap and regenerated.
  - Bath - right side: "Generation not started" race in the regen wait; closed unsaved.
  - Bath - back rest (now v6) / Bath - bottom: their NC programs are 'NC 1006 back rest1' / 'NC 1007 bottom1' (output 1006 / 1007), not 'Bath - … 01'; the script found none and closed without changes.
  - 9 Bad_Component1 (now v15): **Fusion crashed at 16:33:57** during the hidden open (log: CAM Create Iron Document → load of rails v9 as machine model → "program got crashed", no active document). Same pattern as 15:11: a hidden open of a CAM doc whose machine model is the rails design.
- Bath setups had origin mode 'fixturePoint' with fixtures enabled but 0 fixtures. fixtureEnabled stays true via the API (no fixtures, so harmless).
