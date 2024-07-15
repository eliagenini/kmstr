__author__ = 'eliagenini'

import time
import logging
import logging.handlers

from weconnect import weconnect
from weconnect.errors import APICompatibilityError, AuthentificationError, TemporaryAuthentificationError
from api import Vehicle, FuelLevel, TotalRange, Mileage, Parking

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LOG_LEVEL = "INFO"

LOG = logging.getLogger("kmstr")


class Kmstr:
    def __init__(self):
        self.loggingFormat = '%(asctime)s:%(levelname)s:%(module)s:%(message)s'
        self.loggingDateFormat = '%Y-%m-%dT%H:%M:%S%z'

        self.endpoint = 'http://localhost:3000'

        self.conn = None
        self.username = 'elia.genini@gmail.com'
        self.password = '12345678!'
        self.interval = 300

        self.vehicles = []

    def run(self):
        logging.basicConfig(level=DEFAULT_LOG_LEVEL, format=self.loggingFormat, datefmt=self.loggingDateFormat)

        LOG.info("Starting Kmstr")

        try:
            LOG.info("Trying to login into WeConnect")
            self.conn = weconnect.WeConnect(username=self.username, password=self.password, updateAfterLogin=True,
                                            forceReloginAfter=21600)
            self.conn.login()
            self.init_vehicles()

            errors = 0
            while True:
                if errors > 3:
                    exit()

                try:
                    LOG.info("Running importer")
                    self.get_data()
                except weconnect.TooManyRequestsError:
                    errors += 1
                    LOG.warning(
                        'Retrieval error during update. Too many requests from your account. Will try again after 15 minutes')
                except weconnect.RetrievalError:
                    errors += 1

                    LOG.warning('Retrieval error during update.')
                except TemporaryAuthentificationError:
                    errors += 1

                    LOG.warning('Temporary error during reauthentification.')

                LOG.info("Sleeping for %d seconds", self.interval * (errors+1))
                time.sleep(self.interval * (errors+1))

                self.conn.update(force=True)

        except APICompatibilityError as e:
            LOG.warning(
                'There was a problem when communicating with WeConnect. If this problem persists please open a bug report: %s',
                e)
        except AuthentificationError as e:
            LOG.critical('There was a problem when authenticating with WeConnect: %s', e)
        finally:
            if self.conn is not None:
                self.conn.disconnect()

    def init_vehicles(self):
        _vehicle = Vehicle(self.endpoint)
        for vin, vehicle in self.conn.vehicles.items():
            self.vehicles.append(vin)

            if not _vehicle.get(vin, 'vin'):
                LOG.info('# Vehicle {} to create'.format(vin))
                _v = _vehicle.put(
                    {'vin': vehicle.vin.value, 'model': vehicle.model.value, 'nickname': vehicle.nickname.value})
                LOG.info('    Created {}'.format(_v))

    def get_data(self):
        for vehicle in self.vehicles:
            id = Vehicle(self.endpoint).get(vehicle, 'vin')[0].get('id')

            LOG.info('# Getting data for {}'.format(vehicle))

            val = self.conn.getByAddressString(
                '/vehicles/{}/domains/measurements/odometerStatus/odometer'.format(vehicle)).value
            LOG.info('  Mileage: {} km'.format(val))
            Mileage(self.endpoint).put({'vehicle': id, 'mileage': val})

            val = self.conn.getByAddressString(
                '/vehicles/{}/domains/fuelStatus/rangeStatus/totalRange_km'.format(vehicle)).value
            LOG.info('  Total range: {} km'.format(val))
            TotalRange(self.endpoint).put({'vehicle': id, 'range': val})

            val = self.conn.getByAddressString(
                '/vehicles/{}/domains/fuelStatus/rangeStatus/primaryEngine/currentFuelLevel_pct'.format(vehicle)).value
            LOG.info('  Fuel level: {} %'.format(val))
            FuelLevel(self.endpoint).put({'vehicle': id, 'level': val})

            # Position
            lat = self.conn.getByAddressString(
                '/vehicles/{}/parking/parkingPosition/latitude'.format(vehicle)).value
            lon = self.conn.getByAddressString(
                '/vehicles/{}/parking/parkingPosition/longitude'.format(vehicle)).value
            LOG.info('  Parked at {},{}'.format(lat, lon))
            Parking(self.endpoint).put({'vehicle': id, 'latitude': lat, 'longitude': lon})

