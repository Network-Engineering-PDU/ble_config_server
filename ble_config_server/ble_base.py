from typing import List

from dbus_next.service import ServiceInterface, method, dbus_property, Variant
from dbus_next.constants import PropertyAccess


# Bluez BLE DBUS interfaces
ADVERTISING_IFACE  = "org.bluez.LEAdvertisement1"
GATT_SERVICE_IFACE = "org.bluez.GattService1"
GATT_CHAR_IFACE    = "org.bluez.GattCharacteristic1"
APPLICATION_IFACE  = "com.tychetools.gatt_application"


class AdvertisingType:
    BROADCAST  = "broadcast"
    PERIPHERAL = "peripheral"


class Advertising(ServiceInterface):
    def __init__(self, _type, local_name, manufacturer_data=None):
        super().__init__(ADVERTISING_IFACE)
        self.type = _type
        self.local_name = local_name
        if manufacturer_data is None:
            manufacturer_data = {}
        self.manufacturer_data = manufacturer_data
        self.tx_power = 0

    # pylint: disable=invalid-name
    @method()
    def Release(self):
        pass

    @dbus_property()
    def Type(self) -> 's':
        return self.type

    @Type.setter
    def Type(self, value: 's'):
        self.type = value

    @dbus_property()
    def LocalName(self) -> 's':
        return self.local_name

    @LocalName.setter
    def LocalName(self, value: 's'):
        self.local_name = value

    @dbus_property(PropertyAccess.READ)
    def ManufacturerData(self) -> 'a{qv}':
        d = {}
        for k, v in self.manufacturer_data.items():
            d[k] = Variant('ay', v)
        return d

    @dbus_property()
    def TxPower(self) -> 'n':
        return self.tx_power

    @TxPower.setter
    def TxPower(self, value: 'n'):
        self.tx_power = value

    # pylint: enable=invalid-name

    def export(self, bus, path):
        bus.export(path, self)


class Application(ServiceInterface):
    def __init__(self):
        super().__init__(APPLICATION_IFACE)
        self.services = {}

    def add_service(self, name: str, service: "Service"):
        self.services[name] = service

    def export(self, bus, path):
        bus.export(path, self)
        for service in self.services.values():
            service.export(bus, path)


class Service(ServiceInterface):
    def __init__(self, index: int, uuid: str, primary: bool):
        super().__init__(GATT_SERVICE_IFACE)
        self.index = index
        self.uuid = uuid
        self.primary = primary
        self.characteristics = {}

    # pylint: disable=invalid-name
    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> 's':
        return self.uuid

    @dbus_property(access=PropertyAccess.READ)
    def Primary(self) -> 'b':
        return self.primary

    # pylint: enable=invalid-name

    def add_characteristic(self, name: str, characteristic: "Characteristic"):
        self.characteristics[name] = characteristic

    def export(self, bus, path):
        service_path = path + f"/service{self.index}"
        bus.export(service_path, self)
        for characteristic in self.characteristics.values():
            characteristic.export(bus, service_path)


class Characteristic(ServiceInterface):
    def __init__(self, index: int, uuid: str, flags: List[str]):
        super().__init__(GATT_CHAR_IFACE)
        self.index = index
        self.uuid = uuid
        self.service_path = ""
        self.flags = flags
        self.notifying = False
        if not hasattr(self, "value"):
            self.value = ""

    # pylint: disable=invalid-name
    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> 's':
        return self.uuid

    @dbus_property(access=PropertyAccess.READ)
    def Service(self) -> 'o':
        return self.service_path

    @dbus_property(access=PropertyAccess.READ)
    def Value(self) -> "ay":
        return self.value.encode()

    @dbus_property(access=PropertyAccess.READ)
    def Flags(self) -> "as":
        return self.flags

    @dbus_property(access=PropertyAccess.READ)
    def Notifying(self) -> "b":
        return self.notifying

    # pylint: enable=invalid-name

    def export(self, bus, path):
        self.service_path = path
        characteristic_path = path + f"/char{self.index}"
        bus.export(characteristic_path, self)
