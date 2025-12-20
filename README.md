# ble_config_server
Application to configure the network and backend credentials of a Network-Engineering-PDU
gateway using BLE.

## Installation
The Bluetooth configuration server is intended to be included as a package in a 
Linux distribution generated using Yocto. However, it can also be installed
using pip. In the root directory of the project, type the following command:

    pip install .

This will install the Bluetooth configuration server and also the required
dependencies.

## Usage

The BLE server runs as a deamon. To start/stop/restart it, execute:

```
$ ble_config_server start|stop|restart
```

After starting the daemon, the gateway starts advertising itself as
**Network-Engineering-PDU-GW**, and any BLE device can connect to it.

## Log
The application will log events to the `/var/log/ble_config_server.log` file.

## BLE services and characteristics

The BLE server has four services: the security service, the network
configuration service, the application configuration service, and the
factory reset service. The following list shows the Bluetooth services and
characteristics, with their UUIDs.

* Security service: `da510000-0000-5aeb-050a-63f7c09baf2a`
	* Challenge characteristic: `da510000-0001-5aeb-050a-63f7c09baf2a`
* Network configuration service: `da510001-0000-5aeb-050a-63f7c09baf2a`
	* IP address characteristic: `da510001-0001-5aeb-050a-63f7c09baf2a`
	* IP mask characteristic: `da510001-0002-5aeb-050a-63f7c09baf2a`
	* Gateway IP characteristic: `da510001-0003-5aeb-050a-63f7c09baf2a`
	* DNS 1 IP characteristic: `da510001-0004-5aeb-050a-63f7c09baf2a`
	* DNS 2 IP characteristic: `da510001-0005-5aeb-050a-63f7c09baf2a`
	* IP check characteristic: `da510001-0006-5aeb-050a-63f7c09baf2a`
	* Load network characteristic: `da510001-0007-5aeb-050a-63f7c09baf2a`
	* Network interface characteristic: `da510001-0008-5aeb-050a-63f7c09baf2a`
	* Wi-Fi SSID characteristic: `da510001-0009-5aeb-050a-63f7c09baf2a`
	* Wi-Fi passwd characteristic: `da510001-000a-5aeb-050a-63f7c09baf2a`
* Backend configuration service: `da510002-0000-5aeb-050a-63f7c09baf2a`
	* URL characteristic: `da510002-0001-5aeb-050a-63f7c09baf2a`
	* User characteristic: `da510002-0002-5aeb-050a-63f7c09baf2a`
	* Password characteristic: `da510002-0003-5aeb-050a-63f7c09baf2a`
	* Device characteristic: `da510002-0004-5aeb-050a-63f7c09baf2a`
	* Company characteristic: `da510002-0005-5aeb-050a-63f7c09baf2a`
	* Backend check characteristic: `da510002-0006-5aeb-050a-63f7c09baf2a`
	* Netkey characteristic: `da510002-0007-5aeb-050a-63f7c09baf2a`
	* Unicast address characteristic: `da510002-0008-5aeb-050a-63f7c09baf2a`
	* Multi-gw address characteristic: `da510002-0009-5aeb-050a-63f7c09baf2a`
	* Multi-gw port characteristic: `da510002-000a-5aeb-050a-63f7c09baf2a`
	* Multi-gw role characteristic: `da510002-000b-5aeb-050a-63f7c09baf2a`
	* Multi-gw passthrough check characteristic: `da510002-000c-5aeb-050a-63f7c09baf2a`
* Factory reset service: `da510003-0000-5aeb-050a-63f7c09baf2a`
	* Factory reset characteristic: `da510003-0001-5aeb-050a-63f7c09baf2a`

### Security sevice
Since the application advertises itself publicly, anyone can connect to it. The
security service prevents any security issues by blocking reading from and
writing to any of the characteristics of the other two services until a
challenge response is successfully performed. The characteristics will be
blocked again automatically 30 seconds after the device disconnects, or sooner
if another device connects before that.

### Network configuration service
This service configures the network of the gateway, to allow it to connect to
the Internet. Through its characteristics, the current values can be read and
updated. To update them, write an IP adress with the following format:
`x.x.x.x`, where `x` is a number between 0 and 255.

When finished, the configuration can be saved by writing any value to the IP
check characteristic. The application will store the configuration. After it,
the application will check the internet conexion. If
successful, the value `1` will be written to this characteristic, which can be
read from the remote device. Othrewise, the value written will be `-1`.

### Application configuration service
The application configuration service allows to configure the options and
credentials needed to connect to the Network-Engineering-PDU backend. Similar to the network
service, its values can be read and updated through its characteristics. In this
case, the backend check characteristic writes the configuration to the
`~/.Network-Engineering-PDU/gw.config` file, which should not fail, so after saving, the
result will always be a `1`.

### Factory reset configuration service
The factory reset service allows to perform a factory reset to the gateway. To
do so, it removes every file and directory form `/home/root` and reboots the
gateway.
