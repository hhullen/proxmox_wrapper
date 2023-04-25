#!/bin/bash

pip3 freeze > .liblist
for lib in $(cat requirements.txt)
do
    installed=`cat .liblist | grep $lib`
    if [[ -z $installed ]]; then
        pip3 install $lib
    fi
done
rm .liblist

is_alias=`grep proxapi ~/.bashrc`
if [[ -z $is_alias ]]; then
    echo "alias proxapi='python3 `pwd`/main.py'" >> ~/.bashrc
    alias proxapi='python3 `pwd`/main.py'
    echo "alias proxapi added to ~/.bashrc"
fi

is_alias=`grep proxapi ~/.zshrc`
if [[ -z $is_alias ]]; then
    echo "alias proxapi='python3 `pwd`/main.py'" >> ~/.zshrc
    alias proxapi='python3 `pwd`/main.py'
    echo "alias proxapi added to ~/.zshrc"
fi