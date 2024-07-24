import logging
import requests
from requests.adapters import HTTPAdapter, Retry
from haversine import haversine, Unit, inverse_haversine, Direction
from sqlalchemy import and_

from models.geofence import Geofence
from models.location import Location

LOG = logging.getLogger("VWsFriend")


def locationFromLatLonWithGeofence(session, latitude, longitude):
    if latitude is None or longitude is None:
        return None
    geofences: Geofence = session.query(Geofence).filter(and_(Geofence.latitude.isnot(None), Geofence.longitude.isnot(None))).all()
    geofence_distance = [(haversine((latitude, longitude), (geofence.latitude, geofence.longitude), unit=Unit.METERS), geofence) for geofence in geofences]
    geofence_distance = sorted(geofence_distance, key=lambda geofence: geofence[0])
    for distance, geofence in geofence_distance:
        if distance < geofence.radius and geofence.location is not None:
            return geofence.location
    return locationFromLatLon(session, latitude, longitude)


def locationFromLatLon(session, latitude, longitude):
    query = {
        'lat': latitude,
        'lon': longitude,
        'namedetails': 1,
        'format': 'json'
    }
    headers = {
        'User-Agent': 'kmstr'
    }

    osm = requests.Session()
    retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500], raise_on_status=False)
    osm.mount('https://', HTTPAdapter(max_retries=retries))
    try:
        response = osm.get('https://nominatim.openstreetmap.org/reverse', params=query, headers=headers)
        if response.status_code == requests.codes['ok']:
            location = Location(jsonDict=response.json())
            return session.merge(location)
    except requests.exceptions.RetryError as retryError:
        LOG.error('Could not retrieve location: %s', retryError)
    return None


def amenityFromLatLon(session, latitude, longitude, radius, amenity, withFallback=False):
    northWest = inverse_haversine((latitude, longitude), radius, Direction.NORTHWEST, unit=Unit.METERS)
    southEast = inverse_haversine((latitude, longitude), radius, Direction.SOUTHEAST, unit=Unit.METERS)
    query = {
        'q': f'[{amenity}]',
        'viewbox': f'{northWest[1]},{northWest[0]},{southEast[1]},{southEast[0]}',
        'bounded': 1,
        'namedetails': 1,
        'addressdetails': 1,
        'format': 'json'
    }
    headers = {
        'User-Agent': 'VWsFriend'
    }
    osm = requests.Session()
    retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500], raise_on_status=False)
    osm.mount('https://', HTTPAdapter(max_retries=retries))
    try:
        response = osm.get('https://nominatim.openstreetmap.org/search', params=query, headers=headers)
        if response.status_code == requests.codes['ok']:
            places = response.json()
            placesDistance = [(haversine((latitude, longitude), (float(place['lat']), float(place['lon'])), unit=Unit.METERS), place) for place in places]
            placesDistance = sorted(placesDistance, key=lambda geofence: geofence[0])
            for distance, place in placesDistance:
                if distance < radius:
                    location = Location(jsonDict=place)
                    return session.merge(location)
        if withFallback:
            return locationFromLatLon(session, latitude, longitude)
    except requests.exceptions.RetryError as retryError:
        LOG.error('Could not retrieve location: %s', retryError)
    return None
