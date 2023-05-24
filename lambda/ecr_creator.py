import boto3
import os
import base64
import sys
sys.path.append("./lambda")
from const_config import *

if AWS_PROFILE_NAME == "default":
    session = boto3.session.Session(region_name=AWS_REGION_NAME)
else:
    session = boto3.session.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION_NAME)

ecr_client = session.client('ecr')
ec2_client = session.client('ec2')
ec2_resource = session.resource('ec2')
AMI_OS = "amzn2-ami-kernel*"

repository_name = SYSTEM_PREFIX+"-model-function"

response = ecr_client.create_repository(repositoryName=repository_name)

response = ecr_client.get_authorization_token()
username, password = base64.b64decode(response['authorizationData'][0]['authorizationToken']).decode().split(':')
registry = response['authorizationData'][0]['proxyEndpoint'].split("//")[1]

image_uri = f"{registry}/{repository_name}:{SYSTEM_PREFIX}-model-image"
print(image_uri)

credentials = os.popen("cat ~/.aws/credentials").read().split("\n")
access_key_id = ""
secret_access_key = ""
for idx in range(len(credentials)):
    if AWS_PROFILE_NAME in credentials[idx]:
        access_key_id = credentials[idx+1].split("=")[1].strip()
        secret_access_key = credentials[idx+2].split("=")[1].strip()
        break

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
AL2 = images['ImageId']

instance = ec2_resource.create_instances(
    ImageId=AL2,
    InstanceType='t3.large',
    MinCount=1,
    MaxCount=1,
    UserData=f"""#!/bin/bash
cd ~/
mkdir ~/.aws
sudo cat << EOF > ~/.aws/credentials
[default]
aws_access_key_id = {access_key_id}
aws_secret_access_key = {secret_access_key}
EOF
aws s3 cp s3://{SYSTEM_PREFIX}-system-log/lambda_files/model-function.zip .
"""+"""sudo cat << EOF > ./Dockerfile
FROM public.ecr.aws/lambda/python:3.9
RUN yum install unzip -y
RUN /var/lang/bin/python3.9 -m pip install --upgrade pip
RUN pip3 install torch==2.0.1 scikit-learn==1.2.2 pandas==2.0.1 numpy==1.24.3 requests==2.28.1 --target "\${LAMBDA_TASK_ROOT}"
COPY model-function.zip \${LAMBDA_TASK_ROOT}
RUN unzip \${LAMBDA_TASK_ROOT}/model-function.zip
CMD ["lambda_function.lambda_handler"]

EOF
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo service docker start
"""+f"""sudo docker login -u {username} -p {password} {registry}
sudo docker build -t {image_uri} .
sudo docker push {image_uri}""",
    BlockDeviceMappings=[
        {
            'DeviceName': '/dev/xvda',
            'Ebs': {
                'VolumeSize': 20, # 8 GB
                'DeleteOnTermination': True,
                'VolumeType': 'gp2',
            },
        },
    ],
)

images = ecr_client.list_images(repositoryName=repository_name)
while len(images['imageIds']) == 0:
    images = ecr_client.list_images(repositoryName=repository_name)

ec2_client.terminate_instances(InstanceIds=[instance[0].id])
