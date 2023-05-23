import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler

import datetime


def load_data(start_date):
    print("data loading...")
    aws_df_raw = pd.read_csv("../data/aws_data_total.csv")
    aws_df_rec = pd.read_csv("../data/aws_data_rec.csv")

    aws_df_raw['time'] = pd.to_datetime(aws_df_raw['time'], utc=True)
    aws_df_rec['time'] = pd.to_datetime(aws_df_rec['time'], utc=True)

    start_date = start_date
    aws_df_raw = aws_df_raw[aws_df_raw['time'] >= start_date]

    aws_df = pd.concat([aws_df_raw, aws_df_rec])
    
    print("load data complete!")
    return aws_df


def make_dfs_list(aws_df):
    print("creating dataframe list.....")
    instance_list = ['c4.2xlarge', 'c4.4xlarge', 'c4.large', 'c4.xlarge', 'd2.2xlarge', 'd2.4xlarge', 'd2.xlarge',
                     'm4.2xlarge', 'm4.4xlarge', 'm4.large', 'm4.xlarge', 't2.2xlarge', 't2.xlarge']
    az_list = ['apne2-az1', 'apne2-az2', 'apne2-az3']

    group_A_dfs = []
    for instance in instance_list:
        for az in az_list:
            temp_df = aws_df[(aws_df['InstanceType'] == instance) & (aws_df['Region'] == 'ap-northeast-2') &
                             (aws_df['AZ'] == az)]
            if len(temp_df) > 0:
                group_A_dfs.append(temp_df)
    
    print("dataframe list creation complete!")
    return group_A_dfs


def preprocess_data(group_A_dfs, instance_num):
    df1 = group_A_dfs[instance_num]
    
    df1 = df1.groupby(["InstanceType"])['time'].apply(lambda x:pd. date_range(start=x.min() , end=x.max(), freq="10min")).explode ().reset_index().merge(df1, how='left').ffill()


    df1['SpotPrice'] = df1['SpotPrice'].replace(-1, method='ffill')
    df1['SpotPrice'] = df1['SpotPrice'].replace(0, method='ffill')
    df1['SPS'] = df1['SPS'].replace(-1, method='ffill')
    df1['SPS'] = df1['SPS'].replace(0, method='ffill')
    df1['IF'] = df1['IF'].replace(-1, method='ffill')
    df1['IF'] = df1['IF'].replace(0, method='ffill')


    df1['weekday'] = df1['time'].apply(lambda x: datetime.datetime.strftime(x, '%A'))


    # One-hot Encoding 
    weekday_onehot = pd.get_dummies(df1['weekday'], prefix='weekday')
    df1 = pd.concat([df1, weekday_onehot], axis=1)


    weekday_columns = ['weekday_Monday', 'weekday_Tuesday', 'weekday_Wednesday',
                    'weekday_Thursday', 'weekday_Friday', 'weekday_Saturday', 'weekday_Sunday']

    for column in weekday_columns:
        df1[column] = df1[column].astype('float32')

    train_total_seconds = df1['time'].apply(lambda x: x.hour * 3600 + x.minute * 60 + x.second)


    df1['total_sec'] = train_total_seconds


    # 월에 대한 One-hot encoding 구하기
    months = pd.get_dummies(df1['time'].dt.month, prefix='month')

    df1 = pd.concat([df1, months], axis=1)


    for i in range(1, 13):
        col_name = f"month_{i}"
        if col_name not in df1.columns:
            df1[col_name] = False 
            
        if df1[col_name].dtype == bool:
            df1[col_name] = df1[col_name].astype(np.float32)

    SPS_scaler = MinMaxScaler(feature_range=(1, 10))
    s_scaler = SPS_scaler.fit(group_A_dfs[1][['SPS']])      # 모든 sps 값이 포함된 df

    IF_scaler = MinMaxScaler(feature_range=(1, 10))
    i_scaler = IF_scaler.fit(group_A_dfs[3][['IF']])        # 모든 IF 값이 포함된 df

    return df1, s_scaler, i_scaler




def calculate_stability_score(df1, s_scaler, i_scaler):
    
    SPS_norm = s_scaler.transform(df1[['SPS']])

    IF_norm = i_scaler.transform(df1[['IF']])

    spot = df1['SpotPrice'].to_numpy().reshape(-1, 1)


    # 안정성 점수 계산
    df1['Stability_score'] = 5*(2*SPS_norm + IF_norm) - 2*spot      # input
    df1['Stability_score_label'] = df1['Stability_score']           # output 
    
    return df1