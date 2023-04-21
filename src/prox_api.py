from proxmoxer import ProxmoxAPI
import urllib3
import os
import uuid


PASSWORD = os.environ['PROX_PASS']
HOST = "10.10.31.11"
USER = "root@pam"


urllib3.disable_warnings()
proxmox = ProxmoxAPI(host=HOST,
                     user=USER,
                     password=PASSWORD,
                     verify_ssl=False)


# response = proxmox.get_tokens()[0]
# response = proxmox.get("/api2/json/cluster")
# response = proxmox.get("/api2/json/cluster/config/nodes")
response = proxmox.get("/api2/json/nodes/pve2/qemu/102")


node = proxmox.nodes("pve2")

storage = node.storage('StorageLocal2').

# node.qemu.post(
#     # options
#     vmid=200,
#     acpi=1,
#     autostart=1,
#     ostype="l26",
#     boot="order=scsi0;ide2;net0",
#     tablet=1,
#     hotplug="disk,network,usb",
#     kvm=1,
#     freeze=0,
#     localtime=1,
#     smbios1="uuid=" + str(uuid.uuid4()),
#     agent=0,
#     protection=0,
#     spice_enhancements="videostreaming=off,foldersharing=0",
#     vmstatestorage="automatic",
#     #  hardware
#     memory=4096,
#     cores=2,
#     sockets=2,
#     bios="seabios",
#     machine="pc-i440fx-0.0",
#     scsihw="virtio-scsi-pci",
#     ide2="file=local:iso/ubuntu-20.04.4-live-server-amd64.iso,size=1270M",
#     scsi0="StorageLocal2:vm-200-disk-0,size=32G",
#     net0="model=virtio,bridge=vmbr0,firewall=1")


for it in node.qemu.get():
    for i in it:
        print(i, it[i])
    print()


for node in proxmox.nodes.get():
    for vm in proxmox.nodes(node["node"]).qemu.get():
        print(
            f"Node: {node['node']} \t ID: {vm['vmid']} \t Name: {vm['name']} => {vm['status']}")
