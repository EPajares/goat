"""S3 service for Processes API.

Minimal S3 client for file uploads/downloads and presigned URLs.
Uses same credentials as core app.
"""

import hashlib
import logging
import posixpath
from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from lib.config import get_settings

logger = logging.getLogger(__name__)


class S3Service:
    """S3 client for file operations.

    Supports AWS S3 and S3-compatible providers (Hetzner, MinIO).
    """

    def __init__(self) -> None:
        """Initialize S3 client from settings."""
        settings = get_settings()

        extra_kwargs = {}

        # Use endpoint_url if provided (Hetzner, MinIO, etc.)
        if settings.S3_ENDPOINT_URL:
            extra_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

        # Special config for non-AWS providers
        if settings.S3_PROVIDER.lower() == "hetzner":
            extra_kwargs["config"] = Config(
                signature_version="s3v4",
                s3={
                    "payload_signing_enabled": False,
                    "addressing_style": "virtual",
                },
            )

        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
            **extra_kwargs,
        )
        self._settings = settings

    def upload_file(
        self,
        file_content: BinaryIO,
        bucket_name: str,
        s3_key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file to S3.

        Args:
            file_content: File-like object to upload
            bucket_name: S3 bucket name
            s3_key: Object key in S3
            content_type: MIME type

        Returns:
            S3 URI (s3://bucket/key)

        Raises:
            RuntimeError: If upload fails
        """
        try:
            self.s3_client.upload_fileobj(
                file_content,
                bucket_name,
                s3_key,
                ExtraArgs={"ContentType": content_type},
            )
            return f"s3://{bucket_name}/{s3_key}"
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise RuntimeError(f"Failed to upload file: {e}") from e

    def generate_presigned_download_url(
        self,
        bucket_name: str,
        s3_key: str,
        expires_in: int = 3600,
        filename: str | None = None,
    ) -> str:
        """Generate a presigned GET URL for downloading an object.

        Args:
            bucket_name: The S3 bucket name
            s3_key: The object key in S3
            expires_in: URL expiration time in seconds
            filename: Optional filename for Content-Disposition header

        Returns:
            Presigned URL string

        Raises:
            RuntimeError: If URL generation fails
        """
        try:
            params = {"Bucket": bucket_name, "Key": s3_key}

            # Add Content-Disposition to force download
            if filename:
                params["ResponseContentDisposition"] = (
                    f'attachment; filename="{filename}"'
                )

            return self.s3_client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=expires_in,
            )
        except ClientError as e:
            logger.error(f"Presigned download URL failed: {e}")
            raise RuntimeError(f"Failed to generate presigned URL: {e}") from e

    def delete_file(self, bucket_name: str, s3_key: str) -> None:
        """Delete an object from S3.

        Args:
            bucket_name: S3 bucket name
            s3_key: Object key to delete

        Raises:
            RuntimeError: If delete fails
        """
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        except ClientError as e:
            logger.error(f"Delete failed for {bucket_name}/{s3_key}: {e}")
            raise RuntimeError(f"Failed to delete file: {e}") from e

    @staticmethod
    def calculate_sha256(file_content: bytes) -> str:
        """Calculate SHA256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()

    @staticmethod
    def build_s3_key(*parts: str) -> str:
        """Safely join S3 key parts into a normalized path.

        Args:
            *parts: Path components to join

        Returns:
            Normalized S3 key
        """
        return posixpath.join(*(p.strip("/") for p in parts if p))


# Lazy singleton
_s3_service: S3Service | None = None


def get_s3_service() -> S3Service:
    """Get or create S3 service singleton."""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service
