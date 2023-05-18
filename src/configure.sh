#!/bin/bash

if [[ $USER != "root" ]]; then
    echo "Root permissions required to run the script."
    exit 1
fi

#  python and pip installation
apt update && apt full-upgrade && apt install python3 python3-pip

#  install missimg packages
pip3 install -r requirements.txt

#  put config to permanent place
if ! [[ -d "/home/$USER/.proxapi" ]]; then
    mkdir -p /home/$USER/.proxapi
fi
cp configuration/vmsetup.cfg /home/$USER/.proxapi/vmsetup.cfg
echo "VM Configuration file: /home/$USER/.proxapi/vmsetup.cfg"
cp configuration/user-data /home/$USER/.proxapi/user-data
echo "Installation configuration file: /home/$USER/.proxapi/user-data"

#  add alias 'proxapi' to init terminal files
is_alias=`grep proxapi ~/.bashrc`
if [[ -z $is_alias ]]; then
    echo "alias proxapi='python3 `pwd`/main.py'" >> ~/.bashrc
    alias proxapi='python3 `pwd`/main.py'
    echo "alias proxapi added to ~/.bashrc restart terminal required"
fi

is_alias=`grep proxapi ~/.zshrc`
if [[ -z $is_alias ]]; then
    echo "alias proxapi='python3 `pwd`/main.py'" >> ~/.zshrc
    alias proxapi='python3 `pwd`/main.py'
    echo "alias proxapi added to ~/.zshrc restart terminal required"
fi
