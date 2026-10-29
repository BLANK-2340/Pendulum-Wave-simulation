import csv
import json
import math
import tempfile
from pathlib import Path
import unittest
from pendulum_wave.cli import main
from pendulum_wave.convergence import convergence_report, convergence_rows, report_json
from pendulum_wave.evidence import (DEFAULT_ARTIFACT, DEFAULT_ENERGY_ARTIFACT,
                                    validate_energy_report, validate_file, validate_report)
from pendulum_wave.energy_drift import energy_drift_report, report_json as energy_report_json
from pendulum_wave.physics import State, WaveConfig, energy, make_specs, rk4_step, simulate
from pendulum_wave.render import bob_position, render_gif


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
        with self.assertRaises(ValueError):
            render_gif(Path("unused.gif"), WaveConfig(), fps=0)
        with self.assertRaises(ValueError):
            render_gif(Path("unused.gif"), WaveConfig(), duration=60.0, fps=120,
                       width=4096, height=4096)
        with self.assertRaises(ValueError):
            convergence_rows(0.0)

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

    def test_renderer_geometry_and_gif(self) -> None:
        config = WaveConfig(count=1)
        spec = make_specs(config)[0]
        x, y = bob_position(State(0.0, 0.0), spec, (10.0, 20.0), 100.0)
        self.assertAlmostEqual(x, 10.0)
        self.assertAlmostEqual(y, 20.0 + spec.length * 100.0)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "wave.gif"
            frames = render_gif(output, WaveConfig(count=3), duration=0.2,
                                fps=10, substeps=2, width=320, height=240)
            self.assertEqual(frames, 3)
            self.assertGreater(output.stat().st_size, 100)
            self.assertEqual(output.read_bytes()[:6], b"GIF89a")

    def test_rk4_shows_fourth_order_convergence(self) -> None:
        rows = convergence_rows()
        errors = [row[1] for row in rows]
        self.assertTrue(all(coarse > fine for coarse, fine in zip(errors, errors[1:])))
        for _, _, order in rows[1:]:
            self.assertIsNotNone(order)
            self.assertGreater(order, 3.8)

    def test_committed_convergence_evidence_is_canonical_and_recomputed(self) -> None:
        validate_file(DEFAULT_ARTIFACT)
        report = json.loads(DEFAULT_ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(report["experiment"], "rk4_final_state_convergence")

    def test_convergence_evidence_rejects_corruption(self) -> None:
        mutations = []
        extra_key = convergence_report()
        extra_key["unexpected"] = True
        mutations.append(extra_key)
        wrong_error = convergence_report()
        wrong_error["rows"][2]["l2_error"] *= 2.0
        mutations.append(wrong_error)
        wrong_steps = convergence_report()
        wrong_steps["reference"]["steps"] += 1
        mutations.append(wrong_steps)
        non_finite = convergence_report()
        non_finite["rows"][0]["l2_error"] = float("nan")
        mutations.append(non_finite)
        for report in mutations:
            with self.subTest(report=report), self.assertRaises(ValueError):
                validate_report(report)

    def test_json_cli_payload_is_parseable_and_complete(self) -> None:
        report = json.loads(report_json())
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["method"], "classical_rk4")
        self.assertEqual(len(report["rows"]), 4)
        self.assertTrue(all(row["steps"] > 0 for row in report["rows"]))

    def test_energy_drift_decreases_with_step_refinement(self) -> None:
        rows = energy_drift_report()["rows"]
        drifts = [row["max_abs_relative_drift"] for row in rows]
        self.assertTrue(all(coarse > fine for coarse, fine in zip(drifts, drifts[1:])))
        self.assertTrue(all(coarse / fine > 20.0 for coarse, fine in zip(drifts, drifts[1:])))

    def test_committed_energy_evidence_is_canonical_and_recomputed(self) -> None:
        validate_file(DEFAULT_ENERGY_ARTIFACT)
        report = json.loads(DEFAULT_ENERGY_ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(report["experiment"], "rk4_undamped_energy_drift")

    def test_energy_evidence_rejects_corruption(self) -> None:
        mutations = []
        wrong_drift = energy_drift_report()
        wrong_drift["rows"][1]["max_abs_relative_drift"] *= 2.0
        mutations.append(wrong_drift)
        wrong_energy = energy_drift_report()
        wrong_energy["rows"][3]["final_energy_j_per_kg"] = float("inf")
        mutations.append(wrong_energy)
        extra_key = energy_drift_report()
        extra_key["configuration"]["unexpected"] = 1
        mutations.append(extra_key)
        for report in mutations:
            with self.subTest(report=report), self.assertRaises(ValueError):
                validate_energy_report(report)

    def test_energy_json_payload_is_parseable_and_complete(self) -> None:
        report = json.loads(energy_report_json())
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["configuration"]["damping_s_inv"], 0.0)
        self.assertEqual(len(report["rows"]), 4)


if __name__ == "__main__":
    unittest.main()
