# AWS, Azure, GCP sdk import
import boto3
# import azure.core
# import google.cloud
# etc
import base64
import pickle
import time
import sys
import os
from datetime import datetime, timezone
from waiter_manager import waiter_send_message, waiter_userdata_complete, waiter_create_images
sys.path.append('./lambda')
from const_config import *

# ==================================================================================
# ============================== Set Default Variance ==============================
# ==================================================================================
## << AWS >>
if AWS_PROFILE_NAME == "default":
    session = boto3.session.Session(region_name=AWS_REGION_NAME)
else:
    session = boto3.session.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION_NAME)
ec2_client = session.client('ec2')
ec2_resource = session.resource('ec2')
elbv2_client = session.client('elbv2')
s3_client = session.client('s3')
ssm_client = session.client('ssm')
lambda_client = session.client('lambda')
### IAM
IAM_ROLE_ARN = None
### AMI
AMI_OS = "RHEL-9.0*_HVM-*"
AMI_ARM = None
AMI_INTEL = None
NOW_VENDOR = None
NOW_AZ = None
NOW_INSTANCE_ID = None
NOW_INSTANCE = None
### EFS
EFS_PATH = "/checkpoint"
EFS_ID = None
### NETWORK
SUBNET_ID = None
SECURITYGROUP_ID = None
LOAD_BALANCER_NAME = None
TARGET_GROUP_ARN = None
### Lambda
LAMBDA_FUNCTION_URL = None
MODEL_FUNCTION_URL = None
## << GCP >>
### ...
## << AZURE >>
### ...
## << COMMON >>
USERDATA = {}
MIGRATION_START_TIME = None
## << TEMPORALY >>
MIGRATION_TEST_START = None
MIGRATION_TEST_END = None
# ==================================================================================


# Create Latest Red Hat OS When AMI ID is None
def create_ami(architecture):
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

        userdata = USERDATA["AMI_ARM"]

        instance = ec2_resource.create_instances(
            ImageId=ARM_REDHAT,
            InstanceType='t4g.micro',
            MinCount=1,
            MaxCount=1,
            UserData=userdata,
            IamInstanceProfile={
                'Arn': IAM_ROLE_ARN
            },
        )
        waiter_userdata_complete(instance[0].id, "INIT", MIGRATION_START_TIME)
        print("Create Image...")
        resp = ec2_client.create_image(
            Name='Jupyter_ARM',
            Description='ARM Image to Run Jupyter Container(OptiNotebook)',
            NoReboot=False,
            InstanceId=instance[0].id,
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

        userdata = USERDATA["AMI_INTEL"]

        instance = ec2_resource.create_instances(
            ImageId=INTEL_REDHAT,
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1,
            UserData=userdata,
            IamInstanceProfile={
                'Arn': IAM_ROLE_ARN
            },
        )
        waiter_userdata_complete(instance[0].id, "INIT", MIGRATION_START_TIME)
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
    try:
        AMI_ARM = ssm_client.get_parameter(Name="AMI_ARM", WithDecryption=False)['Parameter']['Value']
    except:
        AMI_ARM = create_ami("ARM")
        ssm_client.put_parameter(
            Name="AMI_ARM",
            Value=AMI_ARM,
            Type='String',
            Description="AMI ID for ARM Architecture",
            Overwrite=True
        )
    try:
        AMI_INTEL = ssm_client.get_parameter(Name="AMI_INTEL", WithDecryption=False)['Parameter']['Value']
    except:
        AMI_INTEL = create_ami("x86_64")
        ssm_client.put_parameter(
            Name="AMI_INTEL",
            Value=AMI_INTEL,
            Type='String',
            Description="AMI ID for INTEL/AMD Architecture",
            Overwrite=True
        )
    return AMI_ARM, AMI_INTEL


def select_instance():
    global SUBNET_ID
    nextInstance = ssm_client.get_parameter(Name="NEXT_INSTANCE", WithDecryption=False)['Parameter']['Value']
    nextAz = ssm_client.get_parameter(Name="NEXT_AZ", WithDecryption=False)['Parameter']['Value']
    SUBNET_ID = ssm_client.get_parameter(Name=f"SUBNET_ID_{nextAz}", WithDecryption=False)['Parameter']['Value']
    ssm_client.put_parameter(
        Name="NOW_INSTANCE",
        Value=nextInstance,
        Type='String',
        Description="Instance type now working",
        Overwrite=True
    )
    ssm_client.put_parameter(
        Name="NOW_AZ",
        Value=nextAz,
        Type='String',
        Description="Instance type now working",
        Overwrite=True
    )
    return {"Vendor":"AWS", "InstanceType":nextInstance, "Region":AWS_REGION_NAME, "AZ":nextAz}


def checkpointing(instanceId):
    # Checkpointing from Source Instance
    # Send Checkpointing Execution Line to Source Instance
    print("Checkpointing...")
    sourceVendor = NOW_VENDOR
    try:
        if sourceVendor == 'AWS':
            command = f'sudo podman container checkpoint jupyternb --file-locks --tcp-established --keep --print-stats -e {EFS_PATH}/jupyCheckpoint.tar.gz'
            waiter_send_message(instanceId, command)
            response = elbv2_client.deregister_targets(
                TargetGroupArn=TARGET_GROUP_ARN,
                Targets=[
                    {
                        'Id': instanceId,
                        'Port': 80,
                    },
                ]
            )
            try:
                ec2_client.terminate_instances(InstanceIds=[instanceId])
                s3_client.put_object(Bucket=SYSTEM_PREFIX+'-system-log', Key=f'InterruptLog/{datetime.strftime(datetime.now(timezone.utc), "%Y-%m-%d_%H:%M:%S")}.log', Body=f'{NOW_INSTANCE} terminated at {datetime.strftime(datetime.now(timezone.utc), "%Y-%m-%d %H:%M:%S")}')
            except:
                print("[LOG] Already Terminated")
        elif sourceVendor == 'AZURE':
            pass
        elif sourceVendor == 'GCP':
            pass
        else:
            print("[ERROR] Info is Incorrect(in checkpointing)")
    except Exception as e:
        print("[ERROR]",e)


def load_variable():
    global IAM_ROLE_ARN
    global EFS_ID
    global SUBNET_ID
    global SECURITYGROUP_ID
    global LOAD_BALANCER_NAME
    global TARGET_GROUP_ARN
    global USERDATA
    global NOW_VENDOR
    global NOW_INSTANCE_ID
    global NOW_INSTANCE
    global NOW_AZ
    global LAMBDA_FUNCTION_URL
    global AMI_ARM
    global AMI_INTEL
    try:
        NOW_AZ = ssm_client.get_parameter(Name="NOW_AZ", WithDecryption=False)['Parameter']['Value']
        NOW_INSTANCE = ssm_client.get_parameter(Name="NOW_INSTANCE", WithDecryption=False)['Parameter']['Value']
        NOW_VENDOR = ssm_client.get_parameter(Name="NOW_VENDOR", WithDecryption=False)['Parameter']['Value']
        NOW_INSTANCE_ID = ssm_client.get_parameter(Name="NOW_INSTANCE_ID", WithDecryption=False)['Parameter']['Value']
    except:
        print("[LOG] NOW_VENDOR, NOW_INSTANCE_ID is not needed in INIT")
    IAM_ROLE_ARN = ssm_client.get_parameter(Name="IAM_ROLE_ARN", WithDecryption=False)['Parameter']['Value']
    EFS_ID = ssm_client.get_parameter(Name="EFS_ID", WithDecryption=False)['Parameter']['Value']
    SUBNET_ID = ssm_client.get_parameter(Name=f"SUBNET_ID_{NOW_AZ}", WithDecryption=False)['Parameter']['Value']
    SECURITYGROUP_ID = ssm_client.get_parameter(Name="SECURITYGROUP_ID", WithDecryption=False)['Parameter']['Value']
    LOAD_BALANCER_NAME = ssm_client.get_parameter(Name="LOAD_BALANCER_NAME", WithDecryption=False)['Parameter']['Value']
    TARGET_GROUP_ARN = ssm_client.get_parameter(Name="TARGET_GROUP_ARN", WithDecryption=False)['Parameter']['Value']
    LAMBDA_FUNCTION_URL = ssm_client.get_parameter(Name="LAMBDA_FUNCTION_URL", WithDecryption=False)['Parameter']['Value']
    MODEL_FUNCTION_URL = ssm_client.get_parameter(Name="MODEL_FUNCTION_URL", WithDecryption=False)['Parameter']['Value']
    USERDATA = {
        "AMI_ARM" : f"""#!/bin/bash
sudo yum update -y
sudo yum upgrade -y
sudo yum install podman-4.2.0 -y
sudo podman pull docker.io/jupyter/base-notebook
sudo cat << EOF > /custom.js
Jupyter.toolbar.add_buttons_group([
{'{'} 
'label': 'Manual Migrate',
'icon': 'fa fa-play',
'callback': function () {'{'}
fetch('{LAMBDA_FUNCTION_URL}');
fetch('{MODEL_FUNCTION_URL}');
alert('Migration will start in 2 minutes');
{'}'}
{'}'}
]);
EOF
sudo cat << EOF > /Dockerfile
FROM docker.io/jupyter/base-notebook
COPY /custom.js /home/jovyan/.jupyter/custom/
EOF
sudo podman build -t custom_jupyter /
sudo dnf install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_arm64/amazon-ssm-agent.rpm
sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent
sudo yum -y install git
git clone https://github.com/aws/efs-utils
sudo yum -y install make
sudo yum -y install rpm-build
sudo make -C efs-utils/ rpm
sudo yum -y install efs-utils/build/amazon-efs-utils*rpm""",
        "AMI_INTEL" : f"""#!/bin/bash
sudo yum update -y
sudo yum upgrade -y
sudo yum install podman-4.2.0 -y
sudo podman pull docker.io/jupyter/base-notebook
sudo cat << EOF > /custom.js
Jupyter.toolbar.add_buttons_group([
{'{'} 
'label': 'Manual Migrate',
'icon': 'fa fa-play',
'callback': function () {'{'}
fetch('{LAMBDA_FUNCTION_URL}');
fetch('{MODEL_FUNCTION_URL}');
alert('Migration will start in 2 minutes');
{'}'}
{'}'}
]);
EOF
sudo cat << EOF > /Dockerfile
FROM docker.io/jupyter/base-notebook
COPY /custom.js /home/jovyan/.jupyter/custom/
EOF
sudo podman build -t custom_jupyter /
sudo dnf install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm
sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent
sudo yum -y install git
git clone https://github.com/aws/efs-utils
sudo yum -y install make
sudo yum -y install rpm-build
sudo make -C efs-utils/ rpm
sudo yum -y install efs-utils/build/amazon-efs-utils*rpm""",
        "INIT" : f"""#!/bin/bash
sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent
sudo mkdir {EFS_PATH}
sudo mount -t efs -o tls {EFS_ID}:/ {EFS_PATH}
sudo podman run --name jupyternb -e GRANT_SUDO=yes --user root -p 80:8888 -d custom_jupyter start-notebook.sh --NotebookApp.password='' --NotebookApp.token='' --NotebookNotary.db_file=':memory:'
""",
        "MIGRATE" : f"""#!/bin/bash
sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent
sudo mkdir {EFS_PATH}
sudo mount -t efs -o tls {EFS_ID}:/ {EFS_PATH}"""
    }
    AMI_ARM, AMI_INTEL = load_ami()


# Select AMI Worked on Instance's Architecture
def arch_to_ami(instanceType, ec2_client):
    archs = ec2_client.describe_instance_types(InstanceTypes=[instanceType])['InstanceTypes'][0]['ProcessorInfo']['SupportedArchitectures']
    # load_ami()
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

            waiter = ec2_client.get_waiter('spot_instance_request_fulfilled')
            imageId = arch_to_ami(instanceType, ec2_client)
            userdata = USERDATA[state]

            requestResponse = ec2_client.request_spot_instances(
                InstanceCount=1,
                LaunchSpecification={
                    'ImageId': imageId,
                    'InstanceType':instanceType,
                    'Placement': {'AvailabilityZone':az},
                    'SubnetId': SUBNET_ID,
                    'SecurityGroupIds': [SECURITYGROUP_ID],
                    'IamInstanceProfile': {
                        'Arn': IAM_ROLE_ARN
                    },
                    'UserData': base64.b64encode(userdata.encode('utf-8')).decode('utf-8'),
                },
            )
            spot_instance_request_id = requestResponse['SpotInstanceRequests'][0]['SpotInstanceRequestId']
            waiter.wait(
                SpotInstanceRequestIds=[spot_instance_request_id],
                WaiterConfig={
                    'Delay': 1,
                    'MaxAttempts': 90
                }
            )
            spot_request_resp = ec2_client.describe_spot_instance_requests(SpotInstanceRequestIds=[spot_instance_request_id])['SpotInstanceRequests'][0]['Status']['Code']
            if state == "INIT" or spot_request_resp == "fulfilled":
                s3_client.put_object(Bucket=SYSTEM_PREFIX+'-system-log', Key=f'InterruptLog/{datetime.strftime(datetime.now(timezone.utc), "%Y-%m-%d_%H:%M:%S")}.log', Body=f'{instanceType} created in {az} at {datetime.strftime(datetime.now(timezone.utc), "%Y-%m-%d %H:%M:%S")}')

                describeResponse = ec2_client.describe_instances(
                    Filters=[
                        {
                            'Name': 'spot-instance-request-id',
                            'Values': [spot_instance_request_id]
                        }
                    ]
                )

                requestResponse['InstanceId'] = describeResponse['Reservations'][0]['Instances'][0]['InstanceId']

                instanceId = requestResponse['InstanceId']
                
                result = waiter_userdata_complete(instanceId, state, MIGRATION_START_TIME)

                response = elbv2_client.register_targets(
                    TargetGroupArn=TARGET_GROUP_ARN,
                    Targets=[
                        {
                            'Id': instanceId,
                            'Port': 80,
                        },
                    ]
                )
            
            if state == "MIGRATE":
                global MIGRATION_TEST_START
                MIGRATION_TEST_START = time.time()
                checkpointing(NOW_INSTANCE_ID)
                if spot_request_resp != "fulfilled":
                    while spot_request_resp != "fulfilled":
                        waiter.wait(
                            SpotInstanceRequestIds=[spot_instance_request_id],
                            WaiterConfig={
                                'Delay': 1,
                                'MaxAttempts': 90
                            }
                        )
                        spot_request_resp = ec2_client.describe_spot_instance_requests(SpotInstanceRequestIds=[spot_instance_request_id])['SpotInstanceRequests'][0]['Status']['Code']
                    s3_client.put_object(Bucket=SYSTEM_PREFIX+'-system-log', Key=f'InterruptLog/{datetime.strftime(datetime.now(timezone.utc), "%Y-%m-%d_%H:%M:%S")}.log', Body=f'{instanceType} created in {az} at {datetime.strftime(datetime.now(timezone.utc), "%Y-%m-%d %H:%M:%S")}')

                    describeResponse = ec2_client.describe_instances(
                        Filters=[
                            {
                                'Name': 'spot-instance-request-id',
                                'Values': [spot_instance_request_id]
                            }
                        ]
                    )

                    requestResponse['InstanceId'] = describeResponse['Reservations'][0]['Instances'][0]['InstanceId']

                    instanceId = requestResponse['InstanceId']

                    result = waiter_userdata_complete(instanceId, state, MIGRATION_START_TIME)

                    response = elbv2_client.register_targets(
                        TargetGroupArn=TARGET_GROUP_ARN,
                        Targets=[
                            {
                                'Id': instanceId,
                                'Port': 80,
                            },
                        ]
                    )
                if result == False:
                    result = waiter_userdata_complete(instanceId, "INIT", MIGRATION_START_TIME)
                waiter_send_message(instanceId, f"sudo podman container restore --file-locks --tcp-established --keep --print-stats --import {EFS_PATH}/jupyCheckpoint.tar.gz")
                global MIGRATION_TEST_END
                MIGRATION_TEST_END = time.time()
                print(MIGRATION_TEST_END - MIGRATION_TEST_START)
            
            ssm_client.put_parameter(
                Name="NOW_VENDOR",
                Value=vendor,
                Type='String',
                Description="Cloud Vendor Working on Now",
                Overwrite=True
            )
            ssm_client.put_parameter(
                Name="NOW_INSTANCE_ID",
                Value=instanceId,
                Type='String',
                Description="Instance Id Working on Now",
                Overwrite=True
            )

        elif vendor == 'AZURE':
            # Request AZURE Spot VM in AZURE Subnet
            pass
        elif vendor == 'GCP':
            # Request GCP Spot VM in GCP Subnet
            pass
        else:
            print("[ERROR] Info is Incorrect(in create_instance)")
    except Exception as e:
        print("[ERROR]", e)
    
    return requestResponse


# Migrate to New Instance from Source Instance
def migration(newInstanceInfo, sourceInstanceInfo):
    print("Request New Spot Instance...")
    
    # Request New Spot Instance
    response = create_instance(newInstanceInfo, "MIGRATE")

    print("Complete!")
    print("Refresh your Jupyter page")

    return response

def init(newInstanceInfo):
    print("Initialize...")
    ssm_client.put_parameter(
        Name="NOW_VENDOR",
        Value="AWS",
        Type='String',
        Description="Instance type now working",
        Overwrite=True
    )
    ssm_client.put_parameter(
        Name="NOW_INSTANCE",
        Value=START_INSTANCE_TYPE,
        Type='String',
        Description="Instance type now working",
        Overwrite=True
    )
    ssm_client.put_parameter(
        Name="NOW_AZ",
        Value=newInstanceInfo['AZ'],
        Type='String',
        Description="Availability Zone now working",
        Overwrite=True
    )
    load_variable()

    lambda_client.invoke(
        FunctionName=SYSTEM_PREFIX+"-model-function",
        InvocationType='Event'
    )
    
    response = create_instance(newInstanceInfo, "INIT")

    return response

def lambda_handler(event, context):
    load_variable()
    if 'detail' in event and event['detail']['instance-id'] != NOW_INSTANCE_ID:
        return {
            "statusCode": 501, "Message": "Not Jupyter Spot Instance"
        }
    try:
        IS_MIGRATE = ssm_client.get_parameter(Name="IS_MIGRATE", WithDecryption=False)['Parameter']['Value']
        if IS_MIGRATE == 'Migrating':
            return {"statusCode": 200, "message": "Already Migrating", "migrationTime": 0}
    except:
        pass
    
    ssm_client.put_parameter(
        Name="IS_MIGRATE",
        Value="Migrating",
        Type='String',
        Description="Check Lambda Function is already running",
        Overwrite=True
    )
    global MIGRATION_START_TIME
    MIGRATION_START_TIME = time.time()

    try:
        sourceInstanceInfo = {'Vendor': NOW_VENDOR, 'InstanceId': NOW_INSTANCE_ID}
        newInstanceInfo = select_instance()
        migration(newInstanceInfo, sourceInstanceInfo)
    except:
        newInstanceInfo = select_instance()
        init(newInstanceInfo)
    
    ssm_client.put_parameter(
        Name="IS_MIGRATE",
        Value="Idle",
        Type='String',
        Description="Check Lambda Function is already running",
        Overwrite=True
    )
    return {
        "statusCode": 200, "message": "Migration Complete", "migrationTime": MIGRATION_TEST_END - MIGRATION_TEST_START
    } 

if __name__ == '__main__':
    init({"Vendor":START_VENDOR, "InstanceType":START_INSTANCE_TYPE, "Region":AWS_REGION_NAME, "AZ":AWS_REGION_NAME+"a"})
    response = elbv2_client.describe_load_balancers(
        Names=[LOAD_BALANCER_NAME]
    )

    dns_name = response['LoadBalancers'][0]['DNSName']
    print("=================Connect to Jupyter Notebook=================")
    print(dns_name+"/tree")
    print("=============================================================")

