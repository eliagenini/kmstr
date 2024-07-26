from utils.location_util import location_from_lat_lon_with_geofence


class Position:
    def __init__(self, latitude, longitude, timestamp):
        self.latitude = latitude,
        self.longitude = longitude
        self.timestamp = timestamp

    def get_location(self, session):
        return location_from_lat_lon_with_geofence(session, self.latitude, self.longitude)
