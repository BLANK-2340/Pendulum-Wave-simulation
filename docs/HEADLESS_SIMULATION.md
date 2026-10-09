# Headless pendulum-wave physics

This dependency-free Python module complements the existing Pillow renderer. It
does not alter `pendulum_wave_render.py`, `main.py`, or the existing GIF.

## Run the checks

```sh
python -m unittest discover -s tests -v
```

The tests verify the designed small-angle period schedule, decreasing lengths,
undamped energy conservation over 60 simulated seconds, odd symmetry,
deterministic sampling, input validation, and an end-to-end CSV export.

## Export a simulation

```sh
python -m pendulum_wave.cli --duration 4 --dt 0.008333333333333333 --output states.csv
python -m pendulum_wave.cli --count 5 --duration 0.02 --dt 0.01
```

The default configuration mirrors the existing renderer: 27 pendulums, a
32-second design synchronization time, oscillation counts 25 through 51, a
24-degree initial displacement, gravity 9.81 m/s², and angular damping 0.0006 s⁻¹.

## Model and limitations

Each bob is an independent nonlinear simple pendulum:

`theta'' = -(g / length) sin(theta) - damping * theta'`

The solver is fixed-step classical fourth-order Runge--Kutta. Lengths use the
small-angle period formula so integer oscillation counts align at the design time.
At the default 24-degree amplitude, nonlinear period shift means the wave does not
synchronize perfectly at exactly 32 seconds. String mass, air-flow-dependent drag,
pivot friction, collisions, and coupling are omitted. This is an educational,
deterministic simulation rather than a calibrated physical experiment.

## Validation and continuity — October 9, 2026

- Added a standard-library physics core and CSV CLI without modifying the
  pre-existing renderer or generated asset.
- Python 3.12.14 locally passed all six `unittest` cases, bytecode compilation,
  and a byte-for-byte repeatability check for two independently exported CSVs.
  Published CI status is reported with the associated commit; no unmeasured
  physical-accuracy claim is made.
- Next milestone: connect the renderer to the tested physics package through a new
  optional entry point, then add a reproducible convergence report.
