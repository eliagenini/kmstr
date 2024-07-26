from sqlalchemy import Column, Integer, String, ForeignKey, Float, BigInteger
from sqlalchemy.orm import relationship

from models.base import Base
from models.datetime_decorator import DatetimeDecorator


class Trip(Base):
    __tablename__ = 'trips'
    __table_args__ = {'schema': 'kmstr'}

    id = Column(Integer, primary_key=True)
    vin = Column(String, ForeignKey('kmstr.vehicles.vin'))

    start_date = Column(DatetimeDecorator)
    end_date = Column(DatetimeDecorator)
    start_position_latitude = Column(Float)
    start_position_longitude = Column(Float)
    start_location_id = Column(BigInteger, ForeignKey('kmstr.locations.osm_id'))
    end_position_latitude = Column(Float)
    end_position_longitude = Column(Float)
    end_location_id = Column(BigInteger, ForeignKey('kmstr.locations.osm_id'))
    start_mileage = Column(Integer)
    end_mileage = Column(Integer)

    vehicle = relationship("Vehicle")
    start_location = relationship("Location", foreign_keys=[start_location_id])
    end_location = relationship("Location", foreign_keys=[end_location_id])

    def __init__(self, vehicle, start_date, start_position_latitude, start_position_longitude, start_location, start_mileage):
        self.vehicle = vehicle
        self.start_date = start_date
        self.start_position_latitude = start_position_latitude
        self.start_position_longitude = start_position_longitude
        self.start_location = start_location
        self.start_mileage = start_mileage
