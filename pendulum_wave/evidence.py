"""Strict validation for committed pendulum-wave numerical evidence."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from .convergence import convergence_report


DEFAULT_ARTIFACT = Path(__file__).resolve().parents[1] / "results" / "rk4_convergence.json"


def _require_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ValueError(f"{context} keys differ: expected {sorted(expected)}, got {sorted(actual)}")


def _require_number(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{context} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{context} must be finite")
    return result


def validate_report(report: Any) -> None:
    """Validate schema and independently recompute every numeric field."""
    if not isinstance(report, dict):
        raise ValueError("report must be an object")
    expected = convergence_report()
    _require_keys(report, set(expected), "report")
    if report["schema_version"] != 1:
        raise ValueError("unsupported schema_version")
    if report["experiment"] != expected["experiment"] or report["method"] != expected["method"]:
        raise ValueError("unexpected experiment identity")
    for object_name in ("initial_state", "configuration", "reference"):
        if not isinstance(report[object_name], dict):
            raise ValueError(f"{object_name} must be an object")
        _require_keys(report[object_name], set(expected[object_name]), object_name)
    rows = report["rows"]
    if not isinstance(rows, list) or len(rows) != len(expected["rows"]):
        raise ValueError("rows must contain the four prescribed refinements")
    for index, (actual_row, expected_row) in enumerate(zip(rows, expected["rows"])):
        if not isinstance(actual_row, dict):
            raise ValueError(f"rows[{index}] must be an object")
        _require_keys(actual_row, set(expected_row), f"rows[{index}]")
        if not isinstance(actual_row["final_state"], dict):
            raise ValueError(f"rows[{index}].final_state must be an object")
        _require_keys(actual_row["final_state"], set(expected_row["final_state"]),
                      f"rows[{index}].final_state")

    def compare(actual: Any, wanted: Any, path: str) -> None:
        if isinstance(wanted, dict):
            for key in wanted:
                compare(actual[key], wanted[key], f"{path}.{key}")
        elif isinstance(wanted, list):
            for index, item in enumerate(wanted):
                compare(actual[index], item, f"{path}[{index}]")
        elif wanted is None or isinstance(wanted, str):
            if actual != wanted:
                raise ValueError(f"{path} differs from recomputed value")
        elif isinstance(wanted, int):
            if isinstance(actual, bool) or actual != wanted:
                raise ValueError(f"{path} differs from recomputed value")
        else:
            value = _require_number(actual, path)
            if not math.isclose(value, wanted, rel_tol=1.0e-13, abs_tol=1.0e-15):
                raise ValueError(f"{path} differs from recomputed value")

    compare(report, expected, "report")


def validate_file(path: Path = DEFAULT_ARTIFACT) -> None:
    raw = path.read_text(encoding="utf-8")
    try:
        report = json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON constant: {value}")))
    except (json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"invalid JSON: {error}") from error
    validate_report(report)
    canonical = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if raw != canonical:
        raise ValueError("artifact is not canonical JSON")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_ARTIFACT)
    args = parser.parse_args(argv)
    try:
        validate_file(args.path)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"validated {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
