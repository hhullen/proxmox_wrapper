from argparse import ArgumentParser, Namespace
from .proxmoxapi import ProxmoxAPI


def read_args() -> Namespace:
    parser = ArgumentParser("proxapi",
                            description="Proxmox wrapper on `proxmoxer` Python library. "
                            "Implements a simple command line interface to manage vitrual "
                            "machines on Proxmox cluster.")
    parser.add_argument("mode", type=str,
                        metavar="[action mode]",
                        help="Available: get/create/delete/start/stop/reboot/config/status/clone")
    parser.add_argument("node", type=str,
                        metavar="[node name]",
                        help="cluster node name")
    parser.add_argument("id", type=str,
                        metavar="[machine id]",
                        help="machine identifier")

    parser.add_argument("--start-id", type=int,
                        metavar="[id]",
                        help="id which new id searching will be starting from")
    parser.add_argument("--vm-name", type=str,
                        metavar="[vm-name]",
                        help="virtual machine name to create")
    parser.add_argument("--ram", type=str,
                        metavar="[ram]",
                        help="virtual machine ram size, MiB")
    parser.add_argument("--sockets", type=int,
                        metavar="[sockets]",
                        help="virtual machine sockets amount")
    parser.add_argument("--cores", type=int,
                        metavar="[cores]",
                        help="virtual machine cores amount")
    parser.add_argument("--vm-disk-size", type=int,
                        metavar="[vm disk zise]",
                        help="virtual machine disk size, GB")
    parser.add_argument("--node-storage-name", type=str,
                        metavar="[node storage name]",
                        help="node existing storage name")
    parser.add_argument("--network", type=str,
                        metavar="[vm network]",
                        help="network to set up in format: \"10.10.15.0/24\"")
    return parser.parse_args()


def init_modes(proxmox: ProxmoxAPI):
    modes: dict = {}
    modes["create"] = proxmox.create
    modes["delete"] = proxmox.delete
    modes["start"] = proxmox.start
    modes["stop"] = proxmox.stop
    modes["reboot"] = proxmox.reboot
    modes["config"] = proxmox.configurate
    modes["status"] = proxmox.status
    modes["clone"] = proxmox.clone
    modes["rebuild"] = proxmox.rebuild
    modes["get"] = proxmox.get
    return modes
