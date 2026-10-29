#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
archive_root="$(mktemp -d "${TMPDIR:-/tmp}/pendulum-showcase.XXXXXX")"
trap 'rm -rf "$archive_root"' EXIT

git -C "$repo_root" archive --format=tar HEAD | tar -xf - -C "$archive_root"
cd "$archive_root"

python3 -c 'import PIL; print("Pillow", PIL.__version__)'
PYTHONHASHSEED=0 python3 -W error -m unittest discover -s tests -v
python3 -m compileall -q pendulum_wave tests

python3 -m pendulum_wave.cli --count 5 --duration 0.04 --dt 0.01 \
  --output "$archive_root/states-a.csv"
python3 -m pendulum_wave.cli --count 5 --duration 0.04 --dt 0.01 \
  --output "$archive_root/states-b.csv"
cmp "$archive_root/states-a.csv" "$archive_root/states-b.csv"

python3 -m pendulum_wave.convergence > "$archive_root/convergence-a.md"
python3 -m pendulum_wave.convergence > "$archive_root/convergence-b.md"
cmp "$archive_root/convergence-a.md" "$archive_root/convergence-b.md"
python3 -m pendulum_wave.convergence --format json --output "$archive_root/convergence-a.json"
python3 -m pendulum_wave.convergence --format json --output "$archive_root/convergence-b.json"
cmp "$archive_root/convergence-a.json" "$archive_root/convergence-b.json"
python3 -m pendulum_wave.evidence results/rk4_convergence.json

python3 -m pendulum_wave.energy_drift --format json --output "$archive_root/energy-a.json"
python3 -m pendulum_wave.energy_drift --format json --output "$archive_root/energy-b.json"
cmp "$archive_root/energy-a.json" "$archive_root/energy-b.json"
python3 -m pendulum_wave.evidence results/energy_drift.json

python3 -m pendulum_wave.render --count 5 --duration 0.2 --fps 10 --substeps 2 \
  --width 320 --height 240 --output "$archive_root/wave-a.gif"
python3 -m pendulum_wave.render --count 5 --duration 0.2 --fps 10 --substeps 2 \
  --width 320 --height 240 --output "$archive_root/wave-b.gif"
cmp "$archive_root/wave-a.gif" "$archive_root/wave-b.gif"

python3 - "$archive_root/states-a.csv" "$archive_root/wave-a.gif" <<'PY'
import csv
from pathlib import Path
import sys
from PIL import Image

csv_path, gif_path = map(Path, sys.argv[1:])
with csv_path.open(newline="", encoding="utf-8") as handle:
    rows = list(csv.reader(handle))
assert len(rows) == 6
assert len(rows[0]) == 11
assert [float(row[0]) for row in rows[1:]] == [0.0, 0.01, 0.02, 0.03, 0.04]
with Image.open(gif_path) as image:
    assert image.format == "GIF"
    assert image.size == (320, 240)
    assert image.n_frames == 3
PY

echo "showcase verification passed for $(git -C "$repo_root" rev-parse HEAD)"
