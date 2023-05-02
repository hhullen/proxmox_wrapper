from configuration import Config, config_path, valid
from proxmoxer import ProxmoxAPI
from datetime import datetime
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

    def configurate(self, **vm):
        node = vm.get("node")
        vmid = vm.get("vmid")
        cfg = Config(config_path)
        cfg.update_from_args(vm)
        if self._is_vm_exists(node, vmid):
            vmconfig = self.proxmox.nodes(node).qemu(vmid).config
            response = vmconfig.post(name=cfg.name,
                                     ostype=cfg.ostype,
                                     memory=cfg.ram,
                                     cores=cfg.cores,
                                     sockets=cfg.sockets,
                                     ide1=f"file={cfg.ide1},media=cdrom,size={cfg.size_ide1}",
                                     ide0=f"file={cfg.ide2},media=cdrom,size={cfg.size_ide2}",
                                     scsi0=f"{cfg.node_storage_name}:vm-{vmid}-disk-0,size={cfg.vm_disk_size}G",
                                     net0=f"model=virtio,bridge={cfg.brigde},firewall={cfg.firewall}")
            logging.info(f"Configurated machine: {response}")
        else:
            logging.warning(f"Machine {node}.{vmid} does not exists")

    def create(self, **vm):
        node = vm.get("node")
        vmid = vm.get("vmid")
        cfg = Config(config_path)
        cfg.update_from_args(vm)
        self._create_storage(cfg, node, vmid)
        if not self._is_vm_exists(node, vmid):
            response = self.proxmox.nodes(node).qemu.post(
                # options
                vmid=vmid,
                name=cfg.name,
                acpi=1,
                autostart=1,
                ostype=cfg.ostype,
                boot="order=scsi0;ide0;ide1;net0",
                tablet=1,
                hotplug="disk,network,usb",
                freeze=0,
                localtime=1,
                agent=1,
                protection=0,
                vmstatestorage="automatic",
                #  hardware
                memory=cfg.ram,
                cores=cfg.cores,
                sockets=cfg.sockets,
                ide0=f"file={cfg.ide2},media=cdrom",
                ide1=f"file={cfg.ide1},media=cdrom",
                scsi0=f"{cfg.node_storage_name}:vm-{vmid}-disk-0,size={cfg.vm_disk_size}G",
                net0=f"model=virtio,bridge={cfg.brigde},firewall={cfg.firewall}",
                scsihw="virtio-scsi-pci")
            logging.info(f"Created machine: {response}")
        else:
            logging.warning(f"Machine {node}.{vmid} is already exists")

    def clone(self, **vm):
        node = vm.get("node")
        vmid = vm.get("vmid")
        startid = valid(vm.get("startid"), 100)
        newid = self._get_new_id(startid)
        clonename = valid(vm.get("clonename"), f"clone-{newid}")
        qemu = self.proxmox.nodes(node).qemu(vmid)
        response = qemu.clone.post(node=node,
                                   vmid=vmid,
                                   newid=newid,
                                   name=clonename,
                                   full=1)
        logging.info(f"Cloned {node}.{vmid} => {node}.{newid}: {response}")

    def delete(self, **vm):
        node = vm.get("node")
        vmid = vm.get("vmid")
        response = self.proxmox.nodes(node).qemu(vmid).status.get("current")
        if response['status'] != "stopped":
            logging.info(f"Terminating: {node}.{vmid}")
            response = self.proxmox.nodes(node).qemu(vmid).status.post("stop")
            logging.info(f"Terminated: {response}")

        self._wait_termination(node, vmid, 15)
        response = self.proxmox.nodes(node).qemu(vmid).delete()
        logging.info(f"Deleted: {response}")

    def start(self, **vm):
        node = vm.get("node")
        vmid = vm.get("vmid")
        response = self.proxmox.nodes(node).qemu(vmid).status.get("current")
        if response['status'] == "stopped":
            response = self.proxmox.nodes(node).qemu(
                vmid).status.post("start")
            logging.info(f"Started machine: {response}")
        else:
            logging.warning(f"Machine is already started: {response}")

    def stop(self, **vm):
        node = vm.get("node")
        vmid = vm.get("vmid")
        response = self.proxmox.nodes(node).qemu(vmid).status.get("current")
        if response['status'] != "stopped":
            response = self.proxmox.nodes(node).qemu(
                vmid).status.post("stop")
            logging.info(f"Stopped machine: {response}")
        else:
            logging.warning(f"Machine is already stopped: {response}")

    def reboot(self, **vm):
        node = vm.get("node")
        vmid = vm.get("vmid")
        response = self.proxmox.nodes(node).qemu(vmid).status.post("reset")
        logging.info(f"Reboot machine: {response}")

    def rebuild(self, **vm):
        node = vm.get("node")
        vmid = vm.get("vmid")
        self.delete(node=node, vmid=vmid)
        time.sleep(2)
        self.create(node=node, vmid=vmid)

    def status(self, **vm):
        node = vm.get("node")
        vmid = vm.get("vmid")
        if vmid == "all":
            ids = self._get_node_vm_list(node)
            for id in ids:
                self._print_vm_status(node, id)
        else:
            self._print_vm_status(node, vmid)

    def _print_vm_status(self, node, vmid):
        response = self.proxmox.nodes(node).qemu(vmid).status.get("current")
        uptime = datetime.fromtimestamp(
            int(response['uptime'])) - datetime.fromtimestamp(0)
        status = f"{response['status']} LOCKED" if response.get(
            'lock') else response['status']
        print(f" VM id:\t\t\t{response['vmid']}\n",
              f"QEMU process status:\t{status}\n",
              f"VM name:\t\t{response['name']}\n",
              f"Uptime:\t\t{uptime}\n",
              f"Maximum usable CPUs:\t{response['cpus']}\n",
              f"Memory, MB:\t\t{int(response['mem']) / 1024 / 1024}\n",
              f"Maximum memory, MB:\t{int(response['maxmem']) / 1024 / 1024}\n",
              f"Root disk size, MB:\t{int(response['maxdisk']) / 1024 / 1024}\n")

    def _is_vm_exists(self, node, vmid) -> bool:
        response = self.proxmox.nodes(node).qemu.get()
        for mv in response:
            if mv['vmid'] == vmid:
                return True
        return False

    def _create_storage(self, cfg: Config, node, vmid):
        new_disk_name: str = f"vm-{vmid}-disk-0"
        if self._is_disk_exists(cfg, new_disk_name, node):
            return

        storage = self.proxmox.nodes(node).storage(cfg.node_storage_name)

        response = storage.content.post(filename=f"vm-{vmid}-disk-0",
                                        node=node,
                                        size=f"{cfg.vm_disk_size}G",
                                        storage=cfg.node_storage_name,
                                        vmid=vmid)
        logging.info(f"Created disk: {new_disk_name}. {response}")

    def delete_storage(self, cfg: Config, node, vmid):
        disk_name: str = f"vm-{vmid}-disk-0"
        if self._is_disk_exists(cfg, disk_name, node):
            storage = self.proxmox.nodes(node).storage(cfg.node_storage_name)
            response = storage.content(disk_name).delete(node=node,
                                                         volume=vmid)
            logging.info(f"Deleted disk: {disk_name}. {response}")

    def _is_disk_exists(self, cfg: Config, new_disk_name, node) -> bool:
        disks: list = self.proxmox.nodes(node).storage(
            cfg.node_storage_name).get("content")

        disks = list(map(lambda name: name['volid'].strip(
            f"{cfg.node_storage_name}:"), disks))

        return len(list(filter(lambda name: name == new_disk_name, disks))) > 0

    def _wait_termination(self, node: str, vmid: str, timeout: int):
        response = self.proxmox.nodes(node).qemu(vmid).status.get("current")
        while response['status'] != "stopped" and timeout:
            timeout -= 1
            time.sleep(1)
            response = self.proxmox.nodes(node).qemu(
                vmid).status.get("current")

    def _get_new_id(self, start):
        nodes = self.proxmox.get("nodes")
        ids: list = self._get_all_vm_list(nodes)
        while start in ids:
            start += 1
        return start

    def _get_all_vm_list(self, nodes) -> list:
        ids: list = []
        for node in nodes:
            ids += self._get_node_vm_list(node['node'])
        return ids

    def _get_node_vm_list(self, node) -> list:
        ids: list = []
        qemus = self.proxmox.nodes(node).qemu.get()
        for qemu in qemus:
            ids.append(qemu['vmid'])
        return ids
