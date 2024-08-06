import asyncio
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
async def forecaster_loop(websocket: WebSocket, authorization: str = Header(...), refresh_token: str = Header(...)):
    await websocket.accept()
    try:
        user = await UserService.decode_token(authorization, refresh_token)
        dropdowns, columns = await MultivariateTimeSeries.get_dropdowns()

        while True:
            problem_found = False
            for column in columns:
                try:
                    problem = await MultivariateTimeSeries.forecast_loop(column=column)
                    if problem:
                        problem_found = True
                        
                        # Extract problematic columns and their timestamps
                        problematic_columns_with_timestamps = {
                            col: timestamps for col, timestamps in problem.items() if timestamps
                        }
                        
                        for problematic, timestamps in problematic_columns_with_timestamps.items():
                            await UserService.send_email_request(user.email, problematic, timestamps)
                            logger.info(f"Found an issue for the upcoming day: {problematic}. Sending an email to {user.email}...")
                            # Send the problem string to the client
                            await websocket.send_text(problematic)
                            # Optionally, you can sleep for a short time to avoid tight looping
                            await asyncio.sleep(60)  # Sleep for 10 seconds before checking the next column
                    else:
                        problem_found = False
                        logger.warning("No issues were found for the upcoming day.")
                        
                except Exception as e:
                    problem_found = False
                    logger.error(f"{e}")
                    
                if not problem_found:
                    logger.warning("No issues were found for the upcoming day. Rechecking in 24 hours...")
                    await websocket.send_text("")
                    await asyncio.sleep(86400)  # Wait for 24 hours before running the loop again

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        await websocket.close(code=1000)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{e}"
        )