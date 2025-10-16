from typing import Literal
from urllib.parse import urlparse

PathType = Literal["local", "s3", "http"]


def detect_path_type(path: str) -> PathType:
    scheme = urlparse(path).scheme.lower()
    if scheme in {"s3"}:
        return "s3"
    if scheme in {"http", "https"}:
        return "http"
    return "local"
