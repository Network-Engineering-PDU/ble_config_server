from ble_config_server.network.network_type import NetworkType


class NetworkConfig:
    def __init__(self):
        self.ip = None
        self.mask = None
        self.gateway = None
        self.dns1 = None
        self.dns2 = None
        self.type = None
        self.ssid = None
        self.psk = None
        self.active_eth_iface = "eth0"  # Track which ethernet interface is active
        self.reset()

    def reset(self):
        self.ip = "192.168.0.1"
        self.mask = "255.255.255.0"
        self.gateway = "192.168.0.1"
        self.dns1 = "8.8.8.8"
        self.dns2 = "8.8.4.4"
        self.type = NetworkType.UNCONF
        self.ssid = ""
        self.psk = ""

    def is_static(self):
        return NetworkType.is_static(self.type)

    def is_ethernet(self):
        return (self.type == NetworkType.ETH_DHCP
            or self.type == NetworkType.ETH_STATIC)

    def is_wifi(self):
        return self.type == NetworkType.WIFI
