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

java -Xms1024M -Xmx2536M -jar /home/ubuntu/server.jar
