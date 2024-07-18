from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.statespace.varmax import VARMAX
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator # type: ignore
import tensorflow as tf
from datetime import datetime, timedelta
import random as rd
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from tqdm import tqdm_notebook
from itertools import product
import matplotlib.pyplot as plt
import statsmodels.api as sm
import numpy as np
import warnings, os
import matplotlib.pyplot as plt
import mysql.connector
from mysql.connector import Error
import sys
from dotenv import load_dotenv
import math 
from statistics import mean
warnings.filterwarnings('ignore')
load_dotenv()
from logs.loggers.logger import logger_config
logger = logger_config(__name__)


class MultivariateTimeSeries:
    @staticmethod
    def connect_db():
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
            # Query to read data
            query = "SELECT * FROM oshistory_detail;"
            # Read the data into a pandas DataFrame
            raw_data = pd.read_sql(query, connection)
            # Close the connection
            connection.close()
            logger.info('Data fetched successfully')
            return raw_data
        except mysql.connector.Error as e:
            logger.error(f'Error: {str(e)}')
            raise  # Raise the exception to handle it in the calling code
        except Exception as ex:
            logger.error(f'Error: {str(ex)}')
            raise  # Raise the exception to handle it in the calling code

    @staticmethod
    def data_clean():
        df = MultivariateTimeSeries.connect_db()
        df = df.drop_duplicates(subset='dt', keep='first')
        df.set_index(df['dt'], inplace = True)
        df = df.resample('T').ffill()
        df.index.freq = 'T'
        # Calculate the percentage of missing values
        missing_percentage = df.isnull().mean() * 100
        columns_to_drop = missing_percentage[missing_percentage > 80].index
        # Drop these columns from the DataFrame
        data_cleaned = df.drop(columns=columns_to_drop)
        # Handle columns with less than 80% missing values
        for column in data_cleaned.columns:
            if data_cleaned[column].dtype == 'object':
                # For object (categorical) columns, fill with the mode
                mode_value = data_cleaned[column].mode()[0]
                data_cleaned[column].fillna(mode_value, inplace=True)
            elif data_cleaned[column].dtype == 'int64':
                # For int64 (integer) columns, fill with the mean
                mean_value = data_cleaned[column].mean()
                data_cleaned[column].fillna(mean_value, inplace=True)
            elif data_cleaned[column].dtype == 'datetime64[ns]':
                # For datetime64 columns, forward fill
                data_cleaned[column].fillna(method='ffill', inplace=True)
                # Alternatively, you can use backward fill with: data_cleaned[column].fillna(method='bfill', inplace=True)
        logger.info('Data cleaned successfully')
        return data_cleaned

    @staticmethod
    def ml_process():
        data_cleaned = MultivariateTimeSeries.data_clean()
        # Initialize OneHotEncoder without sparse parameter
        encoder = OneHotEncoder()
        # Initialize DataFrame to store encoded features
        encoded_features = pd.DataFrame(index=data_cleaned.index)  # Start with index from data_cleaned
        # Loop through columns
        for column in data_cleaned.columns:
            if data_cleaned[column].dtype == 'object':
                # Encode categorical (object) columns
                encoded_column = encoder.fit_transform(data_cleaned[[column]])
                # Convert sparse matrix to DataFrame
                encoded_column_df = pd.DataFrame(encoded_column.toarray(), 
                                                 columns=encoder.get_feature_names_out([column]), index=data_cleaned.index)
                encoded_features = pd.concat([encoded_features, encoded_column_df], axis=1)
            elif data_cleaned[column].dtype == 'int64' or data_cleaned[column].dtype == 'float64':
                # Use numerical columns as-is
                encoded_features = pd.concat([encoded_features, data_cleaned[[column]]], axis=1)
            elif data_cleaned[column].dtype == 'datetime64[ns]':
                # Forward fill datetime columns
                data_cleaned[column].fillna(method='ffill', inplace=True)
                encoded_features = pd.concat([encoded_features, data_cleaned[[column]]], axis=1)
        # Assuming 'data' is your DataFrame
        columns_to_drop = ['dt', 'rl', 'session_id']  # List of column names to drop
        # Drop the specified columns
        encoded_features.drop(columns=columns_to_drop)
        numerical_cols = encoded_features.select_dtypes(include=['int64', 'float64']).columns
        encoded_features[numerical_cols] = encoded_features[numerical_cols].astype(float)
        logger.info('Data encoded successfully')
        return encoded_features

    @staticmethod
    def casual(feature1: str, feature2: str):
        macro_data = MultivariateTimeSeries.ml_process()
        ad_fuller_result_1 = adfuller(macro_data[feature1].diff()[1:])
        logger.info(f'ADF Statistic: {ad_fuller_result_1[0]}')
        logger.info(f'p-value: {ad_fuller_result_1[1]}')
        logger.debug('\n---------------------\n')
        ad_fuller_result_2 = adfuller(macro_data[feature2].diff()[1:])
        logger.info(f'ADF Statistic: {ad_fuller_result_2[0]}')
        logger.info(f'p-value: {ad_fuller_result_2[1]}')
        ####
        logger.info(f'{feature1} causes {feature2}?\n')
        logger.debug('------------------')
        granger_1 = grangercausalitytests(macro_data[[feature1, feature2]], 4)
        logger.info(f'{feature2} causes {feature1}?\n')
        logger.debug('------------------')
        granger_2 = grangercausalitytests(macro_data[[feature2, feature1]], 4)
        
    @staticmethod
    def validation_ml(features: list, n_forecast: int = 12):
        macro_data = MultivariateTimeSeries.ml_process()
        macro_data = macro_data[features]
        logger.debug(macro_data.shape)
        train_df=macro_data[:-12]
        test_df=macro_data[-12:]
        model = VAR(train_df.diff()[1:])
        sorted_order=model.select_order(maxlags=30)
        logger.info(sorted_order.summary())
        var_model = VARMAX(train_df, order=(4,0),enforce_stationarity= True)
        fitted_model = var_model.fit(disp=False)
        logger.info(fitted_model.summary())
        predict = fitted_model.get_prediction(start=len(train_df),end=len(train_df) + n_forecast-1)
        predictions=predict.predicted_mean
        pcols = []
        for i in range(len(features)):
            pcols.append(str(features[i]) + "_predicted")
        predictions.columns=pcols
        test_vs_pred=pd.concat([test_df,predictions],axis=1)
        # Plotting
        fig, ax = plt.subplots(figsize=(12, 5))
        test_vs_pred.plot(ax=ax)
        ax.set_title('VARMAX Model Predictions vs Actual Data')
        ax.set_xlabel('Time')
        ax.set_ylabel('Value')
        plt.tight_layout()
        # Show the plot
        plt.show()
        return predictions, test_df, features
        
        
    @staticmethod
    def sklearn_metrics(predictions, test_df, features: list):    
        for i in range(len(features)):
            rmse=math.sqrt(mean_squared_error(predictions[str(features[i]) + "_predicted"],test_df[features[i]]))
            logger.info('Mean value of {} is : {}. Root Mean Squared Error is :{}'.format(features[i],mean(test_df[features[i]]),rmse))
        return rmse

        
    @staticmethod
    def forcast(features: list, plot=False):
        macro_data = MultivariateTimeSeries.ml_process()
        macro_data = macro_data[features]
        logger.info(macro_data.shape)
        train_df=macro_data[:-12]
        test_df=macro_data[-12:]
        #
        model = VAR(train_df.diff()[1:])
        sorted_order=model.select_order(maxlags=20)
        logger.info(sorted_order.summary())
        #
        var_model = VARMAX(train_df, order=(4,0),enforce_stationarity= True)
        fitted_model = var_model.fit(disp=False)
        logger.info(fitted_model.summary())
        # Forecasting future 7 days
        n_forecast = 1 * 24 * 60  # Number of minutes in 7 days (assuming minutely data)
        predict = fitted_model.get_prediction(start=len(train_df), end=len(train_df) + n_forecast - 1)
        # Extracting predicted values
        predictions = predict.predicted_mean
        if plot:
            for x in features:
                fig, ax = plt.subplots(figsize=(12, 5))
                ax.plot(train_df.index, train_df[x], label='Train Data (' + x + ')', color='blue')
                ax.plot(test_df.index, test_df[x], label='Test Data (' + x + ')', color='green')
                ax.plot(predictions.index, predictions[x], label='Predicted Data (' + x + ')', color='red')
                ax.legend()
                plt.title('VARMAX Model Predictions vs Actual Data (' + x + ')')
                plt.xlabel('Time')
                plt.ylabel('Value')
                plt.show()
        logger.info(predictions)
        return predictions
            

if __name__ == '__main__':
    # MultivariateTimeSeries.ml_process()
    
    columns = ['cpuusedpercent', 'cpu_user']
    # MultivariateTimeSeries.casual('cpuusedpercent', 'cpu_user')
    
    # ['server_name_abels-mbp.zte.com.cn_sa', 'physical_mem_free',
    #    'page_file_usage', 'processes', 'tcp_connections', 'cpu_user',
    #    'cpu_sys', 'is_windows_N', 'sys_load', 'swap_mem_usage', 'cpu_io',
    #    'cpu_max', 'cpu_nice', 'swap_pagein', 'swap_pageout', 'server_id',
    #    'cpuusedpercent', 'mem_used', 'mem_used_per']
      
    # predictions, test_df, features = MultivariateTimeSeries.validation_ml(features=columns)
    # MultivariateTimeSeries.sklearn_metrics(predictions, test_df, features=features)
    forcast = MultivariateTimeSeries.forcast(features=columns, plot=True)
    
