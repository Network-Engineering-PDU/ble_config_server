import sys
import asyncio
import logging

import dbus_next
from dbus_next.constants import BusType
from dbus_next.aio import MessageBus

from ble_config_server import app_helper
from ble_config_server import ble_services
from ble_config_server import ble_base
from ble_config_server import utils
from ble_config_server.network import NetworkManager


logger = logging.getLogger(__name__)


# TX power
TX_POW_1_M = 195

# BLE application DBUS names
SERVICE_NAME       = "com.tychetools"
ADV_BEACON_OBJECT  = "/com/tychetools/advertisement_beacon"
ADVERTISING_OBJECT = "/com/tychetools/advertisement"
APPLICATION_OBJECT = "/com/tychetools/gatt_application"

# Bluez DBUS names
BLUEZ_SERVICE_NAME       = "org.bluez"
BLUEZ_ADAPTER_OBJECT     = "/org/bluez/hci0"
BLUEZ_ADAPTER_IFACE      = "org.bluez.Adapter1"
BLUEZ_ADV_MANAGER_IFACE  = "org.bluez.LEAdvertisingManager1"
BLUEZ_GATT_MANAGER_IFACE = "org.bluez.GattManager1"

# General DBUS names
ROOT_OBJECT       = "/"
OBJ_MANAGER_IFACE = "org.freedesktop.DBus.ObjectManager"


class BleServer:
    def __init__(self):
        self.network_manager = NetworkManager()
        self.app_config = {}
        self.device_connected = False
        self.ble_app = None
        self.led_controller = None

    def clean_exit(self):
        if self.led_controller is not None:
            self.led_controller.bt_disconnected()

    def interfaces_added_cb(self, path, interfaces):
        last = path.split("/")[-1]
        if last[0:3] == "dev":
            logger.debug("Device connected")
            self.device_connected = True
            self.led_controller.bt_connected()
            asyncio.create_task(self.update_app_config())

    def interfaces_removed_cb(self, path, interfaces):
        last = path.split("/")[-1]
        if last[0:3] == "dev":
            logger.debug("Device disconnected")
            ble_services.LockCharacteristic.lock()
            self.device_connected = False
            self.led_controller.bt_advertising()
            self.ble_app.services["ip"].characteristics["load"].reset()

    async def update_app_config(self):
        await app_helper.update_app_config(self.app_config)

    async def led_controller_init(self):
        try:
            from ttgateway.leds import get_led_controller
        except ImportError:
            logger.error("Error importing led controller")
            return

        self.led_controller = await asyncio.to_thread(get_led_controller)
        logger.debug(f"Led controller: {self.led_controller.__name__}")

    async def connect_to_dbus(self):
        for retry in range(60):
            try:
                bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
                #await bus.request_name(SERVICE_NAME, NameFlag.DO_NOT_QUEUE)
                if retry > 0:
                    logger.debug("Connected to DBUS after %d seconds", retry)
                return bus
            except FileNotFoundError:
                await asyncio.sleep(1)
        logger.error("Unable to connect to DBUS after %d seconds", retry)
        sys.exit(1)

    async def connect_to_bluez(self, bus, connect_retry):
        for retry in range(90):
            msg = dbus_next.Message(destination=BLUEZ_SERVICE_NAME,
                path=BLUEZ_ADAPTER_OBJECT, interface=BLUEZ_ADAPTER_IFACE,
                member='GetDiscoveryFilters', serial=bus.next_serial())
            reply = await bus.call(msg)
            if reply.message_type == dbus_next.MessageType.ERROR:
                if connect_retry:
                    await asyncio.sleep(1)
                else:
                    break
            else:
                if retry > 0:
                    logger.debug("Connected to BLUEZ after %d seconds", retry)
                    self.led_controller.bt_advertising()
                return
        logger.error("Unable to connect to BLUEZ after %d seconds", retry)
        sys.exit(1)

    async def get_adapter_mac(self, bus):
        adapter_introspection = await bus.introspect(BLUEZ_SERVICE_NAME,
            BLUEZ_ADAPTER_OBJECT)
        adapter_object = bus.get_proxy_object(BLUEZ_SERVICE_NAME,
            BLUEZ_ADAPTER_OBJECT, adapter_introspection)

        adapter = adapter_object.get_interface(BLUEZ_ADAPTER_IFACE)
        return await adapter.get_address()

    def create_advertising(self, bus, bl_adapter_mac):
        adv_type = ble_base.AdvertisingType.PERIPHERAL
        mac = "".join(bl_adapter_mac.split(":"))
        logger.info(f"Adapter mac: {mac}")
        tx_pow = f"{TX_POW_1_M:02x}"
        man_data = {
            0xda51: bytes.fromhex("0221" + "01000000000000000000" + mac
                + "02010403" + tx_pow)
        }
        advertising = ble_base.Advertising(adv_type, "TycheTools-GW", man_data)
        advertising.export(bus, ADVERTISING_OBJECT)

    def create_application(self, bus):
        ip_characteristics = {
            "addr": ble_services.IPAddrChar(0, self.network_manager),
            "mask": ble_services.IPMaskChar(1, self.network_manager),
            "gateway": ble_services.IPGatewayChar(2, self.network_manager),
            "dns1": ble_services.IPDNS1Char(3, self.network_manager),
            "dns2": ble_services.IPDNS2Char(4, self.network_manager),
            "check": ble_services.IPCheckChar(5, self.network_manager),
            "load": ble_services.IPLoadChar(6, self.network_manager),
            "iface": ble_services.IPIfaceChar(7, self.network_manager),
            "w_ssid": ble_services.IPWifiSsidChar(8, self.network_manager),
            "w_pw": ble_services.IPWifiPwChar(9, self.network_manager),
        }
        app_characteristics = {
            "addr": ble_services.AppAddrChar(0, self.app_config),
            "user": ble_services.AppUserChar(1, self.app_config),
            "password": ble_services.AppPasswordChar(2, self.app_config),
            "device_id": ble_services.AppDeviceChar(3, self.app_config),
            "company": ble_services.AppCompanyChar(4, self.app_config),
            "check": ble_services.AppCheckChar(5, self.app_config),
            "netkey": ble_services.AppNetkeyChar(6, self.app_config),
            "uni_addr": ble_services.AppUniAddressChar(7, self.app_config),
            "mg_addr": ble_services.AppMultiGwAddrChar(8, self.app_config),
            "mg_port": ble_services.AppMultiGwPortChar(9, self.app_config),
            "mg_role": ble_services.AppMultiGwRoleChar(10, self.app_config),
            "mg_ptck": ble_services.AppMultiGwPtCheckChar(11, self.app_config),
        }

        self.ble_app = ble_services.BleConfigApplication()
        self.ble_app.services["ip"].add_chars(ip_characteristics)
        self.ble_app.services["app"].add_chars(app_characteristics)
        self.ble_app.export(bus, APPLICATION_OBJECT)

    async def register_application(self, bus):
        root_introspection = await bus.introspect(BLUEZ_SERVICE_NAME,
            ROOT_OBJECT)
        root_object = bus.get_proxy_object(BLUEZ_SERVICE_NAME, ROOT_OBJECT,
            root_introspection)
        obj_manager = root_object.get_interface(OBJ_MANAGER_IFACE)
        obj_manager.on_interfaces_added(self.interfaces_added_cb)
        obj_manager.on_interfaces_removed(self.interfaces_removed_cb)

        adapter_introspection = await bus.introspect(BLUEZ_SERVICE_NAME,
            BLUEZ_ADAPTER_OBJECT)
        adapter_object = bus.get_proxy_object(BLUEZ_SERVICE_NAME,
            BLUEZ_ADAPTER_OBJECT, adapter_introspection)

        adapter = adapter_object.get_interface(BLUEZ_ADAPTER_IFACE)
        await adapter.set_powered(True)

        adv_manager = adapter_object.get_interface(BLUEZ_ADV_MANAGER_IFACE)
        gatt_manager = adapter_object.get_interface(BLUEZ_GATT_MANAGER_IFACE)
        await gatt_manager.call_register_application(APPLICATION_OBJECT, {})
        await adv_manager.call_register_advertisement(ADVERTISING_OBJECT, {})

    async def _run(self):
        await self.network_manager.init()
        self.app_config = await app_helper.get_app_config()

        await self.led_controller_init()
        bus = await self.connect_to_dbus()
        embedded_dev = await utils.is_heimdall() or await utils.is_raspberry()
        await self.connect_to_bluez(bus, embedded_dev)

        bl_adapter_mac = await self.get_adapter_mac(bus)
        self.create_advertising(bus, bl_adapter_mac)

        self.create_application(bus)
        await self.register_application(bus)

        await asyncio.Future()  # run forever

    def run(self):
        if not hasattr(asyncio, "to_thread"): #TODO: Remove when python3.9
            logger.warning("Using custom to_thread function")
            from ble_config_server.to_thread_helper import to_thread
            asyncio.to_thread = to_thread
        asyncio.run(self._run())
