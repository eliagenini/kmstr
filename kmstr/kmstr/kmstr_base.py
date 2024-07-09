__author__ = 'eliagenini'

from weconnect import weconnect

def main():
    print('#  Initialize WeConnect')
    weConnect = weconnect.WeConnect(username='elia.genini@gmail.com', password='12345678!', updateAfterLogin=False, loginOnInit=False)
    print('#  Login')
    weConnect.login()
    print('#  update')
    weConnect.update()
    print('#  print results')
    for vin, vehicle in weConnect.vehicles.items():
        del vin
        print(vehicle)
    print('#  done')

