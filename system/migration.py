# AWS, Azure, GCP sdk import
import boto3
import azure.core
import google.cloud
# etc
import base64
import pickle5

# ==================================================================================
# ============================== Set Default Variance ==============================
# ==================================================================================
## << AWS >>
### Your Account Profile in Your AWS-CLI
AWS_PROFILE_NAME = "spotrank"
AWS_REGION_NAME = "us-west-2"
### IAM
IAM_ROLE_ARN = None
### AMI
AMI_OS = "RHEL-9.0*_HVM-*"
AMI_ARM = None
AMI_INTEL = None
### EFS
EFS_PATH = "/checkpoint"
EFS_ID = None
### NETWORK
SUBNET_ID = None
SECURITYGROUP_ID = None
TARGET_GROUP_ARN = None
## << GCP >>
### ...
## << AZURE >>
### ...
## << COMMON >>
USERDATA = {
    "NEW" : f"""#!/bin/bash
sudo yum update -y
sudo yum upgrade -y
sudo yum install podman-4.2.0 -y
sudo yum install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm
sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent
# Mount EFS
sudo yum install amazon-efs-utils
sudo mkdir {EFS_PTH}
sudo mount -t efs -o tls {EFS_ID}:/ {EFS_PATH}
sudo podman pull docker.io/jupyter/base-notebook
sudo podman run --name jupyternb -e GRANT_SUDO=yes --user root -p 8800:8888 -d jupyter/base-notebook start-notebook.sh --NotebookApp.password='' --NotebookApp.token=''
# 
""",
    "MIGRATE" : f"""#!/bin/bash
sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent
# Mount EFS
sudo mkdir {EFS_PATH}
sudo mount -t efs -o tls {EFS_ID}:/ {EFS_PATH}
sudo podman container restore --file-locks --tcp-established --keep --print-stats --import /checkpoint/jupyCheckpoint.tar.gz
# 
"""
}
# ==================================================================================


def check_userdata_complete(instanceId):
    pass


# Create Latest Red Hat OS When AMI ID is None
def create_ami(architecture):
    ec2_client = boto3.client('ec2', region_name=AWS_REGION_NAME)
    if architecture == "ARM":
        resp = ec2_client.describe_images(
            Filters=[
                {
                    'Name': 'name',
                    'Values': [AMI_OS]
                },
                {
                    'Name': 'architecture',
                    'Values': ['arm64']
                }
            ]
        )
        images = sorted(resp['Images'], key=lambda image: image['CreationDate'])[-1]
        ARM_REDHAT = images['ImageId']

        instance = ec2_client.create_instances(
            ImageId=ARM_REDHAT,
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1,
            # KeyName='jaeil-spotlake'
        )
        check_userdata_complete(instance[0].id)
        resp = instance.create_image(
            Name='Jupyter_ARM',
            Description='ARM Image to Run Jupyter Container(OptiNotebook)',
            NoReboot=False
        )
        ec2_client.terminate_instances(InstanceIds=[instance[0].id])

        return resp.image_id

    if architecture == "x86_64":
        resp = ec2_client.describe_images(
            Filters=[
                {
                    'Name': 'name',
                    'Values': [AMI_OS]
                },
                {
                    'Name': 'architecture',
                    'Values': ['x86_64']
                }
            ]
        )
        images = sorted(resp['Images'], key=lambda image: image['CreationDate'])[-1]
        INTEL_REDHAT = images['ImageId']

        instance = ec2_client.create_instances(
            ImageId=INTEL_REDHAT,
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1,
            # KeyName='jaeil-spotlake'
        )
        check_userdata_complete(instance[0].id)
        resp = instance.create_image(
            Name='Jupyter_x86_64',
            Description='ARM Image to Run Jupyter Container(OptiNotebook)',
            NoReboot=False
        )
        ec2_client.terminate_instances(InstanceIds=[instance[0].id])

        return resp.image_id


# Load AMI ID at the System Manager Parameter Store
def load_ami():
    ssm_client = boto3.client('ssm', region_name=AWS_REGION_NAME)
    try:
        AMI_ARM = ssm_client.get_parameter(Name="AMI_ARM", WithDecryption=True)['Parameter']['Value']
    except:
        AMI_ARM = create_ami("ARM")
    try:
        AMI_INTEL = ssm_client.get_parameter(Name="AMI_INTEL", WithDecryption=True)['Parameter']['Value']
    except:
        AMI_INTEL = create_ami("INTEL")
    ssm_client.put_parameter(
        Name="AMI_ARM",
        Value=AMI_ARM,
        Type='SecureString',
        Description="AMI ID for ARM Architecture",
        Overwrite=True
    )
    ssm_client.put_parameter(
        Name="AMI_INTEL",
        Value=AMI_INTEL,
        Type='SecureString',
        Description="AMI ID for INTEL/AMD Architecture",
        Overwrite=True
    )


def load_variable():
    load_ami()
    ssm_client = boto3.client('ssm', region_name=AWS_REGION_NAME)
    IAM_ROLE_ARN = ssm_client.get_parameter(Name="IAM_ROLE_ARN", WithDecryption=True)['Parameter']['Value']
    AMI_ARM = ssm_client.get_parameter(Name="AMI_ARM", WithDecryption=True)['Parameter']['Value']
    AMI_INTEL = ssm_client.get_parameter(Name="AMI_INTEL", WithDecryption=True)['Parameter']['Value']
    EFS_ID = ssm_client.get_parameter(Name="EFS_ID", WithDecryption=True)['Parameter']['Value']
    SUBNET_ID = ssm_client.get_parameter(Name="SUBNET_ID", WithDecryption=True)['Parameter']['Value']
    SECURITYGROUP_ID = ssm_client.get_parameter(Name="SECURITYGROUP_ID", WithDecryption=True)['Parameter']['Value']
    TARGET_GROUP_ARN = ssm_client.get_parameter(Name="TARGET_GROUP_ARN", WithDecryption=True)['Parameter']['Value']


# Select AMI Worked on Instance's Architecture
def arch_to_ami(instanceType, ec2_client):
    archs = ec2_client.describe_instance_types(InstanceTypes=[instanceType])['InstanceTypes'][0]['ProcessorInfo']['SupportedArchitectures']
    load_ami()
    if 'arm64' in archs or 'arm64_mac' in archs:
        return AMI_ARM
    else:
        return AMI_INTEL


# Make New Instance to Migrate
def create_instance(instanceInfo, state):
    vendor = instanceInfo['Vendor']

    requestResponse = {}
    try:
        if vendor == 'AWS':
            # Request AWS Spot Instance in AWS Subnet
            instanceType = instanceInfo['InstanceType']
            az = instanceInfo['AZ']
            region = instanceInfo['Region']

            ec2_client = boto3.client('ec2', region_name=AWS_REGION_NAME)
            waiter = ec2_client.get_waiter('spot_instance_request_fulfilled')
            imageId = arch_to_ami(instanceType, ec2_client)
            userdata = USERDATA[state]

            requestResponse = ec2_client.request_spot_instances(
                InstanceCount=1,
                LaunchSpecification={
                    'ImageId': imageId,
                    'InstanceType':instanceType,
                    'Placement': {'AvailabilityZone':az},
                    'KeyName': 'jaeil-spotlake',
                    'SubnetId': SUBNET_ID,
                    'SecurityGroupIds': [SECURITYGROUP_ID],
                    'IamInstanceProfile': {
                        'Arn': IAM_ROLE_ARN
                    },
                    'UserData': base64.b64encode(userdata.encode('utf-8')).decode('utf-8'),
                },
            )
            spot_instance_request_id = requestResponse['SpotInstanceRequests'][0]['SpotInstanceRequestId']
            waiter.wait(SpotInstanceRequestIds=[spot_instance_request_id])

            describeResponse = ec2_client.describe_instances(
                Filters=[
                    {
                        'Name': 'spot-instance-request-id',
                        'Values': [spot_instance_request_id]
                    }
                ]
            )

            requestResponse['InstanceId'] = describeResponse['Reservations'][0]['Instances'][0]['InstanceId']

            elbv2 = boto3.client('elbv2', region_name=AWS_REGION_NAME)
            response = elbv2.register_targets(
                TargetGroupArn=TARGET_GROUP_ARN,
                Targets=[
                    {
                        'Id': requestResponse['InstanceId'],
                        'Port': 8800,
                    },
                ]
            )

        elif vendor == 'AZURE':
            # Request AZURE Spot VM in AZURE Subnet
            pass
        elif vendor == 'GCP':
            # Request GCP Spot VM in GCP Subnet
            pass
        else:
            print("[ERROR]Info is Incorrect")
    except Exception as e:
        print("[ERROR]"+e)
    
    return requestResponse


# Migrate to New Instance from Source Instance
def migration(newInstanceInfo, sourceInstanceInfo):
    # Checkpointing from Source Instance
    # Send Checkpointing Execution Line to Source Instance
    sourceVendor = sourceInstanceInfo['Vendor']
    try:
        if sourceVendor == 'AWS':
            ssm_client = boto3.client('ssm', region_name=AWS_REGION_NAME)
            instanceId = sourceInstanceInfo['InstanceId']
            response = ssm_client.send_command(
                InstanceIds=[instanceId,],
                DocumentName="AWS-RunShellScript",
                Parameters={'commands':[f'sudo podman container checkpoint jupyternb --file-locks --tcp-established --keep --print-stats -e {EFS_PATH}jupyCheckpoint.tar.gz']}
            )
            elbv2_client = boto3.client('elbv2', region_name=AWS_REGION_NAME)
            response = elbv2_client.deregister_targets(
                TargetGroupArn=TARGET_GROUP_ARN,
                Targets=[
                    {
                        'Id': instanceId,
                        'Port': 8800,
                    },
                ]
            )
            pass
        elif sourceVendor == 'AZURE':
            pass
        elif sourceVendor == 'GCP':
            pass
        else:
            print("[ERROR]Info is Incorrect")
    except Exception as e:
        print("[ERROR]"+e)

    # Request New Spot Instance
    response = create_instance(newInstanceInfo, "MIGRATE")

    return response

def init(newInstanceInfo, subnetInfo):
    response = create_instance(newInstanceInfo, "NEW")

    return response

def lambda_handler(event, context):
    load_variable()
    elbv2_client = boto3.client('elbv2', region_name=AWS_REGION_NAME)
    response = elbv2_client.describe_target_health(
        TargetGroupArn=TARGET_GROUP_ARN
    )

    num_targets = len(response['TargetHealthDescriptions'])
    if num_targets == 0:
        init()
    else:
        migration(event['NewInstanceInfo'], {'Vendor': 'AWS', 'InstanceId': response['TargetHealthDescriptions'][0]['Target']['Id']})
    
    return {
        "statusCode": 200
    } 

