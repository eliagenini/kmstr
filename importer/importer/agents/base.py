from abc import ABC
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm.exc import ObjectDeletedError

import logging

LOG = logging.getLogger("kmstr")


class BaseAgent(ABC):
    def __init__(self, session, vehicle):
        self.current = None
        self.session = session
        self.vehicle = session.merge(vehicle)

    def commit(self):
        self.session.commit()

    def refresh(self):
        if self.current is not None:
            try:
                self.session.refresh(self.current)
            except ObjectDeletedError:
                LOG.warning('Last range entry was deleted')
                self.current = self.get_last()
            except InvalidRequestError:
                LOG.warning('Last range entry was not persisted')
                self.current = self.get_last()

    def update(self):
        with self.session.begin_nested():
            try:
                self.session.add(self.current)
            except IntegrityError as err:
                LOG.warning(
                    'Could not add entry to the database, this is usually due to an error in the WeConnect API (%s)',
                    err)
        self.session.commit()

    def get_last(self):
        LOG.debug("Looking for last record")
