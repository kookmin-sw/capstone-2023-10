# AWS, Azure, GCP sdk import
import boto3
import azure.core
import google.cloud
# etc

# Set Default Variance
# ...


# Make New Instance to Migrate
def new_instance(instanceInfo, subnetInfo):
    vendor = instanceInfo['Vendor']
    instanceType = instanceInfo['InstanceType']

    requestResponse = {"Vendor" : vendor, "Response" : None}
    try:
        if vendor == 'AWS':
            # Request AWS Spot Instance in AWS Subnet
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
def migration(newInstanceInfo, sourceInstanceInfo):
    # Checkpointing from Source Instance
    # Send Checkpointing Execution Line to Source Instance
    sourceVendor = sourceInstanceInfo['Vendor']
    try:
        if sourceVendor == 'AWS':
            pass
        elif sourceVendor == 'AZURE':
            pass
        elif sourceVendor == 'GCP':
            pass
        else:
            print("Info is Incorrect")
    except Exception as e:
        print(e)

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

