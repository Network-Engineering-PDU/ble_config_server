import os

# TycheTools gw app directory
TT_DIR = os.path.expanduser("~/.tychetools")

# BLE Public key file environment variable
PK_DEFAULT_FILE = "/etc/ble_config_key.pub"
PK_FILE_ENV = "BLE_CONFIG_SERVER_PK_FILE"

# PID file
PID_FILE = "/tmp/ble_config.pid"
