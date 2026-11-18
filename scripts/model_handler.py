import posixpath
import os
from arduous_interface import ArduousInterface


class ConfigKeys:
    model_path = "model_path"
    ctx_path = "ctx_path"
    ctx_config = "ctx_config"
    config = "config"
    fetch_loc = "fetch_loc"
    accelerators = "accelerators"


class Accelerators:
    cpu = "cpu"
    htp = "htp"


class ModelInterface:

    def __init__(
        self,
        id : str,
        model_path: str,
        ctx_path: str,
        ctx_config: str,
        config: str,
        ep_config_path: str,
        fetch_loc: str,
        accelerator: str,
    ):
        self.id = id
        self.model_path = model_path
        self.ctx_path = ctx_path
        self.ctx_config = ctx_config
        self.config = config
        self.ep_config_path = ep_config_path
        self.fetch_loc = fetch_loc
        self.accelerator = accelerator
        try:
            os.mkdir(self.fetch_loc)
        except FileExistsError:
            pass


class ModelHandler:

    def __init__(self, arduous: ArduousInterface, id: str, config: dict):
        self._index = 0
        self.ctx_paths = [
            self._create_ctx_path(config[ConfigKeys.model_path], accelerator)
            for accelerator in config[ConfigKeys.accelerators]
        ]
        self.config_path = config[ConfigKeys.config]

        ep_config_path = self._get_ep_config_path(arduous, config[ConfigKeys.config])
        self.ep_config_paths = [
            self._create_ep_config_path(ep_config_path, accelerator)
            for accelerator in config[ConfigKeys.accelerators]
        ]
        self.fetch_loc = [os.path.join(config[ConfigKeys.fetch_loc], f"{id}_{acc}") for acc in config[ConfigKeys.accelerators]]

        self.models = []
        for ctx_path, ep_config_path_, fetch_loc, acc in zip(
            self.ctx_paths, self.ep_config_paths, self.fetch_loc, config[ConfigKeys.accelerators]
        ):
            self.models.append(
                ModelInterface(
                    f"{id}_{acc}",
                    config[ConfigKeys.model_path],
                    ctx_path,
                    config[ConfigKeys.ctx_config],
                    self.config_path,
                    ep_config_path_,
                    fetch_loc,
                    acc,
                )
            )

    def __iter__(self):
        return self

    def __next__(self) -> ModelInterface:
        if self._index < len(self.models):
            item = self.models[self._index]
            self._index += 1
            return item
        else:
            self._index = 0
            raise StopIteration

    def _create_ctx_path(self, model_path: str, accelerator: str):
        dirname, basename = posixpath.split(model_path)
        return os.path.join(dirname, f"{accelerator}_ctx_{basename}")

    def _create_ep_config_path(self, ep_config_path: str, accelerator: str):
        dirname, basename = posixpath.split(ep_config_path)
        basename_noext = os.path.splitext(basename)[0]
        return os.path.join(dirname, f"{basename_noext}_{accelerator}.json")

    def _get_ep_config_path(self, arduous: ArduousInterface, config_path: str):
        config_content = arduous._read_device_json(config_path)
        return config_content["ep_config"]
