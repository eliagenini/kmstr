__author__ = 'eliagenini'

import datetime
import jwt
import postgrest
from abc import ABC
from typing import Optional

import models.vehicle


def datetime_to_ms(dt: Optional[datetime.datetime] = None):
    if not dt:
        dt = datetime.datetime.now(datetime.UTC)

    return int((dt - datetime.datetime(1970, 1, 1)).total_seconds() * 1e3)


class Api(ABC):
    def __init__(self, endpoint, context):
        self.context = context
        self.endpoint = endpoint
        self.client = self.get_client()

    def get_client(self):
        token = self.generate_jwt('data_producer')
        headers = {'Authorization': 'Bearer ' + token}

        return postgrest.SyncPostgrestClient(
            self.endpoint, schema="kmstr", headers=headers, timeout=60
        )

    def generate_jwt(self, role: str, jwt_secret: Optional[str] = None):
        if jwt_secret is None:
            jwt_secret = 'iquaeC7Pa2eiquishooR7funaiVaigop'  # os.environ["KMSTR_JWT_SECRET"]
        return jwt.encode({'role': role, 'aud': self.endpoint}, jwt_secret, algorithm='HS256')

    def find_all(self):
        r = self.client.from_(self.context).select("*").execute()
        return r.data

    def get(self, id: int | str, key: Optional[str] = None):
        if key is None:
            key = 'id'

        r = self.client.from_(self.context).select("*").eq(key, id).execute()
        return r.data

    def put(self, obj):
        return self.client.from_(self.context).insert(obj).execute()

    def update(self, id: int, obj):
        return self.client.from_(self.context).update(obj).eq("id", id).execute()

    def get_last_by_vehicle(self, vehicle):
        return (self.get_client().from_(self.context).select("*")
                .eq("vehicle", vehicle.id)
                .neq("last_modified", None)
                .order("last_modified", desc=True)
                .limit(1)
                .execute())


class FuelLevel(Api):
    def __init__(self, endpoint):
        super().__init__(endpoint, "fuel_level")


class TotalRange(Api):
    def __init__(self, endpoint):
        super().__init__(endpoint, "total_range")

    def put(self, obj):
        r = super().put(obj)
        return models.range.Range(r.data[0])

    def get_last_range_by_vehicle(self, vehicle):
        r = (self.get_client().from_("total_range").select("*")
             .eq("vehicle", vehicle)
             .order("last_modified", desc=True)
             .limit(1)
             .execute())

        if r.data:
            return models.range.Range(r.data[0])

        return None


class Mileage(Api):
    def __init__(self, endpoint):
        super().__init__(endpoint, "mileage")


class Vehicle(Api):
    def __init__(self, endpoint):
        super().__init__(endpoint, "vehicles")

    def find_all(self):
        results = []
        data = super().find_all()

        for d in data:
            results.append(models.vehicle.Vehicle(d))

        return results

    def get(self, id: int | str, key: Optional[str] = None):
        r = super().get(id, key)
        return models.vehicle.Vehicle(r.data)

    def put(self, obj):
        r = super().put(obj)
        return models.vehicle.Vehicle(r.data[0])


class Parking(Api):
    def __init__(self, endpoint):
        super().__init__(endpoint, "parking")


class Trip(Api):
    def __init__(self, endpoint):
        self.context = "trip"
        super().__init__(endpoint, self.context)

    def get_last_trip_by_vehicle(self, vehicle):
        data = super().get_last_by_vehicle(vehicle)

        return models.trip.Trip(data)
