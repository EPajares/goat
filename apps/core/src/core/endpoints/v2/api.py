from fastapi import APIRouter

from . import (
    asset,
    datasets,
    folder,
    layer,
    project,
    report_layout,
    status,
    system,
    user,
)

router = APIRouter()

router.include_router(user.router, prefix="/user", tags=["User"])
router.include_router(folder.router, prefix="/folder", tags=["Folder"])
router.include_router(layer.router, prefix="/layer", tags=["Layer"])
router.include_router(project.router, prefix="/project", tags=["Project"])
router.include_router(report_layout.router, prefix="/project", tags=["Report Layout"])
router.include_router(system.router, prefix="/system", tags=["System Settings"])
router.include_router(status.router, prefix="/status", tags=["Status"])
router.include_router(asset.router, prefix="/asset", tags=["Asset"])
router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
