# Masterwood Fusion post

This folder is the source of truth for the Masterwood post processor. Edit `masterwood.cps` here. Fusion's Local Posts folder is a symlink to this file.

## What this is

- Fusion Manufacture post (JavaScript `.cps`) for a Masterwood wood CNC mill.
- NC output extension: `.prg`
- Units: millimetres
- Vendor: Masterwood

## How we work

- Launch Grok from this folder: `cd ~/Documents/Vonque/Fusion\ Post\ processor && grok`
- Open the same folder in VS Code. `.cps` files open as JavaScript.
- Change the smallest thing that fixes the NC. Do not rewrite the Autodesk generic kernel unless the kernel is the bug.
- After an edit, post a simple toolpath in Fusion and inspect the `.prg`. That is the test.
- Commit when a change posts correctly. Posts have no unit tests.

## Machine / tools

- Electrospindle / ATC tools are Fusion T1–T10, matching Masterwood C-pockets C1–C10.
- The boring block is a separate library (spindle numbers 1–50). Do not reuse C-pocket numbers for boring tools in the same Fusion library.
- Tool table dump: `~/Downloads/TAB01.DAT`. Length and diameter are stored in 0.01 mm. Converter: `~/Downloads/masterwood_tab01_to_fusion.py`.
- Tool libraries generated from that table: `~/Downloads/Masterwood_C-spindle.json` and `~/Downloads/Masterwood_boring-unit.json`. Diameters come from the machine table, not the tool name.

## Fusion libraries

- **Local** on this Mac follows the symlink. Do not keep a second copy of `masterwood.cps` in Fusion's Posts folder.
- **Cloud** does not update automatically. When a version is ready for the mill PC, drag the post onto **My Posts → Cloud** (enable Cloud Libraries in Preferences → General → Manufacture first). Same Autodesk hub on both computers.

## Do not

- Edit the copy in `~/Downloads` or Fusion's `_backup` folder.
- Invent kinematics, M-codes, or tool-change format. Match existing Masterwood `.prg` output and the current post.
- Upload every in-progress edit to Cloud.
