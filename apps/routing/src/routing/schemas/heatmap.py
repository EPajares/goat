from routing.schemas.catchment_area import (
    CatchmentAreaRoutingTypeActiveMobility,
    CatchmentAreaRoutingTypeCar,
    CatchmentAreaTravelTimeCostActiveMobility,
    CatchmentAreaTravelTimeCostMotorizedMobility,
)

ROUTING_COST_CONFIG = {
    CatchmentAreaRoutingTypeActiveMobility.walking.value: CatchmentAreaTravelTimeCostActiveMobility(
        max_traveltime=30, steps=30, speed=5
    ),
    CatchmentAreaRoutingTypeActiveMobility.bicycle.value: CatchmentAreaTravelTimeCostActiveMobility(
        max_traveltime=30, steps=30, speed=15
    ),
    CatchmentAreaRoutingTypeActiveMobility.pedelec.value: CatchmentAreaTravelTimeCostActiveMobility(
        max_traveltime=30, steps=30, speed=23
    ),
    CatchmentAreaRoutingTypeCar.car.value: CatchmentAreaTravelTimeCostMotorizedMobility(
        max_traveltime=60, steps=60
    ),
}

MATRIX_RESOLUTION_CONFIG = {
    CatchmentAreaRoutingTypeActiveMobility.walking.value: 10,
    CatchmentAreaRoutingTypeActiveMobility.bicycle.value: 9,
    CatchmentAreaRoutingTypeActiveMobility.pedelec.value: 9,
    CatchmentAreaRoutingTypeCar.car.value: 8,
}
