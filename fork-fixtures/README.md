# fork-fixtures: Masterwood 4005L rails + pods for Fusion Machine Sim

Standalone: normal use needs **no script and no AI agent**. Everything below is done by hand in Fusion.

## Install (machine)
1. Copy `masterwood_4005L.mch` into Fusion's machine library (Mac: `~/Library/Application Support/Autodesk/CAM360/machines/`).
2. The machine's geometry is the Fusion design **"Mockup Masterwood - rails"** (project MasterWood Project 4005L). The .mch links to a fixed version (currently **v8**). After you save a new version of the rails design, re-pick the model in the Machine Library (or edit `model_urn` in the .mch) so the sim uses it.
3. Post: `masterwood_4005L.cps` (see its own property docs).

## Frames
- Sim Z0 = pod top = panel bottom. Rails: top Z−100, bottom Z−190. Pods: Z−100..0.
- FRONT (operator, I stops) = sim −Y. Rail scale M (mm from the back/park end of a rail) = 650 − sim Y. I-stop face at M1217.
- Machine X (ventose.prm, rail X− edge) = sim X + 407.5.
- CAM setup: Position = **stock point, bottom centre** (not "fixture point"), so the panel bottom sits on Z0.

## How to place pods: drag the joints (model v8)
Open "Mockup Masterwood - rails". Under **Table**: **Rail 1..8** and, for every rail, its own **8 pods** named `R<n> <type> <a|b>`:
`R1 140x115 a`, `R1 140x115 b`, `R1 125x75Q a`, `R1 125x75Q b`, `R1 120x50Q a`, `R1 120x50Q b`, `R1 125x75L a`, `R1 125x75L b` (same for R2..R8) = 64 pods.
Rail joints are under the root (`Rail n X ...`), pod joints under Table (`R1 140x115 a Y ...`).

- **Default: every pod is parked** in a row behind its rail's back end (sim Y 1160..2010, beyond the X-gantry legs at |Y| 960..1120), so nothing sits under the panel and parked pods never collide with the tool or the machine. They are outside the sim's ±725 Y travel/view; zoom out to see them.
- **Use a pod:** drag it (or right-click its joint → Drive Joints) toward the front onto the rail. It slides along Y only and rides with its rail. Joint value 0 = parked; the name says `M = <park M> - value`, so for a top-plate centre at rail mark M, set value = park M − M. Range: from parked to the front end (top-plate centre M1255).
- **Move a rail:** drag it along X within its travel (table below); its 8 pods come with it.
- **Unused pods:** leave them parked, or right-click → **Suppress** (or hide) to declutter. 64 boxes made no measurable difference: open 0.9–1.2 s vs 0.8 s with 14 pods. Machine Sim speed is untested.
- **Rot 0 vs 180 (low fidelity):** each pod box is its top plate in the **rot 0** position (top plate shifted toward the back/park side of the port). For a pod turned 180° on the same port, slide it **toward the front** by: 125x75 Q **60 mm**, 120x50 Q **36 mm**, 125x75 L **16 mm**, 140x115 **0** (2× the top-plate offset from the port: 30/18/8 mm, guessed from the datasheet drawings). No separate rot-180 copies are modelled.
- **Save a version**, then make the sim use it (see "Use your layout in Machine Sim").
- **Your responsibility (not enforced by the joints):** rails can't pass each other within a field; keep the minimum edge-to-edge spacing (1-2: 135, 2-3: 175, 3-4: 175 mm); field-1 and field-2 rails overlap around X 2450..2815 and must not collide; pods on one rail must not overlap; a pod base must sit over a vacuum port (PLAN.md 3b) and keep away from through cuts (≥ 20 mm suggested); a pod in the sim is only where you dragged it.

## Use your layout in Machine Sim (per job)
1. Manufacture → Manage → **Machine Library** → My Machines → *Masterwood 4005L* → **Edit in Machine Builder**. This opens "Mockup Masterwood - rails".
2. Drag the rails/pods you need for this job; **Finish** (saves the design).
3. In the job document: Browser → right-click the machine (under the setup / Machines) → **Update Machine Model**. Machine Sim now shows this layout.
- Other job documents keep the layout they last pulled until you Update Machine Model there.
- Fallback if the Machine Builder route doesn't pick up the joint pose: open the design normally, drag, **Save**, then re-select the model for the machine definition (Machine Library), or edit `model_urn` `?version=N` in the .mch.
- CAM setup Position = **stock point, bottom centre** so the panel bottom sits on Z0 (pod top).

## Limits in v8
| Joint | Zero (machine X− edge) | Travel |
|---|---|---|
| Rail 1 X | 195 | 105..2215 |
| Rail 2 X | 508 | 243..2350 |
| Rail 3 X | 2525 | 418..2525 |
| Rail 4 X | 2700 | 595..2700 (2700 measured) |
| Rail 5 / 6 / 7 / 8 X | 4615 / 4790 / 4965 / 5105 | 2450..4615 / 2628..4790 / 2803..4965 / 2941..5105 (field 2 = assumption) |
| `Rn <type> a/b` Y | 0 = parked (top-plate centre M −580 … −1298, behind the rail) | parked .. M1255 (front end) |

Park row per rail, back end of rail = sim Y 650; values per rail are identical:
| Pod | parked sim Y | parked M (centre) | value at M1255 |
|---|---|---|---|
| 140x115 a | 1160..1300 | −580 | −1835 |
| 140x115 b | 1310..1450 | −730 | −1985 |
| 125x75Q a | 1460..1535 | −848 | −2103 |
| 125x75Q b | 1545..1620 | −932 | −2188 |
| 120x50Q a | 1630..1680 | −1005 | −2260 |
| 120x50Q b | 1690..1740 | −1065 | −2320 |
| 125x75L a | 1750..1875 | −1162 | −2418 |
| 125x75L b | 1885..2010 | −1298 | −2553 |

## Optional helpers (not needed for normal use)
- `pods/place_pods.py` (plain Python, no Fusion) suggests a balanced pod layout from a toolpath scan and writes a PNG/txt.
- `build_rails.py`, `build_joints.py`: one-time model build scripts (history only).
