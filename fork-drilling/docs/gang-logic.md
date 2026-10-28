# Gang logic for both axes

Drill fork only. The live post is unchanged. Nothing here has been run on the mill.

Sources, used and not committed: `Param/Offset.prm` and `TAB01.DAT` inside `MW310 PARAM.zip`, `tablet.PRG` and the older zijkant programs inside `drill-2026-10-20.zip`, and `1 2 Zijkant Links.PRG`. The `.tlf` for that side panel is in git. `tablet.PRG` has no `.tlf` in the zip, so the Y-pair spacing below is from the offsets, not from a hole-for-hole reconstruction.

## Station layout

`Offset.prm` positions are 0.01 mm. The station number is field 14. Type 1 is a vertical drill.

### Along X (same offset Y, −110.63 mm)

| Station | X mm | Bit in `TAB01.DAT` | Max depth field | In a gang? |
|---|---|---|---|---|
| 1 | 50 | Ø3 puntboor | 0 | corner, also on the Y arm |
| 2 | 82 | Ø5 rijboren | 30 mm | yes |
| 3 | 114 | Ø5 | 30 mm | yes |
| 4 | 146 | Ø5 | 30 mm | yes |
| 5 | 178 | Ø5 | 30 mm | yes |
| 6 | 210 | Ø5 | 30 mm | yes |
| 7 | 242 | empty | — | no |

Pitch 2→3→4→5→6→7 is 32.00 mm. Higher station number is higher offset X. On the zijkant program that is higher program X: `G100` X is station 2, and station 6 is 128 mm further along +X. That reconstruction matches all 122 TLF holes.

### Along Y (same offset X, 50.00 mm)

| Station | Y mm | From the station above | Bit | Max depth field |
|---|---|---|---|---|
| 1 | −110.63 | — | Ø3 | 0 |
| 8 | −174.85 | 64.22 | Ø4.5 | 20 mm |
| 9 | −206.75 | 31.90 | Ø8 | 0 |
| 10 | −238.85 | 32.10 | field Ø7, file name says 6 mm | 0 |
| 11 | −270.85 | 32.00 | empty | — |
| 12 | −302.85 | 32.00 from 11, 64.00 from 10 | Ø35 | 0 |
| 13 | −334.85 | 32.00 | Ø10 | 0 |

Stations 8 and 10 are exactly 64.00 mm apart. That is the pair in `tablet.PRG`:

```
#T81=10,8
#Y81=8,10
#S81=8,10
G100 X2121 Y65 Z13.50 F2 T81
```

No other program in the Prog tree defines `#Y`. Every X-row gang defines `#T`, `#X` and `#S`, and leaves `#Y` out. `#X` / `#S` are the station list mirrored about the ends of the Ø5 row (2 and 6), not millimetre offsets.

There is no second Ø5 on the Y arm. A line of Ø5 holes along Y cannot be a multi-spindle hit. Each hole is one `G100` with station 2.

Horizontal stations (31, 33, 35–38) are not part of this.

## Rules the fork applies

1. A hole drilled with station 2, 3, 4, 5 or 6 is an X-row candidate. The post still assigns the spindles. The CAM tool is T202 for every Ø5 hole.
2. Holes are split by program Y, depth and feed before an X window is built. A different depth or a different feed is a different stroke.
3. On one X row the leftmost remaining hole is station 2. The post looks +32, +64, +96 and +128 mm. Stations with a hole in that slot drop together. The row is walked until it is used up, so a run longer than five spindles becomes several strokes.
4. The full set `2,3,4,5,6` is always `T81`. Any other X subset takes the next free number from `T82`. `#X` and `#S` are that list mirrored about stations 2 and 6. `#Y` is not written.
5. A hole that misses every slot is `G100 … T<the tool's station>`. An Ø5 line along Y is five of those, because each hole has its own Y and the X window never sees a neighbour.
6. A hole whose station is on the Y arm (1, 8, 9, 10, 12, 13) is matched by diameter and by offset Y. Two holes share a stroke only when their program-Y distance equals the offset-Y distance of two loaded stations, the diameters match those stations, and depth and feed match. Station 11 is never used.
7. For a Y stroke, `#T` lists the stations from the more negative offset Y to the less negative one. `G100` X and Y are the hole of the first station. `#Y` and `#S` are each station mirrored about the two ends of **that subset**. `#X` is not written. For stations 10 and 8 this is `#T=10,8`, `#Y=8,10`, `#S=8,10`, the tablet shape, and the second hole is 64 mm toward +program Y.
8. Consecutive boring operations are held and planned together, so the Ø4.5 tool and the Ø7 tool can be two Fusion ops and still one stroke. The buffer is written out when a routing section starts, and again at the end of the program.
9. `maxGangGroups` counts every distinct `#T8n`, X and Y together. The shop archive only uses 81–83. The default stays 3. The test panel sets it to 8 so the Y pair can be `T84`. Anything past the cap is a single `G100`.
10. Gang boring off, a station the table does not list, or a hole with no partner, is one `G100` for the station the user picked.

## Assumptions the files do not prove

These are also the machine checks. A wrong answer changes the NC or the way it should be read.

1. **MACHINE CHECK — Y sign.** Higher offset X is higher program X. That is proven. The fork uses the same sign for Y: station 8 (offset −174.85) is +64 mm in program Y from station 10 (offset −238.85). `tablet.PRG` has no TLF, so this is not reconstructed. If the scrap pair comes out 64 mm the other way, the sign is wrong.
2. **MACHINE CHECK — Y mirror.** `#Y=8,10` matches mirroring stations 10 and 8 about their own ends. It does not match a mirror about station 1 and station 13. Subsets of three or more Y stations are not in any program. The test panel only uses the 2-station pair.
3. **MACHINE CHECK — missing `#X` on a Y gang.** The fork omits `#X`, as `tablet.PRG` does. Confirm a missing line means "same order as `#T`" when the program is mirrored in X only.
4. **MACHINE CHECK — `T84`.** No archived program defines a group above 83. If the control rejects `T84`, set max groups back to 3. The Y pair then becomes two single `G100`s. The holes stay in the right places. Only the one-stroke behaviour is lost.
5. **MACHINE CHECK — station 10 diameter.** The tool name is `Drevelboor 57x6mm.utn`. The diameter field is 700, which is 7.00 mm if the column is 0.01 mm. The fork matches 7.0 mm. Measure the bit. If it is 6 mm, draw Ø6 and we change the table after the measurement. Do not guess in the NC.
6. **MACHINE CHECK — through holes.** The test through-hole is `Z19` on 18 mm, as a single `T1`, with no `M112`. Confirm the Ø3 actually exits, and whether the control wants `M112` for a clean exit. Keep the pod out from under program X100 Y430.
7. **MACHINE CHECK — one Z and one F per stroke.** The fork refuses to put two depths or two feeds in one `G100`, because the block has one Z and one F. Confirm the head really bores every selected spindle to that same depth.
8. **MACHINE CHECK — neighbours stay up.** A subset such as `2,5,6` is assumed to drop only those spindles. The PLC has one output per vertical drill. It does not document `#T81`. One scrap stroke with a gap is the check.
9. **MACHINE CHECK — head vertical before `G100`.** Put the drill ops before any 3+2 routing until this is tried.

## What the test panel is for

`test-panel-800x500.md` places every rule on one 800 × 500 × 18 board: a 12-hole X run, a gapped subset, an off-pitch hole, two depths, two feeds, an Ø5 column along Y, an Ø8 column along Y, the 8+10 pair twice, a through hole and a blind hole, an isolated Ø10, and an Ø8 sitting on the same Y as the shelf row. Two routed crosses are in the expected program for measuring.
