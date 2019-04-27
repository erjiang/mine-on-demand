import boto3
import os

AMI = os.environ['AMI_ID']
SG_ID = os.environ['SG_ID']
SUBNET_ID = os.environ['SUBNET_ID']
KEY_NAME = os.environ['KEY_NAME']
WORLD_VOLUME = os.environ['WORLD_VOLUME']

IP_ADDR = os.environ['IP_ADDR']

REGION_NAME = os.environ['REGION_NAME']

ec2 = boto3.resource('ec2', region_name=REGION_NAME)


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
            'Groups': [SG],
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


if __name__ == '__main__':
    instances = launch_instances()
    instance = instances[0]

    print("Waiting for instance to start running")
    instance.wait_until_running()

    print("Attaching world volume")
    attach_volume(instance)

    print("Done")
