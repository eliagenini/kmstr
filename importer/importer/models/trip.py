class Trip:

    def __init__(self, data):
        self.id = data.get('id')
        self.vehicle = data.get('vehicle')
        self.date = {'start': data.get('start_date'), 'end': data.get('end_date')}
        self.position = {
            'start': Position(data.get('start_position_latitude'), data.get('start_position_longitude')),
            'end': Position(data.get('end_position_latitude'), data.get('end_position_longitude'))}
        self.mileage = {'start': data.get('start_mileage'), 'end': data.get('end_mileage')}
        self.last_modified = data.get('last_modified')


class Position:
    def __init__(self, lat, long):
        self.latitude = lat
        self.longitude = long
