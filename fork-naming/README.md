# Naming fork: "<Fusion document> NN.prg"

`masterwood_4005L_naming.cps` = live `masterwood_4005L.cps` (copy 2026-10-19 13:38, Europe/Brussels; `masterwood_4005L.base.cps`) + `naming.diff`.

- onOpen: doc = `document-path` minus the trailing " vN", minus illegal file characters. NN is chosen and written on `|1 <doc> NN`, plus a key line `( NC <Name/number> )` after M61.
- NN: (a) If Fusion's file name is already `<doc> NN`, it is kept. (b) If a `<doc> NN.prg` in the output folder has this NC program's key line, its NN is reused and the file is overwritten. (c) Otherwise NN = highest existing + 1. Gaps are never refilled.
- onTerminate: moves Fusion's default file (e.g. `1005.prg`) to `<doc> NN.prg`. No duplicate is left behind.
- Property `autoFileName` (default on). `forceMM` is for the harness only.
- Test: `harness/run_naming_test.sh` (posts into `harness/out/ncprograms` only). Last result: `harness/out/run_naming_test.txt`.
