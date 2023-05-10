from environs import Env
import logging
import os


infolog = logging.getLogger("info_logger")
infolog.setLevel(logging.INFO)
_info_format = logging.Formatter(
    '\033[92m%(levelname)s\033[0m: %(asctime)s: %(message)s')
_info_handler = logging.StreamHandler()
_info_handler.setFormatter(_info_format)
infolog.addHandler(_info_handler)

errlog = logging.getLogger("error_logger")
errlog.setLevel(logging.ERROR)
_err_format = logging.Formatter(
    '\033[91m%(levelname)s\033[0m: %(asctime)s: %(message)s')
_err_handler = logging.StreamHandler()
_err_handler.setFormatter(_err_format)
errlog.addHandler(_err_handler)


config_path = f"/home/{os.getenv('USER')}/.proxapi/vmsetup.cfg"


try:
    PASSWORD = os.environ['PROX_PASS']
except:
    errlog.error(
        "Enter a password to ProxmoxVE connection as environment "
        "variable: export PROX_PASS='your_pass_word'")
    exit()

try:
    env: Env = Env()
    env.read_env(config_path)
    HOST = env("PROXMOX_HOST")
    USER = env("USER_NAME")
except:
    errlog.error("Can not read configuration file for HOST and USER field."
                 "Try to run bash configure.sh from src folder in source code directory.")
    exit()


def valid(var, alt):
    return var if var else alt


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
        self.vm_disk_size: str = env("VM_DISK_SIZE")
        self.node_storage_name: str = env("NODE_STORAGE_NAME")
        self.brigde: str = env("BRIDGE")
        self.firewall: str = env("FIREWALL")

    def update_from_args(self, args: dict[str, any]):
        self.name = valid(args.get("vmname"), self.name)
        self.ram = valid(args.get("ram"), self.ram)
        self.sockets = valid(args.get("sockets"), self.sockets)
        self.cores = valid(args.get("cores"), self.cores)
        self.vm_disk_size = valid(args.get("disksize"), self.vm_disk_size)
        self.node_storage_name = valid(
            args.get("storagename"), self.node_storage_name)
