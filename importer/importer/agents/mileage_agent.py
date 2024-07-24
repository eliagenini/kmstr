from datetime import datetime, timezone, timedelta

from sqlalchemy.exc import IntegrityError

from agents.base import BaseAgent

from sqlalchemy import and_

from weconnect.addressable import AddressableLeaf
from models import Mileage
import logging

LOG = logging.getLogger("kmstr")


class MileageAgent(BaseAgent):
    def __init__(self, session, vehicle):
        super().__init__(session, vehicle)

        self.current = self.get_last()

        if self.vehicle.remote is not None:
            if (self.vehicle.remote.statusExists('measurements', 'odometerStatus') and
                    self.vehicle.remote.domains['measurements']['odometerStatus'].enabled):
                self.vehicle.remote.domains['measurements']['odometerStatus'].carCapturedTimestamp.addObserver(
                    self.__on_car_captured_timestamp_change,
                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                    onUpdateComplete=True
                )
                self.__on_car_captured_timestamp_change(
                    self.vehicle.remote.domains['measurements']['odometerStatus'].carCapturedTimestamp, None)

    def get_last(self):
        return (self.session.query(Mileage)
                .filter(and_(Mileage.vehicle == self.vehicle,
                             Mileage.captured_timestamp.isnot(None)))
                .order_by(Mileage.captured_timestamp.desc())
                .first())

    def __on_car_captured_timestamp_change(self, element, flags):  # noqa: C901
        # Check that the data to add is not too old
        if element is not None and element.value is not None and element.value > (
                datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=7)):
            odometer_measurement = self.vehicle.remote.domains['measurements']['odometerStatus']
            current_mileage_km = odometer_measurement.odometer.value

            self.refresh()
            if self.current is None or (odometer_measurement.carCapturedTimestamp.value is not None and
                                        self.current.captured_timestamp != odometer_measurement.carCapturedTimestamp.value and
                                        self.current.mileage_km != current_mileage_km):
                self.current = Mileage(vehicle=self.vehicle,
                                       captured_timestamp=odometer_measurement.carCapturedTimestamp.value,
                                       mileage_km=current_mileage_km)

                with self.session.begin_nested():
                    try:
                        self.session.add(self.current)
                    except IntegrityError as err:
                        LOG.warning(
                            'Could not add mileage entry to the database, this is usually due to an error in the WeConnect API (%s)',
                            err)
                self.session.commit()
