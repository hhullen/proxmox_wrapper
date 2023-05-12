#!/bin/bash

if [[ -n "$1" ]]; then
  sed -i "s/`hostname`/$1/g" /etc/hosts
  systemctl set-hostname $1
fi
