from dateutil import parser
import os
import socket
import sys
import time

import boto3
from mcstatus import MinecraftServer

# if your AMIs have a different name, you can change this. find_latest_image
# will look at images starting with this string.
AMI_PREFIX = os.getenv('AMI_PREFIX') or 'mine-on-demand '
SG_ID = os.environ['SG_ID']
SUBNET_ID = os.environ['SUBNET_ID']
KEY_NAME = os.environ['KEY_NAME']
WORLD_VOLUME = os.environ['WORLD_VOLUME']

SNS_ARN = os.getenv('SNS_ARN')

IP_ADDR = os.environ['SERVER_IP']

USE_SPOT_INSTANCE = True
INSTANCE_TYPE = os.getenv('INSTANCE_TYPE') or 'c5.xlarge'
MAX_SPOT_PRICE = os.getenv('MAX_SPOT_PRICE') or '0.17' # per hour

REGION_NAME = os.environ['REGION_NAME']

ec2 = boto3.resource('ec2', region_name=REGION_NAME)
client = boto3.client('ec2', region_name=REGION_NAME)


def get_my_account_id():
    return boto3.client('sts').get_caller_identity().get('Account')


def find_latest_image():
    """Returns the latest mine-on-demand AMI ID."""
    response = client.describe_images(
        Owners=[get_my_account_id()],
        Filters=[{
            'Name': 'name',
            'Values': [AMI_PREFIX + '*']
        }])
    newest_image = None
    for image in response['Images']:
        if newest_image is None:
            newest_image = image
        elif parser.parse(image['CreationDate']) > parser.parse(newest_image['CreationDate']):
            newest_image = image
    if newest_image:
        return newest_image['ImageId']


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
    return not volume.attachments


def launch_spot_instance():
    request = client.request_spot_instances(
        InstanceCount=1,
        SpotPrice=MAX_SPOT_PRICE,
        Type='one-time',
        InstanceInterruptionBehavior='terminate',
        LaunchSpecification={
            'NetworkInterfaces': [{
                'DeviceIndex': 0,
                'Ipv6Addresses': [
                    {
                        'Ipv6Address': IP_ADDR
                    }
                ],
                'SubnetId': SUBNET_ID,
                'Groups': [SG_ID],
            }],
        #    'BlockDeviceMappings': [
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
            'ImageId': find_latest_image(),
            'InstanceType': INSTANCE_TYPE,
            # not needed for spot instances apparently
            #'InstanceInitiatedShutdownBehavior': 'terminate',
            'KeyName': KEY_NAME,
            'EbsOptimized': True,
        }
    )
    print(request)
    spot_id = request['SpotInstanceRequests'][0]['SpotInstanceRequestId']
    instance_id = request['SpotInstanceRequests'][0].get('InstanceId')
    print("instance_id is %s" % (instance_id,))

    # since we can't tag the instances in the request_spot_instances call, we
    # need to wait for the instances to be created and then tag them separately
    while not instance_id:
        time.sleep(2)
        spot_info = client.describe_spot_instance_requests(
            SpotInstanceRequestIds=[spot_id]
        )
        instance_id = spot_info['SpotInstanceRequests'][0].get('InstanceId')
        print("instance_id is %s" % (instance_id,))

    print("Tagging %s" % (instance_id,))
    ec2.create_tags(
        Resources=[instance_id],
        Tags=[{
            'Key': 'mine-on-demand-managed',
            'Value': 'true'
        }]
    )

    return ec2.Instance(instance_id)


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
        InstanceType=INSTANCE_TYPE,
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

    if USE_SPOT_INSTANCE:
        instance_id = launch_spot_instance()
        instance = None
        # keep checking until we get the instance ID we need
        while not instance:
            time.sleep(2)
            instance = get_active_minecraft_server()
            if instance:
                instance_id = instance.instance_id
                print("Spot instance launched")
            else:
                print("Waiting for spot instance request")
    else:
        instances = launch_instances()
        print("Launching instance...")
        instance = instances[0]

    print("Waiting for instance to start running")
    instance.wait_until_running()

    print("Attaching world volume")
    attach_volume(instance)

    print("Done")
    return True


def notify_sns(msg, subject='Minecraft Server notification'):
    # disable SNS notifications by not setting SNS_ARN
    if not SNS_ARN:
        return False
    # only us-east-1 supports SMS, hence why the SNS topic is there instead of
    # the local region
    sns_client = boto3.client('sns', region_name='us-east-1')
    print("Publishing to %s" % (SNS_ARN,))
    response = sns_client.publish(
        TopicArn=SNS_ARN,
        Message=msg,
        Subject=subject)
    print(response)
    return response


if __name__ == '__main__':
    launch_minecraft_server()
