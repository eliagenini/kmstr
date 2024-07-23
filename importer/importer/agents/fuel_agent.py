from datetime import datetime, timezone, timedelta
from weconnect.addressable import AddressableLeaf

import logging

LOG = logging.getLogger("kmstr")


class FuelAgent:
    def __init__(self, api, vehicle):
        self.api = api
        self.vehicle = vehicle
        self.range = self.api.get_last_range_by_vehicle(vehicle.id)

        if self.vehicle.remote is not None:
            if (self.vehicle.remote.statusExists('fuelStatus', 'rangeStatus')
                    and self.vehicle.remote.domains['fuelStatus']['rangeStatus'].enabled):
                self.vehicle.remote.domains['fuelStatus']['rangeStatus'].carCapturedTimestamp.addObserver(
                    self.__on_car_captured_timestamp_change,
                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                    onUpdateComplete=True)

                self.__on_car_captured_timestamp_change(
                    self.vehicle.remote.domains['fuelStatus']['rangeStatus'].carCapturedTimestamp, None
                )

    def __on_car_captured_timestamp_change(self, element, flags):  # noqa: C901
        # Check that the data to add is not too old
        if element is not None and element.value is not None and element.value > (
                datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=7)):
            range_status = self.vehicle.weConnectVehicle.domains['fuelStatus']['rangeStatus']
            current_total_range_km = range_status.totalRange_km.value
            current_primary_current_soc_pct = None
            current_primary_remaining_range_km = None
            if range_status.primaryEngine.enabled:
                current_primary_current_soc_pct = range_status.primaryEngine.currentSOC_pct.value
                current_primary_remaining_range_km = range_status.primaryEngine.remainingRange_km.value
            current_secondary_current_soc_pct = None
            current_secondary_remaining_range_km = None
            if range_status.secondaryEngine.enabled:
                current_secondary_current_soc_pct = range_status.secondaryEngine.currentSOC_pct.value
                current_secondary_remaining_range_km = range_status.secondaryEngine.remainingRange_km.value

            if self.range is None or (range_status.carCapturedTimestamp.value is not None
                                      and self.range.carCapturedTimestamp != range_status.carCapturedTimestamp.value
                                      and (self.range.totalRange_km != current_total_range_km
                                           or self.range.primary_currentSOC_pct != current_primary_current_soc_pct
                                           or self.range.primary_remainingRange_km != current_primary_remaining_range_km
                                           or self.range.secondary_currentSOC_pct != current_secondary_current_soc_pct
                                           or self.range.secondary_remainingRange_km != current_secondary_remaining_range_km)):
                self.range = self.api.put({
                    'vehicle': self.vehicle.id,
                    'range': current_total_range_km,
                    'last_modified': range_status.carCapturedTimestamp.value
                })
