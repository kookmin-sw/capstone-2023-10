from preprocess import *
from prepare_data import *
from train import train

data = load_data('2022-08-25')

df_list = make_dfs_list(data)
df1, s_scaler, i_scaler = preprocess_data(df_list, 1)
df1 = calculate_stability_score(df1, s_scaler, i_scaler)
df1, input_col, target_col, y_scaler = normalize_features(df1)


split_date = '2023-05-16'
train_df, test_df = split_train_test(df1, split_date)

train_X = train_df[input_col]
train_y = train_df[target_col]
X_train, y_train = make_dataset(train_X, train_y, 6)

model = train(X_train, y_train)
