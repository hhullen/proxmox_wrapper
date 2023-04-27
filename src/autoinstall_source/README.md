# Introduction
To make Linux Ubuntu install fully automated without any user participation two main things required:
1. Image with installation configuration. Let to give answers beforehand for all questions that are asked by installator (for instance username, password, is it requred to install ssh server etc.) in yaml format file.
2. Customized original image. Just original image from ubuntu.com, but to possess the ability to installation with no touching a keyboard it is necessary to edit kernel command line options.  

# Image with installation configuration
To create the image required two files: `meta-data` and `user-data`. Leave the `meta-data` empty. File `user-data` has to contain installation configuration. Here is a simple configuration, that covers all interactive installation parts:
```
#cloud-config
autoinstall:
  version: 1
  locale: en_US.UTF-8
  identity:
    hostname: ubuntu-host
    password: some_password
    username: ubuntu
  refresh-installer:
    update: no
  storage:
    layout:
      name: lvm
  ssh:
    install-server: false
  late-commands:
    - curtin in-target --target=/target -- sudo apt update && sudo apt upgrade
```
Learn more about command lists at [Automated Server installer config file reference](ttps://ubuntu.com/server/docs/install/autoinstall-reference)

To create required image use command:
```
cloud-localds ubuntu_autounstall.iso user-data meta-data
```
Or
```
bash create_image.sh
```
This creates `ubuntu_autounstall.iso` from those two files.
> The image need to be added as optical drive beside installation image and their order does not matter.

# Customized original image
All is needed to get the target is `autoinstall` parameter added to kernel command line when installer booted.
First-thing-first download ubuntu image.
Create work folders:
```
mkdir custom_img
mv ~/Download/ubuntu-22.04.2-live-server-amd64.iso custom_img
cd custom_img
```
Mount image:
```
mkdir isoimage
sudo mount -o loop ubuntu-22.04.2-live-server-amd64.iso isoimage
```
Extract mounted image content:
```
mkdir extracted
sudo rsync -a isomount/ extracted/
```
Edit boot command in file of Grub. This commant run at first:
```
chmod u+w extracted/boot/grub/grub.cfg 
vim extracted/boot/grub/grub.cfg
```
Here, is where `autoinstall` option has to be added:
```
...

menuentry "Try or Install Ubuntu Server" {
        set gfxpayload=keep
        linux   /casper/vmlinuz  autoinstall
        initrd  /casper/initrd
}
...
```
Also, at this file, timeout can be edited (30 seconds by default):
```
set timeout=1
```
Return file permission back:
```
chmod u-w extracted/boot/grub/grub.cfg 
```
Get information from image including the offset and size of the EFI partition:
```
fdisk -l ubuntu-22.04.2-live-server-amd64.iso
```
The command outpu will be like:
```
Device                                  Start     End Sectors  Size Type
ubuntu-22.04.2-live-server-amd64.iso1      64 3848587 3848524  1.8G Microsoft
ubuntu-22.04.2-live-server-amd64.iso2 3848588 3858655   10068  4.9M EFI Syste
ubuntu-22.04.2-live-server-amd64.iso3 3858656 3859255     600  300K Microsoft
```
Create mbr.img image (takes 446 bytes by default):
```
sudo dd bs=1 count=446 if=ubuntu-22.04.2-live-server-amd64.iso of=mbr.img
```
Create EFI.img - the second device from the list (count = sectors, skip = its start):
```
sudo dd bs=512 count=10068 skip=3848588 if=ubuntu-22.04.2-live-server-amd64.iso of=EFI.img
```
Get necessary original base image information to create new one customized being bootable:
```
sudo xorriso -indev ubuntu-22.04.2-live-server-amd64.iso -report_el_torito cmd
```
This command output something like:
```
xorriso 1.5.4 : RockRidge filesystem manipulator, libburnia project.

xorriso : NOTE : Loading ISO image tree from LBA 0
xorriso : UPDATE :     824 nodes read in 1 seconds
libisofs: NOTE : Found hidden El-Torito image for EFI.
libisofs: NOTE : EFI image start and size: 962147 * 2048 , 10068 * 512
xorriso : NOTE : Detected El-Torito boot information which currently is set to be discarded
Drive current: -indev 'ubuntu-22.04.2-live-server-amd64.iso'
Media current: stdio file, overwriteable
Media status : is written , is appendable
Boot record  : El Torito , MBR protective-msdos-label grub2-mbr cyl-align-off GPT
Media summary: 1 session, 964830 data blocks, 1884m data, 35.4g free
Volume id    : 'Ubuntu-Server 22.04.2 LTS amd64'
-volid 'Ubuntu-Server 22.04.2 LTS amd64'
-volume_date uuid '2023021721571500'
-boot_image grub grub2_mbr=--interval:imported_iso:0s-15s:zero_mbrpt,zero_gpt:'ubuntu-22.04.2-live-server-amd64.iso'
-boot_image any partition_table=on
-boot_image any partition_cyl_align=off
-boot_image any partition_offset=16
-boot_image any mbr_force_bootable=on
-append_partition 2 28732ac11ff8d211ba4b00a0c93ec93b --interval:imported_iso:3848588d-3858655d::'ubuntu-22.04.2-live-server-amd64.iso'
-boot_image any appended_part_as=gpt
-boot_image any iso_mbr_part_type=a2a0d0ebe5b9334487c068b6b72699c7
-boot_image any cat_path='/boot.catalog'
-boot_image grub bin_path='/boot/grub/i386-pc/eltorito.img'
-boot_image any platform_id=0x00
-boot_image any emul_type=no_emulation
-boot_image any load_size=2048
-boot_image any boot_info_table=on
-boot_image grub grub2_boot_info=on
-boot_image any next
-boot_image any efi_path='--interval:appended_partition_2_start_962147s_size_10068d:all::'
-boot_image any platform_id=0xef
-boot_image any emul_type=no_emulation
-boot_image any load_size=5154816
```
All is needed are flags from -volid and so on. Then assemble iso image by `xorriso` adding `mrb.img` and `EFI.img` instead of defaulst:
```
xorriso -outdev ubuntu-autoinstall.iso -map extracted / -- \
-volid 'Ubuntu-Server 22.04.2 LTS amd64' \
-volume_date uuid '2023021721571500' \
-boot_image grub grub2_mbr=mbr.img \
-boot_image any partition_table=on \
-boot_image any partition_cyl_align=off \
-boot_image any partition_offset=16 \
-boot_image any mbr_force_bootable=on \
-append_partition 2 28732ac11ff8d211ba4b00a0c93ec93b EFI.img \ 
-boot_image any appended_part_as=gpt \
-boot_image any iso_mbr_part_type=a2a0d0ebe5b9334487c068b6b72699c7 \
-boot_image any cat_path='/boot.catalog' \
-boot_image grub bin_path='/boot/grub/i386-pc/eltorito.img' \
-boot_image any platform_id=0x00 \
-boot_image any emul_type=no_emulation \
-boot_image any load_size=2048 \
-boot_image any boot_info_table=on \
-boot_image grub grub2_boot_info=on \
-boot_image any next \
-boot_image any efi_path='--interval:appended_partition_2_start_962147s_size_10068d:all::' \
-boot_image any platform_id=0xef \
-boot_image any emul_type=no_emulation \
-boot_image any load_size=5154816
```
Outputed `ubuntu-autoinstall.iso` image has kernel command line fix and is bootable.


# Links
- [LiveCDCustomization](https://help.ubuntu.com/community/LiveCDCustomization)
- [How to customize the Ubuntu Live CD?](https://askubuntu.com/questions/48535/how-to-customize-the-ubuntu-live-cd)
- [Automated Server installation](https://ubuntu.com/server/docs/install/autoinstall)
- [Automated Server install quickstart](https://ubuntu.com/server/docs/install/autoinstall-quickstart)
- [Automated Server installer config file reference](ttps://ubuntu.com/server/docs/install/autoinstall-reference)
