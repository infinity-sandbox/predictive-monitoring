import os
import pandas as pd
import mysql.connector
from mysql.connector import Error
import sys
from dotenv import load_dotenv
import os
from server.logs.loggers.logger import logger_config
import pandas as pd
logger = logger_config(__name__)
load_dotenv()
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator
import tensorflow as tf
from datetime import datetime, timedelta
import random as rd



def connect_fetch_db():
    try:
        # Database connection details
        config = {
            'user': os.getenv('MYSQL_DB_USER'),
            'password': os.getenv('MYSQL_DB_PASSWORD'),
            'host': os.getenv('MYSQL_DB_HOST'),
            'database': os.getenv('MYSQL_DB'),
            'port': os.getenv('MYSQL_DB_PORT', '3306')
        }

        # Establish the connection
        connection = mysql.connector.connect(**config)
        logger.info("Connection to MySQL DB successful")
        # Query to read data
        query = "SELECT * FROM oshistory_detail;"

        # Read the data into a pandas DataFrame
        raw_data = pd.read_sql(query, connection)

        # Close the connection
        connection.close()
        logger.debug(f"Connection to MySQL DB closed")
        return raw_data
    except mysql.connector.Error as e:
        logger.error(f"Error connecting to MySQL DB: {e}")
        raise  # Raise the exception to handle it in the calling code

    except Exception as ex:
        logger.error(f"Unexpected error: {ex}")
        raise  # Raise the exception to handle it in the calling code

def data_cleaning(raw_data: pd.DataFrame, ts=False):
    main_data = raw_data[raw_data.server_name == 'abels-mbp.zte.com.cn_sa']
    data = main_data.copy()
    #
    data['Date'] = pd.to_datetime(data['dt'])
    data.set_index(data['Date'], inplace = True)
    if ts:
        cols = ['Date', 'rl', 'session_id', 'server_name', 'is_windows', 'dt']
    else:
        cols = ["Date", "rl","session_id", "server_name","process_queue_len","disk_transfers","context_switches","is_windows","server_id"]
    data.drop(cols, axis = 1, inplace = True)
    #
    Total = data.isnull().sum().sort_values(ascending = False)          
    Percent = (data.isnull().sum()*100/data.isnull().count()).sort_values(ascending = False)   
    missing_data = pd.concat([Total, Percent], axis = 1, keys = ['Total', 'Percentage of Missing Values'])   
    logger.debug(f"Missing data: {missing_data}")
    #
    logger.info(f"Data cleaning complete")
    logger.info(f"Data shape: {data.shape}, Data columns: {data.columns}, Data head: {data.head()}")
    return data

def feature_selection(clean_data: pd.DataFrame):
    clean_data['dt'] = pd.to_datetime(clean_data['dt'])
    clean_data.set_index('dt', inplace=True)
    #
    clean_data.fillna(method='ffill', inplace=True)  # forward fill
    clean_data.dropna(inplace=True)  # drop missing values
    logger.info(f"NULL VALUES: {clean_data.isnull().sum()}")
    logger.info(f"{clean_data.info()}")
    #
    scaler = MinMaxScaler()
    normalized_data = scaler.fit_transform(clean_data)
    normalized_df = pd.DataFrame(normalized_data, columns=clean_data.columns, index=clean_data.index)
    logger.info(f"Normalized Data: {normalized_df}")
    logger.info(f"NORMALIZED SHAPE: {normalized_df.shape}, DATA SHAPE: {clean_data.shape}")
    #
    X = normalized_df.drop(columns=['cpuusedpercent'])
    y = normalized_df['cpuusedpercent']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    rf_regressor = RandomForestRegressor(random_state=42)
    rf_regressor.fit(X_train, y_train)
    y_pred = rf_regressor.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    logger.info(f'Mean Squared Error: {mse}')
    feature_importances = pd.Series(rf_regressor.feature_importances_, index=X.columns)
    feature_importances_sorted = feature_importances.sort_values(ascending=False)
    logger.info(f"FEATURE IMPORTANCE SORTED: {feature_importances_sorted}")
    importance_values = feature_importances_sorted.values.tolist()
    feature_names = feature_importances_sorted.index.tolist()
    feature_importances_dict = {
        'features': list(feature_names),
        'importance': list(importance_values)
    }
    logger.info(f"FEATURE IMPORTANCE DICT: {feature_importances_dict}")
    return feature_importances_dict, mse

def tseries(data: pd.DataFrame, input_datetime: datetime):
    y_minutes = data['cpuusedpercent'].resample('T').mean()  # 'T' stands for minutes
    logger.debug("Head of resampled data (minutes): ")
    logger.debug(y_minutes.head())
    columns_to_keep = ['cpuusedpercent']  # List of columns to keep
    data = data[['cpuusedpercent']].copy()
    logger.debug(f"Verify Result: {data.head()}")
    split_date = '2024-07-07 00:00:00'
    train = data[data.index < split_date]
    test = data[(data.index >= split_date) & (data.index < '2024-07-07 06:00:00')]  # Adjusted for a smaller test set
    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(np.array(train).reshape(-1, 1))
    window_size = 60
    train_generator = TimeseriesGenerator(train_scaled, train_scaled,
                                        length=window_size, batch_size=1)
    for i in range(len(train_generator)):
        X, y = train_generator[i]
    logger.debug(f'AI Batch {train_generator}:')
    model = tf.keras.models.Sequential([
            tf.keras.layers.LSTM(100, input_shape = (window_size, 1), return_sequences = True),
            tf.keras.layers.LSTM(50, return_sequences = True),
            tf.keras.layers.LSTM(10),
            tf.keras.layers.Dense(64, activation ='relu'),
            tf.keras.layers.Dense(32, activation ='relu'),
            tf.keras.layers.Dense(1)
    ])
    model.compile(loss = 'mse', optimizer = 'adam')
    logger.debug(f"Model Summary: \n{model.summary()}")
    rd.seed(10)
    np.random.seed(150)
    tf.random.set_seed(150)
    history = model.fit(train_generator, epochs = 5)
    logger.debug(f"Model History: \n{history}")
    lstm_predictions_scaled = []
    batch = train_scaled[-window_size:]
    current_batch = batch.reshape((1, window_size, 1))
    for i in range(len(test)):
        lstm_pred = model.predict(current_batch)[0]
        #Appending the next month forecast to the forecasts list:
        lstm_predictions_scaled.append(lstm_pred) 
        #Appending the next month forecast to the current batch and 
        #removing the earliest data point in its place to preserve the window size:
        current_batch = np.append(current_batch[:, 1:, :], [[lstm_pred]], axis = 1)
    
    #Since the original values were scaled before training the model, we need to 
    #inverse scale the forecast in order to get the forecast for the original data. 
    lstm_predictions = scaler.inverse_transform(lstm_predictions_scaled)
    logger.info(f"Shape of lstm_predictions: {lstm_predictions.shape}")
    lstm_preds = pd.DataFrame(data=[lstm_predictions[i][0] for i in range(len(lstm_predictions))], columns=['LSTM Forecast'], index=test.index)
    last_lstm_pred_value = lstm_preds.iloc[-1]['LSTM Forecast']
    logger.info(f"lstm_preds: {lstm_preds}")
    logger.info(f"Last LSTM Prediction: {last_lstm_pred_value}")
    try:
        input_datetime1 = input_datetime + timedelta(seconds=0)
        input_data = pd.DataFrame(index=[input_datetime1], columns=['cpuusedpercent'])
        input_data['cpuusedpercent'] = np.nan
        return last_lstm_pred_value
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
    









# Assuming lstm_preds DataFrame is already defined
    # dates = lstm_preds.index.strftime('%Y-%m-%d %H:%M').tolist()
    # values = lstm_preds['LSTM Forecast'].tolist()  # Extract 'LSTM Forecast' column values to list
    # forecast_data = {
    #     'date': dates,
    #     'value': values
    # }
    # logger.debug(f"FORECASTED DATA: \n{forecast_data}")
    # return forecast_data







    




if __name__ == '__main__':
    raw_data = connect_fetch_db()
    cleaned_data = data_cleaning(raw_data, ts=True)
    # features = feature_selection(cleaned_data)
    out = tseries(cleaned_data)