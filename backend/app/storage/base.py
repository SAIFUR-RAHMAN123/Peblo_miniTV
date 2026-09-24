from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """
    Every concrete backend (local disk, R2/S3, ...) implements this. The
    rest of the app -- artwork upload, catalogue publish -- only ever calls
    these four methods, so the backend is swappable without touching
    business logic. Keys are backend-relative paths, e.g.
    'artwork/episode_123/poster.jpg' or 'catalog/catalogue.json'.
    """

    @abstractmethod
    def write(self, key: str, data: bytes, content_type: str) -> None:
        ...

    @abstractmethod
    def write_atomic(self, key: str, data: bytes, content_type: str) -> None:
        """Write such that concurrent readers of `key` never observe a partial
        write -- either the old content or the fully-new content, never a
        half-written file. Used for catalogue publish."""
        ...

    @abstractmethod
    def read(self, key: str) -> bytes:
        ...

    @abstractmethod
    def public_url(self, key: str) -> str:
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        ...