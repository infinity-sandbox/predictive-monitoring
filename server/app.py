import os, sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from server.logs.loggers.logger import logger_config
logger = logger_config(__name__)
from server.api.api_v1.router import router
from fastapi.responses import JSONResponse


app = FastAPI(
    title="applicare os monitoring api",
    openapi_url=f"/api/v1/openapi.json"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def serve_frontend():
    return JSONResponse(
                content={
                    "message": "applicare backend api. welcome to the jungle!",
                }
            )

app.include_router(router, prefix="/api/v1")