# MW310 vertical boring dialect (G100) — reference for the Fusion post

Written 2026-10-19 (Europe/Brussels) from mill files. **Fork work only. The live post is untouched.**
Scope: vertical holes from the boring head on the top face (shelf pins / system holes Ø5 on a 32 mm pitch, dowels, hinge cups). Horizontal boring (G182–G185) is listed but out of scope.

Tags used below:
- **PROVEN**: read from an official MW310 doc, or seen in real programs and checked by reconstruction.
- **INFERRED**: consistent with every example found, but no doc or mill test confirms it.
- **UNKNOWN**: an open question for Johannes or the mill (see `PLAN.md` §9).

## 1. Sources

| Source | Path | What it gave |
|---|---|---|
| MW310 ISO code list (English) | `Mw310.zip → Mw310/English/ISO.TXT` (also in `MW310.rtf` / `MW310.HLP`) | Official word list for G100, G172, G187, M111, M112, … |
| Side-panel golden + its CAD source | `Fusion Post processor/samples/zijkant-links/1 2 Zijkant Links.PRG` + `.tlf` | Gang boring `#T81/#X81/#S81`, T81/T82/T83, rows at Y36 / Y525 |
| Dowel macro | `samples/zijkant-links/Drevelboring met keuze.PRG` (+ `+MACRO+`, `.MAC`) | `#WHILE` loops with `G100 … T9` / `T1` |
| 2023 mill snapshot | `My Drive/Mw310.zip` (Prog/, Param/, Utensili/, English/) | 135 PRG/MAC files with G100 (4,243 G100 lines); 21,605 `FOR_LINEA` line-boring works in 3,529 TLF files |
| Other side panels (older head layout) | `Mw310/Prog/Idealis/A Gedaan/Diependaele/2 Slaapkamer Ava/Kast 6/zijkant rechts.PRG`, `…/Stef Claes/4 Keukenwand/Kast4/zijkant rechts.PRG` | T81/T82/T83 with spindles 3..7, plus M111/M112 |
| Y-row gang | `Mw310/Prog/tablet.PRG` | `#T81=10,8` with `#Y81` / `#S81` |
| Hinge-cup macros | `Mw310/Prog/MACROS/potboring afwijkende centermaat.PRG`, `blum PO.PRG`, `blum stelplaat+MACRO+.PRG` | T12 Ø35, T13, M111 slow entry |
| Factory test program | `Mw310/Prog/PROGRAMMA NOTTE PROJECT 500 L + ELLISSE.prg`, `Mw310/Prog/verticali.prg` | Inline lists `T1,2,3,4,5,6,7,8,9,10`, modal G100 |
| Tool table (live, 2026-10-19 dump) | Obsidian `_reference/mill-files/param/TAB01_2026-10-19.DAT` | What each boring station holds today |
| Boring-station geometry | `MW310 PARAM.zip → Param/Offset.prm` (same in 2023 zip; only the router row 40 and `Q 7` differ) | Station type and XY offsets: the 32 mm row |

**Not found:** a Mw310/MW310 folder modified today in Google Drive. The upload Johannes is doing sits at Obsidian `_reference/mill-files/Full MW310/Mw310/`. It was still syncing, and its text files show up as Google Docs (`*.TXT.gdoc`, `*.log.gdoc`), so I can't read them from the Mac. All analysis below uses `Mw310.zip` (2023) plus the 2026-10-19 param/TAB01 dumps.

## 2. G100 syntax — PROVEN

From `English/ISO.TXT`:

```
G100  PROGRAMMING OF VERTICAL HOLES
      X Hole co-ordinate
      Y        "
      Z        "
      F Boring speed
      T Tool number
```

Form across the archive (4,243 lines): `X Y Z F T` 2,482×, `X Y Z T` 1,680×, `X Y` 80×. **There is never an S word on a G100** (0 of 4,243).

| Word | Meaning | Evidence |
|---|---|---|
| `X`, `Y` | Hole centre in the face frame (G120 K1 = top face, origin per Singolo). Plain numbers or `=#var` expressions are both accepted. | `G100 X173 Y36 Z13 F2 T81` (zijkant) · `G100 X0 Y=#10 Z13 F2 T9` (Drevelboring) · `G100 X=#251 Y=#250 Z=#253 F2 T1` (archive) — PROVEN |
| `Z` | Depth **below the top face**, positive into the wood (same sense as G101 Z+). | TLF `FOR_LINEA PROFLAVORAZIONE 13` → PRG `G100 … Z13` on an 18 mm panel; through-holes are `Z19` on 18 mm (`zijkant rechts.PRG`: `G100 X9 Y93 Z19 F2 T1`) — PROVEN |
| `F` | Boring feed in **m/min** (same unit as G101 F). Archive values are 0.5 … 2 (`F2` lines 976×, `F0.5` for Ø35 cups). | Unit is PROVEN by the post/goldens for G101. On G100 it's INFERRED from value ranges and TAB01 (rijboren 0.60/0.80 m/min). |
| `T` | Boring station number (`T1`…`T50`), a predefined group (`T81`, `T82`, `T83`), or an inline list (`T1,2,3,4,5`). | All three appear — PROVEN |
| (none) | No rpm word. The boring head runs at its own fixed speed. | 0 S words on G100 — PROVEN absence |
| modal | Words left off carry over from the previous G100, e.g. `G100 X54 Y104 Z10 T1,2,3,4,5,6,7,8,9,10` followed by `G100 X4400 Y600`. If F is never given, the tool-table speed is used. | PROVEN that the syntax is accepted (factory test program). The fallback to the table speed is INFERRED. |

Related words (ISO.TXT, PROVEN to exist; the post doesn't need them for v1 drilling):
- `G187 K I J Z F T`: aligned holes along a tilted line (K count, I angle, J pitch). It isn't used anywhere in the archive, so don't use it.
- `G182/G183/G184/G185 X Y Z K F T`: horizontal holes in the left/right/rear/front face. Stations 31, 33, 35–38 (Hor Drevelboor 8 mm).
- `M111 D F`: slow **entry** for vertical boring (D = mm from the surface, F = slow feed). `M112 D F`: slow **exit** on through holes. Reset with `M111 D0 F0` / `M112 D0 F0`. Archive: `M111 D3 F1` 50×, `M111 D3 F0.50` 13× (cups), `M112 D3 F1` 20×.
- `M106 / M107`: horizontal-drill anti-collision off/on.
- `M61 K D`: hood position (already used by the post).

## 3. Boring head layout and tool selection

### 3.1 Stations — PROVEN (Offset.prm + TAB01)

`Offset.prm` rows: `row type X Y Z … tool`, with XY in 0.01 mm relative to the head reference. Type 1 = vertical, 2–5 = horizontal (front/rear/left/right per the MW310 drill-type list), 99 = electrospindle 41, 21 = probe 49.

| Station (T) | Offset X | Offset Y | TAB01 today (2026-10-19) |
|---|---|---|---|
| 1 | 50.00 | −110.63 | Puntboor 3 mm (pilot / through screw holes) |
| **2** | **82.00** | −110.63 | **rijboren 5 mm** (L 55, max depth 30) |
| **3** | **114.00** | −110.63 | **rijboren 5 mm** |
| **4** | **146.00** | −110.63 | **rijboren 5 mm** |
| **5** | **178.00** | −110.63 | **rijboren 5 mm** |
| **6** | **210.00** | −110.63 | **rijboren 5 mm** |
| 7 | 242.00 | −110.63 | empty |
| 8 | 50.00 | −174.85 | Drevelboor 4.5 mm |
| 9 | 50.00 | −206.75 | Drevelboor 8 mm |
| 10 | 50.00 | −238.85 | Puntboor 5 mm (2026; 2023 TAB01 had Drevelboor 57×6) |
| 11 | 50.00 | −270.85 | empty |
| 12 | 50.00 | −302.85 | Potboor 35 mm (hinge cup) |
| 13 | 50.00 | −334.85 | Drevelboor 10 mm |
| 31, 33, 35–38 | — | — | horizontal (Hor Drevelboor 8 mm, 57×6.35) |
| 49 | — | — | Tastatore (probe) |

So the head is an **L shape**. Stations 1–7 form a row **along X at exactly 32.00 mm**, and stations 1, 8–13 form a row **along Y** (≈32 mm, measured offsets). The **only Ø5 gang is stations 2–6 along X**, so 32 mm system rows must run **along machine X** to use multi-spindle strokes. A row along Y can only be drilled one hole at a time (T2).

TAB01 bore-row columns: `n length diameter maxdepth feed …` (0.01 mm, 0.01 m/min). `.utn` line 2 = point type (0 flat, 2 pilot, 3 cup), line 3 = diameter, line 4 = length, line 10 = feed m/min, line 11 = max depth. The Utensili files confirm this. Station pitch along X is PROVEN. Whether the bits alternate rotation is UNKNOWN; it doesn't matter to the post.

### 3.2 Single holes — PROVEN

`G100 X.. Y.. Z.. F.. T<station>` drops that one station. Examples:
- `G100 X0 Y=#10 Z13 F2 T9` (Drevelboring, Ø8)
- `G100 X0 Y=#1 Z14 F0.50 T12` (potboring macro, Ø35)
- `G100 X9 Y93 Z19 F2 T1` (zijkant rechts, Ø3 through)

### 3.3 Multi-spindle strokes: `#T8n / #X8n / #S8n` (+ `#Y8n`)

Golden `1 2 Zijkant Links.PRG`:

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
G100 X333 Y36 Z13 F2 T81
G100 X493 Y36 Z13 F2 T81
G100 X717 Y36 Z13 F2 T81
…
G100 X1197 Y36 Z13 F2 T82
G100 X1357 Y36 Z13 F2 T81
G100 X1517 Y36 Z13 F2 T81
G100 X1677 Y36 Z13 F2 T83
…
```

- `#T8n=a,b,c` defines a **multi-tool n**: the list of stations that drop together when `G100 … T8n` is called. **PROVEN** by reconstruction. The CAD source (`.tlf`) has `FOR_LINEA DIAMETRO 5 PASSO 32 PROFLAVORAZIONE 13` on lines X173→621, 717→1197, 1293→1741 and 1837→2285, at Y36 and Y525. That's 122 holes. Expanding every G100 with "station s drills at X_G100 + 32·(s − first station)" gives **exactly those 122 holes, none missing and none extra** (`harness/check_prg.py` does this). `T82=2,5,6` at X1197 drills 1197 (end of one line) plus 1293 and 1325 (start of the next) in one stroke. `T83=2,3,4` at X1677 drills 1677/1709/1741.
- **G100 X/Y = position of the first listed station.** PROVEN for the X-row (golden) and INFERRED in general (`tablet.PRG` lists `#T81=10,8` with 10 first).
- **Stroke pitch is 160 mm** (5 × 32) because a full stroke uses 5 spindles. A "224" gap means 2 empty positions (here between two `FOR_LINEA` lines).
- `#X8n` / `#S8n` / `#Y8n` are the **mirrored spindle lists** the control uses when the program is run with symmetry (X mirror, both axes, Y mirror). INFERRED from the pattern: every X list is the T list mirrored about the gang centre (`s → first+last − s`: 2↔6, 3↔5, 4↔4; older head 3↔7), and the help text has errors *4012 "Symmetric tool not present"*, *4031 "Symmetry w. respect to both axes with multiple tool"* and *4033 "Erroneous symmetric multiple head"*. For an X row, Y-mirroring doesn't change the order, so goldens give `#X` and `#S` but no `#Y`. For a Y row (`tablet.PRG`: `#T81=10,8 #Y81=8,10 #S81=8,10`) it's the other way round. (The 2026-09-18 note guessed "X offsets / spindle sense". That reading is wrong.)
- Tables are **defined per program**, not in the machine. They must match the **current** TAB01: the 2016-era programs use `#T81=3,4,5,6,7` (Ø5 was on 3–7 then), and 2026 uses `2,3,4,5,6`. **PROVEN** (both exist). Only `T81`–`T83` occur in the archive, so the limit on group numbers is UNKNOWN.
- Inline form `T1,2,3,4,5` also works (`verticali.prg`: `G100 X40 Y140 Z10 F1 T1,2,3,4,5`). The CAD never uses it for production, so prefer the `#T8n` form, which is golden.
- `TAB81.DAT` / `TAB82.DAT` in Param are **not** the T81/T82 groups. They are alternative tool tables (German names, factory) like TAB02/TAB03/TAB15.

### 3.4 CAD line-boring statistics (what the shop actually drills)

The 21,605 `FOR_LINEA` works in the 2023 TLF archive break down like this. The top entries are 7,721× **Ø5 / pitch 32 / depth 13** and 431× Ø5/32/13.5, then dowel lines (Ø8 / pitch 100 or 90 / depth 13 or 20) and Ø3 pilot lines (pitch 100–140, depth 16–19). Tool is always `NUMUTENSILE 0` (CAD picks the station by diameter), `ANGTILTING 90` (vertical). `MODO 1` dominates for Ø5/32, so I *infer* it means "gang strokes" and `MODO 2` means one hole at a time. `TOPDIST`/`BOTTOMDIST 3` are probably the hole-free margins at the line ends (INFERRED).

## 4. Loops and macros (`#WHILE`, `#IF`, `M98`, `G192`) — PROVEN syntax

`Drevelboring met keuze.PRG`:

```
#10=40+#3
#11=DY-80-#4
#WHILE #10<#11
G100 X0 Y=#10 Z13 F2 T9
#10=#10+100
#WEND
#10=DY-40-#4
G100 X0 Y=#10 Z13 F2 T9
#IF#1=1
…
#ENDIF
```

The macro runs from the side-panel program through `M98 K"C:\Mw310\Prog\MACROS\…+MACRO+.PRG"`, after `G192 X9 Y0` (face-origin shift) and parameters `#908/#909/#1..#4`, then `G192 X0 Y0`. The `.MAC` file is just the prompt list for `#1..#4`. **The Fusion post has no reason to emit loops.** Fusion gives explicit hole positions, so the post writes explicit G100 lines (as the CAD does for line boring). Loops are noted here only so nobody "fixes" them.

## 5. Head down / up, slow entry, hood

- There is **no separate deploy, head-down or head-up code**. `G100 … T..` selects the station(s), positions, drops, bores to Z and retracts. INFERRED from ISO.TXT (no such code is listed) and from programs that go straight from routing to G100 with no extra block.
- Slow entry/exit is opt-in through `M111` / `M112` (PROVEN syntax). `potboring afwijkende centermaat.PRG` is the hinge-cup pattern:
  ```
  M111 D3 F0.50
  G100 X0 Y=#1 Z14 F0.50 T12
  M111 D0 F0
  M112 D0 F0
  ```
- `pargen.prm` `DIA_FOR_TIM 1600` / `TIM_DIA_FOR 500`: probably a 500 ms dwell for drills ≥ Ø16 (cups). INFERRED; the control handles it.
- The hood is `M61 K.. D..` (golden zijkant `M61 K0 D11`, post `M61 K0 D1`). Whether drilling needs a different hood position is UNKNOWN.

## 6. Y handling, Singolo and `#911`

- The CAD writes G100 Y as **plain absolute numbers** (`Y36`, `Y525`) in the same face frame where its routing uses `#902=#911-(…)` (e.g. `tablet.PRG`: `G100 X2121 Y65 …` next to `#902=#911-(646)` / `G172 … Y=#902`). `#911=DY`, so `#911-(v)` is just "v from the far edge". Both forms are absolute positions in one frame. PROVEN by `tablet.PRG` and `zijkant rechts.PRG` (Y523/Y37 with DY 558: two rows 35 and 37 mm from the edges).
- **The Fusion post is different.** `formatY` writes `#902=#911-(y_fusion)`, so **mill Y = DY − Fusion Y** (a Y flip, because the Fusion setup origin is at the front edge and machine +Y points to the operator). Drilling **must use the same transform as the routing**, or holes come out mirrored relative to the contours. So the fork writes:
  ```
  #902=#911-(37)
  G100 X136 Y=#902 Z13 F2 T81
  ```
  `G100 … Y=#var` is PROVEN accepted. `#902` itself on G100 isn't in the archive, but any `#n` works, so it's INFERRED safe.
- `|4 DX` / `|6 DY` / `#910` / `#911` must be correct. `Singolo.seq` uses the header DX/DY to shift program zero (AGENTS.md), and this affects drilling exactly as it affects routing.
- The CAD wrappers also emit `G92 U2.50 V2.50 W0` (TLF `OFFSET_DIMA_X/Y 2.5`). The Fusion post doesn't emit it for routing, so it must **not** emit it for drilling either. Keep one origin convention.
- Running a program mirrored (operator symmetry) is why `#X/#S` tables are needed. Always emit them, as the golden does.

## 7. What the post must emit (summary)

```
#T81=2,3,4,5,6           (once, before the first gang G100; mirrored lists too)
#X81=6,5,4,3,2
#S81=6,5,4,3,2
#902=#911-(<fusion y>)
G100 X<x of first station> Y=#902 Z<depth> F<m/min> T81
#902=#911-(<fusion y>)
G100 X<x> Y=#902 Z<depth> F<m/min> T<station>      (single hole)
```

- No S, no G173/G101 for boring-head holes, no A/C.
- Depth = −(Fusion hole-bottom Z) with WCS Z0 at the stock top.
- Full worked examples: `docs/example-side-panel-target.prg` (end state), `docs/example-side-panel-skeleton.prg` (what the fork skeleton emits today), `docs/example-B2-subset-target.prg` (17-hole row → `T81` ×3 + subset `T82=2,3`).

## 8. Proven vs inferred (one table)

| Statement | Status |
|---|---|
| G100 = vertical hole, words X Y Z F T | PROVEN (ISO.TXT) |
| No S on G100 | PROVEN (0/4,243) |
| Z = depth below top, positive | PROVEN (TLF→PRG pair, through holes Z19 on 18 mm) |
| F unit m/min | PROVEN for G101. INFERRED for G100 (values and TAB). |
| `Y=#var` accepted on G100 | PROVEN |
| Stations 1–7 on a 32.00 mm row along X; Ø5 on 2–6 today | PROVEN (Offset.prm + TAB01 2026-10-19) |
| `#T8n` = stations dropping together; G100 X = first listed station; spindle s at +32·(s−first) | PROVEN by exact 122-hole reconstruction of the golden |
| `#X8n/#S8n/#Y8n` = mirrored lists for symmetric runs | INFERRED |
| Group tables must be emitted per program and follow TAB01 | PROVEN (2016 vs 2026 lists) |
| Max number of groups / allowed numbers beyond 83 | UNKNOWN |
| No separate head-down/up code | INFERRED |
| `M111/M112 D F` slow entry/exit | PROVEN syntax; control behaviour from the doc |
| `MODO 1` = gang, `MODO 2` = single | INFERRED |
| Boring head is not modelled in Fusion Machine Sim (`.mch` has only spindle 41) | PROVEN by reading the post / AGENTS. Simulating holes there is only a location check. |
