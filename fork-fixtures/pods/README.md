# fork-fixtures/pods — pod placer v1 (low fidelity, 2026-10-19)

Pipeline (all on a **ZZ throwaway** doc; run Fusion scripts with the Fusion MCP `fusion_mcp_execute`, e.g. `/tmp/fxr/run.sh <file> rw`):
1. `run_cfg.json` — which throwaway doc / setup.
2. `scan_setup.py` (Fusion) — opens the doc invisibly, regenerates invalid toolpaths (saves the throwaway), posts the setup with `podscan.cps` → `scan/toolpaths.jsonl`, writes the panel bottom outline (WCS) → `scan/outline.json`, closes.
3. `place_pods.py` (plain python3, no packages) + `place_cfg.json` → `<out_dir>/layout.json`, `layout.txt`, `layout.png` (top view, 1 px = 1 mm, front/I stop at the bottom; grey = panel bottom, red = keep-out, green = pod top plates, blue = rails + ports, orange = stop-plate zones).
4. `insert_pods.py` (Fusion) — pod boxes (top-plate footprint, sim Z−100…0) as component `PODS fork-fixtures` = setup fixtures; mode `istop` also sets the setup Position X/Y offset so the panel front edge sits on the I-stop face. Saves + closes the throwaway.

Frames: see PLAN.md 3b "Frame convention". Keep-out = every toolpath sample whose tool (radius R up to body length, assumed holder R40 beyond) comes within `clearance` (5) of the pod-top plane, stamped as discs R + clearance (conservative for tilted tools). Ports: pod base 140 must cover a port ring with 5 mm seal margin; bases may not touch stop zones (S2 M425–490, S1/front M1190–1306); 2 mm gap; ≥ 2 pods per used rail; inventory 4/4/4/2; rail edge spacing ≥ 135/175/175 inside the ventose.prm X ranges (field 1 only). rot 0 = top plate shifted toward the back (higher M), 180 = toward the front.
