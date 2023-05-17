# IP Seeker

## Run command from `src/ip_seeker` directory
```
make install
```
The command will build executable file to `src/ip_seeker/dist` directory. As alternate, just `ip_seeker.py` file can be used. 

## Copy executable to Proxmox node
The executable file must be placed in any directory included to `PATH` environment variable to call it from any place in system and through ssh connection.

## Exclude ip from searching
In case any IP can be free but must not to be searched, the `binded.ip` file has to be created at home directory of user on behalf of which ssh connection is established. Excluded IPs goes one after one each on new line. For example:
```
10.10.11.21
10.10.11.22
10.10.11.23
10.10.11.253
```

[Back to main README.md](../../README.md#install-ip-seeker)
