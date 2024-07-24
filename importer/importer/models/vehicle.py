from weconnect.addressable import AddressableLeaf
from sqlalchemy import Boolean, Column, Integer, String

from models.base import Base
from models.datetime_decorator import DatetimeDecorator


class Vehicle(Base):
    __tablename__ = 'vehicles'
    __table_args__ = {'schema': 'kmstr'}

    vin = Column(String(17), primary_key=True)
    model = Column(String(256))
    nickname = Column(String(256))
    online = Column(Boolean)
    last_update = Column(DatetimeDecorator)
    last_change = Column(DatetimeDecorator)

    remote = None

    def __init__(self, vin):
        self.vin = vin

    def connect(self, vehicle):
        self.remote = vehicle
        self.add_observer()

    def add_observer(self):
        if self.remote:
            self.remote.model.addObserver(self.__on_model_change, AddressableLeaf.ObserverEvent.VALUE_CHANGED)

            if self.remote.model.enabled and self.model != self.remote.model.value:
                self.model = self.remote.model.value

            self.remote.nickname.addObserver(self.__on_nickname_change, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            if self.remote.nickname.enabled and self.nickname != self.remote.nickname.value:
                self.nickname = self.remote.nickname.value

    def __on_model_change(self, element, flags):
        if self.model != element.value:
            self.model = element.value

    def __on_nickname_change(self, element, flags):
        if self.nickname != element.value:
            self.nickname = element.value

    def to_string(self):
        return f'{self.nickname} ({self.model})'
