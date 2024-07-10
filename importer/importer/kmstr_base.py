__author__ = 'eliagenini'

import time
import logging
import logging.handlers

from weconnect import weconnect, addressable
from weconnect.errors import APICompatibilityError, AuthentificationError, TemporaryAuthentificationError
from weconnect.domain import Domain
from api import Vehicle

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LOG_LEVEL = "INFO"

LOG = logging.getLogger("kmstr")


def on_we_connect_event(element, flags):
    """Simple callback example

    Args:
        element (AddressableObject): Object for which an event occured
        flags (AddressableLeaf.ObserverEvent): Information about the type of the event
    """
    if isinstance(element, addressable.AddressableAttribute):
        if flags & addressable.AddressableLeaf.ObserverEvent.ENABLED:
            print(f'New attribute is available: {element.getGlobalAddress()}: {element.value}')
        elif flags & addressable.AddressableLeaf.ObserverEvent.VALUE_CHANGED:
            print(f'Value changed: {element.getGlobalAddress()}: {element.value}')
        elif flags & addressable.AddressableLeaf.ObserverEvent.DISABLED:
            print(f'Attribute is not available anymore: {element.getGlobalAddress()}')


class Kmstr:
    def __init__(self):
        self.loggingFormat = '%(asctime)s:%(levelname)s:%(module)s:%(message)s'
        self.loggingDateFormat = '%Y-%m-%dT%H:%M:%S%z'

        self.endpoint = 'http://localhost:3000'

        self.username = 'elia.genini@gmail.com'
        self.password = '12345678!'
        self.interval = 300
        # self.conn.login()
        # self.conn.addObserver(self.on_we_connect_event, addressable.AddressableLeaf.ObserverEvent.ALL)
        # self.conn.update()

    def run(self):
        logging.basicConfig(level=DEFAULT_LOG_LEVEL, format=self.loggingFormat, datefmt=self.loggingDateFormat)

        LOG.info("Starting Kmstr")

        conn = None
        try:
            LOG.info("Trying to login into WeConnect")
            conn = weconnect.WeConnect(username=self.username, password=self.password, updateAfterLogin=False,
                                       loginOnInit=False, maxAgePictures=86400, forceReloginAfter=21600)
            conn.addObserver(on_we_connect_event, addressable.AddressableLeaf.ObserverEvent.ALL)
            starttime = time.time()
            subsequentErrors = 0
            permanentErrors = 0
            sleeptime = self.interval
            while True:
                try:
                    conn.update(updateCapabilities=True,
                                updatePictures=True,
                                force=True,
                                selective=[Domain.ACCESS,
                                           Domain.AUTOMATION,
                                           Domain.USER_CAPABILITIES,
                                           Domain.DEPARTURE_TIMERS,
                                           Domain.FUEL_STATUS,
                                           Domain.VEHICLE_LIGHTS,
                                           Domain.READINESS,
                                           Domain.VEHICLE_HEALTH_INSPECTION,
                                           Domain.VEHICLE_HEALTH_WARNINGS,
                                           Domain.OIL_LEVEL,
                                           Domain.MEASUREMENTS,
                                           Domain.PARKING])

                    sleeptime = self.interval - ((time.time() - starttime) % self.interval)
                    permanentErrors = 0
                    subsequentErrors = 0

                except weconnect.TooManyRequestsError:
                    if subsequentErrors > 0:
                        LOG.error(
                            'Retrieval error during update. Too many requests from your account. Will try again after 15 minutes')
                    else:
                        LOG.warning(
                            'Retrieval error during update. Too many requests from your account. Will try again after 15 minutes')
                    sleeptime = 900
                    subsequentErrors += 1
                except weconnect.RetrievalError:
                    if subsequentErrors > 0:
                        LOG.error('Retrieval error during update. Will try again after configured interval of %ds',
                                  self.interval)
                    else:
                        LOG.warning('Retrieval error during update. Will try again after configured interval of %ds',
                                    self.interval)
                    subsequentErrors += 1
                except TemporaryAuthentificationError:
                    if subsequentErrors > 0:
                        LOG.error(
                            'Temporary error during reauthentification. Will try again after configured interval of %ds',
                            self.interval)
                    else:
                        LOG.warning(
                            'Temporary error during reauthentification. Will try again after configured interval of %ds',
                            self.interval)
                    subsequentErrors += 1
                except APICompatibilityError as e:
                    sleeptime = min((self.interval * pow(2, permanentErrors)), 86400)
                    if subsequentErrors > 0:
                        LOG.critical(
                            'There was a problem when communicating with WeConnect. If this problem persists please open a bug report: %s,'
                            ' will retry after %ds', e, sleeptime)
                    else:
                        LOG.warning(
                            'There was a problem when communicating with WeConnect. If this problem persists please open a bug report: %s,'
                            ' will retry after %ds', e, sleeptime)
                    subsequentErrors += 1
                    permanentErrors += 1

                #  Execute exactly every interval but if it misses its deadline only after the next interval
                time.sleep(sleeptime)
        except AuthentificationError as e:
            LOG.critical('There was a problem when authenticating with WeConnect: %s', e)
        except APICompatibilityError as e:
            LOG.critical('There was a problem when communicating with WeConnect.'
                         ' If this problem persists please open a bug report: %s', e)
        finally:
            if conn is not None:
                conn.disconnect()

    def init_vehicles(self):
        _vehicle = Vehicle(self.endpoint)
        for vin, vehicle in self.conn.vehicles.items():
            if not _vehicle.get(vin, 'vin'):
                print('# Vehicle {} to create'.format(vin))
                _v = _vehicle.put(
                    {'vin': vehicle.vin.value, 'model': vehicle.model.value, 'nickname': vehicle.nickname.value})
                print('    Created {}'.format(_v))
