import os
import tempfile

from app.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    def __init__(self, root: str, public_base_url: str):
        self.root = os.path.abspath(root)
        self.public_base_url = public_base_url.rstrip("/")
        os.makedirs(self.root, exist_ok=True)

    def _path(self, key: str) -> str:
        safe = os.path.normpath(key).lstrip(os.sep)
        if safe.startswith(".."):
            raise ValueError(f"Invalid storage key: {key}")
        return os.path.join(self.root, safe)

    def write(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    def write_atomic(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Write to a temp file in the SAME directory (so the rename below is
        # on the same filesystem, hence atomic), then os.replace() it over
        # the target. os.replace is an atomic rename on POSIX/Windows: a
        # concurrent reader opening `path` gets the fully-old file or the
        # fully-new one, never a partial one.
        fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def read(self, key: str) -> bytes:
        with open(self._path(key), "rb") as f:
            return f.read()

    def public_url(self, key: str) -> str:
        return f"{self.public_base_url}/{key.lstrip('/')}"

    def exists(self, key: str) -> bool:
        return os.path.exists(self._path(key))