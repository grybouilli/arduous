import os
import shlex
import subprocess
import json
import posixpath


class ArduousInterface:

    def __init__(self, root: str = "/data/local/tmp/arduous"):
        self.root = root
        self.get_embedded_ctx = os.path.join(self.root, "get_embedded_ctx")
        self.offline_inferences = os.path.join(self.root, "offline_inferences")

        self.path_to_input = os.path.join(self.root, "audios/bench/input/")
        self.path_to_input_filename = os.path.join(
            self.root, "audios/bench/input/input.wav"
        )
        self.path_to_output = os.path.join(self.root, "audios/bench/output/")
        self.setup_script = os.path.join(self.root, "setup.sh")

    def _adb_shell_env(self, *args: str) -> subprocess.CompletedProcess:
        """Run a command on the device after sourcing setup.sh, in the same shell."""
        command = f"cd {self.root} && source {shlex.quote(self.setup_script)} && {shlex.join(args)}"
        return self._adb("shell", command)

    @staticmethod
    def _adb(*args: str) -> subprocess.CompletedProcess:
        """Run an adb command on the host and raise if it fails."""
        return subprocess.run(
            ["adb", *args], check=True, capture_output=True, text=True
        )

    def _adb_shell(self, *args: str) -> subprocess.CompletedProcess:
        """Run a command on the device, quoting each argument safely."""
        return self._adb("shell", shlex.join(args))

    def _make_path_absolute(self, path: str) -> str:
        if self.root not in path:
            return os.path.join(self.root, path)
        return path

    def run_offline_inferences(
        self, config_path: str, model_path: str | None = None
    ) -> None:
        # adb shell offline_inferences -a config_path -i path_to_input_filename -o path_to_output
        config_path = self._make_path_absolute(config_path)
        model_path = self._make_path_absolute(model_path)
        cmd = [self.offline_inferences, "-a", config_path]
        if model_path is not None:
            cmd += ["-m", model_path]
        cmd += ["-i", self.path_to_input_filename, "-o", self.path_to_output]

        self._adb_shell("mkdir", "-p", self.path_to_output)
        self._adb_shell_env(*cmd)

    def copy_to_input(self, host_path: str) -> None:
        # adb push host_path path_to_input_filename
        self._adb_shell("mkdir", "-p", self.path_to_input)
        self._adb("push", host_path, self.path_to_input_filename)

    def retrieve_outputs(self, host_path: str) -> None:
        # adb pull path_to_output host_path
        os.makedirs(host_path, exist_ok=True)
        self._adb("pull", os.path.join(self.path_to_output, "latencies.npy"), host_path)
        self._adb(
            "pull", os.path.join(self.path_to_output, "output_channel_0.wav"), host_path
        )
        self._adb(
            "pull", os.path.join(self.path_to_output, "output_channel_1.wav"), host_path
        )

    def _read_device_json(self, device_path: str) -> dict:
        """Read and parse a JSON file that lives on the device."""
        result = self._adb_shell("cat", device_path)
        return json.loads(result.stdout)

    @staticmethod
    def _ctx_path_for(model_filename: str) -> str:
        """/path/to/model.onnx -> /path/to/ctx_model.onnx (device paths are POSIX)."""
        dirname, basename = posixpath.split(model_filename)
        return posixpath.join(dirname, f"ctx_{basename}")

    def run_get_embedded_ctx(
        self,
        config_path: str,
        model_path: str | None = None,
        output_path: str | None = None,
    ) -> str:
        # adb shell get_embedded_ctx -a config_path -o output_path
        if output_path is None:
            config = self._read_device_json(config_path)
            try:
                model_filename = config["model_filename"]
            except KeyError:
                raise KeyError(
                    f"'model_filename' not found in {config_path} on the device; "
                    "pass output_path explicitly"
                ) from None
            output_path = self._ctx_path_for(model_filename)

        cmd = [self.get_embedded_ctx, "-a", config_path]
        if model_path is not None:
            cmd += ["-m", model_path]
        cmd += ["-o", output_path]

        self._adb_shell("mkdir", "-p", posixpath.dirname(output_path))
        self._adb_shell_env(*cmd)
        return output_path

    def clean_up(self) -> None:
        # adb shell rm -rf path_to_input path_to_output
        self._adb_shell("rm", "-rf", self.path_to_input, self.path_to_output)
