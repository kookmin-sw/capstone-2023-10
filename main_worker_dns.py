import boto3

region_name = 'ap-northeast-2'  # seoul
profile_name = 'kmubigdata'

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

