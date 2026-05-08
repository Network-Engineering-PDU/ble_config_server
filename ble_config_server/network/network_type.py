import os


class NetworkType:
    UNCONF     = 1
    ETH_DHCP   = 2
    ETH_STATIC = 3
    WIFI       = 4
    LTE_4G     = 5

    @classmethod
    def get_interfaces(cls):
        return ["wwan0", "ppp0", "wlan0", "eth0", "eth1"]

    @classmethod
    def from_interface(cls, interface):
        if interface == "ppp0" or interface == "wwan0":
            return cls.LTE_4G
        if interface == "wlan0":
            return cls.WIFI
        if interface == "eth0" or interface == "eth1":
            return cls.ETH_DHCP
        return cls.UNCONF

    @classmethod
    def get_static(cls, network_type):
        if network_type == cls.ETH_DHCP:
            return cls.ETH_STATIC
        return network_type

    @classmethod
    def is_static(cls, network_type):
        if network_type == cls.ETH_STATIC:
            return True
        return False

    @classmethod
    def to_interface(cls, network_type):
        if network_type == cls.ETH_DHCP or network_type == cls.ETH_STATIC:
            # Prefer the ethernet interface that reports carrier in sysfs.
            # This lets the runtime pick eth0 or eth1 depending on which
            # physical port is connected.
            for ifname in ("eth0", "eth1"):
                carrier_path = f"/sys/class/net/{ifname}/carrier"
                try:
                    with open(carrier_path, "r") as f:
                        if f.read().strip() == "1":
                            return ifname
                except Exception:
                    # file may not exist on some platforms, ignore
                    continue
            # If no carrier-detect file or none report carrier, prefer
            # an interface that exists, falling back to eth0.
            for ifname in ("eth0", "eth1"):
                if os.path.exists(f"/sys/class/net/{ifname}"):
                    return ifname
            return "eth0"
        if network_type == cls.WIFI:
            return "wlan0"
        if network_type == cls.LTE_4G:
            return "ppp0"
        return "unknown_if"
