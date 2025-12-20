import os
import sys
import logging
import hashlib
import asyncio

import dbus_next

from ble_config_server import constants
from ble_config_server.daemon import Daemon
from ble_config_server.ble_app import BleServer


def main():
    commands = ["start", "stop", "restart"]
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        print("Usage: ble_config_server start|stop|restart")
        sys.exit(1)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(
        os.path.expanduser("/var/log/ble_config_server.log"))
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - ' +
        '%(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    root_logger.addHandler(fh)

    ble_server = BleServer()
    daemon = Daemon("BLE Config Server", constants.PID_FILE, ble_server.run,
        ble_server.clean_exit)
    if sys.argv[1] == "start":
        daemon.start()
    elif sys.argv[1] == "stop":
        daemon.stop()
    elif sys.argv[1] == "restart":
        daemon.restart()
