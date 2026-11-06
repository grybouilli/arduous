import os


class DatasetHandler:
    def __init__(self, path: str):
        self.path = path
        self.s1_path = os.path.join(path, "s1")
        self.s2_path = os.path.join(path, "s2")
        self.mixed_clean_path = os.path.join(path, "mix_clean")

        self._filenames: list[str] | None = None
        self._index = 0

    def _list_filenames(self) -> list[str]:
        """Sorted names of the regular files in mixed_clean_path."""
        with os.scandir(self.mixed_clean_path) as entries:
            return sorted(e.name for e in entries if e.is_file())

    def get_next_files(self) -> tuple[str, str, str] | None:
        # returns next files in self.mixed_clean_path, self.s1_path, self.s2_path
        # returns None when all have been listed once
        filenames = self._ensure_listed()
        if self._index >= len(filenames):
            return None

        name = filenames[self._index]
        self._index += 1

        files = (
            os.path.join(self.mixed_clean_path, name),
            os.path.join(self.s1_path, name),
            os.path.join(self.s2_path, name),
        )
        for f in files:
            if not os.path.isfile(f):
                raise FileNotFoundError(f"{name} is missing from the dataset: {f}")
        return files

    def reset(self) -> None:
        """Start over from the first file (and re-scan the folder)."""
        self._filenames = None
        self._index = 0

    def _ensure_listed(self) -> list[str]:
        if self._filenames is None:
            self._filenames = self._list_filenames()
        return self._filenames

    @property
    def total(self) -> int:
        """Number of files in the dataset."""
        return len(self._ensure_listed())

    @property
    def processed(self) -> int:
        """Number of files handed out by get_next_files so far."""
        return self._index
