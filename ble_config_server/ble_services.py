import os
import sys
import asyncio
import logging
from typing import List, Dict

import dbus_next

from ble_config_server import ble_base
from ble_config_server import app_helper
from ble_config_server import utils
from ble_config_server import constants
from ble_config_server.challenge import Challenge


logger = logging.getLogger(__name__)


# BLE UUIDs
SECURITY_SERVICE_UUID   = "da510000-0000-5aeb-050a-63f7c09baf2a"
CHALLENGE_CHAR_UUID     = "da510000-0001-5aeb-050a-63f7c09baf2a"

IP_CONFIG_SERVICE_UUID  = "da510001-0000-5aeb-050a-63f7c09baf2a"
IP_ADDR_CHAR_UUID       = "da510001-0001-5aeb-050a-63f7c09baf2a"
IP_MASK_CHAR_UUID       = "da510001-0002-5aeb-050a-63f7c09baf2a"
IP_GATE_CHAR_UUID       = "da510001-0003-5aeb-050a-63f7c09baf2a"
IP_DNS1_CHAR_UUID       = "da510001-0004-5aeb-050a-63f7c09baf2a"
IP_DNS2_CHAR_UUID       = "da510001-0005-5aeb-050a-63f7c09baf2a"
IP_CHECK_CHAR_UUID      = "da510001-0006-5aeb-050a-63f7c09baf2a"
IP_LOAD_CHAR_UUID       = "da510001-0007-5aeb-050a-63f7c09baf2a"
IP_IFACE_CHAR_UUID      = "da510001-0008-5aeb-050a-63f7c09baf2a"
IP_WIFI_SSID_CHAR_UUID  = "da510001-0009-5aeb-050a-63f7c09baf2a"
IP_WIFI_PW_CHAR_UUID    = "da510001-000a-5aeb-050a-63f7c09baf2a"

APP_CONFIG_SERVICE_UUID = "da510002-0000-5aeb-050a-63f7c09baf2a"
APP_ADDR_CHAR_UUID      = "da510002-0001-5aeb-050a-63f7c09baf2a"
APP_USER_CHAR_UUID      = "da510002-0002-5aeb-050a-63f7c09baf2a"
APP_PASSWORD_CHAR_UUID  = "da510002-0003-5aeb-050a-63f7c09baf2a"
APP_DEVICE_CHAR_UUID    = "da510002-0004-5aeb-050a-63f7c09baf2a"
APP_COMPANY_CHAR_UUID   = "da510002-0005-5aeb-050a-63f7c09baf2a"
APP_CHECK_CHAR_UUID     = "da510002-0006-5aeb-050a-63f7c09baf2a"
APP_NETKEY_CHAR_UUID    = "da510002-0007-5aeb-050a-63f7c09baf2a"
APP_UADDRESS_CHAR_UUID  = "da510002-0008-5aeb-050a-63f7c09baf2a"
APP_MGW_ADDR_CHAR_UUID  = "da510002-0009-5aeb-050a-63f7c09baf2a"
APP_MGW_PORT_CHAR_UUID  = "da510002-000a-5aeb-050a-63f7c09baf2a"
APP_MGW_ROLE_CHAR_UUID  = "da510002-000b-5aeb-050a-63f7c09baf2a"
APP_MGW_PTCK_CHAR_UUID  = "da510002-000c-5aeb-050a-63f7c09baf2a"

RESET_SERVICE_UUID      = "da510003-0000-5aeb-050a-63f7c09baf2a"
RESET_CHAR_UUID         = "da510003-0001-5aeb-050a-63f7c09baf2a"


class LockCharacteristic(ble_base.Characteristic):
    locked = True

    def __init__(self, index: int, uuid: str,
            access: List[str]=None):
        if access is None:
            access = ["read", "write"]
        super().__init__(index, uuid, access)

    @classmethod
    def unlock(cls):
        cls.locked = False

    @classmethod
    def lock(cls):
        cls.locked = True

    @dbus_next.service.method()
    # pylint: disable=invalid-name
    def ReadValue(self, options: "a{sv}") -> "ay":
    # pylint: enable=invalid-name
        if not self.locked:
            logger.debug(f"Read {type(self).__name__}: {self.value}")
            return self.value.encode()
        logger.warning(f"Invalid read access ({type(self).__name__})")
        return "".encode()

    @dbus_next.service.method()
    # pylint: disable=invalid-name
    def WriteValue(self, value: "ay", options: "a{sv}"):
    # pylint: enable=invalid-name
        if not self.locked:
            self.value = value.decode("utf-8")
            logger.debug(f"Write {type(self).__name__} {self.value}")
        else:
            logger.warning(f"Invalid write access ({type(self).__name__})")


class IPAddrChar(LockCharacteristic):
    def __init__(self, index: int, network_manager):
        self.network_manager = network_manager
        super().__init__(index, IP_ADDR_CHAR_UUID)

    @property
    def value(self):
        return self.network_manager.ip

    @value.setter
    def value(self, value):
        self.network_manager.ip = value


class IPMaskChar(LockCharacteristic):
    def __init__(self, index: int, network_manager):
        self.network_manager = network_manager
        super().__init__(index, IP_MASK_CHAR_UUID)

    @property
    def value(self):
        return self.network_manager.mask

    @value.setter
    def value(self, value):
        self.network_manager.mask = value


class IPGatewayChar(LockCharacteristic):
    def __init__(self, index: int, network_manager):
        self.network_manager = network_manager
        super().__init__(index, IP_GATE_CHAR_UUID)

    @property
    def value(self):
        return self.network_manager.gateway

    @value.setter
    def value(self, value):
        self.network_manager.gateway = value


class IPDNS1Char(LockCharacteristic):
    def __init__(self, index: int, network_manager):
        self.network_manager = network_manager
        super().__init__(index, IP_DNS1_CHAR_UUID)

    @property
    def value(self):
        return self.network_manager.dns1

    @value.setter
    def value(self, value):
        self.network_manager.dns1 = value


class IPDNS2Char(LockCharacteristic):
    def __init__(self, index: int, network_manager):
        self.network_manager = network_manager
        super().__init__(index, IP_DNS2_CHAR_UUID)

    @property
    def value(self):
        return self.network_manager.dns2

    @value.setter
    def value(self, value):
        self.network_manager.dns2 = value


class IPIfaceChar(LockCharacteristic):
    def __init__(self, index: int, network_manager):
        self.network_manager = network_manager
        super().__init__(index, IP_IFACE_CHAR_UUID)

    @property
    def value(self):
        return str(self.network_manager.type)

    @value.setter
    def value(self, value):
        self.network_manager.type = int(value)


class IPWifiSsidChar(LockCharacteristic):
    def __init__(self, index: int, network_manager):
        self.network_manager = network_manager
        super().__init__(index, IP_WIFI_SSID_CHAR_UUID)

    @property
    def value(self):
        return self.network_manager.ssid

    @value.setter
    def value(self, value):
        self.network_manager.ssid = value


class IPWifiPwChar(LockCharacteristic):
    def __init__(self, index: int, network_manager):
        self.network_manager = network_manager
        super().__init__(index, IP_WIFI_PW_CHAR_UUID, access=["write"])

    @property
    def value(self):
        return ""

    @value.setter
    def value(self, value):
        self.network_manager.psk = value


class IPLoadChar(LockCharacteristic):
    LOADING = b"loading"
    READY = b"ready"

    TIMEOUT = 60

    def __init__(self, index: int, network_manager):
        self.network_manager = network_manager
        super().__init__(index, IP_LOAD_CHAR_UUID, access=["read"])
        self.load_task = None

    @dbus_next.service.method()
    # pylint: disable=invalid-name
    def ReadValue(self, options: "a{sv}") -> "ay":
    # pylint: enable=invalid-name
        if self.locked:
            logger.warning(f"Invalid read access ({type(self).__name__})")
            return "".encode()

        if self.load_task and self.load_task.done():
            logger.debug(f"Read {type(self).__name__}: ready")
            return self.READY
        if not self.load_task:
            coro = self.network_manager.load()
            self.load_task = asyncio.create_task(coro)
            logger.debug("Loading network config")
        logger.debug(f"Read {type(self).__name__}: loading")
        return self.LOADING

    def reset(self):
        self.load_task = None


class IPCheckChar(LockCharacteristic):
    def __init__(self, index: int, network_manager):
        self.network_manager = network_manager
        super().__init__(index, IP_CHECK_CHAR_UUID)
        self.value = "0"

    @dbus_next.service.method()
    # pylint: disable=invalid-name
    def WriteValue(self, value: "ay", options: "a{sv}"):
    # pylint: enable=invalid-name
        if not self.locked:
            task = asyncio.create_task(self.network_manager.save_and_check())
            task.add_done_callback(self.connection_check_cb)
            self.value = "0"
        else:
            logger.warning("Invalid Network set")

    def connection_check_cb(self, task):
        if task.done():
            if task.result():
                self.value = "1"
            else:
                self.value = "-1"
        else:
            self.value = "0"


class AppAddrChar(LockCharacteristic):
    def __init__(self, index: int, app_config):
        self.app_config = app_config
        super().__init__(index, APP_ADDR_CHAR_UUID)

    @property
    def value(self):
        return self.app_config["url"].value

    @value.setter
    def value(self, value):
        self.app_config["url"].value = value.rstrip("/")


class AppUserChar(LockCharacteristic):
    def __init__(self, index: int, app_config):
        self.app_config = app_config
        super().__init__(index, APP_USER_CHAR_UUID)

    @property
    def value(self):
        return self.app_config["user"].value

    @value.setter
    def value(self, value):
        self.app_config["user"].value = value


class AppPasswordChar(LockCharacteristic):
    def __init__(self, index: int, app_config):
        self.app_config = app_config
        super().__init__(index, APP_PASSWORD_CHAR_UUID)

    @property
    def value(self):
        return self.app_config["password"].value

    @value.setter
    def value(self, value):
        self.app_config["password"].value = value


class AppDeviceChar(LockCharacteristic):
    def __init__(self, index: int, app_config):
        self.app_config = app_config
        super().__init__(index, APP_DEVICE_CHAR_UUID)

    @property
    def value(self):
        return self.app_config["device_id"].value

    @value.setter
    def value(self, value):
        self.app_config["device_id"].value = value


class AppCompanyChar(LockCharacteristic):
    def __init__(self, index: int, app_config):
        self.app_config = app_config
        super().__init__(index, APP_COMPANY_CHAR_UUID)

    @property
    def value(self):
        return self.app_config["company"].value

    @value.setter
    def value(self, value):
        self.app_config["company"].value = value


class AppNetkeyChar(LockCharacteristic):
    def __init__(self, index: int, app_config):
        self.app_config = app_config
        super().__init__(index, APP_NETKEY_CHAR_UUID)

    @property
    def value(self):
        return self.app_config["netkey"].value

    @value.setter
    def value(self, value):
        self.app_config["netkey"].value = value


class AppUniAddressChar(LockCharacteristic):
    def __init__(self, index: int, app_config):
        self.app_config = app_config
        super().__init__(index, APP_UADDRESS_CHAR_UUID)

    @property
    def value(self):
        return str(self.app_config["address"].value)

    @value.setter
    def value(self, value):
        self.app_config["address"].value = int(value)


class AppMultiGwAddrChar(LockCharacteristic):
    def __init__(self, index: int, app_config):
        self.app_config = app_config
        super().__init__(index, APP_MGW_ADDR_CHAR_UUID)

    @property
    def value(self):
        return self.app_config["multi_gw_host"].value

    @value.setter
    def value(self, value):
        self.app_config["multi_gw_host"].value = value


class AppMultiGwPortChar(LockCharacteristic):
    def __init__(self, index: int, app_config):
        self.app_config = app_config
        super().__init__(index, APP_MGW_PORT_CHAR_UUID)

    @property
    def value(self):
        return str(self.app_config["multi_gw_port"].value)

    @value.setter
    def value(self, value):
        self.app_config["multi_gw_port"].value = int(value)


class AppMultiGwRoleChar(LockCharacteristic):
    def __init__(self, index: int, app_config):
        self.app_config = app_config
        super().__init__(index, APP_MGW_ROLE_CHAR_UUID)

    @property
    def value(self):
        return self.app_config["multi_gw_role"].value

    @value.setter
    def value(self, value):
        self.app_config["multi_gw_role"].value = value


class AppMultiGwPtCheckChar(LockCharacteristic):
    def __init__(self, index: int, app_config):
        self.app_config = app_config
        super().__init__(index, APP_MGW_PTCK_CHAR_UUID)
        self.value = "0"

    @dbus_next.service.method()
    # pylint: disable=invalid-name
    def WriteValue(self, value: "ay", options: "a{sv}"):
    # pylint: enable=invalid-name
        if not self.locked:
            task = asyncio.create_task(
                app_helper.check_passthrough_connection())
            task.add_done_callback(self.connection_check_cb)
            self.value = "0"
        else:
            logger.warning("Invalid passthrough set")

    def connection_check_cb(self, task):
        if task.done():
            if task.result():
                self.value = "1"
            else:
                self.value = "-1"
        else:
            self.value = "0"


class AppCheckChar(LockCharacteristic):
    def __init__(self, index: int, app_config):
        self.app_config = app_config
        super().__init__(index, APP_CHECK_CHAR_UUID)
        self.value = "0"

    @dbus_next.service.method()
    # pylint: disable=invalid-name
    def WriteValue(self, value: "ay", options: "a{sv}"):
    # pylint: enable=invalid-name
        if not self.locked:
            asyncio.create_task(app_helper.set_app_config(self.app_config))
            self.value = "1"
            logger.debug("App configuration saved")
        else:
            logger.warning("Invalid app set")


class ResetCharacteristic(LockCharacteristic):
    def __init__(self, index: int):
        super().__init__(index, RESET_CHAR_UUID, ["write"])

    @dbus_next.service.method()
    # pylint: disable=invalid-name
    def WriteValue(self, value: "ay", options: "a{sv}"):
    # pylint: enable=invalid-name
        if not self.locked:
            if value.decode() == "1":
                self.value = "1"
                asyncio.create_task(self.reset())
        else:
            logger.warning("Invalid factory reset")

    async def ensure_is_heimdall(self):
        """ We dont want to remove someone's home dir by accident. """
        return (await utils.is_heimdall()
            and await asyncio.to_thread(os.path.isfile, "/etc/ttversion"))

    async def reset(self):
        if await self.ensure_is_heimdall():
            home_dir = os.path.expanduser("~/")
            logger.info("Factory Reset")
            await utils.shell(f"rm -rf {home_dir}/* {home_dir}/.*")
            await utils.shell("reboot")


class SecCharacteristic(ble_base.Characteristic):
    def __init__(self, index: int):
        super().__init__(index, CHALLENGE_CHAR_UUID, ["read", "write"])
        public_key_file = os.environ.get(constants.PK_FILE_ENV)
        if public_key_file is None:
            if os.path.isfile(constants.PK_DEFAULT_FILE):
                public_key_file = constants.PK_DEFAULT_FILE
            else:
                # This env variable must be set to and ed25519 pem public key
                # file - check OpenSSL
                logger.error("{constants.PK_FILE_ENV} not properly set and no" +
                    f" {constants.PK_DEFAULT_FILE} default file")
                sys.exit(1)
        self.challenge = Challenge(public_key_file)

    def check_repsonse(self, response: bytes):
        if self.challenge.check_response(response):
            logger.debug("Correct password")
            LockCharacteristic.unlock()
        else:
            logger.warning("Incorrect password")
            LockCharacteristic.lock()

    @dbus_next.service.method()
    # pylint: disable=invalid-name
    def ReadValue(self, options: "a{sv}") -> "ay":
    # pylint: enable=invalid-name
        #TODO: Remove challenge from log
        logger.debug(f"Get challenge: {self.challenge.get_challenge()}")
        return self.challenge.get_challenge()

    @dbus_next.service.method()
    # pylint: disable=invalid-name
    def WriteValue(self, value: "ay", options: "a{sv}"):
    # pylint: enable=invalid-name
        asyncio.create_task(asyncio.to_thread(self.check_repsonse, value))


class SecService(ble_base.Service):
    def __init__(self, index: int):
        super().__init__(index, SECURITY_SERVICE_UUID, True)
        sec_char = SecCharacteristic(0)
        self.add_characteristic("sec", sec_char)


class IPConfigService(ble_base.Service):
    def __init__(self, index: int):
        super().__init__(index, IP_CONFIG_SERVICE_UUID, True)

    def add_chars(self, chars: Dict[str, "Characteristic"]):
        for name, char in chars.items():
            self.add_characteristic(name, char)


class AppConfigService(ble_base.Service):
    def __init__(self, index: int):
        super().__init__(index, APP_CONFIG_SERVICE_UUID, True)

    def add_chars(self, chars: Dict[str, "Characteristic"]):
        for name, char in chars.items():
            self.add_characteristic(name, char)


class ResetService(ble_base.Service):
    def __init__(self, index: int):
        super().__init__(index, RESET_SERVICE_UUID, True)
        reset_char = ResetCharacteristic(0)
        self.add_characteristic("reset", reset_char)


class BleConfigApplication(ble_base.Application):
    def __init__(self):
        super().__init__()
        self.add_service("sec", SecService(0))
        self.add_service("ip", IPConfigService(1))
        self.add_service("app", AppConfigService(2))
        self.add_service("reset", ResetService(3))
