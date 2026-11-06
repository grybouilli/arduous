import os

import numpy as np
import soundfile as sf
import torch
from torchmetrics.functional.audio import scale_invariant_signal_distortion_ratio


class MetricsComputer:
    def __init__(self, path: str):
        self.output_path = os.path.join(path)
        self.output_latencies = "latencies.npy"  # contains latencies in ms
        self.output_channel_0 = "output_channel_0.wav"
        self.output_channel_1 = "output_channel_1.wav"

        self.latencies: list[float] = []
        self.sisdr: list[float] = []

    def _output_channel_0_path(self, subdir=""):
        return os.path.join(self.output_path, subdir, self.output_channel_0)

    def _output_channel_1_path(self, subdir=""):
        return os.path.join(self.output_path, subdir, self.output_channel_1)

    def _output_latencies_path(self, subdir=""):
        return os.path.join(self.output_path, subdir, self.output_latencies)

    @staticmethod
    def _load_mono(path: str) -> tuple[torch.Tensor, int]:
        """Load a mono wav as a float32 1-D tensor, plus its sample rate."""
        data, sr = sf.read(path, dtype="float32", always_2d=False)
        if data.ndim != 1:
            raise ValueError(f"{path} has {data.shape[1]} channels, expected mono")
        return torch.from_numpy(data), sr

    def compute_sisdr(
        self, path_to_s1: str, path_to_s2: str, output_subdir: str = "", delay: int = 32
    ) -> None:
        # load path_to_s1, path_to_s2 and both self.output_channel
        # compute all 4 sisdr and add the two highest values to self.sisdr
        # streamable model has an inherent delay because of the convolutions
        # the offline app does not pad the input so we need to account for that delay here
        refs = [self._load_mono(p) for p in (path_to_s1, path_to_s2)]
        outs = [
            self._load_mono(p)
            for p in (
                self._output_channel_0_path(output_subdir),
                self._output_channel_1_path(output_subdir),
            )
        ]

        sample_rates = {sr for _, sr in refs + outs}
        if len(sample_rates) != 1:
            raise ValueError(
                f"Sample rate mismatch between files: {sorted(sample_rates)}"
            )

        scores = []
        for out, _ in outs:
            for ref, _ in refs:
                # Outputs and references may differ slightly in length: truncate to the shortest.
                n = min(out.shape[-1], ref.shape[-1])
                score = scale_invariant_signal_distortion_ratio(out[delay:n], ref[:n-delay])
                scores.append(score.item())

        self.sisdr.extend(sorted(scores, reverse=True)[:2])

    def get_latencies(self, output_subdir: str = "") -> None:
        # load latencies from self.output_latencies
        # add them to self.latencies
        latencies = np.atleast_1d(np.load(self._output_latencies_path(output_subdir)))
        self.latencies.extend(latencies.astype(float).ravel().tolist())

    @staticmethod
    def _print_summary(name: str, values: list[float], unit: str) -> None:
        if not values:
            print(f"{name}: no data")
            return
        arr = np.asarray(values, dtype=float)
        print(
            f"{name} (n={arr.size}): "
            f"min={arr.min():.2f} {unit}, "
            f"max={arr.max():.2f} {unit}, "
            f"avg={arr.mean():.2f} {unit}, "
            f"median={np.median(arr):.2f} {unit}"
        )

    def print_latencies_metrics(self) -> None:
        # print summary on self.latencies
        # min, max, avg, median
        self._print_summary("Latency", self.latencies, "ms")

    def print_sisdr_metrics(self) -> None:
        # print summary on self.sisdr
        # min, max, avg, median
        self._print_summary("SI-SDR", self.sisdr, "dB")
