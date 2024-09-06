__author__ = 'eliagenini'

import base64
import time
import logging
import logging.handlers

from PIL import Image
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import OperationalError

from weconnect import weconnect, addressable
from weconnect.addressable import AddressableLeaf
from weconnect.errors import APICompatibilityError, AuthentificationError, TemporaryAuthentificationError
from weconnect.domain import Domain
from weconnect.elements import vehicle as elementvehicle

from models import Vehicle, Picture
from agents import RangeAgent, MileageAgent, RefuelAgent, ImageAgent, TripAgent, ParkingAgent

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LOG_LEVEL = "INFO"

LOG = logging.getLogger("kmstr")


# def on_we_connect_event(element, flags):
#     """Simple callback example
#
#     Args:
#         element (AddressableObject): Object for which an event occured
#         flags (AddressableLeaf.ObserverEvent): Information about the type of the event
#     """
#     if isinstance(element, addressable.AddressableAttribute):
#         if flags & addressable.AddressableLeaf.ObserverEvent.ENABLED:
#             print(f'New attribute is available: {element.getGlobalAddress()}: {element.value}')
#         elif flags & addressable.AddressableLeaf.ObserverEvent.VALUE_CHANGED:
#             print(f'Value changed: {element.getGlobalAddress()}: {element.value}')
#         elif flags & addressable.AddressableLeaf.ObserverEvent.DISABLED:
#             print(f'Attribute is not available anymore: {element.getGlobalAddress()}')


class Kmstr:
    def __init__(self, username, password, interval, db_hostname, db_username, db_password, db_name, db_port, tz):
        self.session = None

        self.loggingFormat = '%(asctime)s:%(levelname)s:%(module)s:%(message)s'
        self.loggingDateFormat = '%Y-%m-%dT%H:%M:%S%z'

        self.engine = None
        self.session = None
        self.db_url = f'postgresql+psycopg://{db_username}:{db_password}@{db_hostname}:{db_port}/{db_name}'
        self.db_conn_args = {'options': f'-c timezone={tz}'}
        self.endpoint = 'http://localhost:3000'

        self.conn = None
        self.username = username # 'elia.genini@gmail.com'
        self.password = password #'12345678!'
        self.interval = interval
        self.subscriptions = []

        self.agents = {}
        self.vehicles = []
        # self.conn.login()
        # self.conn.addObserver(self.on_we_connect_event, addressable.AddressableLeaf.ObserverEvent.ALL)
        # self.conn.update()

    def run(self):
        logging.basicConfig(level=DEFAULT_LOG_LEVEL, format=self.loggingFormat, datefmt=self.loggingDateFormat)

        LOG.info("Starting Kmstr")

        try:
            self.engine = create_engine(self.db_url, pool_pre_ping=True, connect_args=self.db_conn_args)
            self.session = scoped_session(sessionmaker(bind=self.engine))()

            LOG.info("Trying to login into WeConnect")
            self.conn = weconnect.WeConnect(username=self.username, password=self.password, updateAfterLogin=False,
                                            loginOnInit=False, maxAgePictures=86400, forceReloginAfter=21600)
            self.conn.addObserver(self.on_enable, addressable.AddressableLeaf.ObserverEvent.ENABLED, onUpdateComplete=True)
            # self.conn.addObserver(on_we_connect_event, addressable.AddressableLeaf.ObserverEvent.ALL)

            self.vehicles = self.session.query(Vehicle).all()

            starttime = time.time()
            subsequentErrors = 0
            permanentErrors = 0
            sleeptime = self.interval
            while True:
                try:
                    self.conn.update(updateCapabilities=True,
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

                    for vehicle_agents in self.agents.values():
                        for agent in vehicle_agents:
                            agent.commit()

                        self.session.commit()

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
            if self.conn is not None:
                self.conn.disconnect()

    # def init_vehicles(self):
    #     _vehicle = Vehicle(self.endpoint)
    #     for vin, vehicle in self.conn.vehicles.items():
    #        if not _vehicle.get(vin, 'vin'):
    #            LOG.info('# Vehicle %s to create', vin)
    #            _v = _vehicle.put(
    #                {'vin': vehicle.vin.value, 'model': vehicle.model.value, 'nickname': vehicle.nickname.value})
    #            LOG.info('Created %s', _v)

    def on_enable(self, element, flags):
        if (flags & addressable.AddressableLeaf.ObserverEvent.ENABLED) and isinstance(element, elementvehicle.Vehicle):
            if element.vin not in self.agents:
                self.agents[element.vin.value] = []

            found_vehicle = None
            for vehicle in self.vehicles:
                if element.vin.value == vehicle.vin:
                    LOG.info('Found matching vehicle for vin %s in database', element.vin.value)
                    found_vehicle = vehicle
                    break
            if found_vehicle is None:
                LOG.info('Found no matching vehicle for vin %s in database, will create a new one', element.vin.value)
                found_vehicle = Vehicle(element.vin.value)
                with self.session.begin_nested():
                    self.session.add(found_vehicle)
                self.session.commit()

            found_vehicle.connect(element)

            self.agents[element.vin.value].append(RangeAgent(session=self.session, vehicle=found_vehicle))
            self.agents[element.vin.value].append(MileageAgent(session=self.session, vehicle=found_vehicle))
            self.agents[element.vin.value].append(RefuelAgent(session=self.session, vehicle=found_vehicle))
            self.agents[element.vin.value].append(ImageAgent(session=self.session, vehicle=found_vehicle))
            #self.agents[element.vin.value].append(TripAgent(session=self.session, vehicle=found_vehicle, update_interval=self.interval))
            self.agents[element.vin.value].append(ParkingAgent(session=self.session, vehicle=found_vehicle))
            # self.agents[element.vin.value].append(StateAgent(session=self.Session(), vehicle=foundVehicle, updateInterval=self.interval))
            # self.agents[element.vin.value].append(WarningLightAgent(session=self.Session(), vehicle=foundVehicle))
            # self.agents[element.vin.value].append(MaintenanceAgent(session=self.Session(), vehicle=foundVehicle))
