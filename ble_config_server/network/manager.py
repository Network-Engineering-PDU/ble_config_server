import asyncio
import logging
import requests

from ble_config_server.network.base_device import BaseDevice
from ble_config_server.network.heimdall import Heimdall
from ble_config_server.network.raspberry import Raspberry
from ble_config_server import utils


logger = logging.getLogger(__name__)


class NetworkManager:
    def __init__(self):
        self.device = None

    async def init(self):
        if await utils.is_heimdall():
            self.device = Heimdall()
            logger.info("Board: Heimdall")
        elif await utils.is_raspberry():
            self.device = Raspberry()
            logger.info("Board: Raspberry")
        else:
            self.device = BaseDevice()
        await self.load()

    async def save_and_check(self):
        await self.save()
        for retries in range(10):
            if await self.check_internet_connection():
                logger.info(f"Internet connection ok ({retries})")
                asyncio.create_task(self.load())
                return True
            await asyncio.sleep(1)

        logger.warning("Internet connection error")
        return False

    async def load(self):
        await self.device.load()

    async def save(self):
        await self.device.save()

    def __getattr__(self, name):
        if name != "device" and hasattr(self.device, name):
            return getattr(self.device, name)
        raise AttributeError

    def __setattr__(self, name, value):
        if hasattr(self, "device") and hasattr(self.device, name):
            setattr(self.device, name, value)
        else:
            super().__setattr__(name, value)

    async def check_internet_connection(self):
        def _check_internet_connection():
            try:
                url_check = "http://nmcheck.gnome.org/check_network_status.txt"
                rsp = requests.get(url_check, timeout=5)
                if rsp.ok and rsp.content == b'NetworkManager is online\n':
                    return True
                return False
            except (ConnectionRefusedError, OSError, TimeoutError):
                return False
        return await asyncio.to_thread(_check_internet_connection)
