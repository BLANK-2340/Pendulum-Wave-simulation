"""Reproducible RK4 step-size convergence report."""

from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from typing import Any
from .physics import State, WaveConfig, make_specs, rk4_step


STEP_SIZES = (1.0 / 30.0, 1.0 / 60.0, 1.0 / 120.0, 1.0 / 240.0)
REFERENCE_DT = 1.0 / 1920.0


def final_state(config: WaveConfig, duration: float, dt: float) -> State:
    if not math.isfinite(duration) or duration <= 0.0:
        raise ValueError("duration must be finite and positive")
    if not math.isfinite(dt) or dt <= 0.0:
        raise ValueError("dt must be finite and positive")
    steps = round(duration / dt)
    if not math.isclose(steps * dt, duration, rel_tol=0.0, abs_tol=1.0e-12):
        raise ValueError("duration must be an integer multiple of dt")
    state = State(config.initial_angle, 0.0)
    spec = make_specs(config)[0]
    for _ in range(steps):
        state = rk4_step(state, spec, config, dt)
    return state


def convergence_rows(duration: float = 4.0) -> list[tuple[float, float, float | None]]:
    """Return dt, final-state L2 error, and observed order for one pendulum."""
    config = WaveConfig(count=1, damping=0.0)
    reference = final_state(config, duration, REFERENCE_DT)
    rows: list[tuple[float, float, float | None]] = []
    previous_error = None
    for dt in STEP_SIZES:
        observed = final_state(config, duration, dt)
        error = math.hypot(observed.theta - reference.theta, observed.omega - reference.omega)
        order = None if previous_error is None else math.log2(previous_error / error)
        rows.append((dt, error, order))
        previous_error = error
    return rows


def convergence_report(duration: float = 4.0) -> dict[str, Any]:
    """Return the complete deterministic convergence experiment as structured data."""
    config = WaveConfig(count=1, damping=0.0)
    reference = final_state(config, duration, REFERENCE_DT)
    rows = []
    previous_error = None
    for dt in STEP_SIZES:
        observed = final_state(config, duration, dt)
        error = math.hypot(observed.theta - reference.theta, observed.omega - reference.omega)
        order = None if previous_error is None else math.log2(previous_error / error)
        rows.append({
            "dt_s": dt,
            "steps": round(duration / dt),
            "final_state": {"theta_rad": observed.theta, "omega_rad_s": observed.omega},
            "l2_error": error,
            "observed_order": order,
        })
        previous_error = error
    return {
        "schema_version": 1,
        "experiment": "rk4_final_state_convergence",
        "method": "classical_rk4",
        "duration_s": duration,
        "initial_state": {"theta_rad": config.initial_angle, "omega_rad_s": 0.0},
        "configuration": {
            "gravity_m_s2": config.gravity,
            "damping_s_inv": config.damping,
            "sync_time_s": config.sync_time,
            "base_oscillations": config.base_oscillations,
        },
        "reference": {
            "dt_s": REFERENCE_DT,
            "steps": round(duration / REFERENCE_DT),
            "final_state": {"theta_rad": reference.theta, "omega_rad_s": reference.omega},
        },
        "rows": rows,
    }


def report_json(duration: float = 4.0) -> str:
    """Serialize a report canonically for byte-repeatable evidence files."""
    return json.dumps(convergence_report(duration), indent=2, sort_keys=True, allow_nan=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=4.0)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.format == "json":
        output = report_json(args.duration)
    else:
        lines = ["| dt (s) | final-state L2 error | observed order |", "|---:|---:|---:|"]
        for dt, error, order in convergence_rows(args.duration):
            order_text = "—" if order is None else f"{order:.6f}"
            lines.append(f"| {dt:.12f} | {error:.12e} | {order_text} |")
        output = "\n".join(lines) + "\n"
    if args.output is None:
        print(output, end="")
    else:
        args.output.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
