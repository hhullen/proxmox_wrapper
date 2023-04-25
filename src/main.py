from service import WrappedProxmoxAPI
from argparse import ArgumentParser
import logging
import os

PASSWORD = os.environ['PROX_PASS']
HOST = "10.10.31.11"
USER = "root@pam"


def read_args() -> tuple[str, str, int]:
    parser = ArgumentParser("proxapi",
                            description="ProxmoxAPI CLI. Any action with machine requires "
                            "three arguments: action mode, node name and machine identifier. "
                            "To create new one or configurate existing machine it is necessary to "
                            "setup configuration file palced in 'configuration/vmsetup.cfg'.")
    parser.add_argument("mode", type=str,
                        metavar="[action mode]",
                        help="Available: create/delete/start/stop/reboot/config")
    parser.add_argument("node_name", type=str,
                        metavar="[node name]",
                        help="cluster node name")
    parser.add_argument("vm_id", type=int,
                        metavar="[machine id]",
                        help="machine identifier")

    args = parser.parse_args()
    return args.mode, args.node_name, args.vm_id


def init_modes(proxmox: WrappedProxmoxAPI):
    modes: dict = {}
    modes["create"] = proxmox.create
    modes["delete"] = proxmox.delete
    modes["start"] = proxmox.start
    modes["stop"] = proxmox.stop
    modes["reboot"] = proxmox.reboot
    modes["config"] = proxmox.configurate
    return modes


def main():
    mode, node, vmid = read_args()
    logging.info(f"Request: {mode} {node} {vmid}")
    proxmox = WrappedProxmoxAPI(HOST, USER, PASSWORD)
    modes: dict = init_modes(proxmox)
    if modes.get(mode):
        modes[mode](node, vmid)
    else:
        raise BaseException(
            "Wrong mode specified. Available: [create/delete/start/stop/reboot]")


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO,
                            format='\033[33m%(levelname)s\033[0m: %(message)s')
        main()
    except BaseException as ex:
        logging.error(ex)
