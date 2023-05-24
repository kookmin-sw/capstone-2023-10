import boto3
import sys
import os
import time
sys.path.append('./lambda')
from const_config import *

if AWS_PROFILE_NAME == "default":
    session = boto3.session.Session(region_name=AWS_REGION_NAME)
else:
    session = boto3.session.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION_NAME)
ssm_client = session.client('ssm')
ec2_client = session.client('ec2')

def waiter_userdata_complete(instanceId, state, mst):
    command = 'sudo tail -n 1 /var/log/cloud-init-output.log | grep finished | wc -l'
    while state == "INIT" or (state=="MIGRATE" and time.time() - mst < 90):
        try:
            response = ssm_client.send_command(
                InstanceIds=[instanceId],
                DocumentName='AWS-RunShellScript',
                Parameters={'commands': [command]}
            )
            commandId = response['Command']['CommandId']

            time.sleep(1)

            output_response = ssm_client.get_command_invocation(
                CommandId=commandId,
                InstanceId=instanceId,
            )
            if output_response['StandardOutputContent'].strip() == '1':
                return True
        except Exception as e:
            time.sleep(1)
    return False

def waiter_send_message(instanceId, command):
    response = ssm_client.send_command(
        InstanceIds=[instanceId,],
        DocumentName="AWS-RunShellScript",
        Parameters={'commands':[command]}
    )
    commandId = response['Command']['CommandId']
    while True:
        try:
            command_invocation = ssm_client.get_command_invocation(
                CommandId=commandId,
                InstanceId=instanceId,
            )
            status = command_invocation['Status']
            if status == 'Success':
                break
            elif status == 'Failed':
                print("[ERROR] Run Command Failed")
                exit()
        except Exception as e:
            time.sleep(1)


def waiter_create_images(imageId):
    image = ec2_client.describe_images(ImageIds=[imageId])
    while image['Images'][0]['State']=='pending':
        time.sleep(1)
        image = ec2_client.describe_images(ImageIds=[imageId])
    if image['Images'][0]['State'] != 'available':
        print("[ERROR] Image building failed")
        exit()
