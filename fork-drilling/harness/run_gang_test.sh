#!/bin/bash
# Gang-drilling checks without Fusion.
# Writes harness/out/*.prg, compares harness/expected, runs check_prg.py,
# and proves the live mill post was not edited.
set -eu
set -o pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"
node "$HERE/gang_test.js"
python3 "$HERE/check_live_untouched.py"
mkdir -p "$HERE/out"
rc=0
for prg in \
  "$HERE/expected/zijkant-links-2445x561x18.prg" \
  "$HERE/expected/b2-17.prg" \
  "$HERE/expected/single-fallback.prg" \
  "$HERE/expected/side-panel-720x560x18.prg"
do
  name="$(basename "$prg" .prg)"
  python3 "$HERE/check_prg.py" "$prg" | tee "$HERE/out/$name.check" | grep -vE '^  hole'
  if [ "${PIPESTATUS[0]}" -ne 0 ]; then rc=1; fi
  grep '^  hole' "$HERE/out/$name.check" | awk '{print $2, $3, $4}' > "$HERE/out/$name.holes"
done
if [ -f "$HERE/expected/side-panel-720x560x18.holes" ]; then
  if diff -u "$HERE/expected/side-panel-720x560x18.holes" "$HERE/out/side-panel-720x560x18.holes" > "$HERE/out/side-panel.diff"; then
    echo "HOLES MATCH expected/side-panel-720x560x18.holes"
  else
    echo "HOLES DIFFER (see out/side-panel.diff)"
    rc=1
  fi
fi
# 122 shelf holes, positions only, from the zijkant program.
grep '^  hole' "$HERE/out/zijkant-links-2445x561x18.check" | awk '{print $2, $3, $4}' > "$HERE/out/zijkant-links-2445x561x18.holes"
if [ ! -f "$HERE/expected/zijkant-links-2445x561x18.holes" ]; then
  cp "$HERE/out/zijkant-links-2445x561x18.holes" "$HERE/expected/zijkant-links-2445x561x18.holes"
  echo "wrote expected/zijkant-links-2445x561x18.holes"
else
  if diff -q "$HERE/expected/zijkant-links-2445x561x18.holes" "$HERE/out/zijkant-links-2445x561x18.holes" >/dev/null; then
    echo "HOLES MATCH expected/zijkant-links-2445x561x18.holes ($(wc -l < "$HERE/expected/zijkant-links-2445x561x18.holes") lines)"
  else
    echo "ZIJANT HOLES DIFFER"
    rc=1
  fi
fi
exit "$rc"
