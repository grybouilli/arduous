from argparse import ArgumentParser, BooleanOptionalAction
from arduous_interface import ArduousInterface
from dataset_handler import DatasetHandler
from model_handler import ModelHandler, ModelInterface
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
    "--fresh",
    action=BooleanOptionalAction,
    help="Force reinference on existing data",
    default=False,
)
parser.add_argument(
    "--arduous_loc",
    type=str,
    help="Location of arduous on target",
    default="/data/local/tmp/arduous",
)
parser.add_argument(
    "--stream_delay",
    type=int,
    help="Streamable model sample delay in comparison to offline",
    default=32,
)

args = parser.parse_args()


arduous = ArduousInterface(args.arduous_loc)
dataset = DatasetHandler(args.dataset)
models = []

with open(args.config) as json_data:
    data = json.load(json_data)


def print_progress(done: int, total: int, width: int = 30) -> None:
    frac = done / total if total else 1.0
    filled = int(width * frac)
    print(
        f"[{'#' * filled}{'-' * (width - filled)}] {frac * 100:5.1f}% ({done}/{total})"
    )

print(f"Initializing models...")
for model, config in data.items():
    models.append(ModelHandler(arduous, model, config))

print(f"Compiling models...")
metrics = dict()

for model in models:
    for variant in model:
        metrics[variant.id] = MetricsComputer(variant.fetch_loc)
        if not arduous.path_exists(variant.ctx_path):
            print(f"Compiling model {variant.model_path} into {variant.ctx_path}")
            arduous.run_get_embedded_ctx(variant.ctx_config, variant.model_path, variant.ctx_path, variant.ep_config_path)

try:
    print_progress(dataset.processed, dataset.total)
    next_files = dataset.get_next_files()
    while next_files is not None:
        next_mixed, next_s1, next_s2 = next_files

        arduous.copy_to_input(next_mixed)
        subdir = os.path.splitext(os.path.basename(next_mixed))[0]
        for model in models:
            variant: ModelInterface
            for variant in model:
                target_dir = os.path.join(variant.fetch_loc, subdir)
                if not os.path.exists(target_dir):
                    try:
                        arduous.run_offline_inferences(variant.config, variant.ctx_path, variant.ep_config_path)
                    except Exception:
                        if not arduous.path_exists(variant.ctx_path):
                            arduous.run_offline_inferences(variant.config, variant.model_path, variant.ep_config_path)
                    arduous.retrieve_outputs(target_dir)

                metrics[variant.id].get_latencies(output_subdir=subdir)
                metrics[variant.id].compute_sisdr(next_s1, next_s2, subdir, args.stream_delay)

        print_progress(dataset.processed, dataset.total)
        next_files = dataset.get_next_files()
except KeyboardInterrupt:
    print("\nInterrupted, computing metrics on the results so far...")
finally:
    try:
        for id, metric in metrics.items():
            print(f"--------- {id} ---------")
            metric.print_latencies_metrics()
            metric.print_sisdr_metrics()
            print(f"-----------------------")
    finally:
        arduous.clean_up()
