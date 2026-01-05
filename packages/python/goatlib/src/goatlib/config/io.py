from __future__ import annotations

from goatlib.config.base import BaseSettingsModel


class IOSettings(BaseSettingsModel):
    """Settings for dataset I/O and optional direct S3 access."""

    s3_endpoint_url: str | None = None  # e.g. "https://s3.fsn1.de"
    s3_public_endpoint_url: str | None = (
        None  # Public URL for browser access (e.g., "http://localhost:9000")
    )
    s3_provider: str | None = "aws"  # or "hetzner", "minio"
    s3_force_path_style: bool = False  # MinIO compatibility
    s3_region: str | None = "eu-central-1"
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = "your-secret"
    s3_session_token: str | None = None
    s3_bucket_name: str | None = "goat"
    s3_bucket_path: str | None = ""
    max_upload_dataset_file_size: int = 300 * 1024 * 1024
