import boto3
import os
import sys
sys.path.append("./lambda")
from const_config import *

if AWS_PROFILE_NAME == "default":
    session = boto3.session.Session(region_name='us-west-1')
else:
    session = boto3.session.Session(profile_name=AWS_PROFILE_NAME, region_name='us-west-1')

s3_client = session.client('s3')

bucket_name = f"{SYSTEM_PREFIX}-system-log"

try:
    response = s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': 'us-west-1'})
    os.system(f"aws s3 cp ./model-function.zip s3://{bucket_name}/lambda_files/")
except:
    try:
        os.system(f"aws s3 cp ./model-function.zip s3://{bucket_name}/lambda_files/")
        exit(0)
    except:
        print("System name already exists")
        exit(1)
    print("System has just been deleted")
    exit(1)
print(response)
