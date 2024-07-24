from sqlalchemy import Column, Integer, String, ForeignKey, Float, BigInteger
from sqlalchemy.orm import relationship

from models.base import Base
from models.datetime_decorator import DatetimeDecorator


class Refuel(Base):
    __tablename__ = 'refuels'
    __table_args__ = {'schema': 'kmstr'}

    id = Column(Integer, primary_key=True)
    vin = Column(String, ForeignKey('kmstr.vehicles.vin'))
    location_id = Column(BigInteger, ForeignKey('kmstr.locations.osm_id'))
    date = Column(DatetimeDecorator(), nullable=False)
    mileage_km = Column(Integer, nullable=False)
    start_pct = Column(Integer)
    end_pct = Column(Integer)
    position_latitude = Column(Float)
    position_longitude = Column(Float)

    location = relationship("Location")
    vehicle = relationship("Vehicle")

    def __init__(self, vehicle, date, mileage_km, start_pct, end_pct, latitude, longitude, location):
        self.vehicle = vehicle
        self.date = date
        self.mileage_km = mileage_km
        self.start_pct = start_pct
        self.end_pct = end_pct
        self.position_latitude = latitude
        self.position_longitude = longitude
        self.location = location
