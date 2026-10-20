# Masterwood Fusion post

This folder is the source of truth for the Masterwood post. Fusion's Local Posts folder is a symlink to the live `.cps`.

**Live docs only (do not grow more):**
- Scoreboard (human): Obsidian `Masterwood 4005L/STATUS - where we are.md`
- This file: agent rules, locked machine facts, dialect / post emit rules

Old handoff, session logs, project memory, post review: Obsidian `_archive/` and `Fusion Post processor/_archive/`. **Not current.** Terminal-era Grok handoff is archived — do not treat it as the pickup point.

Do not overwrite confirmed numbers with brochure values (exception noted below for Fusion Machine Sim A travel).

## What this is

- Machine: Masterwood Project 4005L. HMI **MW310 v.2.44R7** on **Syncro** motion (SyncroView32 on mill PC). 5-axis **head/head** (C about Z, then A).
- Native NC is Masterwood dialect (`G172` / `G173` / `G101`), not Fanuc ISO inside a `.prg`.
- Generic Autodesk `masterwood.cps` is 3-axis Fanuc-in-`.prg` (`G0`/`G1`/`T M6`). Reference only — will not run on this mill.
- Production post: `masterwood_4005L.cps` (native MW310 rewrite from goldens). **v1 = routing + 3+2 only.** Simultaneous 5-axis later.
- NC extension: `.prg`. Units: millimetres. Vendor: Masterwood.
- Dialect proven from live programs (`samples/Test.PRG`, `samples/test2.PRG`, plus a 116-file archive historically).

## How we work

- Primary assistant: **CNC** in Grok Bot. Escalate mill-risk / unanswered asks via **VP** when needed.
- Edit surface: `~/Documents/Vonque/Fusion Post processor/` on this Mac. Live post: `masterwood_4005L.cps` (JavaScript).
- Human scoreboard: Obsidian `STATUS - where we are.md`. Update STATUS + this file when facts change — do not grow new markdown.
- Test loop: edit `.cps` → Johannes posts in Fusion (reuse a fixed setup such as the bath) → inspect `.prg` + post log. No Fusion plug-in hook for the agent.
- Prefer **general** post properties/guards. Bath / `1001.prg` is a proving toolpath only — not a special case in the post.
- Commit when a change posts correctly. Ask before Cloud upload or risky mill-side changes.

## Dialect / post must emit

File starts and ends with `%`. **No** `G0`, `M6`, `M30`, or trailing `.`.

### Header (from goldens)

```
%
|1
|2 0
|3 1
|4 DX          panel X (mm) — Fusion stock / setup X
|5 DZ          panel thickness
|6 DY          panel Y (mm)
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

`#910`/`#911` and `|4`/`|6` are panel sizes. **`Singolo.seq` uses them to offset program zero.** Keep DX/DY correct.

### Motion patterns

| Case | Emit |
|---|---|
| Vertical (production post) | `G173 … T41/n S.. E.. A90 C0 D0` then `G101`… |
| Archive / mill UI vertical | often `G172 … T41/n S.. E.. J90` then `G101`… (`Test.PRG`) — match goldens when diffing; production chose G173 A90 C0 |
| 3+2 oriented | `G173 … T41/n S.. E.. A.. C.. D0` then `G101`… (`test2.PRG`: `A80 C-15`, approach `Z-20`) |
| Compensated contour | `G41`/`G42`/`G40` appear in archive; test2 had none |

Rules:
- `D0` on every G173 (all 26 G173s in the 112-file mill archive are `D0`; never another D). Syncro linear **ASSE D** (`EN_ASSED=4`) **moves together with U** (paired X / dual drive) — not carousel, not boring drop, and not posted as its own D word. Do not confuse with G173 `D0`.
- XYZ after G173 stay in **panel WCS** (not a Fanuc tilted plane). Control applies TCP (**RAGGIO 5 A = 184.90 mm**). Post: **no TCP/TWP words**, `supportsTCP` false — output work XYZ + A + C.
- Set A/C on G173; almost never on G101.
- MW310 UI “15°” on Horizontale vlak → file **`C-15`**. Post the **file** number.
- Reject simultaneous 5-axis (`isMultiAxis()` with moving ABC during cut) in v1.

### Units

| Word | Rule | Example |
|---|---|---|
| `S` | rpm / 1000 | `S20` = 20000 rpm (negative S = reverse) |
| `F` on G101 | m/min | `F3` = 3000 mm/min |
| `E` on G173 | plunge, same unit as F | `E2` |

### Z (critical)

**Program:** Z− = above panel, Z0 = top, Z+ = into wood. Fusion is Z+ up → post **`millZ = −FusionZ`**.

### Codes not in v1 (do not invent)

`G100` drill, `G184`/`G185` horizontal boring, `T81` gang boring, `G92`/`G192` shifts, `G170` park, `M60`/`M98`, etc. Routing + 3+2 only until STATUS says otherwise.

### Short post header comment (keep in `.cps`)

```
Masterwood MW310 Project 4005L
Native PRG: % header |1..|14 :1 G120 G173 G101 %
Spindle tools T41/1..T41/10 on the G173 line
G173 … A90 C0 D0   vertical (production)
G173 … A.. C.. D0  3+2
S = rpm/1000, F = m/min, E = plunge
Z+ into the panel (negate Fusion Z)
Work XYZ + A + C; no TWP; no TCP output
A90 = tool down; A0 C0 = tool right; +C clockwise from above
Pivot 184.90 mm is on the control
3+2 only in v1
```

## Kinematics / Fusion Machine Sim

| Pose | Meaning |
|---|---|
| A90 | Tool vertical (down) — G-code |
| A0 C0 | Tool horizontal, pointing **right** (+X) — park and G-code |
| +C | **Clockwise** from above |

C clock (C0 = right / 3 o’clock; machine +Y = operator, Y0 = park/column):
- C0 = right (+X)
- C90 = toward park / column (−Y)
- C180 = left
- C270 = toward operator (+Y)

| Limit / trim | Value |
|---|---|
| Syncro C soft | −140° … +286.8° |
| Syncro A soft | −38.6° … +211.4° |
| Fusion Machine Sim A travel | **0…120°** kept for now (may widen to Syncro later) |
| Fusion Machine Sim C travel | left as-is (±213 style) unless STATUS changes |
| TCP / pivot | **184.90 mm** (`pargen.prm` RAGGIO 5 A = 18490) |
| Head envelope | INGOMBRO 5A = 120 mm |
| OFF.ANG A / C | **0 / 0** |
| Anticollision hood | Q_ANTIC_CUF 75 mm |

Local `.mch` (do not casually undo facing that works):
- C: home **90**, dir `[0,0,−1]`; A: home **0**, dir `[-1,0,0]`, TCP offset **184.9**
- Post **`cSimOffset = −90`**: mill C0 ↔ Fusion C home 90 for `setCurrentABC` / `setTargetC` only. G173 keeps mill C. Do **not** use Fusion `getABC` (complement A).
- When revisiting travel stops: change **min/max only** — leave home, direction, TCP alone.
- Do not put Syncro homing-switch C ≈ −139° in Fusion home.

Fusion CAM: one setup on the panel; Tool Orientation Z = tool axis, X along slot; paths 2D Slot / Pocket / Contour / Trace — not Swarf / Multi-Axis Flow in v1.

## Machine / tools / table

- Spindle unit **41**: pockets **`T41/1`…`T41/10`**. Fusion proposal T101–T110 → post emits `41/n` on the G173 line (**not** `T101 M6`). Do not use Fusion T1–T10 for C-pockets (collide with boring).
- Boring: machine IDs 1–50 on the **back** of the head (+Y / operator side). Probe **T49**. No grooving saw on the boring block. **41/6** in programs = “zaag als frees” (saw as cutter in spindle).
- ATC: **10** pockets on carriage (moves in X with head, not Z); CESTELLO 16A is a **part label**, not 16 pockets. Circle ~100 mm, 36°.
- Park (DRO): **X0 Y0 Z0 A0 C0**, column end, tool right, ram up.
- Machine **+Y toward operator**.
- Z machine: machine Z0 = ram up, **+Z down** into table. Program Z is panel top (G120) as above.
- Work Y max **1360 mm** (plate). Syncro V stroke ~2018 mm is **not** more table — boring-head reach.
- Linear soft (Syncro, 0.01 mm units in prm): X/U ≈ −15…6021.5 mm; Y/V ≈ −6…2018 mm; Z/W ≈ −1…616 mm (full ram). Two X zones when `EN_CAMPO_INT` (zone1 X≤2760, zone2 X≥3380).
- Pneumatic stops locate the **physical** panel only: E/F Y **1139** (near park), I/J Y **1889** (near operator). **A/B do not fire.** Retract while machining — not Fusion WCS, not sim obstacles.
- **Program zero:** mill UI **bottom-left** = left + front (front = operator / +Y), Z on top. **`Singolo.seq`** shifts zero using header DX/DY. Do not set Fusion WCS to a stop or machine home.
- Pods: 8 bars; cup **115×140×100 mm** compressed. Do not pad fixture height in Fusion.
- `.seq` wrappers: **`Singolo.seq`** normal single Fusion `.prg` runner; also `parking.seq` / `gereedschapswissel.seq`.
- Tool table: `~/Downloads/TAB01.DAT` (0.01 mm). Converter / libraries under `~/Downloads/` if still present.

## Fusion libraries / files in this folder

- Local posts → symlink into this folder. No duplicate live `.cps` in Fusion Posts.
- Local Machine Sim: `~/Library/Application Support/Autodesk/CAM360/machines/masterwood_4005L.mch`. Backups only in `machines/backups/`.
- Mill params: `syncro/pargen.prm`, `syncro/Syncro.prm`, `syncro/UteName.dat`. `Syncro Variables.SVV` unnamed — archive interest only.
- Goldens: `samples/Test.PRG`, `samples/test2.PRG`.
- Cloud upload: ask first; enable Cloud Libraries before My Posts → Cloud.

## Calibration notes (reference — do not casual-edit mill)

| Symptom | Where |
|---|---|
| A90 not mechanical vertical | `pargen.prm` OFF.ANG. A (now 0) |
| C0 not 3 o’clock | OFF.ANG. C (now 0) |
| One drill tip wrong | that station XYZ in `Offset.prm` |
| Soft limits / speeds | `Syncro.prm` |
| Pod / origin / DY | WCS / G92 / #911 / battute — not OFF.ANG |

Do not edit OFF.ANG and Offset.prm in the same session. Operator (2026-09-10): 3+2 slots flared at mouth → check J90 vs A≠90 and A zero; L/R drill miss on both spindle and boring → shared WCS/DY vs C 0/180 vs Offset types 2–5.

## Do not

- Edit a copy in `~/Downloads` or Fusion's `_backup` folder.
- Invent M-codes / dialect; match `Test.PRG` / `test2.PRG`.
- Use brochure or Autodesk sample numbers instead of Syncro / goldens (exception: Fusion Machine Sim **A 0…120°** kept on purpose).
- Treat Machine Sim C (`cSimOffset`) as mill G173 C, or Fusion `getABC` as mill A/C.
- Set Fusion WCS to a pneumatic stop or machine home.
- Output TCP/TWP words or machine-solved head XYZ (work XYZ + A + C only).
- Upload every in-progress edit to Cloud, or grow new markdown instead of STATUS + this file.
- Resume work from archived terminal handoff / `_archive/` as if it were current.
