from sklearn.preprocessing import MinMaxScaler, StandardScaler
import numpy as np


def normalize_features(df1):
    mm_scaler_x = MinMaxScaler()
    mm_scaler_y = MinMaxScaler()

    input_col = ['weekday_Friday', 'weekday_Monday', 'weekday_Saturday',
                 'weekday_Sunday', 'weekday_Thursday', 'weekday_Tuesday',
                 'weekday_Wednesday', 'total_sec', 'month_1', 'month_2', 'month_3',
                 'month_4', 'month_5', 'month_8', 'month_9', 'month_10', 'month_11',
                 'month_12', 'month_6', 'month_7', 'Stability_score']

    target_col = ['Stability_score_label']

    x_scaled = mm_scaler_x.fit_transform(df1[input_col])
    y_scaled = mm_scaler_y.fit_transform(df1[target_col])

    df1[input_col] = x_scaled
    df1[target_col] = y_scaled

    return df1, input_col, target_col, mm_scaler_y



def split_train_test(df1, split_date):
    train_df = df1[df1['time'] < split_date]
    test_df = df1[df1['time'] >= split_date]
    return train_df, test_df



def make_dataset(data, label, window_size):
    feature_list = []
    label_list = []
    for i in range(len(data) - window_size):
        feature_list.append(np.array(data.iloc[i:i + window_size]))
        label_list.append(np.array(label.iloc[i + window_size]))
    return np.array(feature_list), np.array(label_list)