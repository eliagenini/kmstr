from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from models.base import Base
from models.datetime_decorator import DatetimeDecorator


class Range(Base):
    __tablename__ = 'ranges'
    __table_args__ = {'schema': 'kmstr'}

    id = Column(Integer, primary_key=True)
    vin = Column(String, ForeignKey('kmstr.vehicles.vin'))
    captured_timestamp = Column(DatetimeDecorator(timezone=True), nullable=False)
    total_range_km = Column(Integer, nullable=False)
    primary_current_pct = Column(Integer)
    primary_remaining_km = Column(Integer)
    secondary_current_pct = Column(Integer)
    secondary_remaining_km = Column(Integer)

    vehicle = relationship("Vehicle")

    def __init__(self, vehicle, captured_timestamp, total_range_km, primary_current_pct, primary_remaining_km,
                 secondary_current_pct, secondary_remaining_km):
        self.vehicle = vehicle
        self.captured_timestamp = captured_timestamp
        self.total_range_km = total_range_km
        self.primary_current_pct = primary_current_pct
        self.primary_remaining_km = primary_remaining_km
        self.secondary_current_pct = secondary_current_pct
        self.secondary_remaining_km = secondary_remaining_km
