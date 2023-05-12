from configuration import HOST, USER, PASSWORD, infolog, errlog
from service import ProxmoxAPI, init_modes, read_args


def main():
    args = read_args()
    infolog.info(f"Request: {args.mode} {args.node} {args.id}")
    proxmox = ProxmoxAPI(HOST, USER, PASSWORD)
    modes: dict = init_modes(proxmox)
    if modes.get(args.mode):
        modes[args.mode](node=args.node,
                         vmid=args.id,
                         clonename=args.clone_name,
                         startid=args.start_id,
                         vmname=args.vm_name,
                         ram=args.ram,
                         sockets=args.sockets,
                         cores=args.cores,
                         disksize=args.vm_disk_size,
                         storagename=args.node_storage_name)
    else:
        raise BaseException(
            "Wrong mode specified. Available: "
            "[create/delete/start/stop/reboot/config/status/clone]")


if __name__ == "__main__":
    try:
        main()
    except BaseException as ex:
        errlog.error(ex)
