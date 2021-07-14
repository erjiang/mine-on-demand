#!/bin/bash
#
# This bash script takes a plain Ubuntu AMI and installs the necessary bits to
# run a Minecraft server on it. It also sets up /home/ubuntu/world to be a
# symlink to the Minecraft world files.
#
# Note that it doesn't download the actual server JAR, because the latest
# version is downloaded at server startup time. (See server_wrapper.py)
#

# need to do this otherwise supervisor won't install properly
# see https://github.com/hashicorp/terraform/issues/1025
until [[ -f /var/lib/cloud/instance/boot-finished ]]; do
  sleep 1
done

sudo add-apt-repository universe

sudo apt update

sudo apt upgrade

sudo apt -y install openjdk-16-jre-headless supervisor python3-virtualenv python3-pip

sudo apt clean

echo "eula=true" > /home/ubuntu/eula.txt

# symlink world to EBS volume
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
