#!/usr/bin/env bash
# One-time (idempotent) setup: ffmpeg with libass, Python deps, the `vedit` CLI, whisper model warm-up.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then
  if command -v apt-get >/dev/null; then
    (apt-get install -y -q ffmpeg || (apt-get update -q && apt-get install -y -q ffmpeg)) >/dev/null
  elif command -v brew >/dev/null; then
    brew install ffmpeg
  else
    echo "Install ffmpeg (with libass) manually" >&2; exit 1
  fi
fi
filters="$(ffmpeg -hide_banner -filters 2>/dev/null)"
[[ "$filters" == *" ass "* ]] || echo "WARNING: this ffmpeg lacks libass — captions won't render" >&2

python3 -m pip install -q -e . 2>&1 | grep -v -i "warning\|root" || true

# Pre-download the default transcription model so the first edit doesn't stall.
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')" >/dev/null 2>&1 || true
echo "vedit ready: $(command -v vedit)"
