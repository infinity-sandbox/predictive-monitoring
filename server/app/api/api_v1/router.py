from fastapi import APIRouter
from app.api.api_v1.handlers import forecast

router = APIRouter()

router.include_router(forecast.api, prefix='/varmax', tags=["varmax"])