from enum import Enum, auto
import logging
from datetime import datetime, timezone, timedelta
from agents.base import BaseAgent
from sqlalchemy import and_

from weconnect.addressable import AddressableLeaf, AddressableAttribute

from models.trip import Trip
from dtos.position import Position
from utils.location_util import location_from_lat_lon_with_geofence

LOG = logging.getLogger("kmstr")


class TripAgent(BaseAgent):
    class Mode(Enum):
        PARKING_POSITION = auto()
        READINESS_STATUS = auto()
        NONE = auto()

    def __init__(self, session, vehicle, update_interval):
        LOG.debug("Initializing TripAgent")
        super().__init__(session, vehicle)

        self.mode = TripAgent.Mode.NONE
        self.current = self.get_last()

        self.last_parking_position = None

        self.update_interval = update_interval

        if self.current is not None:
            if self.current.end_date is not None:
                self.last_parking_position = Position(
                    latitude=self.current.end_position_latitude,
                    longitude=self.current.end_position_longitude,
                    timestamp=self.current.end_date
                )
            else:
                LOG.info(f'Vehicle {self.vehicle.vin} has still an open trip during startup, closing it now')
            self.current = None

        # register for updates:
        if self.vehicle.remote is not None:
            if (self.vehicle.remote.statusExists('parking', 'parkingPosition')
                    and self.vehicle.remote.domains['parking']['parkingPosition'].enabled):

                self.vehicle.remote.domains['parking']['parkingPosition'].carCapturedTimestamp.addObserver(
                    self.__on_car_captured_timestamp_enabled,
                    AddressableLeaf.ObserverEvent.ENABLED,
                    onUpdateComplete=True)

                self.vehicle.remote.domains['parking']['parkingPosition'].carCapturedTimestamp.addObserver(
                    self.__on_car_captured_timestamp_changed,
                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                    onUpdateComplete=True)

                self.__on_car_captured_timestamp_changed(
                    self.vehicle.remote.domains['parking']['parkingPosition'].carCapturedTimestamp,
                    None
                )

                if not self.vehicle.remote.domains['parking']['parkingPosition'].error.enabled:
                    LOG.info(
                        f'Vehicle {self.vehicle.vin} provides a parkingPosition and thus allows to record trips based on position')
                    self.mode = TripAgent.Mode.PARKING_POSITION

                    self.vehicle.remote.domains['parking']['parkingPosition'].carCapturedTimestamp.addObserver(
                        self.__on_car_captured_timestamp_disabled,
                        AddressableLeaf.ObserverEvent.DISABLED,
                        onUpdateComplete=True)

            if self.mode == TripAgent.Mode.NONE:
                if (self.vehicle.remote.statusExists('readiness', 'readinessStatus') and
                        self.vehicle.remote.domains['readiness']['readinessStatus'].enabled):

                    if (self.vehicle.remote.domains['readiness']['readinessStatus'].connectionState is not None and
                            self.vehicle.remote.domains['readiness']['readinessStatus'].connectionState.enabled):

                        self.vehicle.remote.domains['readiness']['readinessStatus'].connectionState.isActive.addObserver(
                            self.__on_is_active_changed,
                            AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                            onUpdateComplete=True
                        )

                        self.vehicle.remote.domains['readiness']['readinessStatus'].connectionState.isActive.addObserver(
                            self.__on_is_active_enabled_disabled,
                            (AddressableLeaf.ObserverEvent.ENABLED | AddressableLeaf.ObserverEvent.DISABLED),
                            onUpdateComplete=True
                        )

                        LOG.info(
                            f'Vehicle {self.vehicle.vin} provides isActive flag in readinessStatus and thus allows to record trips with several minutes'
                            ' inaccuracy')
                        self.mode = TripAgent.Mode.READINESS_STATUS

                self.vehicle.remote.domains.addObserver(self.__on_statuses_change,
                                                        AddressableLeaf.ObserverEvent.ENABLED,
                                                        onUpdateComplete=True)

            if self.mode == TripAgent.Mode.READINESS_STATUS:
                self.vehicle.remote.addObserver(self.__on_later_parking_enabled,
                                                AddressableLeaf.ObserverEvent.UPDATED_FROM_CAR,
                                                onUpdateComplete=True)
            elif self.mode == TripAgent.Mode.NONE:
                LOG.info(f'Vehicle {self.vehicle.vin} currently cannot record trips. This may change in the future.')
                self.vehicle.remote.addObserver(self.__on_later_parking_enabled,
                                                AddressableLeaf.ObserverEvent.UPDATED_FROM_CAR,
                                                onUpdateComplete=True)

    def get_last(self):
        super().get_last()
        return (self.session.query(Trip)
                .filter(and_(Trip.vehicle == self.vehicle,
                             Trip.start_date.isnot(None)))
                .order_by(Trip.start_date.desc())
                .first())

    def __on_later_parking_enabled(self, element, flags):
        if self.vehicle.remote is not None:
            if (self.vehicle.remote.statusExists('parking', 'parkingPosition') and
                    self.vehicle.remote.domains['parking']['parkingPosition'].enabled):

                self.vehicle.remote.domains['parking']['parkingPosition'].carCapturedTimestamp.addObserver(
                    self.__on_car_captured_timestamp_enabled,
                    AddressableLeaf.ObserverEvent.ENABLED,
                    onUpdateComplete=True)

                self.vehicle.remote.domains['parking']['parkingPosition'].carCapturedTimestamp.addObserver(
                    self.__on_car_captured_timestamp_changed,
                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                    onUpdateComplete=True)

                self.__on_car_captured_timestamp_changed(
                    self.vehicle.remote.domains['parking']['parkingPosition'].carCapturedTimestamp, None)

                if not self.vehicle.remote.domains['parking']['parkingPosition'].error.enabled:
                    LOG.info(
                        f'Vehicle {self.vehicle.vin} provides a parkingPosition and thus allows to record trips based on position')
                    self.mode = TripAgent.Mode.PARKING_POSITION

                    self.vehicle.remote.domains['parking']['parkingPosition'].carCapturedTimestamp.addObserver(
                        self.__on_car_captured_timestamp_disabled,
                        AddressableLeaf.ObserverEvent.DISABLED,
                        onUpdateComplete=True)
                    self.vehicle.remote.removeObserver(self.__on_later_parking_enabled,
                                                       AddressableLeaf.ObserverEvent.UPDATED_FROM_CAR)

    def __on_statuses_change(self, element, flags):
        if (isinstance(element, AddressableAttribute) and
                element.getGlobalAddress().endswith('parkingPosition/carCapturedTimestamp')):
            # only add if not in list of observers
            if self.__on_car_captured_timestamp_enabled not in element.getObservers(
                    flags=AddressableLeaf.ObserverEvent.VALUE_CHANGED, onUpdateComplete=True):
                element.addObserver(self.__on_car_captured_timestamp_enabled,
                                    AddressableLeaf.ObserverEvent.ENABLED,
                                    onUpdateComplete=True)
                element.addObserver(self.__on_car_captured_timestamp_changed,
                                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                    onUpdateComplete=True)
                element.addObserver(self.__on_car_captured_timestamp_disabled,
                                    AddressableLeaf.ObserverEvent.DISABLED,
                                    onUpdateComplete=True)
                LOG.info(
                    f'Vehicle {self.vehicle.vin} now provides a parkingPosition and thus allows to record trips based on position')
                self.mode = TripAgent.Mode.PARKING_POSITION
                self.vehicle.remote.domains.removeObserver(self.__on_statuses_change)
                self.__on_car_captured_timestamp_enabled(element, flags)

    def __on_car_captured_timestamp_disabled(self, element: AddressableAttribute, flags):  # noqa: C901
        self.refresh()

        if self.mode == TripAgent.Mode.PARKING_POSITION:
            if element.parent.error.enabled:
                LOG.debug(f'Vehicle {self.vehicle.vin} removed a parkingPosition but there was an error set')
                return
            if self.current is not None:
                LOG.info(f'Vehicle {self.vehicle.vin} removed a parkingPosition but there was an open trip, closing it now')
                self.current = None

            time = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0) - timedelta(seconds=self.update_interval)

            self.current = Trip(
                vehicle=self.vehicle,
                start_date=time,
                start_position_latitude=None,  # None last_parking_position
                start_position_longitude=None,
                start_location=None,
                start_mileage=None)

            if self.last_parking_position is not None:
                self.current.start_position_latitude = self.last_parking_position.latitude
                self.current.start_position_longitude = self.last_parking_position.longitude
                self.current.start_location = self.last_parking_position.get_location(self.session)

            if (self.vehicle.remote.statusExists('measurements', 'odometerStatus') and
                    self.vehicle.remote.domains['measurements']['odometerStatus'].enabled):
                odometer_measurement = self.vehicle.remote.domains['measurements']['odometerStatus']
                if odometer_measurement.odometer.enabled and odometer_measurement.odometer is not None:
                    self.current.start_mileage = odometer_measurement.odometer.value

            self.update()
            LOG.info(f'Vehicle {self.vehicle.vin} started a trip')

    def __on_car_captured_timestamp_changed(self, element, flags):
        if self.mode == TripAgent.Mode.PARKING_POSITION:
            self.set_last_parking_position(self.vehicle.remote.domains['parking']['parkingPosition'])

    def __on_car_captured_timestamp_enabled(self, element, flags):  # noqa: C901
        if self.mode == TripAgent.Mode.PARKING_POSITION:
            parking_position = self.vehicle.remote.domains['parking']['parkingPosition']
            self.set_last_parking_position(parking_position=parking_position)

            if self.current is not None:
                if parking_position.carCapturedTimestamp.enabled and parking_position.carCapturedTimestamp.value is not None:
                    with self.session.begin_nested():
                        if parking_position.carCapturedTimestamp.value > self.current.start_date:
                            self.current.end_date = parking_position.carCapturedTimestamp.value

                            if (parking_position.latitude.enabled and parking_position.latitude.value is not None and
                                    parking_position.longitude.enabled and parking_position.longitude.value is not None):
                                self.current.end_position_latitude = parking_position.latitude
                                self.current.end_position_longitude = parking_position.longitude
                                self.current.end_position_location = location_from_lat_lon_with_geofence(self.session,
                                                                                                         parking_position.latitude,
                                                                                                         parking_position.longitude)

                            if (self.vehicle.remote.statusExists('measurements', 'odometerStatus') and
                                    self.vehicle.remote.domains['measurements']['odometerStatus'].enabled):
                                odometer_measurement = self.vehicle.remote.domains['measurements']['odometerStatus']
                                if odometer_measurement.odometer.enabled and odometer_measurement.odometer is not None:
                                    self.current.end_mileage = odometer_measurement.odometer.value

                            LOG.info(f'Vehicle {self.vehicle.vin} ended a trip')
                        else:
                            self.session.delete(self.current)
                            LOG.info(f'Previously started trip for {self.vehicle.vin} was invalid. Deleting it now.')

                    self.session.commit()
                    self.current = None
            else:
                if flags is not None:
                    LOG.info(f'Vehicle {self.vehicle.vin} provides a parking position, but no trip was started (this is ok during startup)')

    def __on_is_active_changed(self, element, flags):  # noqa: C901
        self.refresh()

        if self.mode == TripAgent.Mode.READINESS_STATUS:
            if element.value:
                if self.current is None:
                    time = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0) - timedelta(
                        seconds=self.update_interval)

                    self.current = Trip(
                        vehicle=self.vehicle,
                        start_date=time,
                        start_position_latitude=None,
                        start_position_longitude=None,
                        start_location=None,
                        start_mileage=None)

                    if (self.vehicle.remote.statusExists('measurements', 'odometerStatus') and
                            self.vehicle.remote.domains['measurements']['odometerStatus'].enabled):
                        odometer_measurement = self.vehicle.remote.domains['measurements']['odometerStatus']
                        if odometer_measurement.odometer.enabled and odometer_measurement.odometer is not None:
                            self.current.start_mileage = odometer_measurement.odometer.value

                    self.update()
                    LOG.info(f'Vehicle {self.vehicle.vin} started a trip')
            else:
                if self.current is not None:
                    with self.session.begin_nested():
                        self.current.end_date = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0)
                        if self.vehicle.remote.statusExists('measurements', 'odometerStatus') \
                                and self.vehicle.remote.domains['measurements']['odometerStatus'].enabled:
                            odometer_measurement = self.vehicle.remote.domains['measurements']['odometerStatus']
                            if odometer_measurement.odometer.enabled and odometer_measurement.odometer is not None:
                                self.current.end_mileage = odometer_measurement.odometer.value
                    self.session.commit()
                    self.current = None

                    LOG.info(f'Vehicle {self.vehicle.vin} ended a trip')
                else:
                    if flags is not None:
                        LOG.info(
                            f'Vehicle {self.vehicle.vin} reports to be inactive, but no trip was started (this is ok during startup)')

    def __on_is_active_enabled_disabled(self, element, flags):  # noqa: C901
        self.refresh()

        if self.mode == TripAgent.Mode.READINESS_STATUS:
            if (flags & AddressableLeaf.ObserverEvent.ENABLED):
                if self.current is None:
                    time = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0) - timedelta(
                        seconds=self.update_interval)

                    self.current = Trip(
                        vehicle=self.vehicle,
                        start_date=time,
                        start_position_latitude=None,
                        start_position_longitude=None,
                        start_location=None,
                        start_mileage=None)

                    if (self.vehicle.remote.statusExists('measurements', 'odometerStatus') and
                            self.vehicle.remote.domains['measurements']['odometerStatus'].enabled):
                        odometer_measurement = self.vehicle.remote.domains['measurements']['odometerStatus']
                        if odometer_measurement.odometer.enabled and odometer_measurement.odometer is not None:
                            self.current.start_mileage = odometer_measurement.odometer.value

                    self.update()
                    LOG.info(f'Vehicle {self.vehicle.vin} started a trip')
            elif (flags & AddressableLeaf.ObserverEvent.DISABLED):
                if self.current is not None:
                    with self.session.begin_nested():
                        self.current.end_date = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0)
                        if self.vehicle.remote.statusExists('measurements', 'odometerStatus') \
                                and self.vehicle.remote.domains['measurements']['odometerStatus'].enabled:
                            odometer_measurement = self.vehicle.remote.domains['measurements']['odometerStatus']
                            if odometer_measurement.odometer.enabled and odometer_measurement.odometer is not None:
                                self.current.end_mileage = odometer_measurement.odometer.value
                    self.session.commit()
                    self.current = None

                    LOG.info(f'Vehicle {self.vehicle.vin} ended a trip')
                else:
                    if flags is not None:
                        LOG.info(
                            f'Vehicle {self.vehicle.vin} reports to be inactive, but no trip was started (this is ok during startup)')

    def set_last_parking_position(self, parking_position):
        if (parking_position.carCapturedTimestamp.enabled and
                parking_position.carCapturedTimestamp.value is not None and
                parking_position.latitude.enabled and
                parking_position.latitude.value is not None and
                parking_position.longitude.enabled and
                parking_position.longitude.value is not None):
            self.last_parking_position = Position(
                latitude=parking_position.latitude.value,
                longitude=parking_position.longitude.value,
                timestamp=parking_position.carCapturedTimestamp.value)
