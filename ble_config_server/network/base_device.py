import re
import logging
from ipaddress import IPv4Interface

from ble_config_server.network.network_type import NetworkType
from ble_config_server.network.config import NetworkConfig
from ble_config_server import utils


logger = logging.getLogger(__name__)


class BaseDevice(NetworkConfig):
    async def load(self):
        self.reset()
        await self.get_current_ip()
        await self.get_wifi_ssid()
        if self.is_ethernet():
            await self.get_static()

    async def get_current_ip(self):
        retval, output = await utils.shell("ip route")
        if retval != 0 or output is None:
            return
        match = re.search("default via ([\d\.]+)", output)
        if match:
            self.gateway = match.group(1)
            network = ".".join(self.gateway.split(".")[:-1] + ["0"])

            match = re.search(f"({network}/\d+) [\w0 ]+ ([\d\.]+)", output)
            if match:
                self.mask = str(IPv4Interface(match.group(1)).netmask)
                self.ip = match.group(2)

                # Check interfaces in order, prioritizing eth0 then eth1
                for iface in NetworkType.get_interfaces():
                    retval, output = \
                            await utils.shell(f"ip address show dev {iface}")
                    if retval == 0 and output is not None:
                        match = re.search("inet ([\d\.]+)", output)
                        if match is not None and self.ip == match.group(1):
                            self.type = NetworkType.from_interface(iface)
                            # Store which ethernet interface is active
                            if iface in ["eth0", "eth1"]:
                                self.active_eth_iface = iface
                            return

    async def get_wifi_ssid(self):
        pass

    async def get_static(self):
        pass

    async def save(self):
        logger.debug("Not a gateway, ignoring network configuration")
