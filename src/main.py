from service import WrappedProxmoxAPI
from argparse import ArgumentParser, Namespace
import logging
import os

PASSWORD = os.environ['PROX_PASS']
HOST = "10.10.31.11"
USER = "root@pam"


def read_args() -> Namespace:
    parser = ArgumentParser("proxapi",
                            description="ProxmoxAPI CLI. Any action with machine requires "
                            "three arguments: action mode, node name and machine identifier. "
                            "To create new one or configurate existing machine it is necessary to "
                            "setup configuration file palced in 'configuration/vmsetup.cfg'. "
                            "To clone any machine two optional arguments can be set: "
                            "--clonename and --startid")
    parser.add_argument("mode", type=str,
                        metavar="[action mode]",
                        help="Available: create/delete/start/stop/reboot/config/status/clone")
    parser.add_argument("node", type=str,
                        metavar="[node name]",
                        help="cluster node name")
    parser.add_argument("id", type=int,
                        metavar="[machine id]",
                        help="machine identifier")
    parser.add_argument("--clonename", type=str,
                        metavar="[name]",
                        help="clone name")
    parser.add_argument("--startid", type=int,
                        metavar="[id]",
                        help="id which new id searching will be starting from")
    return parser.parse_args()


def init_modes(proxmox: WrappedProxmoxAPI):
    modes: dict = {}
    modes["create"] = proxmox.create
    modes["delete"] = proxmox.delete
    modes["start"] = proxmox.start
    modes["stop"] = proxmox.stop
    modes["reboot"] = proxmox.reboot
    modes["config"] = proxmox.configurate
    modes["status"] = proxmox.status
    modes["clone"] = proxmox.clone
    return modes


def main():
    args = read_args()
    logging.info(f"Request: {args.mode} {args.node} {args.id}")
    proxmox = WrappedProxmoxAPI(HOST, USER, PASSWORD)
    modes: dict = init_modes(proxmox)
    if modes.get(args.mode):
        modes[args.mode](node=args.node,
                         vmid=args.id,
                         clonename=args.clonename,
                         startid=args.startid)
    else:
        raise BaseException(
            "Wrong mode specified. Available: [create/delete/start/stop/reboot]")


if __name__ == "__main__":
    # try:
    logging.basicConfig(level=logging.INFO,
                        format='\033[33m%(levelname)s\033[0m: %(message)s')
    main()
    # except BaseException as ex:
    #     logging.error(ex)
