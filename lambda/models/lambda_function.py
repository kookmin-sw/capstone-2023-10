import boto3
import os
import sys
sys.path.append("/mnt/efs")
import pandas as pd
import numpy as np
import pickle
import json
import requests
import torch 
import torch.optim as optim
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from const_config import *

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = None
POOL_PATH = "./InstanceGroups.pkl"
MODEL_PATH = "./model_scaler/"
EWMA = 0.7
# Model parameter

input_size = 21 #number of features # 24
hidden_size = 100 #number of features in hidden state
num_layers = 3 # stacked lstm layers

output_size = 1 # output classes 


weekday_columns = ['weekday_Monday', 'weekday_Tuesday', 'weekday_Wednesday',
                'weekday_Thursday', 'weekday_Friday', 'weekday_Saturday', 'weekday_Sunday']

month_columns = ['month_1', 'month_2', 'month_3',
       'month_4', 'month_5', 'month_8', 'month_9', 'month_10', 'month_11',
       'month_12', 'month_6', 'month_7']

input_col = ['weekday_Friday', 'weekday_Monday', 'weekday_Saturday',
       'weekday_Sunday', 'weekday_Thursday', 'weekday_Tuesday',
       'weekday_Wednesday', 'total_sec', 'month_1', 'month_2', 'month_3',
       'month_4', 'month_5', 'month_8', 'month_9', 'month_10', 'month_11',
       'month_12', 'month_6', 'month_7', 'StabilityScore']

target_col = ['StabilityScore']

# Model Definition
class LSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out


## 모델 불러오기
def load_model(InstanceType, Region, AZ):
    global model
    model = LSTM(input_size, hidden_size, num_layers, output_size).to(device)
    model_name = ("_".join(InstanceType.split(".")))+"_"+("_".join(Region.split("-")))+"_"+("_".join(AZ.split("-")))
    model.load_state_dict(torch.load(MODEL_PATH+model_name+"/"+model_name+"_state.pt", map_location=torch.device(device)))


## 모델 풀 내에서 같은 풀에 속한 인스턴스타입 가져오기
def load_pool(instanceType):
    pools = pickle.load(open(POOL_PATH, "rb"))
    for i in range(len(pools)):
        if instanceType in pools[i]:
            poolSet = set()
            for pool in pools[i]:
                if pool.split('.')[1] == instanceType.split('.')[1]:
                    poolSet.add(pool)
            return poolSet
    print("Incorrect Instance Type")
    exit(1)


def load_data(pools):
    url = "https://be2laqr4wzyjma675v5mdzuizi0zxmjz.lambda-url.us-west-2.on.aws/?"+("&".join(pools))
    spot_data = requests.get(url).json()
    now = datetime.now()
    now = datetime.strptime(datetime.strftime(now, f"%Y-%m-%d %H:{now.minute//10*10}:00"), "%Y-%m-%d %H:%M:%S")
    start_timestamp = (now-timedelta(hours=1)+timedelta(minutes=10))
    timestamp = (now-timedelta(hours=1)+timedelta(minutes=10))
    idx = 0
    while idx < len(spot_data['time']):
        if datetime.strptime(spot_data['time'][idx], "%Y-%m-%d %H:%M:%S") < start_timestamp:
            spot_data['time'][idx] = datetime.strftime(start_timestamp, "%Y-%m-%d %H:%M:%S")
        elif datetime.strptime(spot_data['time'][idx], "%Y-%m-%d %H:%M:%S") > timestamp:
            while timestamp < datetime.strptime(spot_data['time'][idx], "%Y-%m-%d %H:%M:%S"):
                spot_data['AZ'].insert(idx, spot_data['AZ'][idx-1])
                spot_data['Region'].insert(idx, spot_data['Region'][idx-1])
                spot_data['InstanceType'].insert(idx, spot_data['InstanceType'][idx-1])
                spot_data['SpotPrice'].insert(idx, spot_data['SpotPrice'][idx-1])
                spot_data['SPS'].insert(idx, spot_data['SPS'][idx-1])
                spot_data['IF'].insert(idx, spot_data['IF'][idx-1])
                spot_data['time'].insert(idx, datetime.strftime(timestamp, "%Y-%m-%d %H:%M:%S"))
                timestamp = timestamp + timedelta(minutes=10)
                idx+=1
        elif datetime.strptime(spot_data['time'][idx], "%Y-%m-%d %H:%M:%S") < timestamp:
            while timestamp <= now:
                spot_data['AZ'].insert(idx, spot_data['AZ'][idx-1])
                spot_data['Region'].insert(idx, spot_data['Region'][idx-1])
                spot_data['InstanceType'].insert(idx, spot_data['InstanceType'][idx-1])
                spot_data['SpotPrice'].insert(idx, spot_data['SpotPrice'][idx-1])
                spot_data['SPS'].insert(idx, spot_data['SPS'][idx-1])
                spot_data['IF'].insert(idx, spot_data['IF'][idx-1])
                spot_data['time'].insert(idx, datetime.strftime(timestamp, "%Y-%m-%d %H:%M:%S"))
                timestamp = timestamp + timedelta(minutes=10)
                idx+=1
            timestamp = start_timestamp
        elif datetime.strptime(spot_data['time'][idx], "%Y-%m-%d %H:%M:%S") == timestamp:
            timestamp = timestamp + timedelta(minutes=10)
            idx+=1
    while timestamp <= now:
        spot_data['AZ'].append(spot_data['AZ'][-1])
        spot_data['Region'].append(spot_data['Region'][-1])
        spot_data['InstanceType'].append(spot_data['InstanceType'][-1])
        spot_data['SpotPrice'].append(spot_data['SpotPrice'][-1])
        spot_data['SPS'].append(spot_data['SPS'][-1])
        spot_data['IF'].append(spot_data['IF'][-1])
        spot_data['time'].append(datetime.strftime(timestamp, "%Y-%m-%d %H:%M:%S"))
        timestamp = timestamp + timedelta(minutes=10)
    
    data = pd.DataFrame(spot_data)
    data['time'] = pd.to_datetime(data['time'],utc=True)
    data['SPS'] = data['SPS'].astype('int')
    data['SpotPrice'] = data['SpotPrice'].astype('float32')
    data['IF'] = data['IF'].astype('float32')
    data['weekday'] = data['time'].apply(lambda x: datetime.strftime(x, '%A'))
    weekday_onehot = pd.get_dummies(data['weekday'], prefix='weekday')
    data = pd.concat([data, weekday_onehot], axis=1)
    for column in weekday_columns:
        if column not in data.columns:
            data[column] = False
        data[column] = data[column].astype('float32')
    data['total_sec'] = data['time'].apply(lambda x: x.hour * 3600 + x.minute * 60 + x.second)
    data['total_sec'] = data['total_sec'].astype('float32')
    month_onehot = pd.get_dummies(data['time'].dt.month, prefix='month')
    data = pd.concat([data, month_onehot], axis=1)
    for col_name in month_columns:
        if col_name not in data.columns:
            data[col_name] = False 
        if data[col_name].dtype == bool:
            data[col_name] = data[col_name].astype(np.float32)
    data['SpotPrice'] = data['SpotPrice'].replace(-1, method='ffill')
    data['SpotPrice'] = data['SpotPrice'].replace(0, method='ffill')
    data['SPS'] = data['SPS'].replace(-1, method='ffill')
    data['SPS'] = data['SPS'].replace(0, method='ffill')
    data['IF'] = data['IF'].replace(-1, method='ffill')
    data['IF'] = data['IF'].replace(0, method='ffill')
    s_scaler = pickle.load(open(MODEL_PATH+"/_scaler_make_stability_feature/sps_scaler.pickle", "rb"))
    i_scaler = pickle.load(open(MODEL_PATH+"/_scaler_make_stability_feature/if_scaler.pickle", "rb"))
    SPS_norm = s_scaler.transform(data[['SPS']])
    IF_norm = i_scaler.transform(data[['IF']])
    spot = data['SpotPrice'].to_numpy().reshape(-1, 1)
    data['StabilityScore'] = 5*(2*SPS_norm + IF_norm) - 2*spot
    data['StabilityScore'] = data['StabilityScore'].astype('float32')
    data = data.dropna()
    return data


## AZ 로드
def load_azs():
    ec2_client = boto3.client('ec2', region_name=AWS_REGION_NAME)
    response = ec2_client.describe_availability_zones()
    azs = []
    for zone in response['AvailabilityZones']:
        if zone['ZoneName'][-1] == 'a' or zone['ZoneName'][-1] == 'b':
            azs.append((zone['ZoneId'],zone['ZoneName']))
    return azs


## 각 인스턴스 타입들의 하루치 데이터 예측
def pred_until_tomorrow(data):
    data = data.reset_index(drop=True)
    load_model(data['InstanceType'][0], AWS_REGION_NAME, data['AZ'][0])
    model.eval()
    X_pd = data[input_col]
    StabilityScores = 0
    newTime = data['time'][len(data['time'])-1]
    model_name = ("_".join(data['InstanceType'][0].split(".")))+"_"+("_".join(AWS_REGION_NAME.split("-")))+"_"+("_".join(data['AZ'][0].split("-")))
    mm_scaler_y = pickle.load(open(f"{MODEL_PATH}/{model_name}/{model_name}_target_scaler.pickle", "rb"))
    for i in range(144):
        X = torch.tensor(np.array([np.array(X_pd.iloc[i:i+6])]))
        predict = model(X.to(device))
        pred = predict.data.detach().cpu().numpy()
        pred = mm_scaler_y.inverse_transform(pred)
        StabilityScores = EWMA * pred[0][0] + (1-EWMA) * StabilityScores
        newTime = newTime+timedelta(minutes=10)
        newWeekday = "weekday_"+datetime.strftime(newTime, "%A")
        newTotalSec = newTime.hour * 3600 + newTime.minute * 60 + newTime.second
        newMonth = "month_"+str(newTime.month)
        newDict = {}
        for col in input_col:
            if col == "total_sec":
                newDict[col] = [newTotalSec]
            elif col == "StabilityScore":
                newDict[col] = [pred[0][0]]
            elif col == newWeekday or col == newMonth:
                newDict[col] = True
            else:
                newDict[col] = False
        newDf = pd.DataFrame(newDict)
        newDf[weekday_columns] = newDf[weekday_columns].astype('float32')
        newDf[month_columns] = newDf[month_columns].astype('float32')
        newDf['total_sec'] = data['total_sec'].astype('float32')
        newDf['StabilityScore'] = data['StabilityScore'].astype('float32')
        X_pd = pd.concat([X_pd, newDf])
    return StabilityScores


## 1등 점수 인스턴스 타입을 SSM Parameter Store "NEXT_INSTANCE"에 등록
def lambda_handler(event, context):
    ssm_client = boto3.client('ssm', region_name=AWS_REGION_NAME)
    nowInstanceType = ssm_client.get_parameter(Name="NOW_INSTANCE", WithDecryption=False)['Parameter']['Value']
    nowAZ = ssm_client.get_parameter(Name="NOW_AZ", WithDecryption=False)['Parameter']['Value']
    pools = load_pool(nowInstanceType)
    data = load_data(pools)
    azs = load_azs()
    maxScore = 0
    bestInstance = None
    bestAz = None
    for it in pools:
        for az in azs:
            if it == nowInstanceType and az[1] == nowAZ:
                continue
            send_data = data[(data['InstanceType']==it) & (data['Region']==AWS_REGION_NAME) & (data['AZ']==az[0])]
            if len(send_data) > 0:
                score = pred_until_tomorrow(send_data)
                if score > maxScore:
                    maxScore = score
                    bestInstance = it
                    bestAz = az[1]
    print(bestInstance)
    print(bestAz)
    ssm_client.put_parameter(
        Name="NEXT_INSTANCE",
        Value=bestInstance,
        Type='String',
        Description="Instance Type to migrate",
        Overwrite=True
    )
    ssm_client.put_parameter(
        Name="NEXT_AZ",
        Value=bestAz,
        Type='String',
        Description="Instance AZ to migrate",
        Overwrite=True
    )
    return {"statusCode": 200, "message": "Complete"}


if __name__ == "__main__":
    lambda_handler({}, {})
