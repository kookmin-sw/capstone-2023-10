# AWS, Azure, GCP sdk import
import boto3
import azure.core
import google.cloud
# etc

# ==================================================================================
# ============================== Set Default Variance ==============================
# ==================================================================================
# << AWS >>
# Your Account Profile in Your AWS-CLI
AWS_PROFILE_NAME = "spotrank"
AWS_REGION_NAME = "us-west-2"
# Your Account's Red Hat AMI
AMI_ARM = "ami-08911268ee09cb08e"
AMI_INTEL = "ami-0dda7e535b65b6469"
# << GCP >>
# ...
# << AZURE >>
# ...
# ==================================================================================


def arch_to_ami(instanceType, ec2_client):
    archs = ec2_client.describe_instance_types(InstanceTypes=[instanceType])['InstanceTypes'][0]['ProcessorInfo']['SupportedArchitectures']
    print(archs)
    if 'arm64' in archs or 'arm64_mac' in archs:
        return AMI_ARM
    else:
        return AMI_INTEL


# Make New Instance to Migrate
def new_instance(instanceInfo, subnetInfo):
    vendor = instanceInfo['Vendor']

    requestResponse = {"Vendor" : vendor, "Response" : None}
    try:
        if vendor == 'AWS':
            # Request AWS Spot Instance in AWS Subnet
            instanceType = instanceInfo['InstanceType']
            az = instanceInfo['AZ']
            region = instanceInfo['Region']

            session = boto3.session.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION_NAME)
            ec2_client = session.client('ec2')
            waiter = ec2_client.get_waiter('spot_instance_request_fulfilled')
            imageId = arch_to_ami(instanceType, ec2_client)

            SubnetId = subnetInfo['SubnetId']
            requestResponse['Response'] = ec2_client.request_spot_instances(
                InstanceCount=1,
                LaunchSpecification={
                    'ImageId': imageId,
                    'InstanceType':instanceType,
                    'Placement': {'AvailabilityZone':az},
                    'SubnetId':subnetId,
                    'Userdata':''
                }
            )
            pass
        elif vendor == 'AZURE':
            # Request AZURE Spot VM in AZURE Subnet
            pass
        elif vendor == 'GCP':
            # Request GCP Spot VM in GCP Subnet
            pass
        else:
            print("Info is Incorrect")
    except Exception as e:
        print(e)
    
    return requestResponse


# Migrate to New Instance from Source Instance
def migration(newInstanceInfo, sourceInstanceInfo, subnetInfo):
    # Checkpointing from Source Instance
    # Send Checkpointing Execution Line to Source Instance
    sourceVendor = sourceInstanceInfo['Vendor']
    try:
        if sourceVendor == 'AWS':
            session = boto3.session.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION_NAME)
            ssm_client = session.client('ssm')
            instanceId = sourceInstanceInfo['InstanceId']
            response = ssm_client.send_command(
                InstanceIds=[instanceId,],
                DocumentName="AWS-RunShellScript",
                Parameters={'commands':['mkdir test', 'mkdir test2']}
            )
            pass
        elif sourceVendor == 'AZURE':
            pass
        elif sourceVendor == 'GCP':
            pass
        else:
            print("Info is Incorrect")
    except Exception as e:
        print(e)

    # Request New Spot Instance
    response = new_instance(newInstanceInfo, subnetInfo)

    # Restoring to New Instance
    # Send Restoring Execution Line to New Instance
    newVendor = newInstanceInfo['Vendor']
    try:
        if newVendor == 'AWS':
            pass
        elif newVendor == 'AZURE':
            pass
        elif newVendor == 'GCP':
            pass
        else:
            print("Info is Incorrect")
    except Exception as e:
        print(e)

