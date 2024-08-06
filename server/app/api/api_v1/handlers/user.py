from fastapi import APIRouter, HTTPException, Header, status
from app.schemas.user_schema import UserAuth, UserOut, UserUpdate
import pymongo
from app.models.user_model import User
from fastapi.responses import JSONResponse
from app.services.user_service import UserService
from app.services.langchain_service import LangchainAIService
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from app.schemas.auth_schema import TokenSchema, TokenPayload
from logs.loggers.logger import logger_config
logger = logger_config(__name__)
from app.models.user_model import User
from app.api.deps.user_deps import get_current_user
from app.schemas.user_schema import (PasswordResetRequest, 
                                     PasswordResetConfirm, 
                                     UserChat, 
                                     UserChatResponse)
import jwt
from bson import ObjectId
from fastapi import APIRouter, Query

user_router = APIRouter()


@user_router.post('/register', summary="Create new user/Register", response_model=UserOut)
async def create_user(data: UserAuth):
    try:
        return await UserService.create_user(data)
    except pymongo.errors.DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exist"
        )

@user_router.post('/reset/email', summary="Send email reset password", response_model=PasswordResetRequest)
async def reset_password(request: PasswordResetRequest):
    try:
        logger.info(f"Request email: {request.email}")
        await UserService.send_email_request(request.email)
        return JSONResponse(
            content={"message": "Reset email sent successfully!"})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{e}"
        )
        
@user_router.post("/reset/password")
async def reset_password_confirm(request: PasswordResetConfirm):
    try:
        await UserService.reset_password(request.token, request.new_password)
        return JSONResponse(
            content={"message": "Password reset successfully!"})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{e}"
        )

@user_router.post('/chatbot', summary="Chatbot", response_model=UserChatResponse)
async def chat(request: UserChat,
               authorization: str = Header(...),
               refresh_token: str = Header(...)):
    try:
        user = await UserService.decode_token(authorization, refresh_token)
        response = await LangchainAIService.full_chain(request.question, user.username)
        return UserChatResponse(response=response)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{e}"
        )