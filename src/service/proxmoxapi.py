from configuration import ubuntu_autoinstall_config, network_settings, snippets_dir
from configuration import Config, config_dir, valid, errlog, infolog, warnlog
from .proxmoxssh import ProxmoxSSHClient
from datetime import datetime
import time
import yaml
import re


class ProxmoxAPI:
    def __init__(self, host: str, user: str) -> None:
        self.client = ProxmoxSSHClient(host=host,
                                       user=user)

    def get(self, **vm):
        node = vm.get("node")
        info_type = vm.get("vmid")
        if info_type == "id-list":
            vm_list = self._get_node_vm_list(node)
            print(f"VM list on {node}:")
            for item in vm_list:
                print(item)
        else:
            raise BaseException(f"unknown type {info_type}")

    def configurate(self, **vm):
        node, vmid = vm.get("node"), vm.get("vmid")
        cfg = Config(f"{config_dir}/vmsetup.cfg")
        cfg.update_from_args(vm)

        ide0 = f"--ide0 file={cfg.ide1},media=cdrom" if cfg.ide1 else ""
        ide1 = f"--ide1 file={cfg.ide2},media=cdrom" if cfg.ide2 else ""

        if self._is_vm_exists(node, vmid):
            self.client.post(f"/nodes/{node}/qemu/{vmid}/config "
                             f"--name {cfg.name} "
                             f"--ostype {cfg.ostype} "
                             f"--memory {cfg.ram} "
                             f"--cores {cfg.cores} "
                             f"--sockets {cfg.sockets} "
                             f"{ide0} "
                             f"{ide1} "
                             f"--scsi0 {cfg.node_storage_name}:vm-{vmid}-disk-0,size={cfg.vm_disk_size}G "
                             f"--net0 model=virtio,bridge={cfg.brigde},firewall={cfg.firewall} "
                             f"--scsi0 file=local-lvm:cloudinit "
                             f"--cicustom user=snippets:snippets/user-data-{vmid} ")
        else:
            errlog.error(f"Machine {node}.{vmid} does not exists")

    def create(self, **vm):
        node, vmid = vm.get("node"), vm.get("vmid")
        if vmid == "auto":
            start_id = valid(vm.get("startid"), 200)
            vmid = self._get_new_id(start_id)
        cfg = Config(f"{config_dir}/vmsetup.cfg")
        cfg.update_from_args(vm)
        self._create_disk(cfg, node, vmid)

        ide0 = f"--ide0 file={cfg.ide1},media=cdrom" if cfg.ide1 else ""
        ide1 = f"--ide1 file={cfg.ide2},media=cdrom" if cfg.ide2 else ""

        if not self._is_vm_exists(node, vmid):
            self._add_user_data(cfg.name, vmid, cfg.network)
            self.client.post(f"/nodes/{node}/qemu "
                             f"--vmid {vmid} "
                             f"--name {cfg.name} "
                             f"--acpi 1 "
                             f"--autostart 1 "
                             f"--ostype {cfg.ostype} "
                             f"--boot order=\"sata0;scsi0;ide0;net0\" "
                             f"--tablet 1 "
                             f"--hotplug disk,network,usb "
                             f"--freeze 0 "
                             f"--localtime 1 "
                             f"--agent 1 "
                             f"--protection 0 "
                             f"--vmstatestorage automatic "
                             f"--memory {cfg.ram} "
                             f"--cores {cfg.cores} "
                             f"--sockets {cfg.sockets} "
                             f"{ide0} "
                             f"{ide1} "
                             f"--sata0 file={cfg.node_storage_name}:vm-{vmid}-disk-0,size={cfg.vm_disk_size}G "
                             f"--net0 model=virtio,bridge={cfg.brigde},firewall={cfg.firewall} "
                             f"--scsi0 file=local-lvm:cloudinit "
                             f"--cicustom user=snippets:snippets/user-data-{vmid} "
                             f"--scsihw virtio-scsi-pci")
        else:
            errlog.error(f"Machine {node}.{vmid} already exists")

    def clone(self, **vm):
        node, vmid = vm.get("node"), vm.get("vmid")
        startid = valid(vm.get("startid"), 200)
        newid = self._get_new_id(startid)
        clonename = valid(vm.get("vmname"), f"clone-{newid}")
        self.client.post(f"/nodes/{node}/qemu/{vmid}/clone "
                         f"--newid {newid} "
                         f"--name {clonename} "
                         f"--full 1")

    def delete(self, **vm):
        node, vmid = vm.get("node"), vm.get("vmid")
        response = self._get_current_status(node, vmid)
        if response['status'] != "stopped":
            infolog.info(f"Terminating: {node}.{vmid}")
            response = self.client.post(
                f"/nodes/{node}/qemu/{vmid}/status/stop")
            infolog.info(f"Terminated: {response}")

        self._wait_termination(node, vmid, 15)
        response = self.client.delete(f"/nodes/{node}/qemu/{vmid}")

    def start(self, **vm):
        node, vmid = vm.get("node"), vm.get("vmid")
        response = self._get_current_status(node, vmid)
        if response['status'] == "stopped":
            self.client.post(f"/nodes/{node}/qemu/{vmid}/status/start")
        else:
            errlog.error(f"Machine is already started!")

    def stop(self, **vm):
        node, vmid = vm.get("node"), vm.get("vmid")
        response = self._get_current_status(node, vmid)
        if response['status'] != "stopped":
            response = self.client.post(
                f"/nodes/{node}/qemu/{vmid}/status/stop")
            infolog.info(response)
        else:
            errlog.error(f"Machine is not running!")

    def reboot(self, **vm):
        node, vmid = vm.get("node"), vm.get("vmid")
        response = self.client.post(
            f"/nodes/{node}/qemu/{vmid}/status/reset")
        infolog.info(f"Reboot machine: {response}")

    def rebuild(self, **vm):
        node, vmid = vm.get("node"), vm.get("vmid")
        self.delete(node=node, vmid=vmid)
        time.sleep(2)
        self.create(node=node, vmid=vmid)

    def status(self, **vm):
        node, vmid = vm.get("node"), vm.get("vmid")
        if vmid == "all":
            ids = self._get_node_vm_list(node)
            for id in ids:
                self._print_vm_status(node, id)
        else:
            self._print_vm_status(node, vmid)

    def _print_vm_status(self, node, vmid):
        response = self._get_current_status(node, vmid)
        uptime = datetime.fromtimestamp(
            int(response['uptime'])) - datetime.fromtimestamp(0)
        status = f"{response['status']} LOCKED" if response.get(
            'lock') else response['status']
        print(f"VM id:\t\t\t{response['vmid']}",
              f"QEMU process status:\t{status}",
              f"VM name:\t\t{response['name']}",
              f"Uptime:\t\t\t{uptime}",
              f"Maximum usable CPUs:\t{response['cpus']}",
              f"Memory, MB:\t\t{int(response['mem']) / 1024 / 1024}",
              f"Maximum memory, MB:\t{int(response['maxmem']) / 1024 / 1024}",
              f"Root disk size, MB:\t{int(response['maxdisk']) / 1024 / 1024}\n", sep='\n')
        try:
            response = self.client.get(
                f"nodes/{node}/qemu/{vmid}/agent/network-get-interfaces")
            print("QEMU guest agent config:")
            for item in valid(response.get('result'), []):
                print(f"Name:\t{valid(item.get('name'), None)}")
                print(f"Mac:\t{valid(item.get('hardware-address'), None)}")
                for addr in valid(item.get('ip-addresses'), []):
                    print(f"\t{valid(addr.get('ip-address-type'), None)}:"
                          f"\t{valid(addr.get('ip-address'), None)}/"
                          f"{valid(addr.get('prefix'), None)}")
            print()
        except:
            warnlog.warning(
                f"No QEMU guest agent configured on {node}.{vmid}\n")

    def _is_vm_exists(self, node, vmid) -> bool:
        response = self.client.get(f"/nodes/{node}/qemu")
        for vm in response:
            if vm['vmid'] == int(vmid):
                return True
        return False

    def _create_disk(self, cfg: Config, node, vmid):
        new_disk_name: str = f"vm-{vmid}-disk-0"
        if not self._is_vm_exists(node, vmid):
            self._delete_disk(cfg, node, vmid)
            self.client.post(f"/nodes/{node}/storage/{cfg.node_storage_name}/content "
                             f"--filename {new_disk_name} "
                             f"--size {cfg.vm_disk_size}G "
                             f"--vmid {vmid}")

    def _delete_disk(self, cfg: Config, node, vmid):
        disk_name: str = f"vm-{vmid}-disk-0"
        cloud_init_disk: str = f"vm-{vmid}-cloudinit"
        if self._is_disk_exists(cfg, disk_name, node):
            self.client.delete(
                f"/nodes/{node}/storage/{cfg.node_storage_name}/content/{disk_name}")
            self.client.delete(
                f"/nodes/{node}/storage/{cfg.node_storage_name}/content/{cloud_init_disk}")

    def _is_disk_exists(self, cfg: Config, new_disk_name, node) -> bool:
        disks: list = self.client.get(
            f"/nodes/{node}/storage/{cfg.node_storage_name}/content")

        disks = list(map(lambda name: name['volid'].strip(
            f"{cfg.node_storage_name}:"), disks))

        return len(list(filter(lambda name: f"vm-{name}" == new_disk_name, disks))) > 0

    def _wait_termination(self, node: str, vmid: str, timeout: int):
        response = self._get_current_status(node, vmid)
        while response['status'] != "stopped" and timeout:
            timeout -= 1
            time.sleep(1)
            response = self._get_current_status(node, vmid)

    def _get_new_id(self, start):
        nodes = self.client.get("/nodes")
        ids: list = self._get_all_vm_list(nodes)
        while start in ids:
            start += 1
        return start

    def _get_all_vm_list(self, nodes) -> list:
        ids: list = []
        for node in nodes:
            if node['status'] == "online":
                ids += self._get_node_vm_list(node['node'])
        return ids

    def _get_node_vm_list(self, node) -> list:
        ids: list = []
        qemus = self.client.get(f"/nodes/{node}/qemu")
        for qemu in qemus:
            ids.append(qemu['vmid'])
        return ids

    def _get_free_ip_bytes(self, network) -> list:
        ip_address = self.client.execute(
            f"ip_seeker {network} --binded ~/binded.ip --reverse true")
        if not re.findall("[0-9]{0,3}\.[0-9]{0,3}\.[0-9]{0,3}\.[0-9]{0,3}", ip_address):
            raise BaseException(
                f"IP address have not been got correctly in network {network}")
        return ip_address.split('.')

    def _add_user_data(self, vmname, vmid, network):
        autoinstall = ubuntu_autoinstall_config["autoinstall"]
        autoinstall["identity"]["hostname"] = vmname
        if network:
            byte = self._get_free_ip_bytes(network)
            iface = network_settings["network"]["ethernets"]["ens18"]
            iface["addresses"] = [
                f"{byte[0]}.{byte[1]}.{byte[2]}.{byte[3]}/24"]
            iface["gateway4"] = f"{byte[0]}.{byte[1]}.{byte[2]}.1"
            iface["nameservers"]["addresses"][0] = f"{byte[0]}.{byte[1]}.{byte[2]}.1"
            autoinstall["network"] = network_settings

        user_data_string = yaml.dump(
            ubuntu_autoinstall_config, sort_keys=False)
        self.client.execute(
            f"echo -e '#cloud-config\n{user_data_string}' > {snippets_dir}/user-data-{vmid}")

    def _get_current_status(self, node, vmid):
        return self.client.get(f"/nodes/{node}/qemu/{vmid}/status/current")
