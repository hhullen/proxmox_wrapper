from configuration import Config, config_path, valid, errlog, infolog, warnlog
from paramiko import SSHClient, SSHException
from paramiko.channel import ChannelFile, ChannelStderrFile
from datetime import datetime
import json
import time


class ProxmoxSSHClient():
    def __init__(self, host: str, user: str, password: str):
        self.client = SSHClient()
        self.client.load_system_host_keys()
        self.client.connect(hostname=host,
                            username=user,
                            password=password)

    def __del__(self):
        self.client.close()

    def get(self, api_path: str) -> dict | list:
        return self._request(api_path, "get")

    def post(self, api_path: str) -> dict | list:
        return self._request(api_path, "create")

    def put(self, api_path: str) -> dict | list:
        return self._request(api_path, "set")

    def delete(self, api_path: str) -> dict | list:
        return self._request(api_path, "delete")

    def _request(self, api_path: str, method: str) -> dict | list:
        sstdin, stdout, stderr = self.client.exec_command(
            f"pvesh {method} {api_path} --output-format json")
        self._handle_stderr(stderr)
        return self._handle_stdout(stdout)

    def _handle_stderr(self, stderr: ChannelStderrFile):
        stderr: str = stderr.read().decode('utf-8')
        if "WARNING" in stderr:
            self._handle_output(stderr)
        elif stderr:
            raise SSHException(stderr)

    def _handle_stdout(self, stdout: ChannelFile):
        stdout: str = stdout.read().decode("utf-8")
        try:
            return json.loads(stdout)
        except:
            self._handle_output(stdout)
            return stdout

    def _handle_output(self, output: str):
        output = output.strip('\n').split('\n')
        for message in output:
            if "WARNING" in message:
                warnlog.warning(message.strip("WARNING: ").strip(' '))
            else:
                pass
                infolog.info(message.strip(' '))


class ProxmoxAPI:
    def __init__(self, host: str, user: str, password: str) -> None:
        self.client = ProxmoxSSHClient(host=host,
                                       user=user,
                                       password=password)

    def configurate(self, **vm):
        node = vm.get("node")
        vmid = vm.get("vmid")
        cfg = Config(config_path)
        cfg.update_from_args(vm)
        if self._is_vm_exists(node, vmid):
            self.client.post(f"/nodes/{node}/qemu/{vmid}/config "
                             f"--name {cfg.name} "
                             f"--ostype {cfg.ostype} "
                             f"--memory {cfg.ram} "
                             f"--cores {cfg.cores} "
                             f"--sockets {cfg.sockets} "
                             f"--ide1 file={cfg.ide1},media=cdrom,size={cfg.size_ide1} "
                             f"--ide0 file={cfg.ide2},media=cdrom,size={cfg.size_ide2} "
                             f"--scsi0 {cfg.node_storage_name}:vm-{vmid}-disk-0,size={cfg.vm_disk_size}G "
                             f"--net0 model=virtio,bridge={cfg.brigde},firewall={cfg.firewall} ")
        else:
            errlog.error(f"Machine {node}.{vmid} does not exists")

    def create(self, **vm):
        node = vm.get("node")
        vmid = vm.get("vmid")
        if vmid == "auto":
            start_id = valid(vm.get("startid"), 200)
            vmid = self._get_new_id(start_id)
        cfg = Config(config_path)
        cfg.update_from_args(vm)
        self._create_disk(cfg, node, vmid)

        if not self._is_vm_exists(node, vmid):
            self.client.post(f"/nodes/{node}/qemu "
                             f"--vmid {vmid} "
                             f"--name {cfg.name} "
                             f"--acpi 1 "
                             f"--autostart 1 "
                             f"--ostype {cfg.ostype} "
                             f"--boot order=\"sata0;ide0;scsi0;net0\" "
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
                             f"--ide0 file={cfg.ide2},media=cdrom,size={cfg.size_ide2} "
                             f"--sata0 file={cfg.node_storage_name}:vm-{vmid}-disk-0,size={cfg.vm_disk_size}G "
                             f"--net0 model=virtio,bridge={cfg.brigde},firewall={cfg.firewall} "
                             f"--scsi0 file=local-lvm:cloudinit "
                             f"--cicustom user=snippets:snippets/user-data "
                             f"--scsihw virtio-scsi-pci")
        else:
            errlog.error(f"Machine {node}.{vmid} is already exists")

    def clone(self, **vm):
        node = vm.get("node")
        vmid = vm.get("vmid")
        startid = valid(vm.get("startid"), 200)
        newid = self._get_new_id(startid)
        clonename = valid(vm.get("vmname"), f"clone-{newid}")
        response = self.client.post(f"/nodes/{node}/qemu/{vmid}/clone "
                                    f"--newid {newid} "
                                    f"--name {clonename} "
                                    f"--full 1")

    def delete(self, **vm):
        node = vm.get("node")
        vmid = vm.get("vmid")
        response = self.client.get(f"/nodes/{node}/qemu/{vmid}/status/current")
        if response['status'] != "stopped":
            infolog.info(f"Terminating: {node}.{vmid}")
            response = self.client.post(
                f"/nodes/{node}/qemu/{vmid}/status/stop")
            infolog.info(f"Terminated: {response}")

        self._wait_termination(node, vmid, 15)
        response = self.client.delete(f"/nodes/{node}/qemu/{vmid}")

    def start(self, **vm):
        node = vm.get("node")
        vmid = vm.get("vmid")
        response = self.client.get(f"/nodes/{node}/qemu/{vmid}/status/current")
        if response['status'] == "stopped":
            self.client.post(f"/nodes/{node}/qemu/{vmid}/status/start")
        else:
            errlog.error(f"Machine is already started!")

    def stop(self, **vm):
        node = vm.get("node")
        vmid = vm.get("vmid")
        response = self.client.get(f"/nodes/{node}/qemu/{vmid}/status/current")
        if response['status'] != "stopped":
            response = self.client.post(
                f"/nodes/{node}/qemu/{vmid}/status/stop")
            infolog.info(response)
        else:
            errlog.error(f"Machine is not running!")

    def reboot(self, **vm):
        node = vm.get("node")
        vmid = vm.get("vmid")
        response = self.client.post(
            f"/nodes/{node}/qemu/{vmid}/status/reset")
        infolog.info(f"Reboot machine: {response}")

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
        response = self.client.get(f"nodes/{node}/qemu/{vmid}/status/current")
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
        response = self.client.get(f"/nodes/{node}/qemu")
        for vm in response:
            if vm['vmid'] == int(vmid):
                return True
        return False

    def _create_disk(self, cfg: Config, node, vmid):
        new_disk_name: str = f"vm-{vmid}-disk-0"
        self._delete_disk(cfg, node, vmid)
        self.client.post(f"/nodes/{node}/storage/{cfg.node_storage_name}/content "
                         f"--filename {new_disk_name} "
                         f"--size {cfg.vm_disk_size}G "
                         f"--vmid {vmid}")

    def _delete_disk(self, cfg: Config, node, vmid):
        disk_name: str = f"vm-{vmid}-disk-0"
        if self._is_disk_exists(cfg, disk_name, node):
            self.client.delete(
                f"/nodes/{node}/storage/{cfg.node_storage_name}/content/{disk_name}")

    def _is_disk_exists(self, cfg: Config, new_disk_name, node) -> bool:
        disks: list = self.client.get(
            f"/nodes/{node}/storage/{cfg.node_storage_name}/content")

        disks = list(map(lambda name: name['volid'].strip(
            f"{cfg.node_storage_name}:"), disks))

        return len(list(filter(lambda name: f"vm-{name}" == new_disk_name, disks))) > 0

    def _wait_termination(self, node: str, vmid: str, timeout: int):
        response = self.client.get(f"/nodes/{node}/qemu/{vmid}/status/current")
        while response['status'] != "stopped" and timeout:
            timeout -= 1
            time.sleep(1)
            response = self.client.get(
                f"/nodes/{node}/qemu/{vmid}/status/current")

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
