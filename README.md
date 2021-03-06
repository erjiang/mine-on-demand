# Mine-on-Demand

Pay for your Minecraft server while you're using it, shut it down while you're
not.

This codebase includes a web page you can deploy on AWS Lambda, where users can
log in and launch the Minecraft server. The Minecraft world is stored on an EBS
volume that can be attached to new EC2 instances every time you want to play.
When nobody is on the server for an hour, the server automatically shuts itself
down.

## License

This code is provided under the terms of the GNU Affero General Public
License v3 or later. Basically, if you use and modify this code, please share
your modifications under the AGPLv3 as well!

## Changing the AWS region

These instructions were written assuming the us-west-1 region in Northern
California. If you don't want to deploy to us-west-1, then you will need to
replace "us-west-1" with the name of your preferred region in all of the
files in this repo.

## Getting Started

### Create serverless.yml

Copy `launch/serverless.example.yml` to `launch/serverless.yml`. You will be
filling in the configuration values in that file as you go through the rest
of the setup steps.

### Build the AMI

You will need your AWS Access Key and Secret Key from the AWS console. (TODO: Add instructions for creating an IAM user with access key.)

1. Install [HashiCorp Packer](https://www.packer.io/) on your local machine.
1. Set your `AWS_ACCESS_KEY_ID` AND `AWS_SECRET_ACCESS_KEY` environment
   variables to your AWS credentials. It needs to be an account that has enough
   permissions to launch an EC2 instance and build an AMI.
   See also https://www.packer.io/docs/builders/amazon.html
1. Run `make ami` in the root directory of mine-on-demand.
1. Put the AMI ID ("ami-XXXXXXXX") that packer gives you at the end into
   `serverless.yml`.

This will create an AMI in us-west-1 that contains a minecraft server.


### Create your initial world volume

We need to create a BTRFS partition inside a new EBS volume to hold our world
data.

1. Create a new EBS volume that's big enough to hold your Minecraft world
data. You will pay per GB so don't create it too much bigger than your world.
Record the volume ID ("vol-XXXXXXXX") in `serverless.yml`.
1. Using this AMI that you just created, launch an instance (a t3.micro is fine).
1. Go to the EBS volume you created and attach it to your instance.
1. Log in to the EC2 instance and run `sudo parted`.
    1. Type `print devices` to see what devices there are. The world volume
    is probably either `/dev/xvdf` or `/dev/nvme1n1`. It's probably the only
    other device besides your root device. The following instructions will
    use `/dev/xvdf`.
    1. Type `select /dev/xvdf`.
    1. Type `mklabel gpt` to make a partition table.
    1. Type `mkpart primary btrfs 0% 100%` to create one big partition.
    1. Type Ctrl-D or `quit` to quit.
1. Run `sudo mkfs.btrfs /dev/xvdf1` to format the newly created partition.
Your partition might also be called `/dev/nvme1n1p1`.
1. At this point, the Minecraft launch script might automatically detect the
new partition, mount it on `~/world`, and generate a new world to fill it. If
you don't want this, then stop the Minecraft supervisor job (`sudo
supervisorctl stop minecraft`), clean out the `~/world` directory, and load
in your world. Make sure that the partition is mounted by checking that
`/home/ubuntu/world` is listed in `/etc/mtab`. Otherwise, you will be loading
data onto a volume that will be destroyed.
1. Shut down your instance.

### Set up AWS

There are a bunch of things that you need to set up once and include in the sls config.

1. Create a VPC that's IPv6 addressable (let AWS give it an IPv6 block).
1. Create an Internet Gateway and attach it to the VPC.
1. Create a subnet for the VPC. Make sure that IPv6 CIDR block is set to
"Custom IPv6". You can fill out any two-digit hex number for the block.
Remember the subnet ID ("subnet-XXXXXXXX")
1. Go to Route Tables in the VPC dashboard and create a route table.
    1. In its details, go to the Routes tab and add a route with destination
      "::/0" and select your Internet gateway as the target and another route
      with "0.0.0.0/0" for the same Internet gateway.
    1. Go to the Subnet Associations tab and associate it with the subnet you
      just created.
1. Create a security group for the Minecraft server. It needs to allow access
from anywhere on port 25565 and for ICMP. Record the security group ID
("sg-XXXXXXXX") in `serverless.yml`.
1. If you don't have one already, create a keypair for launching EC2
instances. Remember the keypair name (e.g. "my-key-pair").

### Create your Google API project

You will need a Client ID for OAuth, which you can create in the credentials
section of the Google API console. It will look like
"12345-blahblah12345.apps.googleusercontent.com".

You'll need to put this client ID in a file named `.env.local` inside the
`frontend` directory before you build, like so:

```
REACT_APP_GOOGLE_CLIENT_ID=12345-blahblah12345.apps.googleusercontent.com
```

You will also need to include it in your serverless.yml file.

### Whitelist users

The website only allows Google accounts that are in the whitelist. There are
two ways to configure the whitelist: a publicly accessible CSV file served over
HTTP, or an environment variable defined in your serverless.yml file.

**Note:** This whitelist only controls who can access the server status webpage
and launch the server. It does not control who can connect to the Minecraft
server once it is launched.

#### CSV whitelist

By defining `USER_WHITELIST_CSV_URL` in your serverless.yml file, the app will
check users logging in against that CSV file. The CSV file needs to be
accessible without logging in.

The CSV file needs to have authorized emails in the first column, skipping the
first row (which you can use for column headers). Here is an example:

| my friends        |
|-------------------|
| alice@example.com |
| bob@example.com   |
| carol@example.com |

The easiest way to set up a CSV whitelist is to create a Google Sheet. Then,
click on File - Publish to the web. Choose to publish Sheet1 as
"Comma-separated values (.csv)" and make sure you check "Automatically
republish when changes are made."

This allows you to delegate control of the whitelist to multiple users via
Google Drive. For example, you can let certain trusted friends add additional
people to the whitelist.

#### Environment variable whitelist

The other way to set the whitelist is to define the `USER_WHITELIST`
environment variable in your serverless.yml file. If you go this route, make
sure you do not set `USER_WHITELIST_CSV_URL` which takes priority over
`USER_WHITELIST`.

This variable is specified as a string that can be parsed as a JSON array.
Here's an example of what you might write in your serverless.yml file:

    USER_WHITELIST: '["alice@example.com", "bob@example.com"]'

### Build the frontend code

1. Make sure you have a recent-ish version of npm and node.js.
1. Double-check that you've created `.env.local` following the above steps.
1. In the root directory, run `make frontend`.

### Deploy the serverless website

1. Install `sls`: https://serverless.com/framework/docs/providers/aws/guide/installation/
1. Double check that you've replaced all the environment variables with the
actual IDs, options, etc. in your `serverless.yml` file.
1. Run `sls deploy`

## Updating/changing the Minecraft server version

The Minecraft server JAR should be automatically downloaded when the server is
started. See `server_wrapper.py` for details.
