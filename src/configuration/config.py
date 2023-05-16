from environs import Env
import logging
import yaml
import sys
import os


infolog = logging.getLogger("info_logger")
infolog.setLevel(logging.INFO)
_info_format = logging.Formatter(
    '\033[92m%(levelname)s\033[0m: %(asctime)s: %(message)s')
_info_handler = logging.StreamHandler(sys.stdout)
_info_handler.setFormatter(_info_format)
infolog.addHandler(_info_handler)

errlog = logging.getLogger("error_logger")
errlog.setLevel(logging.ERROR)
_err_format = logging.Formatter(
    '\033[91m%(levelname)s\033[0m: %(asctime)s: %(message)s')
_err_handler = logging.StreamHandler(sys.stderr)
_err_handler.setFormatter(_err_format)
errlog.addHandler(_err_handler)

warnlog = logging.getLogger("warning_logger")
warnlog.setLevel(logging.WARNING)
_warn_format = logging.Formatter(
    '\033[93m%(levelname)s\033[0m: %(asctime)s: %(message)s')
_warn_handler = logging.StreamHandler(sys.stderr)
_warn_handler.setFormatter(_warn_format)
warnlog.addHandler(_warn_handler)

home = os.path.expanduser("~")
config_dir = f"{home}/.proxapi"


try:
    PASSWORD = os.environ['PROX_PASS']
except:
    errlog.error(
        "Enter a password to ProxmoxVE connection as environment "
        "variable: export PROX_PASS='your_pass_word'")
    exit()

try:
    env: Env = Env()
    env.read_env(f"{config_dir}/vmsetup.cfg")
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
        self.ide1: str = env("IDE0")
        self.ide2: str = env("IDE1")
        self.vm_disk_size: str = env("VM_DISK_SIZE")
        self.node_storage_name: str = env("NODE_STORAGE_NAME")
        self.brigde: str = env("BRIDGE")
        self.firewall: str = env("FIREWALL")
        self.network: str = ""

    def update_from_args(self, args: dict[str, any]):
        self.name = valid(args.get("vmname"), self.name)
        self.ram = valid(args.get("ram"), self.ram)
        self.sockets = valid(args.get("sockets"), self.sockets)
        self.cores = valid(args.get("cores"), self.cores)
        self.vm_disk_size = valid(args.get("disksize"), self.vm_disk_size)
        self.node_storage_name = valid(
            args.get("storagename"), self.node_storage_name)
        self.network = valid(args.get("network"), self.network)


try:
    with open(f"{config_dir}/user-data") as file:
        ubuntu_autoinstall_config = yaml.safe_load(file)
except:
    warnlog.warning("Cannot load user-data file. Default config is set.")
    _custom_commands = ['echo "@reboot root /bin/bash /root/autoinit/init_script" > /target/etc/cron.d/autoinit',
                        'chmod 755 /target/etc/cron.d/autoinit']
    ubuntu_autoinstall_config = {'autoinstall': {'version': 1,
                                                 'identity': {'realname': 'ubuntu',
                                                              'hostname': 'new-qemu',
                                                              'password': '$1$OjcU1ha7$uFbuvRnUwvRcme9Xy3n3L1',
                                                              'username': 'ubuntu'},
                                                 'locale': 'en_US.UTF-8',
                                                 'refresh-installer': {'update': False},
                                                 'storage': {'layout': {'name': 'lvm'}},
                                                 'ssh': {'install-server': False},
                                                 'network': None,
                                                 'late-commands': _custom_commands}}


network_settings = {"network": {"version": 2,
                                "renderer": "networkd",
                                "ethernets": {"ens18": {"addresses": None,
                                                        "gateway4": "",
                                                        "nameservers": {"addresses": [None,
                                                                                      "8.8.8.8"]}}}}}
