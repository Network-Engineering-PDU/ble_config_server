import logging

import ipaddress

from ble_config_server.network.base_device import BaseDevice
from ble_config_server.network.network_type import NetworkType
from ble_config_server import utils


logger = logging.getLogger(__name__)


class Heimdall(BaseDevice):

    WIFI_CONN = "ble-wifi-conn"
    ETH_CONN = "ble-eth-conn"
    
    def __init__(self):
        super().__init__()
        self.active_eth_iface = "eth0"  # Track which ethernet interface is active

    async def _get_ip_from_if(self, iface):
        _, output = await utils.shell(f"nmcli -t d show {iface}")

        for l in output.split("\n"):
            if "IP4.ADDRESS[1]" in l:
                ip = l.split(":",1)[1].strip()
            if "IP4.GATEWAY" in l:
                self.gateway = l.split(":",1)[1].strip()

        iface_ip = ipaddress.IPv4Interface(ip)
        self.ip = str(iface_ip.ip)
        self.mask = str(iface_ip.netmask)


    async def get_current_ip(self):
        retval, output = await utils.shell(f"nmcli -t con show {self.ETH_CONN}")
        if retval == 0: # Static ethernet is configured
            self.type = NetworkType.ETH_STATIC

            retval, output = await utils.shell(
                f"nmcli -t -f GENERAL.STATE con show {self.ETH_CONN}")
            if "activated" in output:
                iface = NetworkType.to_interface(self.type)
                await self._get_ip_from_if(iface)
                return

        retval, output = await utils.shell(
            f"nmcli -t con show {self.WIFI_CONN}")
        if retval == 0: # Wifi is configured
            self.type = NetworkType.WIFI

            retval, output = await utils.shell(
                f"nmcli -t -f GENERAL.STATE con show {self.WIFI_CONN}")
            if "activated" in output:
                iface = NetworkType.to_interface(self.type)
                await self._get_ip_from_if(iface)
                return

        # In other cases the connection is dhcp - check both eth0 and eth1
        self.type = NetworkType.ETH_DHCP
        
        # Try eth0 first, then eth1
        for eth_iface in ["eth0", "eth1"]:
            retval, output = await utils.shell(
                f"nmcli -t -f GENERAL.STATE d show {eth_iface}")
            if "connected" in output:
                self.active_eth_iface = eth_iface
                await self._get_ip_from_if(eth_iface)
                return

    async def get_wifi_ssid(self):
        retval, output = await utils.shell(
            f"nmcli -t -f 802-11-wireless.ssid con show {self.WIFI_CONN}")
        if retval == 0:
            self.ssid = output.split(":",1)[1].strip()

    async def get_static(self):
        # Con only exist if is static
        retval, _ = await utils.shell(f"nmcli -t con show {self.ETH_CONN}")
        if retval == 0:
            self.type = NetworkType.ETH_STATIC

    async def set_wifi(self):
        await utils.shell(f"nmcli con del {self.WIFI_CONN}")

        await utils.shell("nmcli connection add type wifi " + \
            f"ifname '*' con-name '{self.WIFI_CONN}' ssid '{self.ssid}' " + \
            "802-11-wireless-security.key-mgmt 'wpa-psk' " + \
            f"802-11-wireless-security.psk '{self.psk}' " + \
            "connection.autoconnect yes")
        await utils.shell(f"nmcli con up {self.WIFI_CONN}")


    async def set_ethernet(self):
        await utils.shell(f"nmcli con del {self.ETH_CONN}")

        if self.is_static():
            iface_ip = ipaddress.IPv4Interface(f"{self.ip}/{self.mask}")
            # Create connection for both eth0 and eth1 as wildcard
            await utils.shell("nmcli connection add type " + \
                f"ethernet con-name ble-eth-conn ifname '*' ip4 " + \
                f"{str(iface_ip)} gw4 {self.gateway} ipv4.dns " + \
                f"'{self.dns1},{self.dns2}'")
            await utils.shell(f"nmcli con up {self.ETH_CONN}")
        else:
            # DHCP - create connection for both eth0 and eth1 as wildcard
            await utils.shell("nmcli connection add type " + \
                f"ethernet con-name ble-eth-conn ifname '*' ipv4.method auto")
            await utils.shell(f"nmcli con up {self.ETH_CONN}")

    async def save(self):
        if self.is_ethernet() or self.is_wifi():

            if self.is_ethernet():
                await self.set_ethernet()
            elif self.is_wifi():
                await self.set_wifi()
