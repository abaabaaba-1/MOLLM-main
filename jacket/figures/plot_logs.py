"""
Plot optimization logs for SACS jacket/platform experiments.

特点：
- 递归读取指定目录下的 JSON 日志（默认：moo_results/zgca,gemini-2.5-flash-nothinking）。
- 自动从文件名或参数中推断问题（geo_jk/geo_pf/section_jk/section_pf）与算法标签。
- 支持两种日志结构：
  1) {"results": [ ... ]} 格式（含 hypervolume/avg_top* 等字段）
  2) {"metrics_timeline": [ ... ]} 格式（MOEA/D）
- 可选择指标（默认 hypervolume, avg_top1, avg_top10, avg_top100），并对每个问题绘制所有算法/种子的曲线。
- 新增/补全数据后，只需将 JSON 放入数据目录再次运行脚本即可。

使用示例：
    python plot_logs.py \
        --data-root ../../moo_results/zgca,gemini-2.5-flash-nothinking \
        --output-dir ./outputs \
        --metrics hypervolume avg_top1

可选：如果把日志按问题分为四个子目录（geo_jk/geo_pf/section_jk/section_pf），
可以加 --problem-subdirs 直接使用子目录名作为问题标签。
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import matplotlib

# headless 环境使用 Agg
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np


# 问题名与关键词映射，便于从文件名/参数推断
PROBLEM_HINTS = {
    "section_jk": ("section_jk", "sacs_section_jk", "Demo06_Section", "sacs_expanded_3_obj"),
    "section_pf": ("section_pf", "sacs_section_pf", "Demo13_Section"),
    "geo_jk": ("geo_jk", "sacs_geo_jk", "Demo06_Geo"),
    "geo_pf": ("geo_pf", "sacs_geo_pf", "Demo13_Geo"),
}

# 算法关键词映射（文件名或 params 文本中包含的子串）
# 按优先级从具体基线到通用 OJOLLM 匹配，避免基线被误判为 ojollm
ALGO_HINTS = [
    ("sms", ("baseline_smsemoa", "smsemoa", "sms")),
    ("moead", ("baseline_moead", "moead")),
    ("nsga2", ("baseline_nsga2", "nsga2")),
    ("ga", ("baseline_ga", "_ga_")),
    ("rs", ("baseline_rs", "_rs_")),
    ("ojollm", ("mollm", "llm", "ojollm", "sacs_expanded_3_obj_", "sacs_geo_", "sacs_section_", "demo06_geo", "demo06_section", "demo13_geo", "demo13_section")),
]


@dataclass
class RunEntry:
    problem: str
    algo: str
    seed: Optional[int]
    path: Path
    steps: List[dict]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot MOO logs (hypervolume etc.)")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("../../moo_results/zgca,gemini-2.5-flash-nothinking"),
        help="日志根目录（会递归搜索 JSON）",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./outputs"),
        help="图片与汇总保存目录（默认 jacket/figures/outputs）",
    )
    parser.add_argument(
        "--metrics",
        nargs="+",
        default=["hypervolume", "avg_top1", "avg_top10", "avg_top100"],
        help="需要绘制的指标名",
    )
    parser.add_argument(
        "--problem-subdirs",
        action="store_true",
        help="若数据根目录下已按问题划分子目录，则直接用子目录名作为问题标签",
    )
    return parser.parse_args()


def load_json(path: Path) -> Optional[dict]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] 读取失败 {path}: {exc}")
        return None


def infer_problem(path: Path, data: dict, use_subdir: bool) -> str:
    if use_subdir:
        candidate = path.parent.name.lower()
        for prob, hints in PROBLEM_HINTS.items():
            if candidate in hints:
                return prob
        return candidate

    source = path.name.lower() + " " + json.dumps(data)[:2000].lower()
    for prob, hints in PROBLEM_HINTS.items():
        if any(hint.lower() in source for hint in hints):
            return prob
    return "unknown"


def infer_algo(path: Path, data: dict) -> str:
    text = path.name.lower()
    # 追加 params/config 内容用于匹配
    for key in ("params", "config"):
        if isinstance(data.get(key), (str, dict)):
            try:
                snippet = data[key]
                if isinstance(snippet, dict):
                    snippet = json.dumps(snippet)
                text += " " + snippet.lower()
            except Exception:
                pass
    for algo, hints in ALGO_HINTS:
        if any(h.lower() in text for h in hints):
            return algo
    return "unknown"


def infer_seed(path: Path) -> Optional[int]:
    # 解析类似 *_42.json 的种子
    match = re.search(r"_(\d+)\.json$", path.name)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def extract_steps(data: dict) -> Optional[List[dict]]:
    if isinstance(data, dict):
        if isinstance(data.get("results"), list):
            return data["results"]
        if isinstance(data.get("metrics_timeline"), list):
            return data["metrics_timeline"]
    return None


def iter_runs(data_root: Path, use_subdir: bool) -> Iterable[RunEntry]:
    for path in data_root.rglob("*.json"):
        data = load_json(path)
        if not data:
            continue
        steps = extract_steps(data)
        if not steps:
            continue

        run = RunEntry(
            problem=infer_problem(path, data, use_subdir),
            algo=infer_algo(path, data),
            seed=infer_seed(path),
            path=path,
            steps=steps,
        )
        yield run


def get_axis(run_step: dict) -> Tuple[Optional[float], Optional[float]]:
    """返回 (x, hv)；x 优先 evaluations > generated_num > all_unique_moles > Training_step > 索引"""
    x_candidates = [
        run_step.get("evaluations"),
        run_step.get("generated_num"),
        run_step.get("all_unique_moles"),
        run_step.get("Training_step"),
    ]
    x = next((v for v in x_candidates if isinstance(v, (int, float))), None)
    return x, None


def plot_metric(runs: List[RunEntry], metric: str, output_dir: Path) -> None:
    # 保留函数占位，如需单跑曲线可启用；当前需求仅使用聚合图，不输出单跑曲线
    return


def aggregate_and_plot(prob_runs: List[RunEntry], metric: str, output_dir: Path) -> None:
    """按问题+算法聚合，计算均值/标准差并绘制阴影带；保存 CSV。"""
    if not prob_runs:
        return
    algo_groups: Dict[str, List[RunEntry]] = {}
    for r in prob_runs:
        algo_groups.setdefault(r.algo, []).append(r)

    output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    csv_lines = ["algo,x,mean,std,count"]

    for algo, runs in sorted(algo_groups.items()):
        # 聚合同一算法的多次运行
        x_to_vals: Dict[float, List[float]] = {}
        for run in runs:
            best_so_far: Optional[float] = None
            for idx, step in enumerate(run.steps):
                x, _ = get_axis(step)
                x = float(x if x is not None else idx)
                y = step.get(metric)
                if y is None:
                    continue
                # “report迭代到现在最好的”：采用最大值的累计最优（HV/avg_top* 等为越大越好）
                best_so_far = y if best_so_far is None else max(best_so_far, y)
                x_to_vals.setdefault(x, []).append(float(best_so_far))

        if not x_to_vals:
            continue
        xs = sorted(x_to_vals.keys())
        means = []
        stds = []
        counts = []
        for x in xs:
            vals = np.array(x_to_vals[x], dtype=float)
            means.append(np.mean(vals))
            stds.append(np.std(vals))
            counts.append(len(vals))
            csv_lines.append(f"{algo},{x},{means[-1]},{stds[-1]},{counts[-1]}")

        ax.plot(xs, means, label=f"{algo} (n={len(runs)})")
        ax.fill_between(xs, np.array(means) - np.array(stds), np.array(means) + np.array(stds), alpha=0.2)

    ax.set_xlabel("evaluation / step index")
    ax.set_ylabel(f"{metric} (mean ± std)")
    ax.set_title(f"{prob_runs[0].problem} - {metric} (aggregated)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out_png = output_dir / f"{prob_runs[0].problem}_{metric}_agg.png"
    fig.savefig(out_png, dpi=200)
    plt.close(fig)
    print(f"[SAVE] {out_png}")

    out_csv = output_dir / f"{prob_runs[0].problem}_{metric}_agg.csv"
    out_csv.write_text("\n".join(csv_lines), encoding="utf-8")
    print(f"[SAVE] {out_csv}")


def summarize(runs: List[RunEntry], metrics: List[str], output_dir: Path) -> None:
    problem_groups: Dict[str, Dict[str, List[RunEntry]]] = {}
    for run in runs:
        problem_groups.setdefault(run.problem, {}).setdefault(run.algo, []).append(run)

    summary_lines: List[str] = []
    for prob, algos in sorted(problem_groups.items()):
        summary_lines.append(f"Problem: {prob}")
        for algo, algo_runs in sorted(algos.items()):
            seeds = [r.seed for r in algo_runs if r.seed is not None]
            summary_lines.append(
                f"  Algo={algo}, runs={len(algo_runs)}, seeds={seeds if seeds else 'N/A'}, sample_file={algo_runs[0].path.name}"
            )
        summary_lines.append("")

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.txt"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"[SAVE] {summary_path}")

    # 绘图
    for prob, algos in problem_groups.items():
        prob_runs = [r for rs in algos.values() for r in rs]
        for metric in metrics:
            aggregate_and_plot(prob_runs, metric, output_dir)


def main() -> None:
    args = parse_args()
    runs = list(iter_runs(args.data_root, args.problem_subdirs))
    if not runs:
        print(f"[WARN] 未找到可用日志，检查路径：{args.data_root}")
        return

    summarize(runs, args.metrics, args.output_dir)


if __name__ == "__main__":
    main()
