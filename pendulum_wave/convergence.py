"""Reproducible RK4 step-size convergence report."""

from __future__ import annotations
import argparse
import math
from .physics import State, WaveConfig, make_specs, rk4_step


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
    reference = final_state(config, duration, 1.0 / 1920.0)
    rows: list[tuple[float, float, float | None]] = []
    previous_error = None
    for dt in (1.0 / 30.0, 1.0 / 60.0, 1.0 / 120.0, 1.0 / 240.0):
        observed = final_state(config, duration, dt)
        error = math.hypot(observed.theta - reference.theta, observed.omega - reference.omega)
        order = None if previous_error is None else math.log2(previous_error / error)
        rows.append((dt, error, order))
        previous_error = error
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=4.0)
    args = parser.parse_args(argv)
    print("| dt (s) | final-state L2 error | observed order |")
    print("|---:|---:|---:|")
    for dt, error, order in convergence_rows(args.duration):
        order_text = "—" if order is None else f"{order:.6f}"
        print(f"| {dt:.12f} | {error:.12e} | {order_text} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
