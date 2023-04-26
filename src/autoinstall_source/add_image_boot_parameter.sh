#!/bin/bash


if [[ $USER != "root" ]]; then
    echo "Root permission necessary"
    exit 1
fi

name=`echo $1 | grep -o "\w[^/]*$" | sed 's/\.iso//'`

echo $name

if [[ -z $1 ]]; then
    echo "Path to ISO image required as argument"
    exit 1
fi

mkdir -p /mnt/temp_iso 
mkdir -p /tmp/temp_iso

echo "Mount imgae..."
mount -o loop $1 /mnt/temp_iso

echo "Copying image content to /tmp/temp_iso"
cp -R /mnt/* /tmp/temp_iso

chmod a+wr /tmp/temp_iso/boot/grub/grub.cfg
echo "It is possible to change file: /tmp/temp_iso/boot/grub/grub.cfg. When changes are done, press enter"
read

echo "Writing new imgae..."
genisoimage -V boot_ubuntu -r -o /tmp/$name-autoinstall.iso /tmp/temp_iso
# mkisofs -r -iso-level 4 -b boot/memtest86+.bin -c boot.catalog -no-emul-boot -boot-load-size 4 -boot-info-table -o ubuntu.iso TEMP/temp_iso/


xorriso -outdev ubuntu-autoinstall.iso -map extracted / -- -volid 'Ubuntu-Server 22.04.2 LTS amd64' \
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


echo Image done: /tmp/$name-autoinstall.iso

umount /mnt/temp_iso
rm -rf /mnt/temp_iso