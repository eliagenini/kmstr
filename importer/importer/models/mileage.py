from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from models.base import Base
from models.datetime_decorator import DatetimeDecorator


class Mileage(Base):
    __tablename__ = 'mileages'
    __table_args__ = {'schema': 'kmstr'}

    id = Column(Integer, primary_key=True)
    vin = Column(String, ForeignKey('kmstr.vehicles.vin'))
    captured_timestamp = Column(DatetimeDecorator(timezone=True), nullable=False)
    mileage_km = Column(Integer, nullable=False)

    vehicle = relationship("Vehicle")

    def __init__(self, vehicle, captured_timestamp, mileage_km):
        self.vehicle = vehicle
        self.captured_timestamp = captured_timestamp
        self.mileage_km = mileage_km
