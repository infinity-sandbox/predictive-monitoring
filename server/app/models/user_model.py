from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4
from beanie import Document, Indexed
from pydantic import Field, EmailStr

class User(Document):
    user_id: UUID = Field(default_factory=uuid4)
    username: Indexed(str, unique=True) # type: ignore
    email: Indexed(EmailStr, unique=True) # type: ignore
    hashed_password: str
    phone_number: Optional[str] = None
    address: Optional[str] = None
    security_question: Optional[str] = None
    security_answer: Optional[str] = None
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"

    def __str__(self) -> str:
        return self.email

    def __hash__(self) -> int:
        return hash(self.email)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, User):
            return self.email == other.email
        return False
    
    @property
    def create(self) -> datetime:
        return self.id.generation_time
    
    @classmethod
    async def by_email(self, email: str) -> "User":
        return await self.find_one(self.email == email)
        
    class Settings:
        name = "users"