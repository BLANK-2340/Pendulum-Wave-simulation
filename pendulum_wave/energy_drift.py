"""Reproducible RK4 energy-drift experiment for one undamped pendulum."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from .physics import State, WaveConfig, energy, make_specs, rk4_step


STEP_SIZES = (1.0 / 30.0, 1.0 / 60.0, 1.0 / 120.0, 1.0 / 240.0)
DEFAULT_DURATION = 32.0


def _trajectory_metrics(config: WaveConfig, duration: float, dt: float) -> dict[str, float | int]:
    if config.count != 1 or config.damping != 0.0:
        raise ValueError("energy-drift experiment requires one undamped pendulum")
    if not math.isfinite(duration) or duration <= 0.0:
        raise ValueError("duration must be finite and positive")
    if not math.isfinite(dt) or dt <= 0.0:
        raise ValueError("dt must be finite and positive")
    steps = round(duration / dt)
    if not math.isclose(steps * dt, duration, rel_tol=0.0, abs_tol=1.0e-12):
        raise ValueError("duration must be an integer multiple of dt")

    state = State(config.initial_angle, 0.0)
    spec = make_specs(config)[0]
    initial_energy = energy(state, spec, config.gravity)
    maximum_drift = 0.0
    for _ in range(steps):
        state = rk4_step(state, spec, config, dt)
        relative_drift = (energy(state, spec, config.gravity) - initial_energy) / initial_energy
        maximum_drift = max(maximum_drift, abs(relative_drift))
    final_energy = energy(state, spec, config.gravity)
    return {
        "steps": steps,
        "initial_energy_j_per_kg": initial_energy,
        "final_energy_j_per_kg": final_energy,
        "final_relative_drift": (final_energy - initial_energy) / initial_energy,
        "max_abs_relative_drift": maximum_drift,
    }


def energy_drift_report(duration: float = DEFAULT_DURATION) -> dict[str, Any]:
    """Return deterministic energy-drift measurements across prescribed step sizes."""
    config = WaveConfig(count=1, damping=0.0)
    rows = []
    for dt in STEP_SIZES:
        row = {"dt_s": dt}
        row.update(_trajectory_metrics(config, duration, dt))
        rows.append(row)
    spec = make_specs(config)[0]
    return {
        "schema_version": 1,
        "experiment": "rk4_undamped_energy_drift",
        "method": "classical_rk4",
        "duration_s": duration,
        "initial_state": {"theta_rad": config.initial_angle, "omega_rad_s": 0.0},
        "configuration": {
            "gravity_m_s2": config.gravity,
            "damping_s_inv": config.damping,
            "pendulum_length_m": spec.length,
        },
        "rows": rows,
    }


def report_json(duration: float = DEFAULT_DURATION) -> str:
    """Serialize the energy-drift report as canonical, byte-repeatable JSON."""
    return json.dumps(energy_drift_report(duration), indent=2, sort_keys=True,
                      allow_nan=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=DEFAULT_DURATION)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = energy_drift_report(args.duration)
    if args.format == "json":
        output = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    else:
        lines = [
            "| dt (s) | steps | final relative drift | max absolute relative drift |",
            "|---:|---:|---:|---:|",
        ]
        for row in report["rows"]:
            lines.append(
                f"| {row['dt_s']:.12f} | {row['steps']} | "
                f"{row['final_relative_drift']:.12e} | "
                f"{row['max_abs_relative_drift']:.12e} |"
            )
        output = "\n".join(lines) + "\n"
    if args.output is None:
        print(output, end="")
    else:
        args.output.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
