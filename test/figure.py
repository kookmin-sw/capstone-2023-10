import matplotlib.pyplot as plt
import boto3

# Create an S3 client
s3 = boto3.client('s3')

# Set the bucket name and file key
bucket_name = 'jupyter-migration'
folder_key = 'TestLog/2023-4-29/'

migrationTry = [['', ''], ['', '']]
migrationTime = [[[], []], [[], []]]
migrationState = [[{"True":0, "False":0}, {"True":0, "False":0}], [{"True":0, "False":0}, {"True":0, "False":0}]]

for i in range(1, 3):
    for j in range(1, 101):
        key = folder_key + f"workload{i}/{j}.log"

        # Download the file from S3
        response = s3.get_object(Bucket=bucket_name, Key=key)

        # Read the contents of the file into a variable
        data = response['Body'].read().decode('utf-8')
        strings = data.split(",")

        migrationTry[i-1][(j+1)%2] = data.split(" ")[2][:-1]
        migrationTime[i-1][(j+1)%2].append(float(strings[1].split(":")[1].strip()))
        migrationState[i-1][(j+1)%2][strings[2].split(":")[1].strip()] += 1

print("Migration Success/Fail Counts")
print(f"[workload1] {migrationTry[0][0]}) Success: {migrationState[0][0]['True']}, Fail: {migrationState[0][0]['False']}")
print(f"[workload1] {migrationTry[0][1]}) Success: {migrationState[0][1]['True']}, Fail: {migrationState[0][1]['False']}")
print(f"[workload2] {migrationTry[1][0]}) Success: {migrationState[1][0]['True']}, Fail: {migrationState[1][0]['False']}")
print(f"[workload2] {migrationTry[1][1]}) Success: {migrationState[1][1]['True']}, Fail: {migrationState[1][1]['False']}")

print("Migration Time Performance")
print(f"[workload1] {migrationTry[0][0]}) Min: {min(migrationTime[0][0])}, Max: {max(migrationTime[0][0])}, Avg: {sum(migrationTime[0][0])/len(migrationTime[0][0])}")
print(f"[workload1] {migrationTry[0][1]}) Min: {min(migrationTime[0][1])}, Max: {max(migrationTime[0][1])}, Avg: {sum(migrationTime[0][1])/len(migrationTime[0][1])}")
print(f"[workload2] {migrationTry[1][0]}) Min: {min(migrationTime[1][0])}, Max: {max(migrationTime[1][0])}, Avg: {sum(migrationTime[1][0])/len(migrationTime[1][0])}")
print(f"[workload2] {migrationTry[1][1]}) Min: {min(migrationTime[1][1])}, Max: {max(migrationTime[1][1])}, Avg: {sum(migrationTime[1][0])/len(migrationTime[1][1])}")
