#!/usr/bin/env python3
"""
Utility script to render publication-ready convergence plots from vmec.json.

Example:
    python plot_vmec_convergence.py \
        --input moo_results/zgca,gemini-2.5-flash-nothinking/results/vmec.json \
        --output-dir generated_plots \
        --metrics hypervolume avg_top1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise SystemExit(
        "This script requires Pillow. Install it via `pip install pillow`."
    ) from exc


if hasattr(Image, "Resampling"):
    LANCZOS = Image.Resampling.LANCZOS
    BICUBIC = Image.Resampling.BICUBIC
else:  # Pillow < 10 fallback
    LANCZOS = Image.LANCZOS
    BICUBIC = Image.BICUBIC


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render convergence plots (PNG) for metrics stored in a vmec.json file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("moo_results/zgca,gemini-2.5-flash-nothinking/results/vmec.json"),
        help="Path to vmec.json that contains a `results` array.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Directory where PNG files will be written.",
    )
    parser.add_argument(
        "--metrics",
        nargs="+",
        default=("hypervolume", "avg_top1"),
        help="Metric keys to plot. Each metric produces one PNG.",
    )
    parser.add_argument(
        "--title-prefix",
        default="VMEC",
        help="Prefix to add to each figure title.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1200,
        help="Output width in pixels (before DPI scaling).",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Output height in pixels (before DPI scaling).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="PNG resolution metadata.",
    )
    return parser.parse_args()


def load_results(path: Path) -> Sequence[Dict]:
    data = json.loads(path.read_text())
    try:
        return data["results"]
    except KeyError as exc:  # pragma: no cover - sanity guard
        raise SystemExit(f"{path} does not contain a `results` list.") from exc


def choose_font(size: int) -> ImageFont.FreeTypeFont:
    # Prefer DejaVu Sans (widely available); fall back to default if missing.
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def draw_rotated_text(
    canvas: Image.Image,
    center: Tuple[float, float],
    text: str,
    font: ImageFont.ImageFont,
    fill: Tuple[int, int, int],
    padding: int,
) -> None:
    bbox = font.getbbox(text)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    pad = max(padding, 10)
    tmp = Image.new("RGBA", (width + pad, height + pad), (0, 0, 0, 0))
    tmp_draw = ImageDraw.Draw(tmp)
    tmp_draw.text(
        ((width + pad) / 2, (height + pad) / 2),
        text,
        font=font,
        fill=fill,
        anchor="mm",
    )
    rotated = tmp.rotate(90, expand=True, resample=BICUBIC)
    x0 = int(center[0] - rotated.width / 2)
    y0 = int(center[1] - rotated.height / 2)
    canvas.paste(rotated, (x0, y0), rotated)


def render_chart(
    steps: Sequence[int],
    values: Sequence[float],
    metric: str,
    title_prefix: str,
    size: Tuple[int, int],
    dpi: int,
    color: Tuple[int, int, int],
    output: Path,
) -> None:
    width, height = size
    scale = 2  # render high-res then downsample for crisp text
    base_w, base_h = width * scale, height * scale
    margin_left, margin_right = 190 * scale, 130 * scale
    margin_top, margin_bottom = 150 * scale, 160 * scale
    plot_w = base_w - margin_left - margin_right
    plot_h = base_h - margin_top - margin_bottom

    img = Image.new("RGB", (base_w, base_h), "white")
    draw = ImageDraw.Draw(img)

    font_title = choose_font(46 * scale)
    font_label = choose_font(34 * scale)
    font_tick = choose_font(26 * scale)

    vmin = min(values)
    vmax = max(values)
    if abs(vmax - vmin) < 1e-9:
        vmax = vmin + 1e-6
    span = vmax - vmin
    pad = max(span * 0.08, 1e-4)
    vmax += pad
    vmin -= pad * 0.4

    def x_coord(idx: int) -> int:
        if len(values) == 1:
            return margin_left + plot_w // 2
        return margin_left + int(idx / (len(values) - 1) * plot_w)

    def y_coord(val: float) -> int:
        ratio = (val - vmin) / (vmax - vmin)
        return margin_top + plot_h - int(ratio * plot_h)

    grid_color = (215, 215, 215)
    axis_color = (50, 50, 50)

    # horizontal grid and y ticks
    tick_count = 6
    for i in range(tick_count):
        val = vmin + i * (vmax - vmin) / (tick_count - 1)
        y = y_coord(val)
        draw.line(
            [(margin_left, y), (margin_left + plot_w, y)],
            fill=grid_color,
            width=2,
        )
        draw.text(
            (margin_left - 40 * scale, y),
            f"{val:.4f}",
            font=font_tick,
            fill=axis_color,
            anchor="ra",
        )

    # axes
    draw.line(
        [(margin_left, margin_top), (margin_left, margin_top + plot_h)],
        fill=axis_color,
        width=5,
    )
    draw.line(
        [(margin_left, margin_top + plot_h), (margin_left + plot_w, margin_top + plot_h)],
        fill=axis_color,
        width=5,
    )

    # x ticks
    step_gap = max(1, len(steps) // 8)
    for idx in range(0, len(steps), step_gap):
        x = x_coord(idx)
        draw.line(
            [(x, margin_top + plot_h), (x, margin_top + plot_h + 14 * scale)],
            fill=axis_color,
            width=3,
        )
        draw.text(
            (x, margin_top + plot_h + 18 * scale),
            str(steps[idx]),
            font=font_tick,
            fill=axis_color,
            anchor="ma",
        )
    if (len(steps) - 1) % step_gap != 0:
        x = x_coord(len(steps) - 1)
        draw.line(
            [(x, margin_top + plot_h), (x, margin_top + plot_h + 14 * scale)],
            fill=axis_color,
            width=3,
        )
        draw.text(
            (x, margin_top + plot_h + 18 * scale),
            str(steps[-1]),
            font=font_tick,
            fill=axis_color,
            anchor="ma",
        )

    # metric line
    points = [(x_coord(i), y_coord(v)) for i, v in enumerate(values)]
    draw.line(points, fill=color, width=6 * scale, joint="curve")
    last_x, last_y = points[-1]
    draw.ellipse(
        (last_x - 7 * scale, last_y - 7 * scale, last_x + 7 * scale, last_y + 7 * scale),
        fill=color,
    )
    label_text = f"{values[-1]:.4f}"
    text_width = font_tick.getlength(label_text)
    max_right = margin_left + plot_w - 10 * scale
    if last_x + 20 * scale + text_width > max_right:
        anchor = "rm"
        text_x = max(last_x - 20 * scale, margin_left + text_width + 5 * scale)
    else:
        anchor = "lm"
        text_x = last_x + 20 * scale
    label_y = last_y - 18 * scale
    if label_y < margin_top + 10 * scale:
        label_y = last_y + 18 * scale
    draw.text((text_x, label_y), label_text, font=font_tick, fill=color, anchor=anchor)

    # titles and labels
    readable_metric = metric.replace("_", " ").strip()
    title_metric = readable_metric.title()
    draw.text(
        (margin_left + plot_w // 2, margin_top - 80 * scale),
        f"{title_prefix} {title_metric} Convergence",
        font=font_title,
        fill=(0, 0, 0),
        anchor="ma",
    )
    draw.text(
        (margin_left + plot_w // 2, margin_top + plot_h + 70 * scale),
        "Iteration",
        font=font_label,
        fill=axis_color,
        anchor="ma",
    )
    draw_rotated_text(
        img,
        (margin_left - 150 * scale, margin_top + plot_h / 2),
        title_metric,
        font_label,
        axis_color,
        padding=80 * scale,
    )

    final = img.resize((width, height), LANCZOS)
    final.save(output, dpi=(dpi, dpi))


def main() -> None:
    args = parse_args()
    results = load_results(args.input)
    steps = list(range(1, len(results) + 1))
    args.output_dir.mkdir(parents=True, exist_ok=True)

    palette = [
        (33, 113, 181),
        (214, 39, 40),
        (44, 160, 44),
        (255, 127, 14),
        (148, 103, 189),
    ]

    available_keys = results[0].keys() if results else []
    for idx, metric in enumerate(args.metrics):
        if metric not in available_keys:
            raise SystemExit(f"Metric `{metric}` not found in {args.input}.")
        values = [item[metric] for item in results]
        color = palette[idx % len(palette)]
        output = args.output_dir / f"{Path(args.input).stem}_{metric}.png"
        render_chart(
            steps=steps,
            values=values,
            metric=metric,
            title_prefix=args.title_prefix,
            size=(args.width, args.height),
            dpi=args.dpi,
            color=color,
            output=output,
        )
        print(f"Saved {metric} plot to {output}")


if __name__ == "__main__":  # pragma: no cover
    main()
