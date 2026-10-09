"""Dependency-free pendulum-wave physics utilities."""

from .physics import PendulumSpec, State, WaveConfig, energy, make_specs, rk4_step, simulate

__all__ = ["PendulumSpec", "State", "WaveConfig", "energy", "make_specs", "rk4_step", "simulate"]
