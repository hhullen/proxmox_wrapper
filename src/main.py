from service import WrappedProxmoxAPI, init_modes, read_args
from configuration import HOST, USER
import logging
import os

logging.basicConfig(level=logging.INFO,
                    format='\033[33m%(levelname)s\033[0m: %(message)s')

try:
    PASSWORD = os.environ['PROX_PASS']
except:
    logging.error(
        "Enter a password to ProxmoxVE connection as environment "
        "variable: export PROX_PASS='your_pass_word'")
    exit()


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
        main()
    except BaseException as ex:
        logging.error(ex)
