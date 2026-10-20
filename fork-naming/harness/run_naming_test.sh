#!/bin/bash
# Naming-fork harness. Posts into harness/out/ncprograms only; never touches
# Fusion, its Posts folder, ~/Documents/Fusion 360/NC Programs or the live post.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
FORK="${FORK:-$HERE/../masterwood_4005L_naming.cps}"
APP="$HOME/Library/Application Support/Autodesk/webdeploy/production/Autodesk Fusion.app"
POST="${POST:-$APP/Contents/Libraries/Applications/CAM360/post}"
CNC="${CNC:-$HERE/cnc/face.cnc}"
OUT="$HERE/out/ncprograms"; LOGS="$HERE/out/logs"
rm -rf "$OUT" "$LOGS"; mkdir -p "$OUT" "$LOGS"
DOC="Milling_MM - Post Processor Benchmark"   # document-path in the sample = "$DOC v1"
step=0
post() { # post <programName> <fusionFileName> [extra args...]
  local prog="$1" fname="$2"; shift 2; step=$((step+1))
  "$POST" --noeditor --nointeraction --nobackup --noprogress --property forceMM true \
    --property programName "'$prog'" "$@" --log "$LOGS/$step.log" "$FORK" "$CNC" "$OUT/$fname.prg" >/dev/null 2>&1
  echo "--- step $step: post NC '$prog' as Fusion file '$fname.prg' ${*:-}  (exit $?)"
  (cd "$OUT" && ls -1)
}
show() { local f="$OUT/$1"; echo ">>> $1: $(head -3 "$f" | tr -d '\r' | paste -sd'|' -)   key: $(grep -a '^( NC ' "$f" | tr -d '\r')   CRLF lines: $(grep -c $'\r$' "$f")/$(wc -l < "$f" | tr -d ' ')"; }
post 1001 1001;                  show "$DOC 01.prg"
post 1002 1002;                  show "$DOC 02.prg"
sleep 1; touch -t 202001010000 "$OUT/$DOC 01.prg"
post 1001 1001;                  show "$DOC 01.prg"; ls -l "$OUT/$DOC 01.prg" | awk '{print "    mtime", $6, $7, $8}'
post 1003 "$DOC 07";             show "$DOC 07.prg"
post 1004 1004;                  show "$DOC 08.prg"
post 1005 1005 --security 1000;  show "$DOC 09.prg"
post 1006 1006 --property autoFileName false; show "1006.prg"
grep -h "security\|Renamed\|rror" "$LOGS"/*.log | sort | uniq -c
