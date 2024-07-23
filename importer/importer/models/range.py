class Range:

    def __init__(self, data):
        self.id = data.get('id')
        self.vehicle = data.get('vehicle')
        self.range = data.get('range')
        self.last_modified = data.get('last_modified')
