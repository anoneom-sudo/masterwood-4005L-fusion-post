#!/bin/bash
# Headless test harness for the DRILL FORK. Does not touch Fusion, its posts
# folder, NC Programs, tool library or the live post.
#   ./run_post.sh                      # post every harness/cnc/*.cnc
#   ./run_post.sh path/to/file.cnc     # post one intermediate
#   PROPS="--property forceMM true --property boringToolBase 0" ./run_post.sh
#       (Autodesk inch samples -> mm; sample T1..T50 -> boring stations)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
FORK="$HERE/../masterwood_4005L_drill.cps"
APP="$HOME/Library/Application Support/Autodesk/webdeploy/production/Autodesk Fusion.app"
POST="${POST:-$APP/Contents/Libraries/Applications/CAM360/post}"
OUT="$HERE/out"
mkdir -p "$OUT"
[ -x "$POST" ] || { echo "post engine not found: $POST"; exit 2; }
"$POST" --version 2>&1 | head -1
if [ $# -gt 0 ]; then FILES=("$@"); else FILES=("$HERE"/cnc/*.cnc); fi
rc=0
for cnc in "${FILES[@]}"; do
  [ -f "$cnc" ] || continue
  name="$(basename "$cnc" .cnc)"
  prg="$OUT/$name.prg"
  rm -f "$prg"
  # shellcheck disable=SC2086
  "$POST" --noeditor --nointeraction --nobackup --noprogress ${PROPS:-} \
     --log "$OUT/$name.log" "$FORK" "$cnc" "$prg" >/dev/null 2>&1
  if [ ! -s "$prg" ]; then
    echo "POST FAILED: $name (see $OUT/$name.log)"; grep -iE 'error|exception' "$OUT/$name.log" | head -5; rc=1; continue
  fi
  python3 "$HERE/check_prg.py" "$prg" | tee "$OUT/$name.check" | grep -vE '^  hole' 
  [ "${PIPESTATUS[0]}" -eq 0 ] || rc=1
  # Compare drilled positions (order- and grouping-independent) with expected/<name>.holes
  grep '^  hole' "$OUT/$name.check" | awk '{print $2, $3, $4}' > "$OUT/$name.holes"
  if [ -f "$HERE/expected/$name.holes" ]; then
    if diff -u "$HERE/expected/$name.holes" "$OUT/$name.holes" > "$OUT/$name.diff"; then
      echo "HOLES MATCH expected/$name.holes"
    else
      echo "HOLES DIFFER from expected/$name.holes (see out/$name.diff)"; rc=1
    fi
  fi
done
exit $rc
