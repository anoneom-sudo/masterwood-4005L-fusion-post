# Machine definition backups (not for Fusion Machine Library)

These files are **outside** `~/Library/Application Support/Autodesk/CAM360/machines/` so Fusion does not list them.

**Live file (only one in Fusion Local):** `…/CAM360/machines/masterwood_4005L.mch` (model `4005L mockup`).

## Policy
- Keep backups here, never as sibling `.mch` files in the CAM360 machines folder.
- Prefer sparse **milestone** copies after clear positive feedback (e.g. knuckle OK).
- If a backup must be opened in Fusion temporarily, its `general.model` should start with `BACKUP —`.

## Milestones
- `MILESTONE_knuckle-OK_pointing-left_Chome90.mch` — A on knuckle correct; still faced left (before C home −90 try).
- `MILESTONE_home-position-OK_2026-09-11.mch` — park/home matches mill (C home 90, A dir [-1,0,0], TCP 184.9). Live: `CAM360/machines/masterwood_4005L.mch`.
