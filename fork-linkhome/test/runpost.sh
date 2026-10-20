#!/bin/bash
# runpost.sh post.cps out.prg [extra --property args]
POST="$HOME/Library/Application Support/Autodesk/webdeploy/production/Autodesk Fusion.app/Contents/Libraries/Applications/CAM360/post"
cps="$1"; out="$2"; shift 2
rm -f "$out"
"$POST" --noeditor --nointeraction --nobackup --noprogress \
  --property cMillOffset 180 --property cSimOffset 90 --property headOrientHeight 20 \
  --property useY911 true --property yMillSign 1 --property cMillSign 1 --property orientFeed 15 "$@" \
  --log "${out%.prg}.log" "$cps" /tmp/lh/1009.cnc "$out"
echo "rc=$?"
