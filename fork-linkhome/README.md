# fork-linkhome: Fusion links in tilted ops via a G173 home re-entry

Started 2026-10-19 (Europe/Brussels).

**LIVE since 2026-10-19 13:54.** Linkhome is merged into the live `../masterwood_4005L.cps` together with the auto naming (`autoFileName`). It keeps the live FORKID {B3E91C70-…} and description "Masterwood 4005L MW310". Backup of the live post before the merge: `../_backup/masterwood_4005L.pre-linkhome-20261019-1354.cps`. Johannes dry-ran 1013: it worked and was faster.

- Rebuild the live post from a pre-linkhome live post:
  `python3 make_fork.py <pre-linkhome live.cps> <out.cps> --live` (keeps FORKID and description, adds a header note).
- Fork mode, no `--live`: separate FORKID {45056685-…} and description "(linkhome fork)". `masterwood_4005L_linkhome.cps` here is the old fork, built from the **pre-naming** post. It is superseded by the live post; keep it for reference only.
- Do not run make_fork.py on the current live post. It already contains linkhome, so the patches would fail their exact-match asserts.

## What it does
Inside a tilted op (not vertical, 3+2), Fusion link moves (MOVEMENT_RAPID / MOVEMENT_HIGH_FEED: retract and travel) are buffered.
At the next non-link move in the same section:
1. Fusion's own retract moves are kept as G101 until the tip is at or above the part top (Fusion Z >= 0). The G173 lift is assumed to be straight up in machine Z, not along the tool axis.
2. For the rest of the link: stay-down time (segments at the link feed, with acceleration from a stop) is compared with home time (Z lift to homeZ, XY rapid, drop at E to the orient height, G101 down to the link end, plus overhead).
3. If home is faster and the remaining path is >= minLinkLengthForHome, the travel is replaced by
   `#902=…` / `G173 X Y=#902 Z-<orient> S E T A C D0` (same words as the first G173), then `G101` to the link end with an explicit F.
   Plunge, lead-in, cutting and lead-out moves are never touched.
Links at section end (final retract) and links with nothing left after the retract keep the live output. With `linkViaHome=false` the output is byte-identical to the live post (checked on 1009).

## Properties (group "linking")
| name | default | note |
|---|---|---|
| linkViaHome | true | false = live behaviour |
| rapidSpeedEstimate | 40 m/min | ASSUMPTION, confirm on the mill (XY rapid) |
| rapidSpeedZEstimate | 19.2 m/min | ASSUMPTION: Syncro.prm W "VEL max 19200" read as mm/min |
| homeZEstimate | 150 mm above part top | ASSUMPTION, confirm |
| minLinkLengthForHome | 150 mm | floor: shorter links always stay down |
| linkAccelEstimate | 200 mm/s^2 | ASSUMPTION: Syncro.prm ACC_INT 200 read as mm/s^2. 0 = length / feed only |
| linkHomeOverhead | 0.5 s | ASSUMPTION per G173 |

The decision is logged in the post log (`link HOME len=… stay=…s home=…s`, then a `linkhome:` summary).

## Test (1009 ops, NCProgram14 properties, orientFeed 15)
`test/1009.cnc` was captured from Fusion (doc 9 Bad_Component1, Setup3, 3 ops, legacy CAM.postProcess with `test/cncdump.cps`, nothing in the doc changed).
`test/runpost.sh <post> <out.prg> [--property …]` runs Fusion's headless post engine with the NCProgram14 properties.
The CLI starts in inch, so `test/fork_h.cps` = fork + a harness-only `harnessForceMM` line (`unit = MM`). The live post with the same 2 lines reproduces `~/simx/1009_fusion_setup_order.prg` byte for byte (only `|1` differs).
Result: 19 of 19 mid-op links become G173 re-entries with the defaults. Output `1013.prg` is on the box: /workspace/mill/1013.prg (1009 op order).

## Merge verification 2026-10-19 13:54 (headless engine 5.413.5, `--property forceMM true`, NCProgram14 properties, security 0 and 1000)
- (a) Merged, `linkViaHome false` + `autoFileName false`, compared with the 13:44 live post + `autoFileName false`: **byte-identical** on 1009.cnc and on the 4 naming-harness samples (face, full program, toolchange, deep drilling), at both security levels.
- (b) Merged, `linkViaHome true` + `autoFileName false` on 1009.cnc: equals `/workspace/mill/1013.prg` except `|1` (UNNAMED vs 1013). Sections reordered to 1013's op order; that reorder was already proven exact for 1009. With autoFileName off there is no `( NC … )` line. Results are the same at security 0 and 1000.
- (c) `autoFileName true`: fork-naming `run_naming_test.sh` with the merged post gives the same output as with the 13:44 live post (01, 02, re-post reuses 01, typed name 07, 08, 09 at security 1000, autoFileName false → 1006.prg). 1009.cnc with programName 1013 → renamed to `9 Bad_Component1 01.prg`, `|1 9 Bad_Component1 01`, `( NC 1013 )`. The body is identical to (b), at both security levels.
- The vertical sample programs are unchanged with linkViaHome on (it applies to tilted ops only).
