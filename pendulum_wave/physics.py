"""Testable numerical core for a reproducible, headless pendulum wave."""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Iterator, Sequence


@dataclass(frozen=True)
class WaveConfig:
    count: int = 27
    gravity: float = 9.81
    sync_time: float = 32.0
    base_oscillations: int = 25
    initial_angle: float = math.radians(24.0)
    damping: float = 0.0006

    def __post_init__(self) -> None:
        values = (self.gravity, self.sync_time, self.initial_angle, self.damping)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("configuration values must be finite")
        if not 1 <= self.count <= 10_000:
            raise ValueError("count must be in [1, 10000]")
        if self.gravity <= 0.0 or self.sync_time <= 0.0:
            raise ValueError("gravity and sync_time must be positive")
        if self.base_oscillations <= 0:
            raise ValueError("base_oscillations must be positive")
        if self.damping < 0.0:
            raise ValueError("damping must be non-negative")


@dataclass(frozen=True)
class PendulumSpec:
    index: int
    oscillations: int
    period: float
    length: float


@dataclass(frozen=True)
class State:
    theta: float
    omega: float


def make_specs(config: WaveConfig) -> tuple[PendulumSpec, ...]:
    """Build the small-angle period/length schedule used by a pendulum wave."""
    specs = []
    for index in range(config.count):
        oscillations = config.base_oscillations + index
        period = config.sync_time / oscillations
        length = config.gravity * (period / (2.0 * math.pi)) ** 2
        specs.append(PendulumSpec(index, oscillations, period, length))
    return tuple(specs)


def _derivative(state: State, spec: PendulumSpec, config: WaveConfig) -> State:
    return State(
        state.omega,
        -(config.gravity / spec.length) * math.sin(state.theta) - config.damping * state.omega,
    )


def rk4_step(state: State, spec: PendulumSpec, config: WaveConfig, dt: float) -> State:
    """Advance one independent nonlinear pendulum by one RK4 step."""
    if not math.isfinite(dt) or dt <= 0.0:
        raise ValueError("dt must be finite and positive")
    k1 = _derivative(state, spec, config)
    k2 = _derivative(State(state.theta + 0.5 * dt * k1.theta,
                           state.omega + 0.5 * dt * k1.omega), spec, config)
    k3 = _derivative(State(state.theta + 0.5 * dt * k2.theta,
                           state.omega + 0.5 * dt * k2.omega), spec, config)
    k4 = _derivative(State(state.theta + dt * k3.theta,
                           state.omega + dt * k3.omega), spec, config)
    return State(
        state.theta + dt * (k1.theta + 2.0 * k2.theta + 2.0 * k3.theta + k4.theta) / 6.0,
        state.omega + dt * (k1.omega + 2.0 * k2.omega + 2.0 * k3.omega + k4.omega) / 6.0,
    )


def energy(state: State, spec: PendulumSpec, gravity: float = 9.81) -> float:
    """Mechanical energy for unit mass, zeroed at the pendulum's lowest point."""
    if not math.isfinite(gravity) or gravity <= 0.0:
        raise ValueError("gravity must be finite and positive")
    speed = spec.length * state.omega
    return 0.5 * speed**2 + gravity * spec.length * (1.0 - math.cos(state.theta))


def simulate(config: WaveConfig, duration: float, dt: float,
             initial_states: Sequence[State] | None = None) -> Iterator[tuple[float, tuple[State, ...]]]:
    """Yield deterministic states from t=0 through the last step within duration."""
    if not math.isfinite(duration) or duration < 0.0:
        raise ValueError("duration must be finite and non-negative")
    if not math.isfinite(dt) or dt <= 0.0:
        raise ValueError("dt must be finite and positive")
    specs = make_specs(config)
    states = tuple(initial_states) if initial_states is not None else tuple(
        State(config.initial_angle, 0.0) for _ in specs
    )
    if len(states) != len(specs):
        raise ValueError("initial state count must equal pendulum count")
    if not all(math.isfinite(state.theta) and math.isfinite(state.omega) for state in states):
        raise ValueError("initial states must be finite")
    steps = math.floor(duration / dt + 1.0e-12)
    yield 0.0, states
    for step in range(1, steps + 1):
        states = tuple(rk4_step(state, spec, config, dt) for state, spec in zip(states, specs))
        yield step * dt, states
