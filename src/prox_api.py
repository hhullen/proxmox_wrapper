from proxmoxer import ProxmoxAPI
from configuration import Config
import urllib3
import logging
import time
import os
import sys

args = sys.argv


PASSWORD = os.environ['PROX_PASS']
HOST = "10.10.31.11"
USER = "root@pam"


VM_ID = 201


urllib3.disable_warnings()
proxmox = ProxmoxAPI(host=HOST,
                     user=USER,
                     password=PASSWORD,
                     verify_ssl=False)
cluster = []


def is_mv_exists(vmid) -> bool:
    response = proxmox.nodes("pve2").qemu.get()
    for mv in response:
        if mv['vmid'] == vmid:
            return True
    return False


def collect_info():
    response = proxmox.nodes("pve2").qemu.get()
    for mv in response:

        print(mv['vmid'], '\n')

    # for i in proxmox.nodes("pve2").storage("StorageLocal2").get("content"):
    #     print(i['volid'].strip("StorageLocal2:"), '\n')

    # for i in proxmox.nodes("pve2").storage("local").get("content"):
    #     print(i, '\n')

    # for node in proxmox.nodes.get():
    #     for vm in proxmox.nodes(node["node"]).qemu.get():
    #         cluster.append({"node": node['node'],
    #                         "vmid": vm['vmid'],
    #                         "name": vm['name'],
    #                         "status": vm['status']}
    #                        )
    #         logging.info(
    #             f"Node: {node['node']} \t ID: {vm['vmid']} \t Name: {vm['name']} => {vm['status']}")


def create_storage(cfg: Config):
    new_disk_name: str = f"vm-{cfg.vmid}-disk-0"
    disks: list = proxmox.nodes(cfg.node).storage(
        cfg.node_storage_name).get("content")

    disks = list(map(lambda name: name['volid'].strip(
        f"{cfg.node_storage_name}:"), disks))

    if list(filter(lambda name: name == new_disk_name, disks)):
        return

    response = proxmox.nodes(cfg.node).storage(cfg.node_storage_name).content.post(filename=f"vm-{cfg.vmid}-disk-0",
                                                                                   node=cfg.node,
                                                                                   size=cfg.vm_storage,
                                                                                   storage=cfg.node_storage_name,
                                                                                   vmid=cfg.vmid)
    logging.info(f"Created disk: {new_disk_name}. {response}")


def create_vm():
    cfg = Config("configuration/configuration.cfg")

    create_storage(cfg)

    if not is_mv_exists(cfg.vmid):
        response = proxmox.nodes(cfg.node).qemu.post(
            # options
            vmid=cfg.vmid,
            name=cfg.name,
            acpi=1,
            autostart=1,
            ostype=cfg.ostype,
            boot="order=scsi0;ide2;ide0;net0",
            tablet=1,
            hotplug="disk,network,usb",
            # kvm=0,
            freeze=0,
            localtime=1,
            # smbios1="uuid=" + str(uuid.uuid4()),
            agent=0,
            protection=0,
            # spice_enhancements="videostreaming=off,foldersharing=0",
            vmstatestorage="automatic",
            #  hardware
            memory=cfg.ram,
            cores=cfg.cores,
            sockets=cfg.sockets,
            bios="seabios",
            # machine="pc-i440fx-0.0",
            scsihw="virtio-scsi-pci",
            ide1=f"file={cfg.ide1},media=cdrom,size={cfg.size_ide1}",
            ide2=f"file={cfg.ide2},media=cdrom,size={cfg.size_ide2}",
            scsi0=f"{cfg.node_storage_name}:vm-{cfg.vmid}-disk-0,size={cfg.vm_storage}",
            net0=f"model=virtio,bridge={cfg.brigde},firewall={cfg.firewall}")
        logging.info(f"Created machine: {response}")

    run_machine(cfg)


def run_machine(cfg: Config):
    response = proxmox.nodes(cfg.node).qemu(cfg.vmid).status.get("current")
    if response['status'] == "stopped":
        response = proxmox.nodes(cfg.node).qemu(cfg.vmid).status.post("start")
        logging.info(f"Started machine: {response}")


def delete_vm(node: str, vmid: str):
    response = proxmox.nodes(node).qemu(vmid).status.get("current")
    if response['status'] != "stopped":
        logging.info(f"Terminating: {vmid}")
        response = proxmox.nodes(node).qemu(vmid).status.post("stop")
        logging.info(f"Terminated: {response}")

    wait_termination(node, vmid, 15)
    response = proxmox.nodes(node).qemu(vmid).delete()
    logging.info(f"Deleted: {response}")


def wait_termination(node: str, vmid: str, timeout: int):
    response = proxmox.nodes(node).qemu(vmid).status.get("current")
    while response['status'] != "stopped" and timeout:
        timeout -= 1
        time.sleep(1)
        response = proxmox.nodes(node).qemu(vmid).status.get("current")


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO)
        # collect_info()
        # delete_vm("pve2", "201")
        create_vm()
    except BaseException as _ex:
        logging.critical(_ex)
