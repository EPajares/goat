from typing import Any

from core.crud.base import CRUDBase
from core.db.models.status import Status


class CRUDStatus(CRUDBase[Status, Any, Any]):
    pass


status = CRUDStatus(Status)
