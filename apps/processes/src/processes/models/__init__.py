"""Pydantic models for Processes API."""

from pydantic import BaseModel


class HealthCheck(BaseModel):
    """Health check response model."""

    status: str
    ping: str
