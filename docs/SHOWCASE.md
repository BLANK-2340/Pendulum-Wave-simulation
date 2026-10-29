# Pendulum wave showcase

This project separates a dependency-free, testable nonlinear-pendulum model from
an optional Pillow renderer. The pre-existing renderer, `main.py`, and generated
GIF remain preserved. The task-owned package adds deterministic CSV export,
state-driven rendering, a reproducible RK4 convergence study and independently
validated undamped energy-drift evidence.

## Setup and clean-checkout verification

Python 3.10 or newer is required. Pillow is needed only for rendering and the
complete showcase check.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install "Pillow>=10,<13"
./scripts/verify_showcase.sh
```

The verifier exports committed `HEAD` into a temporary directory. It runs all
fifteen tests with warnings treated as errors, compiles Python bytecode, executes
two byte-identical CSV exports, executes two byte-identical convergence reports,
executes two byte-identical structured convergence artifacts, and renders two
byte-identical energy-drift artifacts, and renders two byte-identical three-frame
GIFs. It validates both committed evidence files against independent
recomputations, then checks the CSV time grid and GIF format, dimensions and
frame count.

## Runnable targets

| Target | Command | Output and scope |
| --- | --- | --- |
| Physics tests | `python -W error -m unittest discover -s tests -v` | Schedule, RK4, energy, symmetry, validation, CLI and renderer checks |
| CSV simulation | `python -m pendulum_wave.cli --duration 4 --dt 0.008333333333333333 --output states.csv` | Deterministic angular position and velocity states |
| GIF renderer | `python -m pendulum_wave.render --duration 4 --fps 30 --substeps 4 --output wave.gif` | Pillow rendering driven only by tested physics states |
| Convergence study | `python -m pendulum_wave.convergence` | Final-state error against a finer numerical reference |
| JSON evidence | `python -m pendulum_wave.convergence --format json --output convergence.json` | Canonical, byte-repeatable experiment metadata, states, errors and orders |
| Energy-drift study | `python -m pendulum_wave.energy_drift` | Four fixed-step measurements over one 32-second undamped trajectory |
| Evidence validator | `python -m pendulum_wave.evidence` | Strict schemas and independent numeric recomputation of both committed artifacts |
| Complete verification | `./scripts/verify_showcase.sh` | Isolated committed archive plus deterministic artifacts |

## Architecture

- [`physics.py`](../pendulum_wave/physics.py) defines validated immutable
  configuration, the small-angle length schedule, nonlinear equations, RK4 step,
  energy and deterministic simulation iterator.
- [`cli.py`](../pendulum_wave/cli.py) streams states to CSV without third-party
  dependencies.
- [`render.py`](../pendulum_wave/render.py) lazily imports Pillow and maps tested
  states to image coordinates under a bounded in-memory frame budget.
- [`convergence.py`](../pendulum_wave/convergence.py) compares four step sizes
  against a `dt=1/1920 s` numerical reference.
- [`energy_drift.py`](../pendulum_wave/energy_drift.py) measures final and maximum
  relative energy drift at four fixed step sizes.

Each bob is an independent nonlinear pendulum:

`theta'' = -(g / length) sin(theta) - damping * theta'`

The default length schedule uses small-angle periods with 25 through 51 designed
oscillations over 32 seconds. Integration uses fixed-step classical RK4.

## Recorded numerical result

The checked-in [convergence report](RK4_CONVERGENCE.md) records final-state L2
errors for one smooth, undamped four-second trajectory. Halving the step size
reduced error by approximately 16 times, with observed orders `4.026925`,
`4.015949`, and `4.008923`. This supports the expected fourth-order behavior for
that controlled trajectory; it is not a universal physical-accuracy claim.
The same run is committed as
[`results/rk4_convergence.json`](../results/rk4_convergence.json); the standalone
validator rejects schema changes, non-finite values, altered step counts, states,
errors or orders, and non-canonical serialization.

The checked-in [energy-drift report](ENERGY_DRIFT.md) records maximum relative
energy drift decreasing from `2.377632494744e-4` at `dt=1/30 s` to
`7.319656431532e-9` at `dt=1/240 s` for one 32-second undamped trajectory. The
standalone validator independently repeats all four trajectories. This is scoped
numerical evidence; RK4 is not symplectic and the result is not a universal or
long-time conservation guarantee.

## Known limitations

- The designed 32-second synchronization uses a small-angle period formula; at
  the default 24-degree amplitude, nonlinear period shift prevents exact physical
  synchronization at that instant.
- The model omits string mass, airflow-dependent drag, pivot friction, coupling,
  collisions and apparatus calibration.
- The convergence reference is a finer numerical solution, not an analytical
  exact state, and covers one short trajectory.
- The energy study covers one undamped trajectory and does not establish exact
  conservation, symplectic behavior or bounded drift over arbitrarily long runs.
- GIF generation retains encoded frames in memory and is bounded to 100 million
  pixels. It is a reproducibility demo, not a rendering-performance benchmark.
- No hardware-performance or real-apparatus validation claim is made.

Next milestone: add a compact machine-readable manifest that indexes the
committed evidence artifacts, their validation commands and measured scope.
