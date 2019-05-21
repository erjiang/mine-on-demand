#!/bin/bash

# is there a better way to tell what the second EBS volume's device name is?
DEVICE_NAME=`dmesg | grep "BTRFS: device" | tail -1 | grep '/dev/.*$' -o`
while [[ -z "$DEVICE_NAME" ]]; do
    echo "Looking for BTRFS device"
    DEVICE_NAME=`dmesg | grep "BTRFS: device" | tail -1 | grep '/dev/.*$' -o`
    sleep 5
done

echo "Mounting BTRFS volume"
sudo mount "$DEVICE_NAME" /home/ubuntu/world -o defaults,noatime

ln -s /home/ubuntu/world/ops.json /home/ubuntu/ops.json

sudo chown ubuntu /home/ubuntu/world

/home/ubuntu/watchdog/bin/python /home/ubuntu/server_wrapper.py
