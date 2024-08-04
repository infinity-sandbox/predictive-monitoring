from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import uuid
import jwt
import smtplib
from pydantic import ValidationError
from fastapi import HTTPException, status
from app.core.config import settings
from passlib.context import CryptContext
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from fastapi import FastAPI, HTTPException, Depends
from typing import Optional
from uuid import UUID
from app.schemas.user_schema import UserAuth
from app.models.user_model import User
from app.core.security import get_password, verify_password
import pymongo
from app.schemas.user_schema import UserUpdate
from app.schemas.auth_schema import TokenSchema, TokenPayload
from logs.loggers.logger import logger_config
import json
import random
logger = logger_config(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    @staticmethod
    async def create_user(user: UserAuth):
        user_in = User(
            username=user.username,
            email=user.email,
            hashed_password=get_password(user.password),
            phone_number=user.phone_number,
            birthdate=user.birthdate,
            parent_name=user.parent_name,
            parent_email=user.parent_email,
            school=user.school,
            user_class=user.user_class,
            user_subject=user.user_subject,
            address=user.address,
            security_question=user.security_question,
            security_answer=user.security_answer
        )
        await user_in.save()
        return user_in

    @staticmethod
    async def authenticate(email: str, password: str) -> Optional[User]:
        logger.debug(
            f"Authenticating user with email: {email} and password: {password} ...")
        user = await UserService.get_user_by_email(email=email)
        logger.info(f"User found: {user}")
        if not user:
            logger.info(f"User not found: {user}")
            return None
        if not verify_password(password=password, hashed_pass=user.hashed_password):
            logger.info(f"Password does not match: {user}")
            return None
        return user

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[User]:
        user = await User.find_one(User.email == email)
        return user

    @staticmethod
    async def get_user_by_id(id: UUID) -> Optional[User]:
        user = await User.find_one(User.user_id == id)
        return user

    @staticmethod
    async def update_user(id: UUID, data: UserUpdate) -> User:
        user = await User.find_one(User.user_id == id)
        if not user:
            raise pymongo.errors.OperationFailure("User not found")

        await user.update({"$set": data.dict(exclude_unset=True)})
        return user

    @staticmethod
    async def send_email_request(email: str):
        user = await UserService.get_user_by_email(email)
        if not user:
            raise pymongo.errors.OperationFailure(
                "User not found or this email is not registered!")
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        access_token = UserService.create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        reset_link = f"{settings.FRONTEND_API_URL}/PasswordResetPage?token={access_token}"
        # Send the reset link to the user's email
        logger.debug(f"Reset link: {reset_link}")
        status = UserService.send_email(email, reset_link)
        if status:
            return logger.debug("Password reset email sent!")
        else:
            return logger.debug("Password reset email not sent!")

    @staticmethod
    async def reset_password(token: str, new_password: str):
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[
                                 settings.ALGORITHM])
            email = payload.get("sub")
            if email is None:
                raise HTTPException(status_code=400, detail="Invalid token")
        except jwt.PyJWTError:
            raise HTTPException(status_code=400, detail="Invalid token")

        user = await UserService.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        hashed_password = get_password(new_password)
        data = {"hashed_password": hashed_password}

        await user.update({"$set": data})
        return {"msg": "Password reset successful"}

    @staticmethod
    def send_email(email: str, reset_link):
        try:
            # Email details
            sender_email = settings.MY_EMAIL
            receiver_email = email
            subject = "PASSWORD RESET LINK REQUEST: AI BOU"
            body = f"Password Reset Link:\n{reset_link}"

            # Create the email message
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = receiver_email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain"))
            # Convert the message to a string
            email_string = message.as_string()

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(settings.MY_EMAIL, settings.EMAIL_APP_PASSWORD)
            server.sendmail(settings.MY_EMAIL, email, email_string)
            return True
        except Exception as e:
            logger.error(f"Error: {e}")
            return False
        finally:
            server.quit()

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    async def decode_token(access_token: str, refresh_token: str):
        try:
            payload = jwt.decode(
                refresh_token, settings.JWT_REFRESH_SECRET_KEY, algorithms=[
                    settings.ALGORITHM]
            )
            token_data = TokenPayload(**payload)
        except (jwt.JWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = await UserService.get_user_by_id(token_data.sub)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid token for user",
            )
        return user
    
    @staticmethod
    async def audio_path_generator(user_id: UUID):
        # TODO: Latter will be converted the location to s3
        root_path = "static"
        user_id = str(user_id)
        # TODO: Latter generate a complex session id to manage everything
        session_id = str(uuid.uuid4())
        #
        session_id = session_id.replace('-', '_')
        user_id = user_id.replace('-', '_')
        wav_file_path = f"{root_path}/{user_id}__{session_id}.wav"
        webm_file_path = f"{root_path}/{user_id}__{session_id}.webm"
        return wav_file_path, webm_file_path

    @staticmethod
    # Load the JSON data from a file
    def load_question_bank(file_path: str):
        with open(file_path, 'r') as file:
            question_bank = json.load(file)
        return question_bank

    @staticmethod
    # Function to get a formatted question and options
    def get_random_question(question_bank, subject: str) -> str:
        try:
            # Find the subject in the question bank
            subject_data = next((item for item in question_bank if item['subject'].lower() == subject.lower()), None)
            
            if not subject_data:
                return "Subject not found"
        except Exception as e:
            logger.error(f"Error: {e}")
            raise Exception(f"Error: {e}")
        # Select a random question
        question_data = random.choice(subject_data['questions'])
        # Format the question and options
        options = question_data['options']
        formatted_options = "\n".join([f"{chr(65+i)}. {option}" for i, option in enumerate(options)])
        formatted_question = f"{question_data['question']}\n{formatted_options}"
        return formatted_question
    
    @staticmethod
    async def get_formated_question(subject: str):
        # Load the question bank
        question_bank = UserService.load_question_bank('app/services/question_bank_sample.json')
        formatted_question = UserService.get_random_question(question_bank, subject)
        return formatted_question
