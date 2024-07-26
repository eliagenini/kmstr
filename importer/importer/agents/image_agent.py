import io
from datetime import datetime, timezone, timedelta
from agents.base import BaseAgent
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm.exc import ObjectDeletedError
from weconnect.addressable import AddressableLeaf
from models import Picture
import logging

LOG = logging.getLogger("kmstr")


class ImageAgent(BaseAgent):
    def __init__(self, session, vehicle):
        LOG.debug("Initializing ImageAgent")
        super().__init__(session, vehicle)

        self.current = self.get_last()

        if self.vehicle.remote is not None:
            for picture in self.vehicle.remote.pictures:
                # New attribute is available: /vehicles/WVGZZZ1T5RW028165/pictures/car: <PIL.PngImagePlugin.PngImageFile image mode=RGBA size=776x436 at 0x740C6889CE30>
                self.vehicle.remote.pictures[picture].addObserver(
                    self.__on_picture_change,
                    AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                    onUpdateComplete=True
                )

                self.__on_picture_change(
                    self.vehicle.remote.pictures[picture], None)

    def get_last(self):
        super().get_last()
        result = {}
        pictures = (self.session.query(Picture)
                    .filter(Picture.vehicle == self.vehicle)
                    .all())

        for picture in pictures:
            result[picture.name] = picture

        return result

    def __on_picture_change(self, element, flags):
        if element is not None and element.value is not None:
            pic_array = io.BytesIO()
            element.value.save(pic_array, format='PNG')

            if element.localAddress not in self.current:
                self.current[element.localAddress] = Picture(
                    vehicle=self.vehicle,
                    name=element.localAddress,
                    image=pic_array.getvalue(),
                    captured_timestamp=element.lastChange
                )
            elif self.current[element.localAddress].captured_timestamp < element.lastChange:
                self.current[element.localAddress].image = pic_array.getvalue()
                self.current[element.localAddress].captured_timestamp = element.lastChange

            with self.session.begin_nested():
                try:
                    self.session.merge(self.current[element.localAddress])
                except IntegrityError as err:
                    LOG.warning(
                        'Could not add picture entry to the database, this is usually due to an error in the WeConnect API (%s)',
                        err)
            self.session.commit()
