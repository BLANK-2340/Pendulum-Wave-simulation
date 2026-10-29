"""Canonical index and validator for committed numerical evidence artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .evidence import validate_file


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "results" / "evidence_manifest.json"
ARTIFACT_SPECS = (
    {
        "path": "results/rk4_convergence.json",
        "validation_command": "python -m pendulum_wave.evidence results/rk4_convergence.json",
        "scope": {
            "duration_s": 4.0,
            "model": "one undamped nonlinear pendulum",
            "measurement": "final-state L2 error against a dt=1/1920 s numerical reference",
            "claim_limit": "controlled step-refinement result, not universal physical accuracy",
        },
    },
    {
        "path": "results/energy_drift.json",
        "validation_command": "python -m pendulum_wave.evidence results/energy_drift.json",
        "scope": {
            "duration_s": 32.0,
            "model": "one undamped nonlinear pendulum",
            "measurement": "final and maximum absolute relative mechanical-energy drift",
            "claim_limit": "fixed-duration RK4 result, not exact or long-time conservation",
        },
    },
)


def build_manifest(root: Path = REPO_ROOT) -> dict[str, Any]:
    """Read indexed artifacts and bind their identity, scope, and content hashes."""
    artifacts = []
    for spec in ARTIFACT_SPECS:
        path = root / spec["path"]
        raw = path.read_bytes()
        report = json.loads(raw)
        artifacts.append({
            "path": spec["path"],
            "sha256": hashlib.sha256(raw).hexdigest(),
            "schema_version": report["schema_version"],
            "experiment": report["experiment"],
            "validation_command": spec["validation_command"],
            "scope": dict(spec["scope"]),
        })
    return {
        "schema_version": 1,
        "project": "BLANK-2340/Pendulum-Wave-simulation",
        "artifacts": artifacts,
    }


def report_json(root: Path = REPO_ROOT) -> str:
    return json.dumps(build_manifest(root), indent=2, sort_keys=True, allow_nan=False) + "\n"


def validate_manifest(report: Any, root: Path = REPO_ROOT) -> None:
    """Validate every indexed artifact, then require an exact regenerated manifest."""
    for spec in ARTIFACT_SPECS:
        validate_file(root / spec["path"])
    if report != build_manifest(root):
        raise ValueError("manifest differs from indexed artifact metadata, scope, or hashes")


def validate_manifest_file(path: Path = DEFAULT_MANIFEST, root: Path = REPO_ROOT) -> None:
    raw = path.read_text(encoding="utf-8")
    try:
        report = json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON constant: {value}")))
    except (json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"invalid JSON: {error}") from error
    validate_manifest(report, root)
    if raw != json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n":
        raise ValueError("manifest is not canonical JSON")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args(argv)
    if args.validate:
        if args.output is not None:
            parser.error("--output cannot be combined with --validate")
        try:
            validate_manifest_file()
        except (OSError, ValueError) as error:
            parser.error(str(error))
        print(f"validated {DEFAULT_MANIFEST}")
        return 0
    output = report_json()
    if args.output is None:
        print(output, end="")
    else:
        args.output.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
