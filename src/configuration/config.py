from environs import Env
import os
import logging

logging.basicConfig(level=logging.INFO,
                    format='\033[33m%(levelname)s\033[0m: %(message)s')


config_path = f"/home/{os.getenv('USER')}/.proxapi/vmsetup.cfg"


try:
    PASSWORD = os.environ['PROX_PASS']
except:
    logging.error(
        "Enter a password to ProxmoxVE connection as environment "
        "variable: export PROX_PASS='your_pass_word'")
    exit()

try:
    env: Env = Env()
    env.read_env(config_path)
    HOST = env("HOST")
    USER = env("USER_NAME")
except:
    logging.error("Can not read configuration file for HOST and USER field."
                  "Try to run bash configure.sh from src folder in source code directory.")
    exit()


class Config:
    def __init__(self, path: str) -> None:
        env: Env = Env()
        env.read_env(path)
        self.name: str = env("NAME")
        self.ostype: str = env("OS_TYPE")
        self.ram: str = env("RAM_MEMORY")
        self.sockets: str = env("SOCKETS")
        self.cores: str = env("CORES")
        self.ide1: str = env("IDE1")
        self.ide2: str = env("IDE2")
        self.size_ide1: str = env("SIZE_IDE1")
        self.size_ide2: str = env("SIZE_IDE2")
        self.vm_storage: str = env("VM_STORAGE")
        self.node_storage_name: str = env("NODE_STORAGE_NAME")
        self.brigde: str = env("BRIDGE")
        self.firewall: str = env("FIREWALL")
