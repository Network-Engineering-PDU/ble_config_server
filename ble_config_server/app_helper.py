import logging
import asyncio

from ttgateway.config import config

from ble_config_server import utils
from ble_config_server import gateway_helper


logger = logging.getLogger(__name__)

class AppConfig:
    def __init__(self, module, field, default_value):
        self.module = module
        self.field = field
        self.value = default_value

    async def get_config(self):
        try:
            value = await gateway_helper.get_config(self.module, self.field)
            if value is None:
                return
            self.value = value
        except (ConnectionRefusedError, FileNotFoundError):
            logger.warning(f"Config {self.module} {self.field} not found.")

    async def set_config(self):
        try:
            await gateway_helper.set_config(self.module, self.field, self.value)
        except (ConnectionRefusedError, FileNotFoundError):
            logger.error(f"Error setting {self.module} {self.field} config.")


async def update_app_config(app_config):
    # TODO: checks
    for _, conf in app_config.items():
        await conf.get_config()

async def get_app_config():
    app_config = {
        "url": AppConfig("backend", "url", "unknown"),
        "user": AppConfig("backend", "user", "unknown"),
        "password": AppConfig("backend", "password", "unknown"),
        "device_id": AppConfig("backend", "device_id", "unknown"),
        "company": AppConfig("backend", "company", "unknown"),
        "netkey": AppConfig("netkey", "", bytes(16).hex()),
        "address": AppConfig("address", "", 0),
        "multi_gw_host": AppConfig("multi_gw_server", "host", "unknown"),
        "multi_gw_port": AppConfig("multi_gw_server", "port", 0),
        "multi_gw_role": AppConfig("gateway", "multi_gw_role", "unknown"),
    }
    update_app_config(app_config)
    return app_config


async def set_app_config(app_config):
    logger.debug("Saving app config")
    await gateway_helper.backup_config()
    await gateway_helper.erase_config()
    for _, conf in app_config.items():
        await conf.set_config()
    config.create_default_gwrc()
    await gateway_helper.save_config()
    await utils.shell("ttdaemon stop")
    await asyncio.sleep(0.5)
    await utils.shell("ttdaemon start")


async def check_passthrough_connection():
    for retries in range(10):
        if await gateway_helper.check_pt_connection():
            logger.info(f"Passthrough connection ok ({retries})")
            return True
        await asyncio.sleep(1)
    logger.warning("Passthrough connection error")
    return False
