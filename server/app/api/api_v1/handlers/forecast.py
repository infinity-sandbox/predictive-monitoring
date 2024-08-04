from fastapi import APIRouter, HTTPException, Header, status
from app.service.multivariate_timeseries import MultivariateTimeSeries
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, FastAPI
from logs.loggers.logger import logger_config
logger = logger_config(__name__)
from fastapi import APIRouter
from app.models.parameters import PredictionRequest, ForecastResponse, DropdownItem
from typing import List, Dict, Optional

api = APIRouter()

@api.post("/forecaster")
async def forecast(request: PredictionRequest):
    predictions, causes, train, test = MultivariateTimeSeries.forecast(request.days, request.column)
    return ForecastResponse(predictions=predictions, causes=causes, train=train, test=test)

@api.get("/dropdown_data", response_model=List[DropdownItem])
async def get_dropdown_data():
    dropdowns = MultivariateTimeSeries.get_dropdowns()
    return dropdowns

