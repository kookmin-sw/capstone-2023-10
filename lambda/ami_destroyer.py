import boto3
import sys
import os
from const_config import *

if AWS_PROFILE_NAME == "default":
    session = boto3.session.Session(region_name=AWS_REGION_NAME)
else:
    session = boto3.session.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION_NAME)
ec2_client = session.client('ec2')
ec2_resource = session.resource('ec2')
ssm_client = session.client('ssm')

AMI_ARM = ssm_client.get_parameter(Name="AMI_ARM", WithDecryption=False)['Parameter']['Value']  
AMI_INTEL = ssm_client.get_parameter(Name="AMI_INTEL", WithDecryption=False)['Parameter']['Value']

try:
    ec2_client.deregister_image(ImageId=AMI_ARM)
except Exception as e:
    print(e)
try:
    ec2_client.deregister_image(ImageId=AMI_INTEL)
except Exception as e:
    print(e)
try:
    ssm_client.delete_parameter(Name='AMI_ARM')
except Exception as e:
    print(e)
try:
    ssm_client.delete_parameter(Name='AMI_INTEL')
except Exception as e:
    print(e)
