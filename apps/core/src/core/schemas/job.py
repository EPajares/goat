from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class JobType(str, Enum):
    """Job types."""

    file_import = "file_import"
    join = "join"
    catchment_area_active_mobility = "catchment_area_active_mobility"
    catchment_area_pt = "catchment_area_pt"
    catchment_area_car = "catchment_area_car"
    oev_gueteklasse = "oev_gueteklasse"
    aggregate_point = "aggregate_point"
    aggregate_polygon = "aggregate_polygon"
    buffer = "buffer"
    trip_count_station = "trip_count_station"
    origin_destination = "origin_destination"
    nearby_station_access = "nearby_station_access"
    heatmap_gravity_active_mobility = "heatmap_gravity_active_mobility"
    heatmap_gravity_motorized_mobility = "heatmap_gravity_motorized_mobility"
    heatmap_closest_average_active_mobility = "heatmap_closest_average_active_mobility"
    heatmap_closest_average_motorized_mobility = (
        "heatmap_closest_average_motorized_mobility"
    )
    heatmap_connectivity_active_mobility = "heatmap_connectivity_active_mobility"
    heatmap_connectivity_motorized_mobility = "heatmap_connectivity_motorized_mobility"
    data_delete_multi = "data_delete_multi"
    update_layer_dataset = "update_layer_dataset"


class JobStatusType(str, Enum):
    """Status types."""

    pending = "pending"
    running = "running"
    finished = "finished"
    failed = "failed"
    timeout = "timeout"
    killed = "killed"


class MsgType(str, Enum):
    """Message types."""

    info = "info"
    warning = "warning"
    error = "error"


class Msg(BaseModel):
    """Message attribute types."""

    type: MsgType = MsgType.info
    text: str


class JobStep(BaseModel):
    """Job step attribute types."""

    status: JobStatusType = JobStatusType.pending
    timestamp_start: datetime | None = None
    timestamp_end: datetime | None = None
    msg: Msg | None = None


class JobStatusFileImport(BaseModel):
    upload: JobStep = JobStep()
    migration: JobStep = JobStep()


class JobStatusJoin(BaseModel):
    join: JobStep = JobStep()


class JobStatusOevGueteklasse(BaseModel):
    station_category: JobStep = JobStep()
    station_buffer: JobStep = JobStep()


class JobStatusAggregationPoint(BaseModel):
    aggregation: JobStep = JobStep()


class JobStatusAggregationPolygon(BaseModel):
    aggregation: JobStep = JobStep()


class JobStatusCatchmentAreaBase(BaseModel):
    catchment_area: JobStep = JobStep()


class JobStatusCatchmentAreaActiveMobility(JobStatusCatchmentAreaBase):
    pass


class JobStatusCatchmentAreaPT(JobStatusCatchmentAreaBase):
    pass


class JobStatusCatchmentAreaCar(JobStatusCatchmentAreaBase):
    pass


class JobStatusBuffer(BaseModel):
    buffer: JobStep = JobStep()


class JobStatusTripCountStation(BaseModel):
    trip_count_station: JobStep = JobStep()


class JobStatusOriginDestination(BaseModel):
    origin_destination: JobStep = JobStep()


class JobStatusNearbyStationAccess(BaseModel):
    nearby_station_access: JobStep = JobStep()


class JobStatusHeatmapGravityBase(BaseModel):
    heatmap_gravity: JobStep = JobStep()


class JobStatusHeatmapGravityActiveMobility(JobStatusHeatmapGravityBase):
    pass


class JobStatusHeatmapGravityMotorizedMobility(JobStatusHeatmapGravityBase):
    pass


class JobStatusHeatmapClosestAverageBase(BaseModel):
    heatmap_closest_average: JobStep = JobStep()


class JobStatusHeatmapClosestAverageActiveMobility(JobStatusHeatmapClosestAverageBase):
    pass


class JobStatusHeatmapClosestAverageMotorizedMobility(
    JobStatusHeatmapClosestAverageBase
):
    pass


class JobStatusHeatmapConnectivityBase(BaseModel):
    heatmap_connectivity: JobStep = JobStep()


class JobStatusHeatmapConnectivityActiveMobility(JobStatusHeatmapConnectivityBase):
    pass


class JobStatusHeatmapConnectivityMotorizedMobility(JobStatusHeatmapConnectivityBase):
    pass


class JobStatusLayerDeleteMulti(BaseModel):
    data_delete_multi: JobStep = JobStep()


# Only add jobs here that are consisting of multiple steps
job_mapping = {
    JobType.file_import: JobStatusFileImport,
    JobType.join: JobStatusJoin,
    JobType.oev_gueteklasse: JobStatusOevGueteklasse,
    JobType.aggregate_point: JobStatusAggregationPoint,
    JobType.aggregate_polygon: JobStatusAggregationPolygon,
    JobType.catchment_area_active_mobility: JobStatusCatchmentAreaActiveMobility,
    JobType.catchment_area_pt: JobStatusCatchmentAreaPT,
    JobType.catchment_area_car: JobStatusCatchmentAreaCar,
    JobType.buffer: JobStatusBuffer,
    JobType.trip_count_station: JobStatusTripCountStation,
    JobType.origin_destination: JobStatusOriginDestination,
    JobType.nearby_station_access: JobStatusNearbyStationAccess,
    JobType.heatmap_gravity_active_mobility: JobStatusHeatmapGravityActiveMobility,
    JobType.heatmap_gravity_motorized_mobility: JobStatusHeatmapGravityMotorizedMobility,
    JobType.heatmap_closest_average_active_mobility: JobStatusHeatmapClosestAverageActiveMobility,
    JobType.heatmap_closest_average_motorized_mobility: JobStatusHeatmapClosestAverageMotorizedMobility,
    JobType.heatmap_connectivity_active_mobility: JobStatusHeatmapConnectivityActiveMobility,
    JobType.heatmap_connectivity_motorized_mobility: JobStatusHeatmapConnectivityMotorizedMobility,
    JobType.data_delete_multi: JobStatusLayerDeleteMulti,
    JobType.update_layer_dataset: JobStatusFileImport,
}
