#!/usr/bin/env python3
"""Compute PIT SI-SDR between separated outputs and LibriMix references.

Layout:
  est_dir/<id>/output_channel_0.wav
  est_dir/<id>/output_channel_1.wav
  est_dir/<id>/latencies.npy
  ref_dir/s1/<id>.wav
  ref_dir/s2/<id>.wav

CSV columns:
  file_id, min latency, mean latency, median latency, max latency,
  s1 si-sdr, s2 si-sdr
"""

import argparse
import csv
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torchaudio.functional as AF
from torchmetrics.functional.audio import (
    permutation_invariant_training,
    pit_permutate,
    scale_invariant_signal_distortion_ratio,
)
from tqdm import tqdm


def load_wav(path, target_sr=None):
    wav, sr = sf.read(str(path), dtype="float32", always_2d=True)
    wav = torch.from_numpy(wav[:, 0])  # mono (first channel)
    if target_sr is not None and sr != target_sr:
        wav = AF.resample(wav, sr, target_sr)
        sr = target_sr
    return wav, sr


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "est_dir", type=Path, help="Folder with <id>/output_channel_[0-1].wav"
    )
    p.add_argument("ref_dir", type=Path, help="LibriMix folder containing s1/ and s2/")
    p.add_argument(
        "--csv", type=Path, default=Path("metrics.csv"), help="CSV output path"
    )
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument(
        "--stream_delay",
        type=int,
        help="Streamable model sample delay in comparison to offline",
        default=32,
    )
    args = p.parse_args()

    ids = sorted(d.name for d in args.est_dir.iterdir() if d.is_dir())
    rows = []  # per-utterance dicts
    all_latencies = []
    for utt_id in tqdm(ids):
        latency_path = args.est_dir / utt_id / "latencies.npy"
        est_paths = [
            args.est_dir / utt_id / f"output_channel_{c}.wav" for c in range(2)
        ]
        ref_paths = [
            args.ref_dir / "s1" / f"{utt_id}.wav",
            args.ref_dir / "s2" / f"{utt_id}.wav",
        ]

        if not all(q.exists() for q in est_paths + ref_paths + [latency_path]):
            print(f"[skip] missing files for id {utt_id}")
            continue

        # References define the sample rate; resample estimates if they differ
        refs = [load_wav(q) for q in ref_paths]
        ref_sr = refs[0][1]
        refs = [r[0] for r in refs]
        ests = [load_wav(q, target_sr=ref_sr)[0] for q in est_paths]

        lat = np.asarray(np.load(latency_path)).reshape(-1)
        all_latencies.append(lat)

        # Align lengths, compensating for the streaming delay
        n = min(min(len(x) for x in ests), min(len(x) for x in refs))
        preds = (
            torch.stack([x[args.stream_delay : n] for x in ests])
            .unsqueeze(0)
            .to(args.device)
        )  # [1, spk, time]
        target = (
            torch.stack([x[: n - args.stream_delay] for x in refs])
            .unsqueeze(0)
            .to(args.device)
        )  # [1, spk, time]

        _, best_perm = permutation_invariant_training(
            preds,
            target,
            metric_func=scale_invariant_signal_distortion_ratio,
            mode="speaker-wise",
            eval_func="max",
        )
        # Reorder estimates so that preds_perm[:, i] is matched to target[:, i]
        preds_perm = pit_permutate(preds, best_perm)
        per_spk = scale_invariant_signal_distortion_ratio(preds_perm, target)[0]

        rows.append(
            {
                "file_id": utt_id,
                "min latency": float(np.min(lat)),
                "mean latency": float(np.mean(lat)),
                "median latency": float(np.median(lat)),
                "max latency": float(np.max(lat)),
                "s1 si-sdr": per_spk[0].item(),
                "s2 si-sdr": per_spk[1].item(),
            }
        )

    if not rows:
        print("No utterances evaluated.")
        return

    # Per-utterance PIT score = mean of the two matched speaker scores
    scores = torch.tensor([(r["s1 si-sdr"] + r["s2 si-sdr"]) / 2 for r in rows])
    overall_latencies = np.concatenate(all_latencies)
    print(f"\nEvaluated {len(rows)} utterances")
    print(f"Min SI-SDR: {scores.min():.3f} dB")
    print(
        f"Mean SI-SDR: {scores.mean():.3f} dB  (std {scores.std():.3f}, median {scores.median():.3f})"
    )
    print(f"Max SI-SDR: {scores.max():.3f} dB")
    print(
        f"Latency: {np.min(overall_latencies)}ms (min) {np.median(overall_latencies)}ms (median) "
        f"{np.mean(overall_latencies)}ms (avg) {np.max(overall_latencies)}ms (max)"
    )

    fields = [
        "file_id",
        "min latency",
        "mean latency",
        "median latency",
        "max latency",
        "s1 si-sdr",
        "s2 si-sdr",
    ]
    csv_path = args.est_dir / args.csv
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: (v if k == "file_id" else f"{v:.4f}") for k, v in r.items()})
    print(f"Per-utterance results saved to {csv_path}")


if __name__ == "__main__":
    main()
