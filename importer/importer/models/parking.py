from sqlalchemy import Column, Integer, String, ForeignKey, Float, BigInteger
from sqlalchemy.orm import relationship

from models.base import Base
from models.datetime_decorator import DatetimeDecorator


class Parking(Base):
    __tablename__ = 'parkings'
    __table_args__ = {'schema': 'kmstr'}

    id = Column(Integer, primary_key=True)
    vin = Column(String, ForeignKey('kmstr.vehicles.vin'))
    location_id = Column(BigInteger, ForeignKey('kmstr.locations.osm_id'))
    latitude = Column(Float)
    longitude = Column(Float)
    captured_timestamp = Column(DatetimeDecorator(timezone=True), nullable=False)

    location = relationship("Location")
    vehicle = relationship("Vehicle")

    def __init__(self, vehicle, latitude, longitude, location, captured_timestamp):
        self.vehicle = vehicle
        self.latitude = latitude
        self.longitude = longitude
        self.location = location
        self.captured_timestamp = captured_timestamp
