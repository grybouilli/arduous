#!/usr/bin/env python3
"""Plot a latency / quality Pareto front from several experiments.

Expected layout:
  F/folder_exp_A/metrics.csv
  F/folder_exp_B/metrics.csv
  ...

metrics.csv columns:
  file_id, min latency, mean latency, median latency, max latency,
  s1 si-sdr, s2 si-sdr

For each experiment:
  * x = latency in ms (aggregate of the per-file latency column, see --latency_stat)
  * y = negative SI-SDR in dB (lower is better); drawn as a violin over the
    per-utterance SI-SDR (mean of s1 and s2), with a marker at the mean.
The Pareto front (lower-left is better) is computed on (latency, mean -SI-SDR).
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

LATENCY_COLS = {
    "min": "min latency",
    "mean": "mean latency",
    "median": "median latency",
    "max": "max latency",
}


def load_experiments(root: Path, latency_stat: str, utt_stat: str, exp_hw : str | None = None):
    """Return a list of dicts: name, latency, neg_sisdr (array)."""
    exps = []
    for csv_path in sorted(root.glob(f"*{"" if exp_hw is None else f"_{exp_hw}"}/metrics.csv")):
        df = pd.read_csv(csv_path)
        if df.empty:
            print(f"[skip] empty {csv_path}")
            continue
        lat_col = LATENCY_COLS[latency_stat]
        # Aggregate latency over utterances (one value per experiment)
        lat = df[lat_col].mean() if utt_stat == "mean" else df[lat_col].median()
        sisdr = (df["s1 si-sdr"] + df["s2 si-sdr"]) / 2.0  # per-utterance score
        exps.append(
            {
                "name": csv_path.parent.name,
                "latency": float(lat),
                "neg_sisdr": -sisdr.to_numpy(),
            }
        )
    return exps


def pareto_front(points):
    """Indices of non-dominated points (minimise both coordinates), sorted by x."""
    idx = []
    for i, (xi, yi) in enumerate(points):
        dominated = any(
            (xj <= xi and yj <= yi) and (xj < xi or yj < yi)
            for j, (xj, yj) in enumerate(points)
            if j != i
        )
        if not dominated:
            idx.append(i)
    return sorted(idx, key=lambda i: points[i][0])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("folder", type=Path, help="Folder F containing <exp>/metrics.csv")
    p.add_argument("--out", type=Path, default=Path("pareto.png"), help="Output image")
    p.add_argument("--hw", type=str, default=None, help="Target hardware")
    p.add_argument(
        "--latency_stat",
        choices=list(LATENCY_COLS),
        default="mean",
        help="Which per-file latency column to use for the x axis",
    )
    p.add_argument(
        "--utt_stat",
        choices=["mean", "median"],
        default="mean",
        help="How to aggregate the per-file latency values across utterances",
    )
    p.add_argument(
        "--plot_type",
        choices=["violin", "box"],
        default="violin",
        help="Distribution plot drawn for each experiment",
    )
    p.add_argument("--show", action="store_true", help="Display the plot interactively")
    args = p.parse_args()

    exps = load_experiments(args.folder, args.latency_stat, args.utt_stat, args.hw)
    if not exps:
        print(f"No {args.folder}/*/metrics.csv found.")
        return

    xs = np.array([e["latency"] for e in exps])
    means = np.array([e["neg_sisdr"].mean() for e in exps])

    # Violin width in data units (fraction of the x range)
    span = xs.max() - xs.min()
    width = 0.06 * span if span > 0 else 1.0

    fig, ax = plt.subplots(figsize=(9, 6))
    cmap = plt.get_cmap("tab10")

    for i, e in enumerate(exps):
        color = cmap(i % 10)
        if args.plot_type == "violin":
            parts = ax.violinplot(
                e["neg_sisdr"],
                positions=[e["latency"]],
                widths=width,
                showmeans=False,
                showmedians=False,
                showextrema=False,
            )
            for body in parts["bodies"]:
                body.set_facecolor(color)
                body.set_edgecolor(color)
                body.set_alpha(0.35)
        else:
            bp = ax.boxplot(
                e["neg_sisdr"],
                positions=[e["latency"]],
                widths=width,
                patch_artist=True,
            )
            for box in bp["boxes"]:
                box.set_facecolor(color)
                box.set_edgecolor(color)
                box.set_alpha(0.35)
            for key in ("whiskers", "caps"):
                for line in bp[key]:
                    line.set_color(color)
            for line in bp["medians"]:
                line.set_color(color)
                line.set_linewidth(1.8)
            for flier in bp["fliers"]:
                flier.set_markeredgecolor(color)
                flier.set_markersize(3)
        ax.scatter(
            e["latency"],
            means[i],
            color=color,
            edgecolor="k",
            zorder=3,
            s=40,
            label=e["name"],
        )
        ax.annotate(
            e["name"],
            (e["latency"], means[i]),
            textcoords="offset points",
            xytext=(8, 8),
            fontsize=9,
            color=color,
        )

    # Pareto front on the mean points
    front = pareto_front(list(zip(xs, means)))
    ax.step(
        xs[front],
        means[front],
        where="post",
        color="k",
        linestyle="--",
        linewidth=1.2,
        zorder=2,
        label="Pareto front (means)",
    )

    ax.set_xlabel(f"Latency [ms] ({args.latency_stat} latency)")
    ax.set_ylabel("Negative SI-SDR [dB] (lower is better)")
    ax.set_title("Latency vs. quality Pareto front")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(args.out, dpi=200)
    print(f"Saved plot to {args.out}")
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
