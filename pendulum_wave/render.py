"""Pillow renderer driven by the tested headless physics package."""

from __future__ import annotations
import argparse
import colorsys
import math
from pathlib import Path
from .physics import PendulumSpec, State, WaveConfig, make_specs, simulate


def bob_position(state: State, spec: PendulumSpec, pivot: tuple[float, float],
                 pixels_per_meter: float) -> tuple[float, float]:
    """Convert an angular state to image coordinates without rounding."""
    if not math.isfinite(pixels_per_meter) or pixels_per_meter <= 0.0:
        raise ValueError("pixels_per_meter must be finite and positive")
    radius = spec.length * pixels_per_meter
    return (pivot[0] + radius * math.sin(state.theta),
            pivot[1] + radius * math.cos(state.theta))


def _color(index: int, count: int) -> tuple[int, int, int]:
    red, green, blue = colorsys.hsv_to_rgb(index / max(1, count), 0.62, 1.0)
    return int(255 * red), int(255 * green), int(255 * blue)


def render_gif(output: Path, config: WaveConfig, duration: float = 4.0,
               fps: int = 30, substeps: int = 4, width: int = 960,
               height: int = 540) -> int:
    """Render a GIF and return its frame count.

    Pillow is imported lazily so the numerical core and CSV CLI remain
    dependency-free.
    """
    if not 1 <= fps <= 120 or not 1 <= substeps <= 32:
        raise ValueError("fps must be in [1,120] and substeps in [1,32]")
    if not 200 <= width <= 4096 or not 200 <= height <= 4096:
        raise ValueError("width and height must be in [200,4096]")
    if not math.isfinite(duration) or not 0.0 <= duration <= 60.0:
        raise ValueError("duration must be finite and in [0,60]")
    frame_count = math.floor(duration * fps) + 1
    if frame_count * width * height > 100_000_000:
        raise ValueError("render exceeds the 100-million-pixel in-memory safety limit")
    try:
        from PIL import Image, ImageDraw
    except ImportError as error:
        raise RuntimeError("GIF rendering requires Pillow: python -m pip install Pillow") from error

    specs = make_specs(config)
    pivot_y = max(24, height // 9)
    margin_x = max(24, width // 16)
    spacing = 0.0 if config.count == 1 else (width - 2 * margin_x) / (config.count - 1)
    pivots = tuple((margin_x + index * spacing, float(pivot_y)) for index in range(config.count))
    scale = (height - pivot_y - 30) / max(spec.length for spec in specs)
    frames = []
    dt = 1.0 / (fps * substeps)
    for step, (time_s, states) in enumerate(simulate(config, duration, dt)):
        if step % substeps:
            continue
        image = Image.new("RGB", (width, height), (8, 12, 28))
        draw = ImageDraw.Draw(image)
        draw.line((margin_x - 12, pivot_y, width - margin_x + 12, pivot_y),
                  fill=(180, 190, 215), width=3)
        positions = []
        for index, (state, spec, pivot) in enumerate(zip(states, specs, pivots)):
            bob = bob_position(state, spec, pivot, scale)
            positions.append(bob)
            color = _color(index, config.count)
            draw.line((pivot[0], pivot[1], bob[0], bob[1]), fill=(135, 145, 170), width=1)
            draw.ellipse((bob[0] - 6, bob[1] - 6, bob[0] + 6, bob[1] + 6), fill=color)
        if len(positions) > 1:
            draw.line(positions, fill=(100, 210, 255), width=2)
        draw.text((12, 12), f"t={time_s:.2f}s", fill=(225, 232, 248))
        frames.append(image)
    output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(output, save_all=True, append_images=frames[1:],
                   duration=round(1000 / fps), loop=0, optimize=False)
    return len(frames)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("headless_pendulum_wave.gif"))
    parser.add_argument("--duration", type=float, default=4.0)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--substeps", type=int, default=4)
    parser.add_argument("--count", type=int, default=27)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    args = parser.parse_args(argv)
    frames = render_gif(args.output, WaveConfig(count=args.count), args.duration,
                        args.fps, args.substeps, args.width, args.height)
    print(f"wrote {frames} frames to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
