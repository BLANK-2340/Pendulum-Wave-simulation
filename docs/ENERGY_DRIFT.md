# Undamped RK4 energy-drift evidence

This controlled experiment measures numerical energy drift for the task-owned
fixed-step RK4 integrator. It follows one undamped nonlinear pendulum for 32
seconds from the default 24-degree release angle. Mechanical energy is evaluated
after every step using unit mass.

## Reproduce and validate

```bash
python -m pendulum_wave.energy_drift
python -m pendulum_wave.evidence results/energy_drift.json
```

The committed [`energy_drift.json`](../results/energy_drift.json) is canonical,
byte-repeatable JSON. Its standalone validator rejects schema changes,
non-finite values, altered energies, drift values, step counts and
non-canonical serialization, and independently repeats every trajectory.

## Recorded result

Recorded with Python 3.12.14 on October 29, 2026:

| dt (s) | steps | final relative drift | max absolute relative drift |
|---:|---:|---:|---:|
| 0.033333333333 | 960 | -2.377632494744e-04 | 2.377632494744e-04 |
| 0.016666666667 | 1920 | -7.444887459689e-06 | 7.444887459689e-06 |
| 0.008333333333 | 3840 | -2.324666473017e-07 | 2.331840271442e-07 |
| 0.004166666667 | 7680 | -7.244659415045e-09 | 7.319656431532e-09 |

Maximum absolute relative drift decreases monotonically across these four step
sizes. Each halving reduces it by more than 20 times in this experiment. The
finest run's maximum relative drift is approximately 7.32e-9.

## Interpretation and limitations

- RK4 is not a symplectic method, so this result does not establish bounded
  long-time energy error or exact conservation.
- The evidence covers one initial angle, pendulum length, duration and undamped
  trajectory. Damped motion intentionally falls outside the conservation test.
- Floating-point behavior may vary slightly across Python implementations or
  architectures; validation uses tight numeric tolerances while canonical files
  remain byte-repeatable within one runtime.
- This is a numerical-correctness experiment, not a hardware benchmark or
  real-apparatus measurement.
