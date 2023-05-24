from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.chrome.service import Service
import boto3
from datetime import datetime
import time
import os
import sys
sys.path.append('../lambda/migrations/')
from lambda_function import system_off, init, migration, lambda_handler
sys.path.append('../lambda/')
from const_config import *

def get_jupyter_url():
    ssm_client = boto3.client('ssm', region_name='ap-northeast-2')
    NOW_INSTANCE_ID = ssm_client.get_parameter(Name="NOW_INSTANCE_ID", WithDecryption=True)['Parameter']['Value']
    ec2_client = boto3.client('ec2', region_name='ap-northeast-2')
    resp = ec2_client.describe_instances(InstanceIds=[NOW_INSTANCE_ID])
    
    JUPYTER = "http://"+resp['Reservations'][0]['Instances'][0]['PublicIpAddress']+"/tree"
    return JUPYTER


def get_notebook_url():
    ssm_client = boto3.client('ssm', region_name='ap-northeast-2')
    NOW_INSTANCE_ID = ssm_client.get_parameter(Name="NOW_INSTANCE_ID", WithDecryption=True)['Parameter']['Value']
    ec2_client = boto3.client('ec2', region_name='ap-northeast-2')
    resp = ec2_client.describe_instances(InstanceIds=[NOW_INSTANCE_ID])
    
    JUPYTER = "http://"+resp['Reservations'][0]['Instances'][0]['PublicIpAddress']+"/notebooks/TEST.ipynb"
    return JUPYTER


def MakeNewJupyterFile(driver):
    cnt=0
    while cnt < 1000:
        try:
            driver.get(get_jupyter_url())
            driver.implicitly_wait(10)
            break
        except:
            cnt+=1
            time.sleep(0.1)
    
    if cnt == 1000:
        return "0"

    buttonNew = driver.find_element(By.ID, 'new-dropdown-button').click()
    time.sleep(0.1)
    buttonPython = driver.find_element(By.ID, 'kernel-python3').click()
    time.sleep(0.1)

    driver.switch_to.window(driver.window_handles[1])
    driver.implicitly_wait(10)
    time.sleep(0.1)
    buttonTitle=None
    cnt=0
    while cnt < 1000:
        try:
            buttonTitle = driver.find_element(By.ID, 'notebook_name').click()
            break
        except:
            cnt+=1
            time.sleep(0.1)
    
    if cnt == 1000:
        return "1"
    
    time.sleep(0.1)
    inputTitle = driver.find_element(By.TAG_NAME, 'input')
    time.sleep(0.1)
    inputTitle.clear()
    time.sleep(0.1)
    inputTitle.send_keys("TEST")
    time.sleep(0.1)
    buttonRename = driver.find_element(By.CLASS_NAME, 'btn-primary').click()
    time.sleep(0.1)

    codeCells = driver.find_elements(By.CLASS_NAME, 'code_cell')
    time.sleep(0.1)
    inputCode = codeCells[0].find_element(By.CLASS_NAME, 'CodeMirror-lines')
    time.sleep(0.1)
    inputCode.click()
    time.sleep(0.1)
    driver.switch_to.active_element.send_keys('std = "Hello World!"')
    time.sleep(0.1)

    runCell = driver.find_element(By.ID, 'run_int').find_elements(By.TAG_NAME, 'button')[0]
    time.sleep(0.1)
    runCell.click()
    time.sleep(0.1)

    codeCells = driver.find_elements(By.CLASS_NAME, 'code_cell')
    time.sleep(0.1)
    inputCode = codeCells[1].find_element(By.CLASS_NAME, 'CodeMirror-lines')
    time.sleep(0.1)
    inputCode.click()
    time.sleep(0.1)
    driver.switch_to.active_element.send_keys('std')
    time.sleep(0.1)
    runCell.click()
    time.sleep(0.1)
    outputCode = codeCells[1].find_element(By.CLASS_NAME, 'output_text').text.strip()

    saveCell = driver.find_element(By.ID, 'save-notbook').find_elements(By.TAG_NAME, 'button')[0]
    time.sleep(0.1)
    saveCell.click()
    time.sleep(0.1)

    return outputCode

def Migrate():
    result = lambda_handler({}, {})
    return result['migrationTime']

def CheckMigratedJupyterFile(driver):
    cnt=0
    while cnt < 1000:
        try:
            driver.get(get_notebook_url())
            driver.implicitly_wait(10)
            break
        except:
            cnt+=1
            time.sleep(0.1)

    if cnt == 1000:
        return "0"

    time.sleep(0.1)
    driver.execute_script("window.onbeforeunload = null;")
    time.sleep(0.1)
    codeCells=None
    while True:
        try:
            codeCells = driver.find_elements(By.CLASS_NAME, 'code_cell')
            break
        except:
            time.sleep(0.1)
    time.sleep(0.1)
    inputCode = codeCells[1].find_element(By.CLASS_NAME, 'CodeMirror-lines')
    time.sleep(0.1)
    inputCode.click()
    time.sleep(0.1)
    runCell = driver.find_element(By.ID, 'run_int').find_elements(By.TAG_NAME, 'button')[0]
    time.sleep(0.1)
    runCell.click()
    time.sleep(0.1)
    outputs = codeCells[1].find_elements(By.CLASS_NAME, 'output_text')
    outputCodes = []
    for output in outputs:
        outputCodes.append(output.text.strip())
    return outputCodes


if __name__ == '__main__':
    CHROME_DRIVER = "./chromedriver/"
    CHROME_DRIVER_NAME = "chromedriver"
    bucket_name = SYSTEM_PREFIX + "-system-log"

    driver = webdriver.Chrome(service=Service(CHROME_DRIVER+CHROME_DRIVER_NAME))
    Workloads = [
        {"Vendor":"AWS", "InstanceType":"c4.xlarge", "Region":"ap-noertheast-2", "AZ":"ap-northeast-2a"}
    ]
    mig_to = [["c4.xlarge", "m4.xlarge"]]
    today = datetime.today()
    s3 = boto3.client('s3')
    print(f"{today.year}/{today.month}/{today.day}")
    print("Starting Test")
    for idx in range(len(Workloads)):
        print("Testing",idx)
        init_start = time.time()
        try:
            init(Workloads[idx])
        except:
            result = f"Attempt {idx+1}) INIT Fail\n" 
            s3.put_object(Bucket=bucket_name, Key=f'ExecuteTimeLog/{today.year}-{today.month}-{today.day}/workload{idx+1}/{i+1}.log', Body=result)
            print(result)
            continue

        init_end = time.time()
        time.sleep(1)
        output1 = MakeNewJupyterFile(driver)
        if output1 == "0":
            system_off()
            result = f"Attempt {i+1}) Fail\n" 
            s3.put_object(Bucket=bucket_name, Key=f'ExecuteTimeLog/{today.year}-{today.month}-{today.day}/workload{idx+1}/{i+1}.log', Body=result)
            print(result)
            continue
        elif output1 == "1":
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            system_off()
            result = f"Attempt {i+1}) Fail\n" 
            s3.put_object(Bucket=bucket_name, Key=f'ExecuteTimeLog/{today.year}-{today.month}-{today.day}/workload{idx+1}/{i+1}.log', Body=result)
            print(result)
            continue
        for i in range(100):
            test_start = time.time()
            migrate_time = None
            try:
                migrate_time = Migrate()
            except:
                result = f"Attempt {i+1}) Fail\n" 
                s3.put_object(Bucket=bucket_name, Key=f'ExecuteTimeLog/{today.year}-{today.month}-{today.day}/workload{idx+1}/{i+1}.log', Body=result)
                print(result)
                continue
            test_end = time.time()
            time.sleep(1)
            output2 = CheckMigratedJupyterFile(driver)
            if output2 == "0":
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                system_off()
                result = f"Attempt {i+1}) Fail\n" 
                s3.put_object(Bucket=bucket_name, Key=f'ExecuteTimeLog/{today.year}-{today.month}-{today.day}/workload{idx+1}/{i+1}.log', Body=result)
                print(result)
                continue
            end = time.time()
            result = f"[Attempt {i+1}] {mig_to[idx][i%2]}->{mig_to[idx][(i+1)%2]}) Init Time: {init_end - init_start}, Migrate Time: {migrate_time}, Migrate: {output1 in output2}, Total Time: {test_end - test_start}\n"
            s3.put_object(Bucket=bucket_name, Key=f'ExecuteTimeLog/{today.year}-{today.month}-{today.day}/workload{idx+1}/{i+1}.log', Body=result)
            print(result)
        driver.close()
        time.sleep(0.1)
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(0.1)
        system_off()
