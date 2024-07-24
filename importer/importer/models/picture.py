from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship

from models.base import Base
from models.datetime_decorator import DatetimeDecorator


class Picture(Base):
    __tablename__ = 'pictures'
    __table_args__ = {'schema': 'kmstr'}

    id = Column(Integer, primary_key=True)
    vin = Column(String, ForeignKey('kmstr.vehicles.vin'))
    name = Column(String)
    image = Column(LargeBinary)
    captured_timestamp = Column(DatetimeDecorator(timezone=True), nullable=False)

    vehicle = relationship("Vehicle")

    def __init__(self, vehicle, name, image, captured_timestamp):
        self.vehicle = vehicle
        self.name = name
        self.image = image
        self.captured_timestamp = captured_timestamp
