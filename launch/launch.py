import os
import socket
import sys
import time

import boto3
from mcstatus import MinecraftServer

AMI = os.environ['AMI_ID']
SG_ID = os.environ['SG_ID']
SUBNET_ID = os.environ['SUBNET_ID']
KEY_NAME = os.environ['KEY_NAME']
WORLD_VOLUME = os.environ['WORLD_VOLUME']

IP_ADDR = os.environ['SERVER_IP']

REGION_NAME = os.environ['REGION_NAME']

ec2 = boto3.resource('ec2', region_name=REGION_NAME)
client = boto3.client('ec2', region_name=REGION_NAME)


def get_active_minecraft_server():
    """Returns ec2.instance of any ec2 instance that has tag
    mine-on-demand-managed=true"""
    tagFilter = [{
        'Name': 'tag:mine-on-demand-managed',
        'Values': ['true']
    }, {
        'Name': 'instance-state-name',
        # exclude terminated instances
        'Values': ['pending', 'running', 'stopping', 'stopped', 'shutting-down']
    }]
    results = client.describe_instances(Filters=tagFilter)
    if not results['Reservations']:
        return None
    for r in results['Reservations'][0]['Instances']:
        return ec2.Instance(r['InstanceId'])


def get_public_ip_address_of_server():
    i = get_active_minecraft_server()
    if not i:
        return None
    else:
        return i.public_ip_address


def is_volume_free(volume_id):
    volume = ec2.Volume(volume_id)
    print(volume.attachments)
    return not volume.attachments


def launch_instances():
    instances = ec2.create_instances(
        MinCount=1,
        MaxCount=1,
        NetworkInterfaces=[{
            'DeviceIndex': 0,
            'Ipv6Addresses': [
                {
                    'Ipv6Address': IP_ADDR
                }
            ],
            'SubnetId': SUBNET_ID,
            'Groups': [SG_ID],
        }],
    #    BlockDeviceMappings=[
    #        {
    #            'Ebs': {
    #                'SnapshotId': 'snap-0b95f8c0766c1aabf',
    #                'VolumeSize': 8,
    #                'DeleteOnTermination': True,
    #                'VolumeType': 'gp2',
    #                'Encrypted': False
    #            },
    #        },
    #    ],
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [{
                    'Key': 'mine-on-demand-managed',
                    'Value': 'true'
            }]
        }],
        ImageId=AMI,
        InstanceType='t3.medium',
        # this way the instance can shut itself down
        InstanceInitiatedShutdownBehavior='terminate',
        KeyName=KEY_NAME,
        DryRun=False,
        EbsOptimized=True,
    )
    return instances


def attach_volume(instance):
    instance.attach_volume(
        Device='/dev/sdf',
        VolumeId=WORLD_VOLUME
    )


def launch_minecraft_server():
    """Returns True if successful, False if not or server is already running."""
    print("Checking if server is already running")
    i = get_active_minecraft_server()
    if i:
        return "Server %s seems to be already running" % (i.instance_id,)
        return

    print("Checking if world volume is free")
    if not is_volume_free(WORLD_VOLUME):
        return "World volume is not free. Server may already be running."

    instances = launch_instances()
    print("Launching instance...")
    instance = instances[0]

    print("Waiting for instance to start running")
    instance.wait_until_running()

    print("Attaching world volume")
    attach_volume(instance)

    print("Done")
    return True


if __name__ == '__main__':
    for x in launch_minecraft_server():
        print(x)
