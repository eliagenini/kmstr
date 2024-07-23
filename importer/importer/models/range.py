class Range:

    def __init__(self, data):
        self.id = data['id']
        self.vehicle = data['vehicle']
        self.range = data['range']
        self.last_modified = data['last_modified']
