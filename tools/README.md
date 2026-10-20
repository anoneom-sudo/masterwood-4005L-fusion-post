# Masterwood 4005L spindle tools: MW310 standard speeds → Fusion

Made 2026-10-19 by Grok Bot. Nothing in Fusion has been changed.

- `masterwood_4005L_tools_proposed.json`: a Fusion tool-library JSON (`{"data":[...]}`) with the 10 tools of the Fusion cloud library
  "Tool Library" / folder `Masterwood_C-spindle`. Each preset has n/n_ramp = TAB01 max rpm, v_f/leadIn/leadOut/transition = TAB01 working speed,
  and v_f_plunge/v_f_ramp = TAB01 entry speed (m/min ×1000). v_c, f_n and f_z are recalculated. Geometry is unchanged.
- `masterwood_4005L_tools_cloudcache_us-gmail6604694.json.orig`: a verbatim copy of Fusion's cache of that cloud library
  (`~/Library/Application Support/Autodesk/Autodesk Fusion 360/YR6BYKLLZGSDWSTW/NsHubLibrariesCache/adsk.libraries.manufacturing.tools/us-gmail6604694.json`).
  This is a cache, not an import file.

TAB01.DAT `C n` columns (decoded): length (0.01 mm), diameter (0.01 mm), working depth (0.01 mm), working speed (0.01 m/min),
entry speed (0.01 m/min), max rpm (×1000), rotation (0 = R, 1 = L), then 4 columns still unknown, then the .utn name.
How they were decoded: the MW310 tool-editor field order (English messaggi.txt: Diameter, Length, Max RPM (x 1000), Entry speed, Working speed, Working depth, Rotation),
the matching per-tool `.utn` files in Mw310.zip/Mw310/Utensili/, and Test.tlf/Test.PRG for 41/10 (S20 E2 F3 = TAB01 C10 20 / 200 / 300).

How to import: Manufacture > Manage > Tool Library. Right-click Local (or Cloud) > Import Libraries > pick this JSON > Open.
It comes in as a new library. Check it first, then use it in place of the old one.
