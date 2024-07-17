from fastapi import APIRouter
from app.api.api_v1.handlers import fetchData

router = APIRouter()

router.include_router(fetchData.fetch_data, prefix='/fetch_data', tags=["data"])