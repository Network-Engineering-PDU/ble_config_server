import json
import asyncio

import ttgateway.commands as cmds
from ttgateway.config import Config


async def get_config(module, field):
    cmd = cmds.ConfigGet(module, field)
    rsp = await send_cmd(cmd)
    if rsp is not None and rsp["success"]:
        return rsp["data"]["value"]
    return None


async def set_config(module, field, value):
    cmd = cmds.ConfigSet(module, field, value)
    rsp = await send_cmd(cmd)
    if rsp is not None:
        return rsp["success"]
    return None


async def save_config():
    cmd = cmds.ConfigSave()
    rsp = await send_cmd(cmd)
    if rsp is not None:
        return rsp["success"]
    return None


async def backup_config():
    cmd = cmds.ConfigBackup()
    rsp = await send_cmd(cmd)
    if rsp is not None:
        return rsp["success"]
    return None


async def erase_config():
    cmd = cmds.ConfigErase()
    rsp = await send_cmd(cmd)
    if rsp is not None:
        return rsp["success"]
    return None


async def check_pt_connection():
    cmd = cmds.GatewayMngrCheckPT()
    rsp = await send_cmd(cmd)
    if rsp is not None:
        return rsp["data"]["status"]
    return None


async def send_cmd(cmd):
    try:
        reader, writer = await asyncio.open_unix_connection(
            Config.SERVER_SOCKET)
        writer.write(cmd.serialize())
        await writer.drain()
        data_length = int.from_bytes(await reader.read(4), "little")
        data = await reader.read(data_length)
        return json.loads(data.decode())
    except ConnectionRefusedError:
        return None
