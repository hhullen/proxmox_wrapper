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
This creates `ubuntu_autounstall.iso` from those two files.
> The image need to be added as optical drive beside installation image and their order does not matter.
  
# Customized original image


# Links
- [LiveCDCustomization](https://help.ubuntu.com/community/LiveCDCustomization)
- [How to customize the Ubuntu Live CD?](https://askubuntu.com/questions/48535/how-to-customize-the-ubuntu-live-cd)
- [Automated Server installation](https://ubuntu.com/server/docs/install/autoinstall)
- [Automated Server install quickstart](https://ubuntu.com/server/docs/install/autoinstall-quickstart)
- [Automated Server installer config file reference](ttps://ubuntu.com/server/docs/install/autoinstall-reference)
