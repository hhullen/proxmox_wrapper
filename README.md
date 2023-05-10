# ProxmoxAPI Command Line Interface
Proxmox wrapper on `proxmoxer` Python library. Implements a simple command line interface to manage vitrual machines on Proxmox cluster. `Written predominantly for Linux`.

# Initial setting
> To setup configuration installed `Python3` is required.

### 1.Run command
```
bash configure.sh
```
The script will:
- installs missing python libraries
- adds alias `proxapi` to init terminal files. So, it is necessary to reload terminal to use `proxapi` command.
- creates virtual machine configuration file to `/home/$USER/.proxapi/vmsetup.cfg`. Configure connection parameters and vm parameters in this file.

### 2. Get images
The next two things is needed the `Image with installation configuration` and the `Customized original image`. How to do that described in `README.md` at `aurounstall_source` directoty.

### 3. Upload images
Upload the `Image with installation configuration` and the `Customized original image` to Proxmox cluster node storage.

### 4. Update images location
Update images location in configuration file `/home/$USER/.proxapi/vmsetup.cfg`. Path must be in format: `node_storage_name:image_name.iso`
Place autoinstall config image to `IDE1` and main image to installation to `IDE2` and set their sizes for instance:
```
...
IDE1="local:iso/ubuntu_autounstall.iso"
SIZE_IDE1="364K"
IDE2="local:iso/ubuntu-22.04.2-server-autoinstall.iso"
SIZE_IDE2="1900M"
...
```

# Using
### Command line interface is used with `proxapi` command with three required arguments and some other optional.
- Required arguments
    1. `Action mode` - can take next values:  
        - `create` - creates new one VM with set configuration  
        - `delete` - delete existing VM  
        - `start` - start existing stopped VM  
        - `stop` - stop existing running VM  
        - `reboot` - reboot existing running VM  
        - `config` - configurate existing stopped VM  
        - `status` - print some VM parameters and their state  
        - `clone` - make clone from existing VM  
        - `rebuild` - make delete and create VM  

        all of them requiren next two arguments
    
    2. `Node name` - can take name of existing cluster node

    3. `Machine id `- identifier of VM the action excecutes with. In case `status` command called, it can take value `all` to show information from all node VMs. In case `create` command called, it can take value `auto` to create new vm with any free id.

- Optional arguments - can be specified with defifinite flag:
    1. `--clone-name [name]` - clone name
    2. `--start-id [id]` - set start VM id value which the next free id will be chosen after (to clone or create any vm)
    3. `--vm-name [vm-name]` - name to new created VM
    4. `--ram [ram]` - RAM memory. Specify just a number without units which is MiB by default.
    5. `--sockets [sockets]` - VM sockets amount
    6. `--cores [cores]` - VM cores amount
    7. `--vm-disk-size [vm disk zise]` - VM disk size. Specify just a number without units which is GB by default.
    8. `--node-storage-name [node storage name]` - existing storage name of node for specify where to create new disk for new VM.
    9. `--help`, `-h` - to ges short description

# Some using examples
```
proxapi create pve3 203 --vm-name "test-name-1" --ram 4096 \
--sockets 2 --cores 2 --vm-disk-size 40
```
```
proxapi start pve3 203
```
```
proxapi clone pve3 203 --clone-name "cloned-vm-0" --startid 200
```
```
proxapi stop pve3 203
```
```
proxapi config pve3 203 --vm-disk-size 100 --ram 8192
```
