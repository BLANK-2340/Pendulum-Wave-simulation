"""Command-line CSV exporter for headless pendulum-wave simulations."""

from __future__ import annotations
import argparse
import csv
import math
from pathlib import Path
import sys
from .physics import WaveConfig, make_specs, simulate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=4.0)
    parser.add_argument("--dt", type=float, default=1.0 / 120.0)
    parser.add_argument("--count", type=int, default=27)
    parser.add_argument("--sync-time", type=float, default=32.0)
    parser.add_argument("--base-oscillations", type=int, default=25)
    parser.add_argument("--angle-deg", type=float, default=24.0)
    parser.add_argument("--damping", type=float, default=0.0006)
    parser.add_argument("--output", type=Path, help="CSV path; stdout when omitted")
    return parser


def write_csv(args: argparse.Namespace) -> int:
    config = WaveConfig(count=args.count, sync_time=args.sync_time,
                        base_oscillations=args.base_oscillations,
                        initial_angle=math.radians(args.angle_deg), damping=args.damping)
    specs = make_specs(config)
    handle = args.output.open("w", newline="", encoding="utf-8") if args.output else sys.stdout
    try:
        writer = csv.writer(handle, lineterminator="\n")
        header = ["time_s"]
        for spec in specs:
            header.extend((f"p{spec.index}_theta_rad", f"p{spec.index}_omega_rad_s"))
        writer.writerow(header)
        rows = 0
        for time_s, states in simulate(config, args.duration, args.dt):
            row: list[float] = [time_s]
            for state in states:
                row.extend((state.theta, state.omega))
            writer.writerow(row)
            rows += 1
    finally:
        if args.output:
            handle.close()
    if args.output:
        print(f"wrote {rows} rows for {config.count} pendulums to {args.output}", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    return write_csv(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
