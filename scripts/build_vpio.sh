#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT_DIR/src/pipecat_macos_transport/macos/vpio_helper.c"
OUT="$ROOT_DIR/src/pipecat_macos_transport/macos/libvpio.dylib"

mkdir -p "$(dirname "$OUT")"

echo "Compiling libvpio.dylib → $OUT"
clang -std=c11 -O2 \
  -dynamiclib -o "$OUT" "$SRC" \
  -framework AudioToolbox -framework AudioUnit

echo "Done."

