import boto3
from datetime import datetime
from const_config import *

if AWS_PROFILE_NAME == "default":
    session = boto3.session.Session(region_name=AWS_REGION_NAME)
else:
    session = boto3.session.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION_NAME)
ec2_client = session.client('ec2')
elbv2_client = session.client('elbv2')
ssm_client = session.client('ssm')

NOW_INSTANCE_ID = ssm_client.get_parameter(Name="NOW_INSTANCE_ID", WithDecryption=False)['Parameter']['Value']
NOW_INSTANCE = ssm_client.get_parameter(Name="NOW_INSTANCE", WithDecryption=False)['Parameter']['Value']


try:
    response = elbv2_client.deregister_targets(
        TargetGroupArn=TARGET_GROUP_ARN,
        Targets=[
            {
                'Id': NOW_INSTANCE_ID,
                'Port': 80,
            },
        ]
    )
except:
    pass
try:
    ec2_client.terminate_instances(InstanceIds=[NOW_INSTANCE_ID])
    s3_client.put_object(Bucket=SYSTEM_PREFIX+'-system-log', Key=f'InterruptLog/{datetime.strftime(datetime.now(timezone.utc), "%Y-%m-%d_%H:%M:%S")}.log', Body=f'{NOW_INSTANCE} terminated at {datetime.strftime(datetime.now(timezone.utc), "%Y-%m-%d %H:%M:%S")}')
except:
    pass
try:
    ssm_client.delete_parameter(Name='NOW_INSTANCE_ID')
except:
    pass
try:
    ssm_client.delete_parameter(Name='NOW_VENDOR')
except:
    pass
try:
    ssm_client.delete_parameter(Name='NOW_AZ')
except:
    pass
try:
    ssm_client.delete_parameter(Name='NOW_INSTANCE')
except:
    pass
try:
    ssm_client.delete_parameter(Name='NEXT_AZ')
except:
    pass
try:
    ssm_client.delete_parameter(Name='NEXT_INSTNACE')
except:
    pass
try:
    ssm_client.delete_parameter(Name='IS_MIGRATE')
except:
    pass