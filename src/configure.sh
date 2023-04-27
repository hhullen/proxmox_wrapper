#!/bin/bash

#  install missimg packages
pip3 freeze > .liblist
for lib in $(cat requirements.txt)
do
    installed=`cat .liblist | grep $lib`
    if [[ -z $installed ]]; then
        pip3 install $lib
    fi
done
rm .liblist

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

#  put config to permanent place
if ! [[ -d "/home/$USER/.proxapi" ]]; then
    mkdir -p /home/$USER/.proxapi
fi
cp configuration/vmsetup.cfg /home/$USER/.proxapi/vmsetup.cfg
echo "VM Configuration file: /home/$USER/.proxapi/vmsetup.cfg"
