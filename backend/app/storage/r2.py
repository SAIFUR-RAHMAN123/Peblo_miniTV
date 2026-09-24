"""
Cloudflare R2 backend (S3-compatible), sketched but not exercised in this
take-home (no bucket/credentials to test against). Wiring it up for real is
~20 lines with boto3 pointed at R2's S3-compatible endpoint:

    https://<account_id>.r2.cloudflarestorage.com

`write_atomic` on R2/S3 is naturally atomic: PutObject either fully succeeds
(the object now exists with the new bytes) or fully fails (old object, if
any, is untouched) -- there is no partial-object state a reader can observe,
so no local temp-file/rename dance is needed here, unlike local disk.
"""
from app.storage.base import StorageBackend


class R2Storage(StorageBackend):
    def __init__(self, bucket: str, account_id: str, access_key_id: str,
                 secret_access_key: str, public_base_url: str):
        import boto3
        self.bucket = bucket
        self.public_base_url = public_base_url.rstrip("/")
        self.client = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )

    def write(self, key: str, data: bytes, content_type: str) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)

    def write_atomic(self, key: str, data: bytes, content_type: str) -> None:
        self.write(key, data, content_type)

    def read(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def public_url(self, key: str) -> str:
        return f"{self.public_base_url}/{key.lstrip('/')}"

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False