import os
import asyncio


async def shell(cmd):
    process = await asyncio.create_subprocess_shell(cmd,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT)
    stdout, _ = await process.communicate()
    retval = await process.wait()
    output = stdout.decode()
    return retval, output


async def async_write(file, data):
    def _write(file, data):
        with open(file, "w") as f:
            f.write(data)
    await asyncio.to_thread(_write, file, data)


async def async_read(file):
    def _read(file):
        with open(file) as f:
            return f.read()
    return await asyncio.to_thread(_read, file)


async def is_heimdall():
    try:
        from ttgateway.config import config
    except ImportError:
        return False
    await asyncio.to_thread(config.read)
    return config.gateway.platform.startswith("heimdall")


async def is_raspberry():
    return os.uname().nodename == "raspberrypi"
