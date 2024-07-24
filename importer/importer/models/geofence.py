from sqlalchemy import Column, String, Float, Integer, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from models.base import Base

class Geofence(Base):
    __tablename__ = 'geofences'
    __table_args__ = {'schema': 'kmstr'}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    radius = Column(Float)
    location_id = Column(BigInteger, ForeignKey('kmstr.locations.osm_id'))
    location = relationship("Location")

    def __init__(self, id):
        self.id = id
