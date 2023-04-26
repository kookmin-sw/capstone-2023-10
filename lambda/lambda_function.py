# AWS, Azure, GCP sdk import
import boto3
import azure.core
import google.cloud
# etc
import base64
import pickle5
import time

# ==================================================================================
# ============================== Set Default Variance ==============================
# ==================================================================================
## << AWS >>
### Your Account Profile in Your AWS-CLI
AWS_PROFILE_NAME = "spotrank"
AWS_REGION_NAME = "ap-northeast-2"
### IAM
IAM_ROLE_ARN = None
### AMI
AMI_OS = "RHEL-9.0*_HVM-*"
AMI_ARM = None
AMI_INTEL = None
NOW_VENDOR = None
NOW_INSTANCE_ID = None
### EFS
EFS_PATH = "/checkpoint"
EFS_ID = None
### NETWORK
SUBNET_ID = None
SECURITYGROUP_ID = None
LOAD_BALANCER_NAME = None
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
sudo yum install amazon-efs-utils
sudo mkdir {EFS_PATH}
sudo mount -t efs -o tls {EFS_ID}:/ {EFS_PATH}
sudo podman pull docker.io/jupyter/base-notebook
sudo podman run --name jupyternb -e GRANT_SUDO=yes --user root -p 8800:8888 -d jupyter/base-notebook start-notebook.sh --NotebookApp.password='' --NotebookApp.token=''
sudo podman container checkpoint jupyternb --file-locks --tcp-established --keep --print-stats -e {EFS_PATH}/jupyCheckpoint.tar.gz""",
    "MIGRATE" : f"""#!/bin/bash
sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent
sudo mkdir {EFS_PATH}
sudo mount -t efs -o tls {EFS_ID}:/ {EFS_PATH}
sudo podman container restore --file-locks --tcp-established --keep --print-stats --import {EFS_PATH}/jupyCheckpoint.tar.gz
sudo podman start jupyternb"""
}
# ==================================================================================


def select_instance(instanceInfo={"Vendor":"Empty"}):
    if instanceInfo['vendor'] == "Empty":
        pass
    else:
        pass


def waiter_userdata_complete(instanceId):
    input()

def waiter_create_images(imageId):
    ec2_client = boto3.client('ec2', region_name=AWS_REGION_NAME)
    time.sleep(5)
    image = ec2_client.describe_images(ImageIds=[imageId])
    while image['Images'][0]['State']=='pending':
        time.sleep(5)
        image = ec2_client.describe_images(ImageIds=[imageId])
    if image['Images'][0]['State'] != 'available':
        print("[ERROR] Image building failed")
        exit()


# Create Latest Red Hat OS When AMI ID is None
def create_ami(architecture):
    ec2_client = boto3.client('ec2', region_name=AWS_REGION_NAME)
    ec2_resource = boto3.resource('ec2', region_name=AWS_REGION_NAME)
    if architecture == "ARM":
        print("Create ARM REDHAT OS...")
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

        userdata = USERDATA["NEW"]

        instance = ec2_resource.create_instances(
            ImageId=ARM_REDHAT,
            InstanceType='t4g.micro',
            MinCount=1,
            MaxCount=1,
            KeyName="jaeil-seoul",
            UserData=userdata,
            # KeyName='jaeil-spotlake'
        )
        waiter_userdata_complete(instance[0].id)
        print("Create Image...")
        resp = ec2_client.create_image(
            Name='Jupyter_ARM',
            Description='ARM Image to Run Jupyter Container(OptiNotebook)',
            NoReboot=False,
            InstanceId=instance[0].id
        )
        waiter_create_images(resp['ImageId'])
        ec2_client.terminate_instances(InstanceIds=[instance[0].id])

        return resp['ImageId']

    if architecture == "x86_64":
        print("Create x86_64 REDHAT OS...")
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

        userdata = USERDATA["NEW"]

        instance = ec2_resource.create_instances(
            ImageId=INTEL_REDHAT,
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1,
            KeyName="jaeil-seoul",
            UserData=userdata,
            # KeyName='jaeil-spotlake'
        )
        waiter_userdata_complete(instance[0].id)
        print("Create Image...")
        resp = ec2_client.create_image(
            Name='Jupyter_x86_64',
            Description='ARM Image to Run Jupyter Container(OptiNotebook)',
            NoReboot=False,
            InstanceId=instance[0].id
        )
        waiter_create_images(resp['ImageId'])
        ec2_client.terminate_instances(InstanceIds=[instance[0].id])

        return resp['ImageId']


# Load AMI ID at the System Manager Parameter Store
def load_ami():
    global AMI_ARM
    global AMI_INTEL
    ssm_client = boto3.client('ssm', region_name=AWS_REGION_NAME)
    try:
        AMI_ARM = ssm_client.get_parameter(Name="AMI_ARM", WithDecryption=False)['Parameter']['Value']
    except:
        AMI_ARM = create_ami("ARM")
    try:
        AMI_INTEL = ssm_client.get_parameter(Name="AMI_INTEL", WithDecryption=False)['Parameter']['Value']
    except:
        AMI_INTEL = create_ami("x86_64")
    ssm_client.put_parameter(
        Name="AMI_ARM",
        Value=AMI_ARM,
        Type='String',
        Description="AMI ID for ARM Architecture",
        Overwrite=True
    )
    ssm_client.put_parameter(
        Name="AMI_INTEL",
        Value=AMI_INTEL,
        Type='String',
        Description="AMI ID for INTEL/AMD Architecture",
        Overwrite=True
    )


def load_variable():
    load_ami()
    global IAM_ROLE_ARN
    global EFS_ID
    global SUBNET_ID
    global SECURITYGROUP_ID
    global LOAD_BALANCER_NAME
    global TARGET_GROUP_ARN
    ssm_client = boto3.client('ssm', region_name=AWS_REGION_NAME)
    IAM_ROLE_ARN = ssm_client.get_parameter(Name="IAM_ROLE_ARN", WithDecryption=False)['Parameter']['Value']
    EFS_ID = ssm_client.get_parameter(Name="EFS_ID", WithDecryption=False)['Parameter']['Value']
    SUBNET_ID = ssm_client.get_parameter(Name="SUBNET_ID", WithDecryption=False)['Parameter']['Value']
    SECURITYGROUP_ID = ssm_client.get_parameter(Name="SECURITYGROUP_ID", WithDecryption=False)['Parameter']['Value']
    LOAD_BALANCER_NAME = ssm_client.get_parameter(Name="LOAD_BALANCER_NAME", WithDecryption=False)['Parameter']['Value']
    TARGET_GROUP_ARN = ssm_client.get_parameter(Name="TARGET_GROUP_ARN", WithDecryption=False)['Parameter']['Value']


# Select AMI Worked on Instance's Architecture
def arch_to_ami(instanceType, ec2_client):
    archs = ec2_client.describe_instance_types(InstanceTypes=[instanceType])['InstanceTypes'][0]['ProcessorInfo']['SupportedArchitectures']
    load_ami()
    if 'arm64' in archs or 'arm64_mac' in archs:
        return AMI_ARM
    else:
        return AMI_INTEL


# Make New Instance to Migrate
def create_instance(instanceInfo):
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
            userdata = USERDATA["MIGRATE"]

            requestResponse = ec2_client.request_spot_instances(
                InstanceCount=1,
                LaunchSpecification={
                    'ImageId': imageId,
                    'InstanceType':instanceType,
                    'Placement': {'AvailabilityZone':az},
                    'KeyName': 'jaeil-seoul',
                    'SubnetId': SUBNET_ID,
                    'SecurityGroupIds': [SECURITYGROUP_ID],
                    'IamInstanceProfile': {
                        'Arn': IAM_ROLE_ARN
                    },
                    'UserData': base64.b64encode(userdata.encode('utf-8')).decode('utf-8'),
                },
            )
            spot_instance_request_id = requestResponse['SpotInstanceRequests'][0]['SpotInstanceRequestId']
            try:
                waiter.wait(SpotInstanceRequestIds=[spot_instance_request_id])
            except:
                status = ec2_client.describe_spot_instance_requests(SpotInstanceRequestIds=[spot_instance_request_id])
                print(status)
                exit()

            print(spot_instance_request_id)

            describeResponse = ec2_client.describe_instances(
                Filters=[
                    {
                        'Name': 'spot-instance-request-id',
                        'Values': [spot_instance_request_id]
                    }
                ]
            )

            print(describeResponse)

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
            print(response)

            ssm_client = boto3.client('ssm', region_name=AWS_REGION_NAME)
            
            ssm_client.put_parameter(
                Name="NOW_VENDOR",
                Value=vendor,
                Type='String',
                Description="Cloud Vendor Working on Now",
                Overwrite=True
            )
            ssm_client.put_parameter(
                Name="NOW_INSTANCE_ID",
                Value=requestResponse['InstanceId'],
                Type='String',
                Description="Cloud Vendor Working on Now",
                Overwrite=True
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
        print("[ERROR]", e)
    
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
        print("[ERROR]",e)

    # Request New Spot Instance
    response = create_instance(newInstanceInfo)

    return response

def init(newInstanceInfo):
    print("Initialize...")
    load_variable()
    response = create_instance(newInstanceInfo)

    return response

def lambda_handler(event, context):
    load_variable()

    try:
        ssm_client = boto3.client('ssm', region_name=AWS_REGION_NAME)
        elbv2_client = boto3.client('elbv2', region_name=AWS_REGION_NAME)
        response = elbv2_client.describe_target_health(
            TargetGroupArn=TARGET_GROUP_ARN
        )
        NOW_VENDOR = ssm_client.get_parameter(Name="NOW_VENDOR", WithDecryption=True)['Parameter']['Value']
        NOW_INSTANCE_ID = ssm_client.get_parameter(Name="NOW_INSTANCE_ID", WithDecryption=True)['Parameter']['Value']
        sourceInstanceInfo = {'Vendor': NOW_VENDOR, 'InstanceId': NOW_INSTANCE_ID}
        newInstanceInfo = select_instance(sourceInstanceInfo)
        migration(newInstanceInfo, sourceInstanceInfo)
    except:
        newInstanceInfo = select_instance()
        init(newInstanceInfo)
    
    return {
        "statusCode": 200
    } 

if __name__ == '__main__':
    init({"Vendor":"AWS", "InstanceType":"t3.medium", "Region":"ap-noertheast-2", "AZ":"ap-northeast-2a"})
    client = boto3.client('elbv2', region_name=AWS_REGION_NAME)
    response = client.describe_load_balancers(
        Names=['my-load-balancer']
    )

    dns_name = response['LoadBalancers'][0]['DNSName']
    print("=================Connect to Jupyter Notebook=================")
    print(dns_name+"/tree")
    print("=============================================================")
