# Masterwood Fusion post

This folder is the source of truth for the Masterwood post. Fusion's Local Posts folder is a symlink to the live `.cps`.

- Machine record: `MASTERWOOD_4005L_PROJECT_MEMORY.md`
- Post spec (3+2 first): `FUSION_MASTERWOOD_4005L_POST_HANDOFF.md`

Do not overwrite confirmed numbers with brochure values.

## What this is

- Machine: Masterwood Project 4005L, MW310 control, 5-axis head/head.
- Native NC is Masterwood dialect (`G172` / `G173` / `G101`), not Fanuc ISO inside a `.prg`.
- Current `masterwood.cps` is the generic Autodesk 3-axis post. It emits G0/G1/`T101 M6` and will not run on this mill. Keep it as reference only.
- Production post: `masterwood_4005L.cps` (native G172/G173, v1 = 3+2). Do not patch the generic file and expect it to cut.
- NC extension: `.prg`. Units: millimetres. Vendor: Masterwood.

## How we work

- Launch Grok from this folder: `cd ~/Documents/Vonque/Fusion\ Post\ processor && grok`
- Open the same folder in VS Code. `.cps` files open as JavaScript.
- Edit `masterwood_4005L.cps`. Follow `FUSION_MASTERWOOD_4005L_POST_HANDOFF.md`. 3+2 first; simultaneous 5-axis later.
- Golden NC: `samples/Test.PRG` (G172 J90) and `samples/test2.PRG` (G173 A80 C-15).
- Match live MW310 programs (`Test.PRG`, `test2.PRG`). Do not match Autodesk ISO style.
- After an edit, post a simple toolpath in Fusion and inspect the `.prg`. That is the test.
- Commit when a change posts correctly. Posts have no unit tests.

## Machine / tools

- Native electrospindle IDs: **41/1–41/10** (`UteName.dat`). Fusion proposal: T101–T110, mapped by the post to `T41/1` … not `T101 M6`.
- Do not use Fusion T1–T10 for C-pockets; those numbers collide with the boring head.
- Boring head: machine IDs 1–50. Probe is 49.
- Vertical route: `G172 … T41/n J90` then `G101`. Oriented: `G173 … T41/n A.. C.. D0` then `G101`.
- Z: Z− is above the panel, Z0 = surface, Z+ into the panel. Flip Fusion Z+ up on output.
- A=90 is tool vertical. A=0 C=0 is spindle horizontal, pointing right.
- C software limits: −140° … +286.8°. A: −38.6° … +211.4°. Pivot radius **184.90 mm**.
- Work Y max **1360 mm** (plate). Do not program the Syncro V stroke 2018 mm as table Y.
- Pod working height **100 mm** compressed. Do not pad fixture height.
- Tool table dump: `~/Downloads/TAB01.DAT`. Length and diameter are stored in 0.01 mm. Converter: `~/Downloads/masterwood_tab01_to_fusion.py`.
- Tool libraries generated from that table: `~/Downloads/Masterwood_C-spindle.json` and `~/Downloads/Masterwood_boring-unit.json`. Diameters come from the machine table, not the tool name.

## Fusion libraries

- **Local** on this Mac follows the symlink. Do not keep a second copy of `masterwood.cps` in Fusion's Posts folder.
- **Cloud** does not update automatically. When a version is ready for the mill PC, drag the post onto **My Posts → Cloud** (enable Cloud Libraries in Preferences → General → Manufacture first). Same Autodesk hub on both computers.

## Do not

- Edit the copy in `~/Downloads` or Fusion's `_backup` folder.
- Invent kinematics, M-codes, or tool-change format. Match existing Masterwood `.prg` output (`Test.PRG`, `test2.PRG`).
- Use brochure strokes or rapids over `Syncro.prm`.
- Upload every in-progress edit to Cloud.
