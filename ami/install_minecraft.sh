#!/bin/bash
#
# This bash script takes a plain Ubuntu AMI and installs the necessary bits to
# run a Minecraft server on it. It also sets up /home/ubuntu/world to be a
# symlink to the Minecraft world files.
#

# minecraft server 1.14.2 JAR
# change this link to install a different package
SERVER_URL=https://launcher.mojang.com/v1/objects/808be3869e2ca6b62378f9f4b33c946621620019/server.jar

# need to do this otherwise supervisor won't install properly
# see https://github.com/hashicorp/terraform/issues/1025
until [[ -f /var/lib/cloud/instance/boot-finished ]]; do
  sleep 1
done

sudo add-apt-repository universe

sudo apt update

sudo apt upgrade

sudo apt -y install openjdk-8-jre-headless supervisor python-virtualenv python-pip

sudo apt clean

curl -o /home/ubuntu/server.jar "$SERVER_URL"

echo "eula=true" > /home/ubuntu/eula.txt

# symlink world to EBS volume
echo '/dev/xvdf1 /home/ubuntu/world btrfs noatime,defaults 0 0' >> /etc/fstab
mkdir /home/ubuntu/world

# move the supervisor conf file that packer previously uploaded to the right
# place, since the packer file provisioner doesn't have permissions to do it
sudo cp /home/ubuntu/mc-supervisor.conf /etc/supervisor/conf.d/
sudo cp /home/ubuntu/watchdog.conf /etc/supervisor/conf.d/

# set up the watchdog
virtualenv -p python3 /home/ubuntu/watchdog/
. /home/ubuntu/watchdog/bin/activate
pip install -r /home/ubuntu/watchdog/requirements.txt
deactivate

# make the launcher executable
chmod +x /home/ubuntu/launch_minecraft.sh
