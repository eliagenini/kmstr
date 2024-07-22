from weconnect.addressable import AddressableLeaf


class Vehicle:

    def __init__(self, data):
        self.id = data.get('id')
        self.vin = data.get('vin')
        self.model = data.get('model')
        self.nickname = data.get('nickname')
        self.lastUpdate = data.get('last_update')
        self.lastChange = data.get('last_change')

        self.remote = None

    def connect(self, vehicle):
        self.remote = vehicle
        self.add_observer()

    def add_observer(self):
        if self.remote:
            self.remote.model.addObserver(self.__on_model_change, AddressableLeaf.ObserverEvent.VALUE_CHANGED)

            if self.remote.model.enabled and self.model != self.remote.model.value:
                self.model = self.remote.model.value

            self.remote.nickname.addObserver(self.__on_nickname_change, AddressableLeaf.ObserverEvent.VALUE_CHANGED)
            if self.remote.nickname.enabled and self.nickname != self.remote.nickname.value:
                self.nickname = self.remote.nickname.value

    def __on_model_change(self, element, flags):
        if self.model != element.value:
            self.model = element.value

    def __on_nickname_change(self, element, flags):
        if self.nickname != element.value:
            self.nickname = element.value
