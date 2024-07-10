__author__ = 'eliagenini'

from abc import ABC
from typing import Optional
import datetime
import jwt
import os

import postgrest


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
            jwt_secret = 'iquaeC7Pa2eiquishooR7funaiVaigop'  #os.environ["KMSTR_JWT_SECRET"]
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


class FuelStatus(Api):
    def __init__(self, endpoint):
        super().__init__(endpoint, "fuel_status")


class FuelType(Api):
    def __init__(self, endpoint):
        super().__init__(endpoint, "fuel_type")


class Mileage(Api):
    def __init__(self, endpoint):
        super().__init__(endpoint, "mileage")


class Vehicle(Api):
    def __init__(self, endpoint):
        super().__init__(endpoint, "vehicles")
