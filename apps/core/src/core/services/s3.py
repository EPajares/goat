import hashlib
import logging
import posixpath
from typing import BinaryIO, Dict

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from core.core.config import settings
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self) -> None:
        """
        Initialize an S3 client that can talk to either AWS S3
        or an S3-compatible provider like Hetzner.
        """
        extra_kwargs = {}

        # Use endpoint_url if provided (Hetzner, MinIO, etc.)
        if settings.S3_ENDPOINT_URL:
            extra_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

        # Special config if talking to non-AWS
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

    def generate_presigned_post(
        self,
        bucket_name: str,
        s3_key: str,
        content_type: str,
        max_size: int,
        expires_in: int = 300,
    ) -> Dict[str, str]:
        try:
            result = self.s3_client.generate_presigned_post(
                Bucket=bucket_name,
                Key=s3_key,
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                    ["content-length-range", 0, max_size],
                ],
                ExpiresIn=expires_in,
            )

            # Replace internal URL (minio:9000) with public one (localhost:9000)
            if settings.S3_PUBLIC_ENDPOINT_URL:
                result["url"] = result["url"].replace(
                    settings.S3_ENDPOINT_URL, settings.S3_PUBLIC_ENDPOINT_URL
                )

            return result

        except ClientError as e:
            logger.error(f"S3 presigned POST failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate presigned POST: {e}",
            )

    def upload_file(
        self,
        file_content: BinaryIO,
        bucket_name: str,
        s3_key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file server-side (API → S3)."""
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {e}",
            )

    def generate_presigned_download_url(
        self, bucket_name: str, s3_key: str, expires_in: int = 3600
    ) -> str:
        """Generate a presigned GET URL for downloading an object."""
        try:
            return self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": s3_key},
                ExpiresIn=expires_in,
            )
        except ClientError as e:
            logger.error(f"Presigned download URL failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate presigned download URL: {e}",
            )

    def delete_file(self, bucket_name: str, s3_key: str) -> None:
        """Delete an object from S3."""
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        except ClientError as e:
            logger.error(f"Delete failed for {bucket_name}/{s3_key}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {e}",
            )

    @staticmethod
    def calculate_sha256(file_content: bytes) -> str:
        return hashlib.sha256(file_content).hexdigest()

    @staticmethod
    def build_s3_key(*parts: str) -> str:
        """Safely join S3 key parts into a normalized prefix/key."""
        return posixpath.join(*(p.strip("/") for p in parts if p))


s3_service = S3Service()
