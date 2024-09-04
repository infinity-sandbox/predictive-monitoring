import asyncio
from fastapi import HTTPException
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.statespace.varmax import VARMAX
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import random as rd
import pandas as pd
from typing import Dict, List, Any
from sklearn.preprocessing import OneHotEncoder
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
from app.services.user_service import UserService
from app.models.parameters import ForecastResponse
from app.services.langchain_service import LangchainAIService
warnings.filterwarnings('ignore')
load_dotenv()
from logs.loggers.logger import logger_config
logger = logger_config(__name__)
import signal
from app.core.config import settings
from utils.thresholds import oshistory_detail_thresholds


class MultivariateTimeSeries:
    @staticmethod
    def connect_db():
        try:
            # Database connection details
            config = {
                'user': settings.MYSQL_DB_USER,
                'password': settings.MYSQL_DB_PASSWORD,
                'host': settings.MYSQL_DB_HOST,
                'database': settings.MYSQL_DB,
                'port': settings.MYSQL_DB_PORT
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
                # Alternatively, you can use backward fill with: data_cleaned[column]. \
                # fillna(method='bfill', inplace=True)
        logger.info('Data cleaned successfully')
        return data_cleaned

    @staticmethod
    def ml_process():
        data_cleaned = MultivariateTimeSeries.data_clean()
        # Initialize OneHotEncoder without sparse parameter
        encoder = OneHotEncoder()
        # Initialize DataFrame to store encoded features
        encoded_features = pd.DataFrame(index=data_cleaned.index)  
        # Start with index from data_cleaned
        # Loop through columns
        for column in data_cleaned.columns:
            if data_cleaned[column].dtype == 'object':
                # Encode categorical (object) columns
                encoded_column = encoder.fit_transform(data_cleaned[[column]])
                # Convert sparse matrix to DataFrame
                encoded_column_df = pd.DataFrame(encoded_column.toarray(), 
                                                 columns=encoder.get_feature_names_out([column]), 
                                                 index=data_cleaned.index)
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
        encoded_features.drop(columns=columns_to_drop, inplace=True)
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
        predict = fitted_model.get_prediction(
            start=len(train_df),end=len(train_df) + n_forecast-1)
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
        for i in range(len(features)):
            rmse=math.sqrt(mean_squared_error(
                predictions[str(features[i]) + "_predicted"],test_df[features[i]]))
            logger.info('Mean value of {} is : {}. Root Mean Squared Error is :{}'.format(
                features[i],mean(test_df[features[i]]),rmse))
        return predictions, test_df, features
        
    @staticmethod
    def check_stationarity(series):
        if series.nunique() == 1:
            logger.warning(f"Series {series.name} is constant.")
            return False
        result = adfuller(series)
        return result[1] < 0.05  # p-value < 0.05 indicates stationarity

    @staticmethod
    def handler(signum, frame):
        raise TimeoutException()

    @staticmethod
    def feature_selection(column: str, pridiction: pd.DataFrame):
        clean_data = pridiction.copy()
        #
        scaler = MinMaxScaler()
        normalized_data = scaler.fit_transform(clean_data)
        normalized_df = pd.DataFrame(
            normalized_data, columns=clean_data.columns, index=clean_data.index)
        logger.info(f"Normalized Data: {normalized_df}")
        logger.info(f"NORMALIZED SHAPE: {normalized_df.shape}, DATA SHAPE: {clean_data.shape}")
        #
        X = normalized_df.drop(columns=[column])
        y = normalized_df[column]
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
        return feature_importances_dict
    
    @staticmethod
    async def _feature_selection(column: str):
        df = MultivariateTimeSeries.ml_process()
        clean_data = df.copy()
        #
        scaler = MinMaxScaler()
        normalized_data = scaler.fit_transform(clean_data)
        normalized_df = pd.DataFrame(
            normalized_data, columns=clean_data.columns, index=clean_data.index)
        logger.info(f"Normalized Data: {normalized_df}")
        logger.info(f"NORMALIZED SHAPE: {normalized_df.shape}, DATA SHAPE: {clean_data.shape}")
        #
        X = normalized_df.drop(columns=[column])
        y = normalized_df[column]
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
        return feature_importances_dict

    @staticmethod
    async def forecast(column: str, days: int = 1):
        macro_data = MultivariateTimeSeries.ml_process()
        features = macro_data.columns.tolist()
        logger.info(f"Features: {features}")
        macro_data = macro_data[features]
        logger.info(macro_data.shape)
        # Ensure all data is numeric
        macro_data = macro_data.apply(pd.to_numeric, errors='coerce')
        logger.info(macro_data.dtypes)
        for feature in features:
            if macro_data[feature].nunique() == 1:
                logger.warning(f"Feature {feature} is constant and will be excluded.")
                macro_data = macro_data.drop(columns=[feature])
            elif not MultivariateTimeSeries.check_stationarity(macro_data[feature]):
                logger.warning(f"Feature {feature} is not stationary. Differencing the data.")
                macro_data[feature] = macro_data[feature].diff().dropna()
        # Drop row that are not inside macro_data (for dropdown values) 
        if column not in macro_data.columns:
            logger.error(f"Column '{column}' not found in predictions.")
            return HTTPException(
                status_code=404, detail=f"Column '{column}' not found in predictions.")
        macro_data = macro_data.dropna()
        if macro_data.shape[1] < 2:
            logger.error(
                "Not enough features left after filtering for stationarity and constant series.")
            return None, None, None, None
        
        # Define thresholds
        very_small_data_threshold = 50
        small_data_threshold = 5000
        large_data_threshold = 10000

        def calculate_maxlags(num_observations, 
                              max_lags_for_very_small_data=1,
                              max_lags_for_small_data=10, 
                              max_lags_for_large_data=20):
            if num_observations <= very_small_data_threshold:
                logger.debug("Very small dataset detected.")
                # For very small datasets
                return min(max_lags_for_very_small_data, num_observations - 1)
            if num_observations <= small_data_threshold:
                logger.debug("Small dataset detected.")
                # For small datasets
                return min(max_lags_for_small_data, num_observations - 1)
            elif num_observations >= large_data_threshold:
                logger.debug("Large dataset detected.")
                # For large datasets
                return min(max_lags_for_large_data, num_observations // 4)
            else:
                logger.debug("Medium dataset detected.")
                # For medium datasets
                return min(num_observations // 4, num_observations - 1)
            
        # NOTE: increase the percentage of data used for training
        TRAIN_PERC = 0.1 # 10% of data used for training
        
        train_size = int(len(macro_data) * TRAIN_PERC)
        
        # Total number of rows in the dataset
        total_size = len(macro_data)

        # Define the split point (10% of the total data)
        split_point = int(total_size * TRAIN_PERC)
        # Split the data into test and train DataFrames
        
        #TODO: change test to train and vice versa
        test_df = macro_data.iloc[:total_size - split_point]  # First 90% of the data
        train_df = macro_data.iloc[total_size - split_point:]  # Last 10% of the data

        # train_df = macro_data.iloc[:train_size]
        # test_df = macro_data.iloc[train_size:]
        #
        corr_matrix = train_df.corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        high_corr_features = [column for column in upper.columns if any(upper[column] > 0.9)]
        if high_corr_features:
            logger.warning(f"High multicollinearity detected among features: {high_corr_features}")
            train_df = train_df.drop(columns=high_corr_features)
        
        if train_df.isnull().sum().sum() > 0:
            logger.error("Missing values detected in train_df.")
            train_df = train_df.dropna()
        try:
            # Ensure your train_df is defined and contains the correct data
            num_observations = train_df.shape[0]
            num_equations = train_df.shape[1]
            logger.debug(f"ROWS -> (Number of observations): {num_observations}")
            logger.debug(f"COLUMNS -> Number of equations: {num_equations}")
            # Calculate maxlags as a fraction of the number of observations
            maxlags = calculate_maxlags(num_observations)
            logger.debug(f"Maxlags: {maxlags}")
            
            # Ensure maxlags is positive and less than the number of observations
            if maxlags <= 0:
                logger.error(f"Calculated maxlags is too small: {maxlags}")
                return None, None, None, None
            
            # Fit the VAR model
            model = VAR(train_df.diff().dropna())
            sorted_order = model.select_order(maxlags=maxlags)
            logger.info(sorted_order.summary())
        except np.linalg.LinAlgError as e:
            logger.error(f"LinAlgError during select_order: {e}")
            return None, None, None, None
        except Exception as e:
            logger.error(f"Exception during select_order: {e}")
            return None, None, None, None
        reduced_order = (1, 0)
        var_model = VARMAX(train_df, order=reduced_order, enforce_stationarity=True)
        logger.info(f"Fitting VARMAX model with order {reduced_order}...")
        signal.signal(signal.SIGALRM, MultivariateTimeSeries.handler)
        signal.alarm(60 * 60) # one hour timeout
        try:
            fitted_model = var_model.fit(disp=True)
            signal.alarm(0)
        except TimeoutException:
            logger.error("Fitting VARMAX model timed out.")
            return None, None, None, None
        except Exception as e:
            logger.error(f"Error fitting VARMAX model: {e}")
            return None, None, None, None
        logger.info(fitted_model.summary())
        n_forecast = days * 24 * 60
        predict = fitted_model.get_prediction(
            start=len(train_df), end=len(train_df) + n_forecast - 1)
        predictions = predict.predicted_mean
        predictions = predictions.head(10)
        train_df = train_df.tail(20)
        
        logger.info(
            f"prediction shape: {predictions.shape}\n" \
            f"prediction head: {predictions.head()}\n" \
            f"prediction tail: {predictions.tail()}\n" \
            f"prediction info: {predictions.info()}\n" \
            f"prediction index dtype: {predictions.index.dtype}"
            )
        logger.info(
            f"train_df shape: {train_df.shape}\n" \
            f"train_df head: {train_df.head()}\n" \
            f"train_df tail: {train_df.tail()}\n" \
            f"train_df info: {train_df.info()}\n" \
            f"train_df index dtype: {train_df.index.dtype}"
        )
        # if column not in predictions.columns:
        #     logger.error(f"Column '{column}' not found in predictions.")
        #     return HTTPException(status_code=404, detail=f"Column '{column}' \
        # not found in predictions.")
        feature_importances_dict = MultivariateTimeSeries.feature_selection(column, predictions)
        # Pair the features with their importances
        features_with_importances = list(
            zip(feature_importances_dict['features'], feature_importances_dict['importance']))
        # Sort the pairs by importance values in descending order
        sorted_features = sorted(features_with_importances, key=lambda x: x[1], reverse=True)
        # Extract the top 3 features
        top_3_features = [feature for feature, importance in sorted_features[:3]]
        # Ensure the additional feature is not already in the top features
        if column not in top_3_features:
            # Append the additional feature to the list
            top_features_with_additional = top_3_features + [column]
        else:
            # If already present, keep the top 3 features list as is
            top_features_with_additional = top_3_features
        
        # Ensure the index is in datetime format
        if not isinstance(train_df.index, pd.DatetimeIndex):
            train_df.index = pd.to_datetime(train_df.index)
    
        # Ensure the index is sorted in ascending order
        train_df_sorted = train_df.sort_index()
        # Get the last timestamp from the sorted index
        last_time_train_df = train_df_sorted.index[-1]
        # Log the last timestamp
        logger.debug(f"Last timestamp in train_df: {last_time_train_df}")
        
        last_time_train_df = pd.Timestamp(last_time_train_df)
        filtered_predictions = predictions[predictions.index > last_time_train_df]
        logger.debug(f"Filtered predictions: {filtered_predictions.head(3)}")
        
        prid_dict_list = MultivariateTimeSeries.convert_to_dict(filtered_predictions, 
                                                                top_features_with_additional)
        train_dict_list = MultivariateTimeSeries.convert_to_dict(train_df, 
                                                                 top_features_with_additional)
        test_dict_list = MultivariateTimeSeries.convert_to_dict(test_df.tail(1), 
                                                                top_features_with_additional)
        logger.info(f"Feature importance dictionary: {feature_importances_dict}")
        logger.debug(f"{prid_dict_list[0].keys()}")
        return prid_dict_list, feature_importances_dict, train_dict_list, test_dict_list
    
    @staticmethod
    async def _forecast_loop(column: str, days: int = 1):
        macro_data = MultivariateTimeSeries.ml_process()
        features = macro_data.columns.tolist()
        logger.info(f"Features: {features}")
        macro_data = macro_data[features]
        logger.info(macro_data.shape)
        # Ensure all data is numeric
        macro_data = macro_data.apply(pd.to_numeric, errors='coerce')
        logger.info(macro_data.dtypes)
        for feature in features:
            if macro_data[feature].nunique() == 1:
                logger.warning(f"Feature {feature} is constant and will be excluded.")
                macro_data = macro_data.drop(columns=[feature])
            elif not MultivariateTimeSeries.check_stationarity(macro_data[feature]):
                logger.warning(f"Feature {feature} is not stationary. Differencing the data.")
                macro_data[feature] = macro_data[feature].diff().dropna()
        # Drop row that are not inside macro_data (for dropdown values) 
        if column not in macro_data.columns:
            logger.warning(f"Column '{column}' not found in predictions.")
            return HTTPException(
                status_code=404, detail=f"Column '{column}' not found in predictions.")
        macro_data = macro_data.dropna()
        if macro_data.shape[1] < 2:
            logger.error(
                "Not enough features left after filtering for stationarity and constant series.")
            return None
        
        # Define thresholds
        small_data_threshold = 3000
        large_data_threshold = 10000

        def calculate_maxlags(num_observations, 
                              max_lags_for_small_data=10, 
                              max_lags_for_large_data=20):
            if num_observations <= small_data_threshold:
                logger.debug("Small dataset detected.")
                # For small datasets
                return min(max_lags_for_small_data, num_observations - 1)
            elif num_observations >= large_data_threshold:
                logger.debug("Large dataset detected.")
                # For large datasets
                return min(max_lags_for_large_data, num_observations // 4)
            else:
                logger.debug("Medium dataset detected.")
                # For medium datasets
                return min(num_observations // 4, num_observations - 1)
        # NOTE: this is just for testing purposes (selects small portion of data)
        # train_df = macro_data[:-12]
        # test_df = macro_data[-12:]
        # logger.info(train_df.head())
        # logger.info(train_df.info())
        # Split data into training and testing based on time
        # DEBUG:remove this line when deploying (proven this casues maxlags too large error)
        # macro_data = macro_data.iloc[:1298]
        # NOTE: increase the percentage of data used for training
        TRAIN_PERC = 0.01 # 10% of data used for training
        train_size = int(len(macro_data) * TRAIN_PERC)
        train_df = macro_data.iloc[:train_size]
        test_df = macro_data.iloc[train_size:]
        #
        corr_matrix = train_df.corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        high_corr_features = [column for column in upper.columns if any(upper[column] > 0.9)]
        if high_corr_features:
            logger.warning(f"High multicollinearity detected among features: {high_corr_features}")
            train_df = train_df.drop(columns=high_corr_features)
        
        if train_df.isnull().sum().sum() > 0:
            logger.error("Missing values detected in train_df.")
            train_df = train_df.dropna()
        try:
            # Ensure your train_df is defined and contains the correct data
            num_observations = train_df.shape[0]
            num_equations = train_df.shape[1]
            logger.debug(f"ROWS -> (Number of observations): {num_observations}")
            logger.debug(f"COLUMNS -> Number of equations: {num_equations}")
            # Calculate maxlags as a fraction of the number of observations
            # maxlags = min(20, num_observations // 4)
            # maxlags = min(10, num_observations // 4, num_observations - 1)
            maxlags = calculate_maxlags(num_observations)
            logger.debug(f"Maxlags: {maxlags}")
            
            # Ensure maxlags is positive and less than the number of observations
            if maxlags <= 0:
                logger.error(f"Calculated maxlags is too small: {maxlags}")
                return None
            
            # Fit the VAR model
            model = VAR(train_df.diff().dropna())
            sorted_order = model.select_order(maxlags=maxlags)
            logger.info(sorted_order.summary())
        except np.linalg.LinAlgError as e:
            logger.error(f"LinAlgError during select_order: {e}")
            return None
        except Exception as e:
            logger.error(f"Exception during select_order: {e}")
            return None
        reduced_order = (1, 0)
        var_model = VARMAX(train_df, order=reduced_order, enforce_stationarity=True)
        logger.info(f"Fitting VARMAX model with order {reduced_order}...")
        signal.signal(signal.SIGALRM, MultivariateTimeSeries.handler)
        signal.alarm(60 * 60) # one hour timeout
        try:
            fitted_model = var_model.fit(disp=True)
            signal.alarm(0)
        except TimeoutException:
            logger.error("Fitting VARMAX model timed out.")
            return None
        except Exception as e:
            logger.error(f"Error fitting VARMAX model: {e}")
            return None
        logger.info(fitted_model.summary())
        n_forecast = days * 24 * 60
        predict = fitted_model.get_prediction(start=len(train_df), 
                                              end=len(train_df) + n_forecast - 1)
        predictions = predict.predicted_mean
        #
        logger.info(predictions.head())
        logger.info(predictions.shape)
        logger.info(predictions.info())
        #
        # issues = MultivariateTimeSeries.send_signal(predictions)
        issues = await LangchainAIService.problem_detection()
        # NOTE: OUTPUT sample
        # {
        #     'physical_mem_free': [Timestamp('2024-07-06 00:03:00')], # Falling below threshold 5
        #     'page_file_usage': [
            # Timestamp('2024-07-06 00:03:00'), Timestamp('2024-07-06 00:04:00')], 
            # # Exceeding threshold 500
        #     'processes': [Timestamp('2024-07-06 00:03:00'), Timestamp('2024-07-06 00:04:00')], 
        # # Falling below threshold 0
        #     'tcp_connections': [], # No values exceed threshold 15
        #     'cpu_user': [], # No values exceed threshold 16
        #     'cpu_sys': [
            # Timestamp('2024-07-06 00:01:00'), 
            # Timestamp('2024-07-06 00:03:00'), 
            # Timestamp('2024-07-06 00:04:00')], # Falling below threshold 0.01
        #     'sys_load': [
            # Timestamp('2024-07-06 00:01:00'), 
            # Timestamp('2024-07-06 00:02:00'), 
            # Timestamp('2024-07-06 00:04:00')], # Exceeding threshold 2
        #     'swap_pageout': [Timestamp('2024-07-06 00:01:00'), 
        # Timestamp('2024-07-06 00:02:00')], # Exceeding threshold 10
        #     'cpuusedpercent': [Timestamp('2024-07-06 00:01:00')], # Exceeding threshold 14
        #     'mem_used_per': [Timestamp('2024-07-06 00:04:00')] # Exceeding threshold 0.02
        # }
        return issues
    
    @staticmethod
    async def forecast_loop():
        issues = await LangchainAIService.problem_detection()
        return issues
    
    @staticmethod
    def convert_to_dict(df: pd.DataFrame, column_names: list):
        # Validate column_names
        for column_name in column_names:
            if column_name not in df.columns:
                raise ValueError(f"Column '{column_name}' not found in DataFrame.")
        # Initialize the list to store the dictionaries
        dict_list = []
        # Create a dictionary for each column
        for column_name in column_names:
            column_dict = {
                'date': df.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                column_name: df[column_name].tolist()
            }
            dict_list.append(column_dict)
        return dict_list
    
    @staticmethod
    async def get_dropdowns():
        macro_data = MultivariateTimeSeries.ml_process()
        columns = macro_data.columns.tolist()
        dropdown_data = [{"value": col, "label": col} for col in columns]
        return dropdown_data, columns
    
    # Define the periodic task function
    @staticmethod
    async def periodic_forecast_and_email(columns, user):
        while True:
            try:
                problem = None
                for column in columns:
                    problem = await MultivariateTimeSeries.forecast_loop(column=column)
                    if problem:
                        break
            except Exception as e:
                logger.error(f"{e}")
                problem = None

            if problem:
                await UserService.send_email_request(user.email, problem)
                predictions, causes, train, test = await MultivariateTimeSeries.forecast(
                    column=problem)
                logger.debug("Issue found and email sent.")
            else:
                logger.debug("No issues were found for the upcoming day.")

            # Wait for 24 hours (86400 seconds) before running the loop again
            await asyncio.sleep(86400)
    
    @staticmethod
    async def find_issues_based_on_thresholds(df: pd.DataFrame, thresholds: dict) -> dict:
        """
        Find and return the columns and timestamps where values either exceed or fall below given 
        thresholds,
        depending on the threshold type for each column.

        Args:
            df (pd.DataFrame): The DataFrame containing the data with a datetime index.
            thresholds (dict): A dictionary where keys are column names and values are tuples with 
                               the threshold value and a flag indicating if it's a 'min' or 'max' 
                               threshold.

        Returns:
            dict: A dictionary where keys are column names and values are lists of timestamps
            where the threshold was exceeded or not met.
        """
        issues = {}

        for column, (threshold, threshold_type) in thresholds.items():
            if column in df.columns:
                if threshold_type == 'max':
                    # Metrics where exceeding the threshold is an issue
                    issue_rows = df[df[column] > threshold]
                elif threshold_type == 'min':
                    # Metrics where falling below the threshold is an issue
                    issue_rows = df[df[column] < threshold]
                else:
                    # Handle unknown threshold type
                    raise ValueError(f"Unknown threshold type for column {column}")

                # Collect the indices or timestamps
                issues[column] = issue_rows.index.tolist()
            else:
                # Handle the case where the column is not in the DataFrame
                issues[column] = []

        return issues
    
    @staticmethod
    def has_empty_lists_or_none_values(d: Dict[str, List[Any]]) -> bool:
        
        """
        Checks if the dictionary contains any empty lists or lists with only None values.

        Args:
            d (dict): The dictionary to check.

        Returns:
            bool: True if there are empty lists or lists with only None values, False otherwise.
        """
        return all(not value for value in d.values())

    @staticmethod
    async def send_signal(df):
        # Define thresholds for each column
        # Example usage
        # Find indices or timestamps where values exceed thresholds
        issues = await MultivariateTimeSeries.find_issues_based_on_thresholds(
            df, 
            oshistory_detail_thresholds)
        logger.debug(f"ISSUES: {issues}")
        return issues
    
class TimeoutException(Exception):
        pass
               
if __name__ == '__main__':
    forecast = MultivariateTimeSeries.forecast_loop(column="cpuusedpercent")
    