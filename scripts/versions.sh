#!/usr/bin/env bash
# Record exact tool versions so results can be repeated. Fails if a tool is missing.
set -u
out="${1:-logs/tool-versions.txt}"; mkdir -p "$(dirname "$out")"
rc=0
{
  echo "date: $(date -u +%FT%TZ)"
  echo "commit: $(git rev-parse --short HEAD 2>/dev/null || echo none)"
  for t in verilator yosys make python3; do
    if command -v "$t" >/dev/null; then echo "$t: $($t --version 2>&1 | head -1)"
    else echo "$t: MISSING"; rc=1; fi
  done
} | tee "$out"
exit $rc
