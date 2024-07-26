from datetime import datetime, timezone, timedelta
from agents.base import BaseAgent
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm.exc import ObjectDeletedError
from weconnect.addressable import AddressableLeaf
from models import Range
import logging

LOG = logging.getLogger("kmstr")


class RangeAgent(BaseAgent):
    def __init__(self, session, vehicle):
        LOG.debug("Initializing RangeAgent")
        super().__init__(session, vehicle)

        self.current = self.get_last()

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

    def get_last(self):
        super().get_last()
        return (self.session.query(Range)
                .filter(and_(Range.vehicle == self.vehicle,
                             Range.captured_timestamp.isnot(None)))
                .order_by(Range.captured_timestamp.desc())
                .first())

    def __on_car_captured_timestamp_change(self, element, flags):  # noqa: C901
        # Check that the data to add is not too old
        if element is not None and element.value is not None and element.value > (
                datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=7)):
            range_status = self.vehicle.remote.domains['fuelStatus']['rangeStatus']
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

            self.refresh()

            if self.current is None or (range_status.carCapturedTimestamp.value is not None and
                                        self.current.captured_timestamp != range_status.carCapturedTimestamp.value and
                                        (self.current.total_range_km != current_total_range_km or
                                         self.current.primary_current_pct != current_primary_current_soc_pct or
                                         self.current.primary_remaining_km != current_primary_remaining_range_km or
                                         self.current.secondary_current_pct != current_secondary_current_soc_pct or
                                         self.current.secondary_remaining_km != current_secondary_remaining_range_km)):

                self.current = Range(vehicle=self.vehicle,
                                     captured_timestamp=range_status.carCapturedTimestamp.value,
                                     total_range_km=current_total_range_km,
                                     primary_current_pct=current_primary_current_soc_pct,
                                     primary_remaining_km=current_primary_remaining_range_km,
                                     secondary_current_pct=current_secondary_current_soc_pct,
                                     secondary_remaining_km=current_secondary_remaining_range_km)

                self.update()
