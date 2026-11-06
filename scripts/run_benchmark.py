from argparse import ArgumentParser, BooleanOptionalAction
from arduous_interface import ArduousInterface
from dataset_handler import DatasetHandler
import json
from metrics_computer import MetricsComputer
import os

parser = ArgumentParser()
parser.add_argument(
    "config",
    type=str,
    help="Path to config file containing paths to models and their configs (expected .json)",
)
parser.add_argument(
    "dataset",
    type=str,
    help="Path to data containing s1, s2 and mix_clean (expected folder)",
)
parser.add_argument(
    "--fetch_loc",
    type=str,
    help="Host path to copy outputs to",
    default="./output",
)
parser.add_argument(
    "--compile",
    action=BooleanOptionalAction,
    help="Whether the models should be compiled",
    default=False,
)
parser.add_argument(
    "--arduous_loc",
    type=str,
    help="Location of arduous on target",
    default="/data/local/tmp/arduous",
)

args = parser.parse_args()

arduous = ArduousInterface(args.arduous_loc)
dataset = DatasetHandler(args.dataset)
metrics = MetricsComputer(args.fetch_loc)

with open(args.config) as json_data:
    data = json.load(json_data)


def print_progress(done: int, total: int, width: int = 30) -> None:
    frac = done / total if total else 1.0
    filled = int(width * frac)
    print(
        f"[{'#' * filled}{'-' * (width - filled)}] {frac * 100:5.1f}% ({done}/{total})"
    )


try:
    print_progress(dataset.processed, dataset.total)
    next_files = dataset.get_next_files()
    while next_files is not None:
        next_mixed, next_s1, next_s2 = next_files

        arduous.copy_to_input(next_mixed)
        # print("Running for {}".format(next_mixed))
        for model_path, config_path in data.items():
            if args.compile:
                model_path = arduous.run_get_embedded_ctx(config_path, model_path)
            # print("Using model {}".format(model_path))
            arduous.run_offline_inferences(config_path, model_path)

            subdir = os.path.splitext(os.path.basename(next_mixed))[0]
            output_loc = os.path.join(args.fetch_loc, subdir)
            arduous.retrieve_outputs(output_loc)

            metrics.get_latencies(output_subdir=subdir)
            metrics.compute_sisdr(next_s1, next_s2, subdir)

        print_progress(dataset.processed, dataset.total)
        next_files = dataset.get_next_files()
except KeyboardInterrupt:
    print("\nInterrupted, computing metrics on the results so far...")
finally:
    try:
        metrics.print_latencies_metrics()
        metrics.print_sisdr_metrics()
    finally:
        arduous.clean_up()
