from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserAuth(BaseModel):
    username: str = Field(..., min_length=5, max_length=50, description="user username")
    email: EmailStr = Field(..., description="user email")
    password: str = Field(..., min_length=5, max_length=24, description="user password")
    confirm_password: str = Field(..., min_length=5, max_length=24, description="confirm password")
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15, description="user phone number")
    address: Optional[str] = Field(None, description="user address")
    security_question: Optional[str] = Field(None, description="user security question")
    security_answer: Optional[str] = Field(None, description="user security answer")
    

class UserOut(BaseModel):
    user_id: UUID
    username: str
    email: EmailStr
    

class UserUpdate(BaseModel):
    username: str = Field(..., min_length=5, max_length=50, description="user username")
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15, description="user phone number")
    address: Optional[str] = Field(None, description="user address")
    security_question: Optional[str] = Field(None, description="user security question")
    security_answer: Optional[str] = Field(None, description="user security answer")
    
    
class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    
class UserChat(BaseModel):
    question: str

class UserChatResponse(BaseModel):
    response: str