import logging
from datetime import datetime, timezone, timedelta
from agents.base import BaseAgent

from utils.location_util import amenity_from_lat_lon
from weconnect.addressable import AddressableLeaf, AddressableAttribute

from models import Refuel

LOG = logging.getLogger("kmstr")


class RefuelAgent(BaseAgent):
    def __init__(self, session, vehicle):
        LOG.debug("Initializing RefuelAgent")
        super().__init__(session, vehicle)

        self.primary_current_soc_pct = None
        self.current = None

        self.last_position = None

        if self.vehicle.remote is not None:
            if (self.vehicle.remote.statusExists('fuelStatus', 'rangeStatus') and
                    self.vehicle.remote.domains['fuelStatus']['rangeStatus'].enabled):
                self.vehicle.remote.domains['fuelStatus']['rangeStatus'].carCapturedTimestamp.addObserver(
                    self.__on_car_captured_timestamp_change,
                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                    onUpdateComplete=True)

                self.__on_car_captured_timestamp_change(
                    self.vehicle.remote.domains['fuelStatus']['rangeStatus'].carCapturedTimestamp, None
                )

            if (self.vehicle.remote.statusExists('parking', 'parkingPosition') and
                    self.vehicle.remote.domains['parking']['parkingPosition'].enabled):
                self.vehicle.remote.domains['parking']['parkingPosition'].carCapturedTimestamp.addObserver(
                    self.__on_parking_position_car_captured_timestamp_changed,
                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                    onUpdateComplete=True)
                self.__on_parking_position_car_captured_timestamp_changed(self.vehicle.remote.domains['parking']['parkingPosition'].carCapturedTimestamp,
                                                                          None)
            else:
                self.vehicle.remote.domains.addObserver(self.__on_statuses_change,
                                                        AddressableLeaf.ObserverEvent.ENABLED,
                                                        onUpdateComplete=True)

    def __on_statuses_change(self, element, flags):
        if isinstance(element, AddressableAttribute) and element.getGlobalAddress().endswith('parkingPosition/carCapturedTimestamp'):
            # only add if not in list of observers
            if self.__on_parking_position_car_captured_timestamp_changed not in element.getObservers(flags=AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                                                                                     onUpdateComplete=True):
                element.addObserver(self.__on_parking_position_car_captured_timestamp_changed,
                                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                                    onUpdateComplete=True)
                self.vehicle.remote.domains.removeObserver(self.__on_statuses_change)
                self.__on_parking_position_car_captured_timestamp_changed(element, flags)

    def __on_car_captured_timestamp_change(self, element, flags):  # noqa: C901
        self.refresh()

        if element is not None and element.value is not None:
            range_status = self.vehicle.remote.domains['fuelStatus']['rangeStatus']
            if (range_status.primaryEngine.currentSOC_pct.enabled
                    and element is not None and element.value > (
                            datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=1))):
                current_primary_current_soc_pct = range_status.primaryEngine.currentSOC_pct.value

                mileage_km = None
                if self.vehicle.remote.statusExists('measurements', 'odometerStatus'):
                    odometer_measurement = self.vehicle.remote.domains['measurements']['odometerStatus']
                    if odometer_measurement.odometer.enabled:
                        mileage_km = odometer_measurement.odometer.value

                position_latitude = None
                position_longitude = None
                location = None
                if self.vehicle.remote.statusExists('parking', 'parkingPosition'):
                    parking_position = self.vehicle.remote.domains['parking']['parkingPosition']
                    if parking_position.latitude.enabled and parking_position.latitude.value is not None \
                            and parking_position.longitude.enabled and parking_position.longitude.value is not None:
                        position_latitude = parking_position.latitude.value
                        position_longitude = parking_position.longitude.value
                        location = amenity_from_lat_lon(self.session, parking_position.latitude.value, parking_position.longitude.value, 150, 'fuel', withFallback=True)

                if position_latitude is None and self.last_position is not None and (self.last_position[0] > (element.value - timedelta(minutes=15))):
                    _, position_latitude, position_longitude = self.last_position
                    location = amenity_from_lat_lon(self.session, position_latitude, position_longitude, 150, 'fuel', withFallback=True)

                # Refuel event took place (as the car somethimes finds one or two percent of fuel somewhere lets give a 5 percent margin)
                if self.primary_current_soc_pct is not None and (
                        (current_primary_current_soc_pct - 5) > self.primary_current_soc_pct):
                    if self.current is None or (
                            self.current.date < (element.value - timedelta(minutes=30))):
                        LOG.info('Vehicle %s refueled from %d percent to %d percent', self.vehicle.vin,
                                 self.primary_current_soc_pct,
                                 current_primary_current_soc_pct)
                        self.current = Refuel(
                            vehicle=self.vehicle,
                            date=element.value,
                            mileage_km=mileage_km,
                            start_pct=self.primary_current_soc_pct,
                            end_pct=current_primary_current_soc_pct,
                            latitude=position_latitude,
                            longitude=position_longitude,
                            location=location)
                        self.update()
                    else:
                        LOG.info(
                            'Vehicle %s refueled from %d percent to %d percent. It looks like this session is continueing the previous refuel session',
                            self.vehicle.vin, self.primary_current_soc_pct, current_primary_current_soc_pct)
                        with self.session.begin_nested():
                            self.current.end_pct = current_primary_current_soc_pct
                            if self.current.mileage_km is None:
                                self.current.mileage_km = mileage_km
                        self.session.commit()
                    self.primary_current_soc_pct = current_primary_current_soc_pct
                # SoC decreased, normal usage
                elif self.primary_current_soc_pct is None or current_primary_current_soc_pct < self.primary_current_soc_pct:
                    self.primary_current_soc_pct = current_primary_current_soc_pct

    def __on_parking_position_car_captured_timestamp_changed(self, element, flags):
        if self.vehicle.remote.statusExists('parking', 'parkingPosition'):
            parking_position = self.vehicle.remote.domains['parking']['parkingPosition']
            if parking_position.carCapturedTimestamp.enabled and parking_position.carCapturedTimestamp.value is not None \
                    and parking_position.latitude.enabled and parking_position.latitude.value is not None \
                    and parking_position.longitude.enabled and parking_position.longitude.value is not None:
                position_timestamp = parking_position.carCapturedTimestamp.value
                position_latitude = parking_position.latitude.value
                position_longitude = parking_position.longitude.value
                self.last_position = (position_timestamp, position_latitude, position_longitude)
                return
        self.last_position = None
