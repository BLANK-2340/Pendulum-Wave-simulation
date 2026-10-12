# RK4 convergence check

This experiment checks the numerical order of the task-owned fixed-step RK4
integrator in `pendulum_wave.physics`. It is a correctness study, not a
performance benchmark.

## Reproduce

```bash
python -m pendulum_wave.convergence
```

The experiment integrates one undamped pendulum for 4 seconds from
`theta = 0.7 rad` and `omega = 0 rad/s`. The reference final state uses
`dt = 1/1920 s`. Each row compares a coarser final state with that reference
using the L2 norm over `(theta, omega)`. Observed order is
`log2(error_previous / error_current)`.

## Recorded result

Recorded with Python 3.12.14 on October 12, 2026:

| dt (s) | final-state L2 error | observed order |
|---:|---:|---:|
| 0.033333333333 | 1.951322111831e-04 | — |
| 0.016666666667 | 1.197026074343e-05 | 4.026925 |
| 0.008333333333 | 7.399160205468e-07 | 4.015949 |
| 0.004166666667 | 4.595960274311e-08 | 4.008923 |

Halving the time step reduces the final-state error by approximately 16x,
which is the expected behavior for a fourth-order method in this regime.
The bundled test requires monotonically decreasing errors and an observed
order greater than 3.8 for every refinement.

## Limitations

- The fine-step solution is a numerical reference, not a closed-form exact
  solution.
- This short, smooth, undamped trajectory does not characterize every initial
  condition, damping regime, or long-time energy behavior.
- Floating-point roundoff eventually limits refinement studies; the selected
  steps remain well above that floor in the recorded run.
