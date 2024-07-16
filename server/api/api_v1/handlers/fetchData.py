from fastapi import APIRouter, HTTPException, Header, status
from fastapi.responses import JSONResponse
from typing import List
from fastapi import APIRouter, Depends, FastAPI
from server.logs.loggers.logger import logger_config
logger = logger_config(__name__)
from fastapi import APIRouter
from server.api.api_v1.handlers.pipeline import connect_fetch_db, data_cleaning, feature_selection, tseries
from pydantic import BaseModel
from datetime import datetime

class PredictionRequest(BaseModel):
    date: datetime


fetch_data = APIRouter()

    
@fetch_data.get("/importance")
async def fetchData():
    raw_data = connect_fetch_db()
    cleaned_data_for_features = data_cleaning(raw_data)
    feature_importances_dict, mse = feature_selection(cleaned_data_for_features)
    return {
        "ml_metric": mse,
        "casual_features": feature_importances_dict
    }

@fetch_data.post("/predict")
async def predict(request: PredictionRequest):
    prediction_date = request.date
    raw_data = connect_fetch_db()
    cleaned_data = data_cleaning(raw_data, ts=True)
    prediction_result = tseries(cleaned_data, prediction_date)
    prediction_result_message = f"cpu performance(%): {prediction_result}"
    return {"prediction": prediction_result_message}
