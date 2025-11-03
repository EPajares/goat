from enum import Enum

from core.db.models.data_store import DataStore, DataStoreBase


class DataStoreType(str, Enum):
    """Data store type."""

    postgis = "postgis"
    external = "external"


class DataStoreCreate(DataStoreBase):
    pass


class DataStoreUpdate(DataStoreBase):
    pass


class DataStoreRead(DataStore):
    pass
