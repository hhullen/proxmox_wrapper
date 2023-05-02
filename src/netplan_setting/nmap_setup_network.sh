#!/bin/bash

apt-get install nmap -y > /dev/null

mask=24
ip="10.10.31.0"
config=config_path

if [[ -n $1 ]]; then
  ip=$1
fi
if [[ -n $2 ]]; then
  mask=$2
fi

last_ip=`nmap -sP $ip/$mask | grep report | awk '{print $5}' | tail -1`
echo "# Last address: $last_ip"

p1=`echo $last_ip | grep -o "^[0-9]*"`
p2=`echo $last_ip | grep -o "^[0-9]*\.[0-9]*" | grep -o "[0-9]*$"`

p3=`echo $last_ip | grep -o "[0-9]*\.[0-9]*$" | grep -o "^[0-9]*"`
p4=`echo $last_ip | grep -o "[0-9]*$"`

p4=$(($p4 + 1))

if [[ $p4 -gt 254 ]]; then
    echo "Out of range IP: $p1.$p2.$p3.$p4"
    exit 1
fi

echo "# New address: $p1.$p2.$p3.$p4"

function set_addres() {
  echo "network:"
  echo "  ethernets:"
  echo "    ens18:"
  echo "      addresses:"
  echo "      - $1.$2.$3.$4/$5"
  echo "      gateway4: 10.10.15.1"
  echo "      nameservers:"
  echo "        addresses: [10.10.15.1, 8.8.8.8]"
  echo "  version: 2"
  echo "  renderer: networkd"
}

set_addres "$p1" "$p2" "$p3" "$p4" "$mask" > $config
