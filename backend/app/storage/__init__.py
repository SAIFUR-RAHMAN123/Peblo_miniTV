from functools import lru_cache

from app.core.config import get_settings
from app.storage.base import StorageBackend
from app.storage.local import LocalStorage


@lru_cache
def get_storage() -> StorageBackend:
    settings = get_settings()
    if settings.storage_backend == "local":
        return LocalStorage(root=settings.storage_local_root, public_base_url=settings.storage_public_base_url)
    if settings.storage_backend == "r2":
        from app.storage.r2 import R2Storage
        return R2Storage(
            bucket=settings.r2_bucket,
            account_id=settings.r2_account_id,
            access_key_id=settings.r2_access_key_id,
            secret_access_key=settings.r2_secret_access_key,
            public_base_url=settings.r2_public_base_url,
        )
    raise ValueError(f"Unknown storage backend: {settings.storage_backend}")