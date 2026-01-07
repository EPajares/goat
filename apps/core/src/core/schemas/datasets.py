from typing import Dict

from pydantic import BaseModel, Field


class DatasetImportRequest(BaseModel):
    """Schema for requesting a presigned upload URL for a new dataset import."""

    filename: str = Field(..., example="data.gpkg")
    content_type: str = Field(
        "application/octet-stream",
        description="MIME type of the file being uploaded",
        example="application/geopackage+sqlite3",
    )
    file_size: int = Field(
        ...,
        gt=0,
        description="Size of the file in bytes",
        example=1048576,
    )


class PresignedPostResponse(BaseModel):
    """Schema for presigned POST response to upload file directly to S3."""

    url: str = Field(..., example="https://mybucket.s3.amazonaws.com/")
    fields: Dict[str, str] = Field(
        ...,
        example={
            "key": "goat/123/imports/data.gpkg",
            "Content-Type": "application/geopackage+sqlite3",
            "x-amz-algorithm": "AWS4-HMAC-SHA256",
            "x-amz-credential": "AKIA.../us-east-1/s3/aws4_request",
            "x-amz-date": "20240621T120000Z",
            "policy": "eyJleHBpcmF0aW9uIjoi...",
            "x-amz-signature": "abcd1234...",
        },
    )
