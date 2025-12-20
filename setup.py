import setuptools

#with open("README.md", "r") as fh:
#    long_description = fh.read()

setuptools.setup(
    name="ble_config_server",
    version="1.2.0",
    author="Tychetools",
    description="Tychetools BLE configuration server for the gateway",
    #long_description=long_description,
    #long_description_content_type="text/markdown",
    url="https://bitbucket.org/tychetools/ble_config_server.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.7",
    install_requires=[
        "dbus-next==0.2.3",
        "cryptography==41.0.1",
    ],
    entry_points={
        "console_scripts": {
            "ble_config_server = ble_config_server.__init__:main",
        }
    }
)
