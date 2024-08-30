import asyncio
import json
from fastapi import APIRouter, HTTPException, Header, status
from app.services.multivariate_timeseries import MultivariateTimeSeries
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, FastAPI
from logs.loggers.logger import logger_config
from app.services.user_service import UserService
logger = logger_config(__name__)
from fastapi import APIRouter
from app.models.parameters import PredictionRequest, ForecastResponse, DropdownItem
from typing import List, Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Header, HTTPException, status

api = APIRouter()

@api.post("/forecaster")
async def forecast(request: PredictionRequest):
    predictions, causes, train, test = await MultivariateTimeSeries.forecast(request.column, request.days)
    return ForecastResponse(predictions=predictions, causes=causes, train=train, test=test)

@api.get("/dropdown_data", response_model=List[DropdownItem])
async def get_dropdown_data():
    dropdowns, columns = await MultivariateTimeSeries.get_dropdowns()
    return dropdowns

@api.websocket("/forecast/loop")
async def forecaster_loop(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        message = json.loads(data)
        authorization = message.get("authorization")
        refresh_token = message.get("refresh_token")
        
        if not authorization or not refresh_token:
            raise WebSocketDisconnect(code=403)

        user = await UserService.decode_token(authorization, refresh_token)
        
        # Proceed with the loop as before
        dropdowns, columns = await MultivariateTimeSeries.get_dropdowns()

        while True:
            problem_found = False
            try:
                problem = await MultivariateTimeSeries.forecast_loop()
                logger.warning(f"Problem: {problem}")
                pr = MultivariateTimeSeries.has_empty_lists_or_none_values(problem)
                logger.warning(f"Problematic bool: {pr}")
                if not pr:
                    problem_found = True
                    problematic_columns_with_timestamps = {
                        col: timestamps for col, timestamps in problem.items() if timestamps
                    }
                    logger.warning(f"Problematic columns with timestamps: {problematic_columns_with_timestamps}")
                    for problematic, timestamps in problematic_columns_with_timestamps.items():
                        await UserService._send_email_request(user.email, problematic, timestamps)
                        logger.info(f"Found an issue: {problematic}. Sending an email to {user.email}...")
                        await websocket.send_text(f"An issue was detected in {problematic} ...")
                        await asyncio.sleep(180)
                else:
                    problem_found = False
                    logger.warning("No issues were found for the upcoming day.")
                    await websocket.send_text("No issue detected")
                    await asyncio.sleep(180)

            except Exception as e:
                problem_found = False
                logger.error(f"{e}")
            
            if not problem_found:
                logger.warning("No issues were found for the upcoming day...")
                await websocket.send_text("No issue detected")
                await asyncio.sleep(180)

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        await websocket.close(code=1000)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{e}"
        )