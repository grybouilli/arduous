# build
# create env folders on target
# push all dependencies on target
# push setup.sh on target
# push executable on target
import subprocess
from argparse import ArgumentParser, BooleanOptionalAction
from arduous_interface import ArduousInterface
import re
import os

parser = ArgumentParser()
parser.add_argument("--android_ndk", type=str, default="/opt/android-ndk-r29")
parser.add_argument("--qnn", action=BooleanOptionalAction, default=True)
parser.add_argument("--ninja", action=BooleanOptionalAction, default=True)
parser.add_argument("--android_abi", type=str, default="arm64-v8a")
parser.add_argument("--build_dir", type=str, default="build")
parser.add_argument("--arduous_home", type=str, default="arduous")
parser.add_argument("--qnn_arch", type=str, default="hexagon-v73")
parser.add_argument(
    "--force",
    action=BooleanOptionalAction,
    help="Force copying libraries to the target even if they already exist there",
    default=False
)
args = parser.parse_args()

############################################
## Generate CMake
############################################
generate_cmd_args = []
if args.qnn:
    generate_cmd_args.append("-DONNX_USE_QNN=ON")
if args.ninja:
    generate_cmd_args.append("-GNinja")
    generate_cmd_args.append("-DCMAKE_CXX_FLAGS=\"-fdiagnostics-color=always\"")
generate_cmd_args.append(f"-B {args.build_dir}")
generate_cmd_args.append(f"-DANDROID_ABI={args.android_abi}")
generate_cmd_args.append(
    f"-DCMAKE_TOOLCHAIN_FILE={args.android_ndk}/build/cmake/android.toolchain.cmake"
)

subprocess.run(["cmake", *generate_cmd_args])
subprocess.run(["cmake", "--build", args.build_dir])

############################################
## Create arduous home on target
############################################
arduous = ArduousInterface(f"/data/local/tmp/{args.arduous_home}")

path_to_qairt = os.path.join(args.build_dir, "import", "qairt")
pattern = re.compile(r"^(\d+\.\d+)\.\d+\.\d+$")

qairt_version, qairt_folder = next(
    (float(m.group(1)), os.path.join(path_to_qairt, folder))
    for folder in os.listdir(path_to_qairt)
    if os.path.isdir(os.path.join(path_to_qairt, folder))
    if (m := pattern.match(folder))
)
arduous.create_home(qairt_version=qairt_version)

############################################
## Push qairt and libonnxruntime on target
############################################
# TODO: Check for existence first and then push if not there + check --force option to force copy even if libraries exist
############################################
## Push qairt and libonnxruntime on target
############################################


def remote_file_exists(remote_path: str) -> bool:
    """Return True if the file exists on the target device."""
    try:
        result = arduous._adb("shell", f"test -f {remote_path}")
    except subprocess.CalledProcessError:
        return False
    # If _adb returns a CompletedProcess instead of raising on failure
    return getattr(result, "returncode", 0) == 0


def push_if_needed(local_path: str, remote_dir: str, force: bool = False) -> None:
    """Push local_path to remote_dir unless it's already there (or force is set)."""
    remote_path = f"{remote_dir}/{os.path.basename(local_path)}"
    if not force and remote_file_exists(remote_path):
        print(f"[skip] {remote_path} already exists (use --force to overwrite)")
        return
    arduous._adb("push", local_path, remote_dir)


# libonnxruntime
path_to_libonnxruntime = os.path.join(
    args.build_dir,
    "_deps",
    "onnxruntime-src",
    "jni",
    args.android_abi,
    "libonnxruntime.so",
)
push_if_needed(path_to_libonnxruntime, f"{arduous.root}/lib", args.force)

# Push only necessary libraries from qairt
qnn_deps = [
    "libGenie.so",
    "libQnnHtpPrepare.so",
    "libQnnGpu.so",
    "libQnnHtp.so",
    "libQnnHtpNetRunExtensions.so",
    "libQnnHtpV68Stub.so",
    "libQnnHtpV69Stub.so",
    "libQnnHtpV73Stub.so",
    "libQnnHtpV75Stub.so",
    "libQnnHtpV79Stub.so",
    "libQnnHtpV81Stub.so",
    "libQnnIr.so",
    "libQnnSaver.so",
    "libQnnSystem.so",
]  # (removed the duplicated libQnnHtpPrepare.so entry)

hexagon_dep = "libQnnHtpV", "Skel.so"
path_to_hexagon = os.path.join(qairt_folder, "lib", "hexagon-v")
path_to_qnn = os.path.join(qairt_folder, "lib", "aarch64-android")
qairt_remote_dir = f"{arduous.root}/lib/qairt{qairt_version}"

for dep in qnn_deps:
    push_if_needed(f"{path_to_qnn}/{dep}", qairt_remote_dir, args.force)

for version in range(68, 86):
    current_path_to_hexagon = os.path.join(f"{path_to_hexagon}{version}", "unsigned")
    if os.path.exists(current_path_to_hexagon):
        push_if_needed(
            f"{current_path_to_hexagon}/{hexagon_dep[0]}{version}{hexagon_dep[1]}",
            qairt_remote_dir,
            args.force,
        )


############################################
## Push arduous apps
############################################

arduous_apps = ["offline_inferences", "get_embedded_ctx"]
for app in arduous_apps:
    arduous._adb("push", f"{args.build_dir}/{app}", f"{arduous.root}")

setup_sh_content = f"export LD_LIBRARY_PATH={arduous.root}/lib:{arduous.root}/lib/qairt{qairt_version}\nexport ADSP_LIBRARY_PATH={arduous.root}/lib/qairt{qairt_version}"

arduous._adb("shell", f"echo \"{setup_sh_content}\" > {arduous.root}/setup.sh")
