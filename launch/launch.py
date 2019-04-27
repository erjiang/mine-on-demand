import boto3

AMI = 'ami-00af8e72f7a286b9e'
SG = 'sg-0c60ae91e65a479dd'
SUBNET_ID = 'subnet-3830357e'
SPOT_PRICE = '0.016'
KEY_NAME = 'eric-west-1'
WORLD_VOLUME = 'vol-0e6018d54a535e733'

ec2 = boto3.resource('ec2', region_name='us-west-1')

#instances = ec2.create_instances(
#    MinCount=1,
#    MaxCount=1,
##    BlockDeviceMappings=[
##        {
##            'Ebs': {
##                'SnapshotId': 'snap-0b95f8c0766c1aabf',
##                'VolumeSize': 8,
##                'DeleteOnTermination': True,
##                'VolumeType': 'gp2',
##                'Encrypted': False
##            },
##        },
##    ],
#    ImageId=AMI,
#    InstanceType='t3.medium',
#    KeyName=KEY_NAME,
#    SecurityGroupIds=[SG],
#    SubnetId=SUBNET_ID,
#    DryRun=True,
#    EbsOptimized=True,
#)

#instance = instances[0]
instance = ec2.Instance('i-01e25792a5174bc7a')

print("Waiting for instance to start running")
instance.wait_until_running()

instance.attach_volume(
    Device='/dev/sdf',
    VolumeId=WORLD_VOLUME,
    DryRun=False
)

#response = client.request_spot_instances(
#    DryRun=False,
#    SpotPrice=SPOT_PRICE,
#    ClientToken='string',
#    InstanceCount=1,
#    Type='one-time',
#    LaunchSpecification={
#        'ImageId': AMI,
#        'KeyName': 'eric-west-1.pem',
#        'InstanceType': 't3.medium',
#        'Placement': {
#            'AvailabilityZone': 'us-west-1a',
#        },
#        'BlockDeviceMappings': [
#            {
#                'Ebs': {
#                    'SnapshotId': 'snap-0b95f8c0766c1aabf',
#                    'VolumeSize': 8,
#                    'DeleteOnTermination': True,
#                    'VolumeType': 'gp2',
#                    'Encrypted': False
#                },
#            },
#        ],
#        'EbsOptimized': True,
#        'Monitoring': {
#            'Enabled': True
#        },
#        'SecurityGroupIds': [ SG ]
#    }
#)
#
