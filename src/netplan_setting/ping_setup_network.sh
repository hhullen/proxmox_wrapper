#!/bin/bash


mask=24
ip="10.10.15.0"
config=/etc/netplan/00-installer-config.yaml

if [[ -n $1 ]]; then
  ip=$1
fi
if [[ -n $2 ]]; then
  mask=$2
fi

p1=`echo $ip | grep -o "^[0-9]*"`
p2=`echo $ip | grep -o "^[0-9]*\.[0-9]*" | grep -o "[0-9]*$"`

p3=`echo $ip | grep -o "[0-9]*\.[0-9]*$" | grep -o "^[0-9]*"`
p4=`echo $ip | grep -o "[0-9]*$"`


function set_address() {
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


for (( i = 254; i > 250; i-- )) {
  resp_curr=`ping $p1.$p2.$p3.$i -c 3 | grep -o Unreachable`
  resp_next=`ping $p1.$p2.$p3.$(($i - 1)) -c 3 | grep -o Unreachable`
  if [[ -n $resp_curr && -n $resp_next ]]; then
    cp $config "backup-$config"
    set_address "$p1" "$p2" "$p3" "$i" "$mask" >> $config
    netplan apply
    echo "Set free address: $p1.$p2.$p3.$i;"
    exit 0
  fi
}

echo "Cannot find free address" >&2
exit 1
