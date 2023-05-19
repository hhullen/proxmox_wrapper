from argparse import ArgumentParser, Namespace
import subprocess
import ipaddress
import logging
import sys
import os


errlog = logging.getLogger("error_logger")
errlog.setLevel(logging.ERROR)
_err_format = logging.Formatter(
    '\033[91m%(levelname)s\033[0m: %(asctime)s: %(message)s')
_err_handler = logging.StreamHandler(sys.stderr)
_err_handler.setFormatter(_err_format)
errlog.addHandler(_err_handler)


def get_binded(path) -> list:
    if not path:
        return []

    try:
        with open(path, 'r') as file:
            binded = file.read()
            return binded.split('\n')
    except:
        raise FileNotFoundError(
            "Can not find file with binded addresses. "
            "Expample: ip_seeker 10.10.31.11/24 ~/bind_list.ip")


def read_args() -> Namespace:
    parser = ArgumentParser("ip_seeker",
                            description="Free ip seeker")
    parser.add_argument("network", type=str,
                        metavar="[network]",
                        help="example: 10.10.31.0/24")

    parser.add_argument("--binded", type=str,
                        metavar="[file path]",
                        help="path to file with binded addresses")
    parser.add_argument("--reverse", type=str,
                        metavar="[true/false]",
                        help="revers searching")
    return parser.parse_args()


def seek_free_address(addresses: list):
    if len(addresses) < 2:
        raise BaseException(
            "Can not find address from available. Network specified wrong, possible")

    home = os.path.expanduser("~")
    with open(f"{home}/ip_seek.log", "a") as logfile:
        for i in range(0, len(addresses) - 1):
            cmd_1 = ['ping', addresses[i], '-c', '1']
            cmd_2 = ['ping', addresses[i + 1], '-c', '1']
            code_1 = subprocess.call(cmd_1, stdout=logfile)
            code_2 = subprocess.call(cmd_2, stdout=logfile)
            if code_1 != 0 and code_2 != 0:
                return addresses[i]
    sys.stderr.write("Impossible find free addres in the network")
    exit(1)


def main():
    args = read_args()
    binded: list = get_binded(args.binded)
    network = ipaddress.ip_network(args.network)
    addresses = []

    for address in network.hosts():
        if address.compressed not in binded:
            addresses.append(address.compressed)

    if args.reverse == "true":
        addresses.reverse()

    free_address = seek_free_address(addresses)
    sys.stdout.write(free_address)


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        errlog.error(ex)
