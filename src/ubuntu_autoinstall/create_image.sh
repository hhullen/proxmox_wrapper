#!/bin/bash

sudo apt install cloud-image-utils
rm -rf ubuntu_autounstall.iso
cloud-localds ubuntu_autounstall.iso user-data meta-data
