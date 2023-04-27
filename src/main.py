from service import WrappedProxmoxAPI, init_modes, read_args
import logging
import os

PASSWORD = os.environ['PROX_PASS']
HOST = "10.10.31.11"
USER = "root@pam"


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
            "Wrong mode specified. Available: [create/delete/start/stop/reboot/config/status/clone]")


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO,
                            format='\033[33m%(levelname)s\033[0m: %(message)s')
        main()
    except BaseException as ex:
        logging.error(ex)
