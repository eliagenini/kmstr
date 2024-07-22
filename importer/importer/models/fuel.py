from weconnect.addressable import AddressableLeaf


class Fuel:

    def __init__(self, data):
        self.id = data.get('id')
        self.vehicle = data.get('vehicle')
        self.level = data.get('level')
        self.last_modified = data.get('last_modified')

