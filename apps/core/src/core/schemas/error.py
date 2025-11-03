from typing import Any, Callable

from fastapi import HTTPException, status


class FeatureNotFoundError(Exception):
    """Raised when the requested feature is not found."""

    pass


class LayerError(Exception):
    """Base class for exceptions related to layers."""

    pass


class LayerSizeError(LayerError):
    """Raised when the layer size is not valid to continue the operation."""

    pass


class LayerExtentError(LayerError):
    """Raised when the layer extent is not valid to continue the operation."""

    pass


class LayerProjectTypeError(LayerError):
    """Raised when the layer_project is not of type BaseModel, SQLModel or dict."""

    pass


class FeatureCountError(LayerError):
    """Raised when the operation cannot be performed on more than a certain number of features."""

    pass


class GeometryTypeError(LayerError):
    """Raised when the operation requires another geometry type."""

    pass


class AreaSizeError(LayerError):
    """Raised when the operation cannot be performed on more than a certain area."""

    pass


class OutOfGeofenceError(LayerError):
    """Raised when the operation cannot be performed outside the geofence."""

    pass


class UnsupportedLayerTypeError(LayerError):
    """Raised when the layer type is not supported."""

    pass


class ColumnTypeError(LayerError):
    """Raised when the column type is not supported."""

    pass


class LayerNotFoundError(LayerError):
    """Raised when the layer is not found."""

    pass


class FolderNotFoundError(Exception):
    """Raised when the layer is not found."""

    pass


class SQLError(Exception):
    """Base class for exceptions related to SQL."""

    pass


class TimeoutError(Exception):
    """Raised when a job timouts."""

    pass


class JobKilledError(Exception):
    """Raised when a job is killed."""

    pass


class NoCRSError(Exception):
    """Raised when CRS is not found."""

    pass


class DataOutCRSBoundsError(Exception):
    """Raised when data is outside CRS bounds."""

    pass


class Ogr2OgrError(Exception):
    """Raised when ogr2ogr fails."""

    pass


class RoutingEndpointError(Exception):
    """Raised when the routing endpoint fails to compute an catchment area."""

    pass


class R5EndpointError(Exception):
    """Raised when the R5 endpoint fails to compute an catchment area."""

    pass


class R5CatchmentAreaComputeError(Exception):
    """Raised when the catchment area data returned by R5 is invalid."""

    pass


class ThumbnailComputeError(Exception):
    """Raised when the thumbnail cannot be computed."""

    pass


class OperationNotSupportedError(Exception):
    """Raised when the operation is not supported."""

    pass


class ColumnNotFoundError(Exception):
    """Raised when the column is not found."""

    pass


class UnknownError(Exception):
    """Raised when an unknown error occurs."""

    pass


# Define the mapping between custom errors and HTTP status codes
ERROR_MAPPING = {
    LayerSizeError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    LayerExtentError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    LayerProjectTypeError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    FeatureCountError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    GeometryTypeError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    AreaSizeError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    OutOfGeofenceError: status.HTTP_403_FORBIDDEN,
    UnsupportedLayerTypeError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ColumnTypeError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    LayerNotFoundError: status.HTTP_404_NOT_FOUND,
    SQLError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    TimeoutError: status.HTTP_408_REQUEST_TIMEOUT,
    JobKilledError: status.HTTP_410_GONE,
    NoCRSError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    DataOutCRSBoundsError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    Ogr2OgrError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    RoutingEndpointError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    R5EndpointError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    R5CatchmentAreaComputeError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    OperationNotSupportedError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ColumnNotFoundError: status.HTTP_404_NOT_FOUND,
    ValueError: status.HTTP_400_BAD_REQUEST,
}


async def http_error_handler(
    func: Callable[..., Any], *args: Any, **kwargs: Any
) -> Any:
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        error_status_code = ERROR_MAPPING.get(type(e))
        if error_status_code:
            raise HTTPException(status_code=error_status_code, detail=str(e))
        else:
            # Raise generic HTTP error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )


class HTTPErrorHandler:
    def __enter__(self) -> "HTTPErrorHandler":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            error_status_code = ERROR_MAPPING.get(exc_type)
            if error_status_code:
                raise HTTPException(status_code=error_status_code, detail=str(exc_val))
            else:
                # Raise generic HTTP error
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(exc_val),
                )
