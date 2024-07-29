from enum import Enum, auto
import logging
from datetime import datetime, timezone, timedelta
from agents.base import BaseAgent
from sqlalchemy import and_

from weconnect.addressable import AddressableLeaf, AddressableAttribute

from models.parking import Parking
from dtos.position import Position
from utils.location_util import location_from_lat_lon_with_geofence

LOG = logging.getLogger("kmstr")


class ParkingAgent(BaseAgent):

    def __init__(self, session, vehicle):
        LOG.debug("Initializing PositionAgent")
        super().__init__(session, vehicle)

        self.current = self.get_last()

        # register for updates:
        if self.vehicle.remote is not None:
            if (self.vehicle.remote.statusExists('parking', 'parkingPosition')
                    and self.vehicle.remote.domains['parking']['parkingPosition'].enabled):

                self.vehicle.remote.domains['parking']['parkingPosition'].carCapturedTimestamp.addObserver(
                    self.__on_car_captured_timestamp_changed,
                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                    onUpdateComplete=True)

                self.__on_car_captured_timestamp_changed(
                    self.vehicle.remote.domains['parking']['parkingPosition'].carCapturedTimestamp,
                    None
                )

    def get_last(self):
        super().get_last()
        return (self.session.query(Parking)
                .filter(Parking.vehicle == self.vehicle)
                .order_by(Parking.captured_timestamp.desc())
                .first())

    def __on_car_captured_timestamp_changed(self, element, flags):
        parking_position = self.vehicle.remote.domains['parking']['parkingPosition']
        if (self.current is None or (parking_position.carCapturedTimestamp.enabled and
                                     parking_position.carCapturedTimestamp.value is not None and
                                     parking_position.carCapturedTimestamp.value > self.current.captured_timestamp and
                                     parking_position.latitude.enabled and
                                     parking_position.latitude.value is not None and
                                     parking_position.longitude.enabled and
                                     parking_position.longitude.value is not None)):
            self.current = self.get_current_parking_position(parking_position)
            self.update()

    def get_current_parking_position(self, parking_position):
        location = location_from_lat_lon_with_geofence(
            self.session,
            latitude=parking_position.latitude.value,
            longitude=parking_position.longitude.value
        )

        return Parking(
            vehicle=self.vehicle,
            latitude=parking_position.latitude.value,
            longitude=parking_position.longitude.value,
            location=location,
            captured_timestamp=parking_position.carCapturedTimestamp.value
        )
