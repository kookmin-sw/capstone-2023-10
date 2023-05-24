import boto3
import os
import sys
from datetime import datetime, timedelta
from dateutil.tz import tzutc
sys.path.append('../lambda/')
from const_config import *

session = boto3.session.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION_NAME)
s3_client = session.client('s3')
ec2_client = session.client('ec2')
pricint_client = session.client('pricing')

bucket_name = SYSTEM_PREFIX+"-system-log"

contents = s3_client.list_objects(Bucket=bucket_name, Prefix='InterruptLog/')['Contents']

queue = []
totalOndemandCost = 0.0
totalSpotCost = 0.0
interrupted = 0

for key in contents:
    obj = (s3_client.get_object(Bucket=bucket_name, Key=key['Key'])['Body'].read()).decode('utf-8').split()
    if obj[1] == "created":
        queue.append((obj[0], obj[3], datetime.strptime(obj[5]+" "+obj[6], "%Y-%m-%d %H:%M:%S").replace(tzinfo=tzutc())+timedelta(hours=9)))
    elif obj[1] == "terminated":
        interrupted += 1
        instanceType, az, created_timestamp = queue.pop(0)
        if instanceType != obj[0]:
            print("Something Wrong!")
            exit(1)
        terminated_timestamp = datetime.strptime(obj[3]+" "+obj[4], "%Y-%m-%d %H:%M:%S").replace(tzinfo=tzutc())+timedelta(hours=9)
        client = boto3.client('pricing', region_name='us-east-1')
        response = client.get_products(
            ServiceCode='AmazonEC2',
            Filters=[
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'regionCode',
                    'Value': 'ap-northeast-2'
                },
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'instanceType',
                    'Value': instanceType
                },
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'tenancy',
                    'Value': 'Shared'
                },
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'preInstalledSw',
                    'Value': 'NA'
                },
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'capacitystatus',
                    'Value': 'Used'
                },
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'operatingSystem',
                    'Value': 'Linux'
                }
            ],
            MaxResults=100
        )
        priceHistory = ec2_client.describe_spot_price_history(
            InstanceTypes=[instanceType],
            AvailabilityZone=az,
            StartTime=created_timestamp,
            EndTime=terminated_timestamp
        )['SpotPriceHistory']
        priceHistory = priceHistory[::-1]
        for idx in range(len(priceHistory)):
            if priceHistory[idx]['Timestamp'] < created_timestamp:
                if idx+1 == len(priceHistory):
                    totalSpotCost += (terminated_timestamp-created_timestamp).total_seconds() / 3600.0 * float(priceHistory[idx]['SpotPrice'])
                    totalOndemandCost += (terminated_timestamp-created_timestamp).total_seconds() / 3600.0 * float(list(list(eval(response['PriceList'][0])['terms']['OnDemand'].values())[0]['priceDimensions'].values())[0]['pricePerUnit']['USD'])
                    break
                else:
                    continue
            if idx+1 == len(priceHistory):
                totalSpotCost += (terminated_timestamp-priceHistory[idx]['Timestamp']).total_seconds() / 3600.0 * float(priceHistory[idx]['SpotPrice'])
                totalOndemandCost += (terminated_timestamp-priceHistory[idx]['Timestamp']).total_seconds() / 3600.0 * float(list(list(eval(response['PriceList'][0])['terms']['OnDemand'].values())[0]['priceDimensions'].values())[0]['pricePerUnit']['USD'])
                break
            totalSpotCost += (priceHistory[idx+1]['Timestamp']-priceHistory[idx]['Timestamp']).total_seconds() / 3600.0 * float(priceHistory[idx]['SpotPrice'])
            totalOndemandCost += (priceHistory[idx+1]['Timestamp']-priceHistory[idx]['Timestamp']).total_seconds() / 3600.0 * float(list(list(eval(response['PriceList'][0])['terms']['OnDemand'].values())[0]['priceDimensions'].values())[0]['pricePerUnit']['USD'])
            

print(interrupted)
print(totalOndemandCost)
print(totalSpotCost)
