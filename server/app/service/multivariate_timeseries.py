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
warnings.filterwarnings('ignore')
load_dotenv()
from logs.loggers.logger import logger_config
logger = logger_config(__name__)
import logging
import signal


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
        for i in range(len(features)):
            rmse=math.sqrt(mean_squared_error(predictions[str(features[i]) + "_predicted"],test_df[features[i]]))
            logger.info('Mean value of {} is : {}. Root Mean Squared Error is :{}'.format(features[i],mean(test_df[features[i]]),rmse))
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
        normalized_df = pd.DataFrame(normalized_data, columns=clean_data.columns, index=clean_data.index)
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
    def forecast(days: int, column: str):
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
        macro_data = macro_data.dropna()
        if macro_data.shape[1] < 2:
            logger.error("Not enough features left after filtering for stationarity and constant series.")
            return None
        train_df = macro_data[:-12]
        test_df = macro_data[-12:]
        logger.info(train_df.head())
        logger.info(train_df.info())
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
            model = VAR(train_df.diff().dropna())
            sorted_order = model.select_order(maxlags=20)
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
        signal.alarm(60 * 10)
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
        predict = fitted_model.get_prediction(start=len(train_df), end=len(train_df) + n_forecast - 1)
        predictions = predict.predicted_mean
        plot = False
        if plot:
            for x in features:
                if x in predictions.columns:
                    fig, ax = plt.subplots(figsize=(12, 5))
                    ax.plot(train_df.index, train_df[x], label=f'Train Data ({x})', color='blue')
                    ax.plot(test_df.index, test_df[x], label=f'Test Data ({x})', color='green')
                    ax.plot(predictions.index, predictions[x], label=f'Predicted Data ({x})', color='red')
                    ax.legend()
                    plt.title(f'VARMAX Model Predictions vs Actual Data ({x})')
                    plt.xlabel('Time')
                    plt.ylabel('Value')
                    plt.show()
        logger.info(predictions.head())
        logger.info(predictions.shape)
        logger.info(predictions.info())
        if column not in predictions.columns:
            logger.error(f"Column '{column}' not found in predictions.")
            return HTTPException(status_code=404, detail=f"Column '{column}' not found in predictions.")
        feature_importances_dict = MultivariateTimeSeries.feature_selection(column, predictions)
        # Pair the features with their importances
        features_with_importances = list(zip(feature_importances_dict['features'], feature_importances_dict['importance']))
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
        prid_dict_list = MultivariateTimeSeries.convert_to_dict(predictions, top_features_with_additional)
        train_dict_list = MultivariateTimeSeries.convert_to_dict(train_df, top_features_with_additional)
        test_dict_list = MultivariateTimeSeries.convert_to_dict(test_df, top_features_with_additional)
        logger.info(f"Feature importance dictionary: {feature_importances_dict}")
        logger.info(f"{prid_dict_list[0].keys()}")
        return prid_dict_list, feature_importances_dict, train_dict_list, test_dict_list
    
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
    def get_dropdowns():
        macro_data = MultivariateTimeSeries.ml_process()
        columns = macro_data.columns.tolist()
        dropdown_data = [{"value": col, "label": col} for col in columns]
        return dropdown_data
    
class TimeoutException(Exception):
        pass
               
# if __name__ == '__main__':
#     forecast = MultivariateTimeSeries.forcast(days=1, column="cpuusedpercent")
