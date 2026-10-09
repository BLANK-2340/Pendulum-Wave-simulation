import csv
import math
import tempfile
from pathlib import Path
import unittest
from pendulum_wave.cli import main
from pendulum_wave.physics import State, WaveConfig, energy, make_specs, rk4_step, simulate


class PhysicsTests(unittest.TestCase):
    def test_length_schedule_matches_designed_periods(self) -> None:
        config = WaveConfig(count=27)
        specs = make_specs(config)
        self.assertTrue(all(a.length > b.length for a, b in zip(specs, specs[1:])))
        for spec in specs:
            recovered = 2.0 * math.pi * math.sqrt(spec.length / config.gravity)
            self.assertAlmostEqual(recovered, spec.period, places=14)
            self.assertAlmostEqual(spec.period * spec.oscillations, config.sync_time, places=14)

    def test_rk4_conserves_undamped_energy(self) -> None:
        config = WaveConfig(count=1, damping=0.0)
        spec = make_specs(config)[0]
        state = State(config.initial_angle, 0.0)
        initial = energy(state, spec, config.gravity)
        for _ in range(60 * 240):
            state = rk4_step(state, spec, config, 1.0 / 240.0)
        self.assertLess(abs(energy(state, spec, config.gravity) - initial) / initial, 2.0e-7)

    def test_equations_are_odd_symmetric(self) -> None:
        config = WaveConfig(count=1)
        spec = make_specs(config)[0]
        positive = rk4_step(State(0.3, -0.2), spec, config, 0.01)
        negative = rk4_step(State(-0.3, 0.2), spec, config, 0.01)
        self.assertAlmostEqual(positive.theta, -negative.theta, places=15)
        self.assertAlmostEqual(positive.omega, -negative.omega, places=15)

    def test_simulation_is_deterministic(self) -> None:
        config = WaveConfig(count=3)
        first = list(simulate(config, 0.03, 0.01))
        self.assertEqual(first, list(simulate(config, 0.03, 0.01)))
        self.assertEqual([time for time, _ in first], [0.0, 0.01, 0.02, 0.03])
        self.assertEqual(first[0][1], (State(config.initial_angle, 0.0),) * 3)

    def test_invalid_inputs_are_rejected(self) -> None:
        for kwargs in ({"count": 0}, {"gravity": 0.0}, {"sync_time": float("inf")},
                       {"base_oscillations": 0}, {"damping": -0.1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                WaveConfig(**kwargs)
        with self.assertRaises(ValueError):
            list(simulate(WaveConfig(), -1.0, 0.01))
        with self.assertRaises(ValueError):
            list(simulate(WaveConfig(), 1.0, 0.0))
        with self.assertRaises(ValueError):
            list(simulate(WaveConfig(count=2), 1.0, 0.1, [State(0.0, 0.0)]))

    def test_cli_writes_parseable_csv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "states.csv"
            self.assertEqual(main(["--count", "2", "--duration", "0.02", "--dt", "0.01",
                                   "--output", str(output)]), 0)
            with output.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(rows[0], ["time_s", "p0_theta_rad", "p0_omega_rad_s",
                                       "p1_theta_rad", "p1_omega_rad_s"])
            self.assertEqual(len(rows), 4)
            self.assertEqual([float(row[0]) for row in rows[1:]], [0.0, 0.01, 0.02])


if __name__ == "__main__":
    unittest.main()
