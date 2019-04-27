#!/bin/bash

# minecraft server 1.14 download link:
# change this link to install a different package
SERVER_URL=https://launcher.mojang.com/v1/objects/f1a0073671057f01aa843443fef34330281333ce/server.jar

# need to do this otherwise supervisor won't install properly
# see https://github.com/hashicorp/terraform/issues/1025
until [[ -f /var/lib/cloud/instance/boot-finished ]]; do
  sleep 1
done

sudo add-apt-repository universe

sudo apt update

sudo apt upgrade

sudo apt -y install openjdk-8-jre-headless supervisor

sudo apt clean

curl -o /home/ubuntu/server.jar "$SERVER_URL"

echo "eula=true" > /home/ubuntu/eula.txt

# symlink world to EBS volume
echo '/dev/xvdf1 /home/ubuntu/world btrfs noatime,defaults 0 0' >> /etc/fstab
mkdir /home/ubuntu/world

# move the supervisor conf file that packer previously uploaded to the right
# place, since the packer file provisioner doesn't have permissions to do it
sudo cp /home/ubuntu/mc-supervisor.conf /etc/supervisor/conf.d/

chmod +x /home/ubuntu/launch_minecraft.sh
