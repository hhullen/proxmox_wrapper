from proxmoxer import ProxmoxAPI
from configuration import Config
import urllib3
import logging
import time


class WrappedProxmoxAPI:
    def __init__(self, host: str, user: str, password: str) -> None:
        logging.basicConfig(level=logging.INFO,
                            format='\033[33m%(levelname)s\033[0m: %(message)s')
        urllib3.disable_warnings()
        self.proxmox = ProxmoxAPI(host=host,
                                  user=user,
                                  password=password,
                                  verify_ssl=False)

    def configurate(self, node, vmid):
        cfg = Config("configuration/vmsetup.cfg")
        if self._is_vm_exists(node, vmid):
            vmconfig = self.proxmox.nodes(node).qemu(vmid).config
            response = vmconfig.post(name=cfg.name,
                                     ostype=cfg.ostype,
                                     memory=cfg.ram,
                                     cores=cfg.cores,
                                     sockets=cfg.sockets,
                                     ide1=f"file={cfg.ide1},media=cdrom,size={cfg.size_ide1}",
                                     ide2=f"file={cfg.ide2},media=cdrom,size={cfg.size_ide2}",
                                     scsi0=f"{cfg.node_storage_name}:vm-{vmid}-disk-0,size={cfg.vm_storage}",
                                     net0=f"model=virtio,bridge={cfg.brigde},firewall={cfg.firewall}")
            logging.info(f"Configurated machine: {response}")
        else:
            logging.warning(f"Machine {node}.{vmid} does not exists")

    def create(self, node, vmid):
        cfg = Config("configuration/vmsetup.cfg")
        self._create_storage(cfg, node, vmid)
        if not self._is_vm_exists(node, vmid):
            response = self.proxmox.nodes(node).qemu.post(
                # options
                vmid=vmid,
                name=cfg.name,
                acpi=1,
                autostart=1,
                ostype=cfg.ostype,
                boot="order=scsi0;ide2;ide0;net0",
                tablet=1,
                hotplug="disk,network,usb",
                freeze=0,
                localtime=1,
                agent=0,
                protection=0,
                vmstatestorage="automatic",
                #  hardware
                memory=cfg.ram,
                cores=cfg.cores,
                sockets=cfg.sockets,
                ide1=f"file={cfg.ide1},media=cdrom,size={cfg.size_ide1}",
                ide2=f"file={cfg.ide2},media=cdrom,size={cfg.size_ide2}",
                scsi0=f"{cfg.node_storage_name}:vm-{vmid}-disk-0,size={cfg.vm_storage}",
                net0=f"model=virtio,bridge={cfg.brigde},firewall={cfg.firewall}",
                scsihw="virtio-scsi-pci")
            logging.info(f"Created machine: {response}")
        else:
            logging.warning(f"Machine {node}.{vmid} is already exists")

    def delete(self, node, vmid):
        response = self.proxmox.nodes(node).qemu(vmid).status.get("current")
        if response['status'] != "stopped":
            logging.info(f"Terminating: {node}.{vmid}")
            response = self.proxmox.nodes(node).qemu(vmid).status.post("stop")
            logging.info(f"Terminated: {response}")

        self._wait_termination(node, vmid, 15)
        response = self.proxmox.nodes(node).qemu(vmid).delete()
        logging.info(f"Deleted: {response}")

    def start(self, node, vmid):
        response = self.proxmox.nodes(node).qemu(vmid).status.get("current")
        if response['status'] == "stopped":
            response = self.proxmox.nodes(node).qemu(
                vmid).status.post("start")
            logging.info(f"Started machine: {response}")
        else:
            logging.warning(f"Machine is already started: {response}")

    def stop(self, node, vmid):
        response = self.proxmox.nodes(node).qemu(vmid).status.get("current")
        if response['status'] != "stopped":
            response = self.proxmox.nodes(node).qemu(
                vmid).status.post("stop")
            logging.info(f"Stopped machine: {response}")
        else:
            logging.warning(f"Machine is already stopped: {response}")

    def reboot(self, node, vmid):
        response = self.proxmox.nodes(node).qemu(vmid).status.post("reset")
        logging.info(f"Reboot machine: {response}")

    def _is_vm_exists(self, node, vmid) -> bool:
        response = self.proxmox.nodes(node).qemu.get()
        for mv in response:
            if mv['vmid'] == vmid:
                return True
        return False

    def _create_storage(self, cfg: Config, node, vmid):
        new_disk_name: str = f"vm-{vmid}-disk-0"
        disks: list = self.proxmox.nodes(node).storage(
            cfg.node_storage_name).get("content")

        disks = list(map(lambda name: name['volid'].strip(
            f"{cfg.node_storage_name}:"), disks))

        if list(filter(lambda name: name == new_disk_name, disks)):
            return

        storage = self.proxmox.nodes(node).storage(cfg.node_storage_name)

        response = storage.content.post(filename=f"vm-{vmid}-disk-0",
                                        node=node,
                                        size=cfg.vm_storage,
                                        storage=cfg.node_storage_name,
                                        vmid=vmid)
        logging.info(f"Created disk: {new_disk_name}. {response}")

    def _wait_termination(self, node: str, vmid: str, timeout: int):
        response = self.proxmox.nodes(node).qemu(vmid).status.get("current")
        while response['status'] != "stopped" and timeout:
            timeout -= 1
            time.sleep(1)
            response = self.proxmox.nodes(node).qemu(
                vmid).status.get("current")
