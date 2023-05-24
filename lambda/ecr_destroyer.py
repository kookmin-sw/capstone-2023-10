import boto3
from const_config import *

if AWS_PROFILE_NAME == "default":
    session = boto3.session.Session(region_name=AWS_REGION_NAME)
else:
    session = boto3.session.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION_NAME)

ecr = session.client('ecr')

repository_name = SYSTEM_PREFIX+"-model-function"

response = ecr.delete_repository(
    repositoryName=repository_name,
    force=True
)

print(response)
