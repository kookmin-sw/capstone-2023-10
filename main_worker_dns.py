import boto3

### 임시코드
import time

###

profile_name = 'kmubigdata'
region_name = 'us-west-2'

session = boto3.session.Session(profile_name=profile_name, region_name=region_name)
ec2_client = session.client('ec2')
ec2_resource = session.resource('ec2')
elb_client = session.client('elbv2')


def create_instances(instance_type, ami, key_name, max_count=1, min_count=1, userdata=''):
    new_instances = ec2_resource.create_instances(InstanceType=instance_type, ImageId=ami,
                                                  MaxCount=max_count, MinCount=min_count, KeyName=key_name,
                                                  SecurityGroups=['SSH'],
                                                  UserData=userdata
                                                  )

    return new_instances


def terminate_instances(instance_ids):
    ec2_client.terminate_instances(InstanceIds=instance_ids)

    return


def request_spot_instances(image_id, instance_type, key_name, az=None, instance_count=1, user_data=''):
    if az is None:
        new_instances = ec2_client.request_spot_instances(InstanceCount=instance_count,
                                                          LaunchSpecification={
                                                              'ImageId': image_id,
                                                              'InstanceType': instance_type,
                                                              'KeyName': key_name,
                                                              'UserData': user_data,
                                                          })
    else:
        new_instances = ec2_client.request_spot_instances(InstanceCount=instance_count,
                                                          LaunchSpecification={
                                                              'ImageId': image_id,
                                                              'InstanceType': instance_type,
                                                              'KeyName': key_name,
                                                              'UserData': user_data,
                                                              "Placement": {
                                                                  "AvailabilityZone": az
                                                              },
                                                          })

    return new_instances


def cancel_spot_instance_requests(spot_instance_request_ids):
    if type(spot_instance_request_ids) == list:
        ec2_client.cancel_spot_instance_requests(SpotInstanceRequestIds=spot_instance_request_ids)
    elif type(spot_instance_request_ids) == str:
        ec2_client.cancel_spot_instance_requests(SpotInstanceRequestIds=[spot_instance_request_ids])
    else:
        raise Exception("spot_instance_ids must be \'str\' or \'list\'")


def get_spot_instance_request_ids(spot_instances):
    spot_instance_request_ids = spot_instances.get('SpotInstanceRequests')

    ids = []
    for spot_instance in spot_instance_request_ids:
        spot_instance_request_id = spot_instance.get('SpotInstanceRequestId')
        ids.append(spot_instance_request_id)

    return ids


def describe_spot_instance_requests(spot_instance_request_ids):
    status = ec2_client.describe_spot_instance_requests(SpotInstanceRequestIds=spot_instance_request_ids)

    return status


def create_load_balancer(name, subnets, scheme='internet-facing', lb_type='network'):
    return elb_client.create_load_balancer(
        Name=name,
        Subnets=subnets,
        Scheme=scheme,
        Type=lb_type
    )


### test codes

## 온디맨드 인스턴스 생성 및 종료
# create_instances('t2.medium', 'ami-0ee93c90bc65c86c2', 'kh-oregon')
# terminate_instances(['i-06569c50a3236d0a9'])

## 스팟 인스턴스 생성 후 상태 확인 및 종료
# new_instances = request_spot_instances('ami-016b1f9568b08fffb', 'a1.medium', 'kh-oregon', 1, f'{region_name}c')
# spot_instance_request_ids = get_spot_instance_request_ids(new_instances)
# print(f'request spot instance ids : {spot_instance_request_ids}')
# print(new_instances)
# time.sleep(5)
# status = describe_spot_instance_requests(spot_instance_request_ids)
# print(status)
# time.sleep(15)
# cancel_spot_instance_requests(spot_instance_request_ids)
# print(f'canceled spot instance ids : {spot_instance_request_ids}')

