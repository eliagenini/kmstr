from enum import Enum, auto
import logging
from datetime import datetime, timezone, timedelta
from agents.base import BaseAgent

from weconnect.addressable import AddressableLeaf, AddressableAttribute
from weconnect.elements.plug_status import PlugStatus

from models.trip import Trip, Position

LOG = logging.getLogger("kmstr")


class TripAgent(BaseAgent):
    class Mode(Enum):
        PARKING_POSITION = auto()
        READINESS_STATUS = auto()
        NONE = auto()

    def __init__(self, session, vehicle, update_interval):
        super().__init__(session, vehicle)

        self.mode = TripAgent.Mode.NONE
        self.trip = self.api.get_last_trip_by_vehicle(vehicle.id)
        self.last_parking_position = None

        self.update_interval = update_interval

        if self.trip is not None:
            if self.trip.date.get('end') is not None:
                end_position = self.trip.position.get('end')

                self.last_parking_position = ParkingPosition(
                    end_position.latitude,
                    end_position.longitude,
                    self.trip.date.get('end')
                )
            else:
                LOG.info(f'Vehicle {self.vehicle.vin} has still an open trip during startup, closing it now')
            self.trip = None

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
                    self.vehicle.remote.domains['parking']['parkingPosition'].carCapturedTimestamp, None)

                if not self.vehicle.remote.domains['parking']['parkingPosition'].error.enabled:
                    LOG.info(
                        f'Vehicle {self.vehicle.vin} provides a parkingPosition and thus allows to record trips based on position')
                    self.mode = TripAgent.Mode.PARKING_POSITION

                    self.vehicle.remote.domains['parking']['parkingPosition'].carCapturedTimestamp.addObserver(
                        self.__on_car_captured_timestamp_disabled,
                        AddressableLeaf.ObserverEvent.DISABLED,
                        onUpdateComplete=True)

            if self.mode == TripAgent.Mode.NONE:
                if self.vehicle.remote.statusExists('readiness', 'readinessStatus') \
                        and self.vehicle.remote.domains['readiness']['readinessStatus'].enabled:
                    if self.vehicle.remote.domains['readiness']['readinessStatus'].connectionState is not None \
                            and self.vehicle.remote.domains['readiness']['readinessStatus'].connectionState.enabled:
                        self.vehicle.remote.domains['readiness']['readinessStatus'].connectionState.isActive \
                            .addObserver(self.__on_is_active_changed, AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                         onUpdateComplete=True)
                        self.vehicle.remote.domains['readiness']['readinessStatus'].connectionState.isActive \
                            .addObserver(self.__on_is_active_enabled_disabled, (
                                AddressableLeaf.ObserverEvent.ENABLED | AddressableLeaf.ObserverEvent.DISABLED),
                                         onUpdateComplete=True)
                        LOG.info(
                            f'Vehicle {self.vehicle.vin} provides isActive flag in readinessStatus and thus allows to record trips with several minutes'
                            ' inaccuracy')
                        self.mode = TripAgent.Mode.READINESS_STATUS
                self.vehicle.remote.domains.addObserver(self.__on_statuses_change,
                                                        AddressableLeaf.ObserverEvent.ENABLED,
                                                        onUpdateComplete=True)

            if self.mode == TripAgent.Mode.READINESS_STATUS:
                if self.vehicle.remote.statusExists('charging', 'plugStatus'):
                    plugStatus = self.vehicle.remote.domains['charging']['plugStatus']
                    if plugStatus.enabled and plugStatus.plugConnectionState.enabled:
                        plugStatus.plugConnectionState.addObserver(self.__on_plug_connection_state_changed,
                                                                   AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                   onUpdateComplete=True)
                self.vehicle.remote.addObserver(self.__on_later_parking_enabled,
                                                AddressableLeaf.ObserverEvent.UPDATED_FROM_CAR,
                                                onUpdateComplete=True)
            elif self.mode == TripAgent.Mode.NONE:
                LOG.info(f'Vehicle {self.vehicle.vin} currently cannot record trips. This may change in the future.')
                self.vehicle.remote.addObserver(self.__on_later_parking_enabled,
                                                AddressableLeaf.ObserverEvent.UPDATED_FROM_CAR,
                                                onUpdateComplete=True)

    def __on_later_parking_enabled(self, element, flags):
        if self.vehicle.remote is not None:
            if self.vehicle.remote.statusExists('parking', 'parkingPosition') \
                    and self.vehicle.remote.domains['parking']['parkingPosition'].enabled:
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
        if isinstance(element, AddressableAttribute) and element.getGlobalAddress().endswith(
                'parkingPosition/carCapturedTimestamp'):
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
        # if self.trip is not None:
        #     try:
        #         self.session.refresh(self.trip)
        #     except ObjectDeletedError:
        #         LOG.warning('Last trip entry was deleted')
        #         self.trip = None
        #     except InvalidRequestError:
        #         LOG.warning('Last trip entry was not persisted')
        #         self.trip = None

        if self.mode == TripAgent.Mode.PARKING_POSITION:
            if element.parent.error.enabled:
                LOG.debug(f'Vehicle {self.vehicle.vin} removed a parkingPosition but there was an error set')
                return
            if self.trip is not None:
                LOG.info(
                    f'Vehicle {self.vehicle.vin} removed a parkingPosition but there was an open trip, closing it now')
                self.trip = None
            time = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0) - timedelta(
                seconds=self.update_interval)

            # if Privacy.NO_LOCATIONS not in self.privacy:
            startPositionLatitude = self.lastParkingPositionLatitude
            startPositionLongitude = self.lastParkingPositionLongitude
            # else:
            #     startPositionLatitude = None
            #     startPositionLongitude = None
            _trip = {
                'vehicle': self.vehicle.id,
                'date': {
                    'start': time
                },
                'position': {
                    'start': Position(lat=startPositionLatitude, long=startPositionLongitude)
                }
            }

            if self.vehicle.remote.statusExists('measurements', 'odometerStatus') \
                    and self.vehicle.remote.domains['measurements']['odometerStatus'].enabled:
                odometerMeasurement = self.vehicle.remote.domains['measurements']['odometerStatus']
                if odometerMeasurement.odometer.enabled and odometerMeasurement.odometer is not None:
                    _trip['mileage'] = {
                        'start': odometerMeasurement.odometer.value
                    }

            self.trip = self.api.put(_trip)
            LOG.info(f'Vehicle {self.vehicle.vin} started a trip')

    def __on_car_captured_timestamp_changed(self, element, flags):
        if self.mode == TripAgent.Mode.PARKING_POSITION:
            parkingPosition = self.vehicle.remote.domains['parking']['parkingPosition']
            if parkingPosition.carCapturedTimestamp.enabled and parkingPosition.carCapturedTimestamp.value is not None:
                self.lastParkingPositionTimestamp = parkingPosition.carCapturedTimestamp.value
            if parkingPosition.latitude.enabled and parkingPosition.latitude.value is not None \
                    and parkingPosition.longitude.enabled and parkingPosition.longitude.value is not None:
                self.lastParkingPositionLatitude = parkingPosition.latitude.value
                self.lastParkingPositionLongitude = parkingPosition.longitude.value

    def __on_car_captured_timestamp_enabled(self, element, flags):  # noqa: C901
        if self.mode == TripAgent.Mode.PARKING_POSITION:
            parkingPosition = self.vehicle.remote.domains['parking']['parkingPosition']
            if parkingPosition.carCapturedTimestamp.enabled and parkingPosition.carCapturedTimestamp.value is not None:
                self.lastParkingPositionTimestamp = parkingPosition.carCapturedTimestamp.value
            if parkingPosition.latitude.enabled and parkingPosition.latitude.value is not None \
                    and parkingPosition.longitude.enabled and parkingPosition.longitude.value is not None:
                self.lastParkingPositionLatitude = parkingPosition.latitude.value
                self.lastParkingPositionLongitude = parkingPosition.longitude.value
            if self.trip is not None:
                if parkingPosition.carCapturedTimestamp.enabled and parkingPosition.carCapturedTimestamp.value is not None:
                    if parkingPosition.carCapturedTimestamp.value > self.trip.startDate:
                        self.trip.date['end'] = parkingPosition.carCapturedTimestamp.value

                        if parkingPosition.latitude.enabled and parkingPosition.latitude.value is not None \
                                and parkingPosition.longitude.enabled and parkingPosition.longitude.value is not None:
                            self.trip.position['end'] = Position(lat=parkingPosition.latitude, long=parkingPosition.longitude)

                        if self.vehicle.remote.statusExists('measurements', 'odometerStatus') \
                                and self.vehicle.remote.domains['measurements']['odometerStatus'].enabled:
                            odometerMeasurement = self.vehicle.remote.domains['measurements']['odometerStatus']
                            if odometerMeasurement.odometer.enabled and odometerMeasurement.odometer is not None:
                                self.trip.mileage['end'] = odometerMeasurement.odometer.value

# TODO: update (trip)
                        self.trip = None

                        LOG.info(f'Vehicle {self.vehicle.vin} ended a trip')
                    else:
                        self.session.delete(self.trip)
                        self.trip = None
                        LOG.info(f'Previously started trip for {self.vehicle.vin} was invalid. Deleting it now.')
            else:
                if flags is not None:
                    LOG.info(
                        f'Vehicle {self.vehicle.vin} provides a parking position, but no trip was started (this is ok during startup)')

    def __on_is_active_changed(self, element, flags):  # noqa: C901
        if self.trip is not None:
            try:
                self.session.refresh(self.trip)
            except ObjectDeletedError:
                LOG.warning('Last trip entry was deleted')
                self.trip = None
            except InvalidRequestError:
                LOG.warning('Last trip entry was not persisted')

        if self.mode == TripAgent.Mode.READINESS_STATUS:
            if self.vehicle.remote.statusExists('charging', 'plugStatus'):
                plugStatus = self.vehicle.remote.domains['charging']['plugStatus']
                if plugStatus.enabled and plugStatus.plugConnectionState.enabled \
                        and plugStatus.plugConnectionState.value == PlugStatus.PlugConnectionState.CONNECTED:
                    return
            if element.value:
                if self.trip is None:
                    time = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0) - timedelta(
                        seconds=self.update_interval)
                    self.trip = Trip(self.vehicle, time, None, None, None, None)
                    if self.vehicle.remote.statusExists('measurements', 'odometerStatus') \
                            and self.vehicle.remote.domains['measurements']['odometerStatus'].enabled:
                        odometerMeasurement = self.vehicle.remote.domains['measurements']['odometerStatus']
                        if odometerMeasurement.odometer.enabled and odometerMeasurement.odometer is not None:
                            self.trip.start_mileage_km = odometerMeasurement.odometer.value
                    with self.session.begin_nested():
                        try:
                            self.session.add(self.trip)
                        except IntegrityError as err:
                            LOG.warning(
                                'Could not add trip to the database, this is usually due to an error in the WeConnect API (%s)',
                                err)
                    self.session.commit()
                    LOG.info(f'Vehicle {self.vehicle.vin} started a trip')
            else:
                if self.trip is not None:
                    with self.session.begin_nested():
                        self.trip.endDate = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0)
                        if self.vehicle.remote.statusExists('measurements', 'odometerStatus') \
                                and self.vehicle.remote.domains['measurements']['odometerStatus'].enabled:
                            odometerMeasurement = self.vehicle.remote.domains['measurements']['odometerStatus']
                            if odometerMeasurement.odometer.enabled and odometerMeasurement.odometer is not None:
                                self.trip.end_mileage_km = odometerMeasurement.odometer.value
                    self.session.commit()

                    self.trip = None

                    LOG.info(f'Vehicle {self.vehicle.vin} ended a trip')
                else:
                    if flags is not None:
                        LOG.info(
                            f'Vehicle {self.vehicle.vin} reports to be inactive, but no trip was started (this is ok during startup)')

    def __on_is_active_enabled_disabled(self, element, flags):  # noqa: C901
        if self.trip is not None:
            try:
                self.session.refresh(self.trip)
            except ObjectDeletedError:
                LOG.warning('Last trip entry was deleted')
                self.trip = None
            except InvalidRequestError:
                LOG.warning('Last trip entry was not persisted')

        if self.mode == TripAgent.Mode.READINESS_STATUS:
            if self.vehicle.remote.statusExists('charging', 'plugStatus'):
                plugStatus = self.vehicle.remote.domains['charging']['plugStatus']
                if plugStatus.enabled and plugStatus.plugConnectionState.enabled \
                        and plugStatus.plugConnectionState.value == PlugStatus.PlugConnectionState.CONNECTED:
                    return
            if (flags & AddressableLeaf.ObserverEvent.ENABLED):
                if self.trip is None:
                    time = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0) - timedelta(
                        seconds=self.update_interval)
                    self.trip = Trip(self.vehicle, time, None, None, None, None)
                    if self.vehicle.remote.statusExists('measurements', 'odometerStatus') \
                            and self.vehicle.remote.domains['measurements']['odometerStatus'].enabled:
                        odometerMeasurement = self.vehicle.remote.domains['measurements']['odometerStatus']
                        if odometerMeasurement.odometer.enabled and odometerMeasurement.odometer is not None:
                            self.trip.start_mileage_km = odometerMeasurement.odometer.value
                    with self.session.begin_nested():
                        try:
                            self.session.add(self.trip)
                        except IntegrityError as err:
                            LOG.warning(
                                'Could not add trip to the database, this is usually due to an error in the WeConnect API (%s)',
                                err)
                    self.session.commit()
                    LOG.info(f'Vehicle {self.vehicle.vin} started a trip')
            elif (flags & AddressableLeaf.ObserverEvent.DISABLED):
                if self.trip is not None:
                    with self.session.begin_nested():
                        self.trip.endDate = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0)
                        if self.vehicle.remote.statusExists('measurements', 'odometerStatus') \
                                and self.vehicle.remote.domains['measurements']['odometerStatus'].enabled:
                            odometerMeasurement = self.vehicle.remote.domains['measurements']['odometerStatus']
                            if odometerMeasurement.odometer.enabled and odometerMeasurement.odometer is not None:
                                self.trip.end_mileage_km = odometerMeasurement.odometer.value
                    self.session.commit()

                    self.trip = None

                    LOG.info(f'Vehicle {self.vehicle.vin} ended a trip')
                else:
                    if flags is not None:
                        LOG.info(
                            f'Vehicle {self.vehicle.vin} reports to be inactive, but no trip was started (this is ok during startup)')

    def __on_plug_connection_state_changed(self, element, flags):  # noqa: C901
        if self.trip is not None:
            try:
                self.session.refresh(self.trip)
            except ObjectDeletedError:
                LOG.warning('Last trip entry was deleted')
                self.trip = None
            except InvalidRequestError:
                LOG.warning('Last trip entry was not persisted')

        plugStatus = self.vehicle.remote.domains['charging']['plugStatus']
        if element.value == PlugStatus.PlugConnectionState.CONNECTED:
            if self.trip is not None:
                with self.session.begin_nested():
                    if plugStatus.carCapturedTimestamp.enabled:
                        self.trip.endDate = plugStatus.carCapturedTimestamp.value
                    else:
                        self.trip.endDate = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0)
                    if self.vehicle.remote.statusExists('measurements', 'odometerStatus') \
                            and self.vehicle.remote.domains['measurements']['odometerStatus'].enabled:
                        odometerMeasurement = self.vehicle.remote.domains['measurements']['odometerStatus']
                        if odometerMeasurement.odometer.enabled and odometerMeasurement.odometer is not None:
                            self.trip.end_mileage_km = odometerMeasurement.odometer.value
                self.session.commit()

                self.trip = None

                LOG.info(f'Vehicle {self.vehicle.vin} ended a trip (car was connected to charger)')
        elif element.value == PlugStatus.PlugConnectionState.DISCONNECTED:
            if self.vehicle.remote.statusExists('readiness', 'readinessStatus'):
                readinessStatus = self.vehicle.remote.domains['readiness']['readinessStatus']
                if readinessStatus.connectionState is not None and readinessStatus.connectionState.enabled \
                        and readinessStatus.connectionState.isActive.enabled and readinessStatus.connectionState.isActive.value is not None:
                    if self.trip is None:
                        if plugStatus.carCapturedTimestamp.enabled:
                            time = plugStatus.carCapturedTimestamp.value
                        else:
                            time = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0) - timedelta(
                                seconds=self.update_interval)
                        self.trip = Trip(self.vehicle, time, None, None, None, None)
                        if self.vehicle.remote.statusExists('measurements', 'odometerStatus') \
                                and self.vehicle.remote.domains['measurements']['odometerStatus'].enabled:
                            odometerMeasurement = self.vehicle.remote.domains['measurements']['odometerStatus']
                            if odometerMeasurement.odometer.enabled and odometerMeasurement.odometer is not None:
                                self.trip.start_mileage_km = odometerMeasurement.odometer.value
                        with self.session.begin_nested():
                            try:
                                self.session.add(self.trip)
                            except IntegrityError as err:
                                LOG.warning(
                                    'Could not add trip to the database, this is usually due to an error in the WeConnect API (%s)',
                                    err)
                        self.session.commit()
                        LOG.info(f'Vehicle {self.vehicle.vin} started a trip (car was disconnected from charger)')


class ParkingPosition:
    def __init__(self, lat, long, ts):
        self.latitude = lat
        self.longitude = long
        self.timestamp = ts
