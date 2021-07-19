#!/bin/bash

echo $(date -u) Initiating server...

# is there a better way to tell what the second EBS volume's device name is?
# TODO: maybe we can know the EBS volume ID and filter by SERIAL
DEVICE_NAME=`lsblk -o KNAME,MOUNTPOINT | grep -v loop | grep -v / | tail -n1 | awk '{$1=$1};1'`
while [[ -z "$DEVICE_NAME" ]]; do
    sleep 5
    echo $(date -u) "Looking for BTRFS device"
    DEVICE_NAME=`lsblk -o KNAME,MOUNTPOINT | grep -v loop | grep -v / | tail -n1 | awk '{$1=$1};1'`
done

echo $(date -u) "Mounting BTRFS volume"
sudo mount /dev/"$DEVICE_NAME" /home/ubuntu/world -o defaults,noatime

ln -s /home/ubuntu/world/ops.json /home/ubuntu/ops.json

sudo chown ubuntu /home/ubuntu/world

/home/ubuntu/watchdog/bin/python /home/ubuntu/server_wrapper.py
