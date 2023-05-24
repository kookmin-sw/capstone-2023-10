import boto3
from const_config import *

if AWS_PROFILE_NAME == "default":
    session = boto3.session.Session(region_name='us-west-1')
else:
    session = boto3.session.Session(profile_name=AWS_PROFILE_NAME, region_name='us-west-1')

s3_client = session.client('s3')
s3_resource = session.resource('s3')

bucket_name = f"{SYSTEM_PREFIX}-system-log"

# Get the bucket
bucket = s3_resource.Bucket(bucket_name)

# Delete all objects in the bucket
bucket.objects.all().delete()

response = s3_client.delete_bucket(Bucket=bucket_name)
print(response)
