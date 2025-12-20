import re
import logging
from ipaddress import IPv4Interface

from ble_config_server.network.base_device import BaseDevice
from ble_config_server.network.network_type import NetworkType
from ble_config_server import utils


logger = logging.getLogger(__name__)


RASP_CONFIG_FILE_PARAMS = """hostname
clientid
persistent

option domain_name_servers, domain_name, domain_search, host_name
option classless_static_routes
option interface_mtu
require dhcp_server_identifier
slaac private

"""


class Raspberry(BaseDevice):
    RASP_CONFIG_FILE = "/etc/dhcpcd.conf"
    RASP_WIFI_FILE = "/etc/wpa_supplicant/wpa_supplicant.conf"

    async def sudo_read(self, file):
        filename = file.split("/")[-1]
        tmp = f"/tmp/bcs-{filename}.read"
        await utils.shell(f"sudo -n cp {file} {tmp}")
        await utils.shell(f"sudo -n chmod 666 {tmp}")
        data = await utils.async_read(tmp)
        await utils.shell(f"rm {tmp}")
        return data

    async def sudo_write(self, file, data):
        filename = file.split("/")[-1]
        tmp = f"/tmp/bcs-{filename}.write"
        await utils.async_write(tmp, data)
        await utils.shell(f"sudo -n mv {tmp} {file}")
        await utils.shell(f"rm {tmp}")

    async def get_wifi_ssid(self):
        try:
            wpa_data = await self.sudo_read(self.RASP_WIFI_FILE)
            match = re.search("ssid=\"([^\"]+)\"", wpa_data)
            if match:
                self.ssid = match.group(1)
                return
        except FileNotFoundError:
            pass
        self.ssid = ""

    async def get_static(self):
        try:
            config = await utils.async_read(self.RASP_CONFIG_FILE)
            index = config.find("interface eth0")
            if index != -1 and config[index-1] != "#":
                self.type = NetworkType.get_static(self.type)
                return
        except FileNotFoundError:
            pass

    async def set_wifi(self):
        if self.ssid and self.psk:
            wpa_config = "ctrl_interface=/var/run/wpa_supplicant\n"
            wpa_config += "update_config=1\n"
            wpa_config += "network={\n"
            wpa_config += f"\tssid=\"{self.ssid}\"\n"
            wpa_config += f"\tpsk=\"{self.psk}\"\n"
            wpa_config += "}\n"
            await self.sudo_write(self.RASP_WIFI_FILE, wpa_config)
            await utils.shell("sudo -n wpa_cli -i wlan0 reconfigure")
        # Reset DHCP config
        await self.sudo_write(self.RASP_CONFIG_FILE, RASP_CONFIG_FILE_PARAMS)

    async def set_ethernet(self):
        # Default config
        config = RASP_CONFIG_FILE_PARAMS
        # New config
        if self.is_static():
            ip_and_mask = str(IPv4Interface(f"{self.ip}/{self.mask}"))
            config += "interface eth0\n"
            config += f"\tstatic ip_address={ip_and_mask}\n"
            config += f"\tstatic routers={self.gateway}\n"
            config += f"\tstatic domain_name_servers={self.dns1} {self.dns2}\n"
        await self.sudo_write(self.RASP_CONFIG_FILE, config)

    async def save(self):
        if self.is_ethernet() or self.is_wifi():
            if self.is_ethernet():
                await self.set_ethernet()
            elif self.is_wifi():
                await self.set_wifi()

            await utils.shell("sudo -n ip link set eth0 down")
            await utils.shell("sudo -n ip link set wlan0 down")
            iface = NetworkType.to_interface(self.type)
            await utils.shell(f"sudo -n ip link set {iface} up")
            logger.info("Network configuration saved")
