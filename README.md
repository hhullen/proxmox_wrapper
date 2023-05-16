# ProxmoxAPI Command Line Interface
Proxmox wrapper on `proxmoxer` Python library. Implements a simple command line interface to manage vitrual machines on Proxmox cluster and allow to run QEMU and install Ubuntu autimatically. `Predominantly for Linux`.

## Contents

- [Installation](#installation)  
    - [Run command from `src` directory](#run-command-from-src-directory)  
    - [Get customized Ubuntu image](#get-customized-ubuntu-image)  
    - [Upload image](#upload-image)
    - [Install IP seeker](#install-ip-seeker)
- [Using](#using)  
    - [Information](#information)  
- [Some using examples](#some-using-examples)


# Installation
> To setup configuration installed `Python3` and `pip3` is required.

## Run command from `src` directory
```
make install
```
This command build executable file `proxapi` and place it into `dist` directory. Move it into any directory the $PATH variable includes to call as any other utilits. Also, creates virtual machine configuration file to `~/.proxapi/vmsetup.cfg` and Ubuntu-autoinstall configuration file `~/.porxapi/user-data`. 

As alternative, do not build executable, but setup work with source code by alias. Run command:
```
bash configure.sh
```
The script will:
- installs missing python libraries
- adds alias `proxapi` to init terminal files. So, it is necessary to reload terminal to use `proxapi` command.
- creates virtual machine configuration file to `~/.proxapi/vmsetup.cfg` and Ubuntu-autoinstall configuration file `~/.porxapi/user-data`.  

### `~/.proxapi/vmsetup.cfg`
``` bash
USER_NAME="root"
PROXMOX_HOST="10.10.11.12"

NAME="qemu-host-name"
OS_TYPE=l26

RAM_MEMORY=2048
SOCKETS=1
CORES=2

IDE1="local:iso/ubuntu_autounstall.iso"
SIZE_IDE1="364K"
IDE2="local:iso/ubuntu-22.04.2-sfxdx-custom.iso"
SIZE_IDE2="1900M"
VM_DISK_SIZE=17
NODE_STORAGE_NAME="VM"

BRIDGE="vmbr100"
FIREWALL=1

```    

### `~/.porxapi/user-data`
``` yaml
#cloud-config
autoinstall:
  version: 1
  identity:
    realname: ubuntu
    password: "$1$OjcU1ha7$uFbuvRnUwvRcme9Xy3n3L1"
    username: ubuntu
  locale: en_US.UTF-8
  refresh-installer:
    update: false
  storage:
    layout:
      name: lvm
  ssh:
    install-server: false
  network:
    network:
      version: 2
      renderer: networkd
      ethernets:
        ens18:
          addresses:
          - 10.10.15.253/24
          gateway4: 10.10.15.1
          nameservers:
            addresses:
            - 10.10.31.1
            - 8.8.8.8
  late-commands:
  - echo "@reboot root /bin/bash /root/autoinit/init_script" > /target/etc/cron.d/autoinit
  - chmod 755 /target/etc/cron.d/autoinit

```
> `$1$OjcU1ha7$uFbuvRnUwvRcme9Xy3n3L1` is a password encrypted by command `openssl passwd "ubuntu"`.  
> Note the password has to be encrypted. Several tools can generate the crypted password, such as mkpasswd from the whois package, or openssl passwd. Depending on the special characters in the password hash, quoting may be required, so it’s safest to just always include the quotes around the hash.
Learn more about command lists at [Automated Server installer config file reference](https://ubuntu.com/server/docs/install/autoinstall-reference).

Set `PROXMOX_HOST` and `USER_NAME` in `~/.proxapi/vmsetup.cfg` to make available ssh connection to Proxmox master node.

## Get customized Ubuntu image
It is necessary to customize original Ubuntu image to use `Ununtu autoinstall` function. Set `autoinstall` option to boot kernel command line is required to start and continue installation without any user interaction. How to customize, described in [README.md](./src/ubuntu_autoinstall/README.md) placed in `src/ubuntu_autoinstall` directory.   

## Upload image
Once the required things done, make sure the image uploaded to Proxmox volume and specified its location on Proxmox to any `ide[n]` in `~/.proxapi/vmsetup.cfg`. 
```
...
IDE0="local:iso/ubuntu-22.04.2-server-custom-autoinstall.iso"
...
```

## Install IP seeker
IP seeker search free ip in specified network and return it to calling programm. It works on Proxmox master node and gives an ability to set ip of VM by command line option. how to install described in [README.md](./src/ip_seeker/README.md) placed in `src/ip_seeker` directory. 

# Using
### Command line interface is used with `proxapi` command with three required arguments and some other optional.
- Required arguments
    1. `Action mode` can take next values:  
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
    
    2. `Node name` can take name of existing cluster node

    3. `Machine id ` identifier of VM the action excecutes with. In case `status` command called, it can take value `all` to show information from all node VMs. In case `create` command called, it can take value `auto` to create new vm with any free id (start searching free id from 200 by default).

- Optional arguments - can be specified with defifinite flag:
    2. `--start-id [id]` - set start VM id value which the next free id will be chosen after (to clone or create any vm)  
    3. `--vm-name [vm-name]` - name to new created VM  
    4. `--ram [ram]` - RAM memory. Specify just a number without units which is MiB by default.  
    5. `--sockets [sockets]` - VM sockets amount  
    6. `--cores [cores]` - VM cores amount  
    7. `--vm-disk-size [vm disk zise]` - VM disk size. Specify just a number without units which is GB by default.  
    8. `--node-storage-name [node storage name]` - existing storage name of node for specify where to create new disk for new VM.  
    9. `--help`, `-h` - to ges short description  
    10. `--network` - to setup qemu guest agent network

>> In case some optional arguments specified they override value took from `~/.proxapi/vmsetup.cfg` and `~/.porxapi/user-data`.

# Some using examples
```
proxapi create pve14 203 --vm-name test-name-1 --ram 4096 \
--sockets 2 --cores 2 --vm-disk-size 40 --network 10.10.11.19/24
```
```
proxapi start pve14 203
```
```
proxapi clone pve14 203 --vm-name cloned-vm-0 --start-id 200
```
```
proxapi stop pve14 203
```
```
proxapi config pve14 203 --vm-disk-size 100 --ram 8192
```
```
proxapi status pve14 all
```
```
proxapi create pve14 auto  --vm-name new-one --network 10.10.11.19/24
```