#!/usr/bin/env bash
# Thin wrapper: runs Leo's synthesis flow if present (synth/run.sh [block]).
cd "$(git rev-parse --show-toplevel)"
[ -x synth/run.sh ] || { echo "synth/run.sh not there yet (Leo)"; exit 0; }
mkdir -p logs/latest && synth/run.sh "$@" 2>&1 | tee logs/latest/synth.log; exit "${PIPESTATUS[0]}"
