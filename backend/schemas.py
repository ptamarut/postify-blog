from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Post sheme
class PostCreate(BaseModel):
    title: str
    content: str
    category: str
    image_filename: Optional[str] = None

class PostRead(BaseModel):
    id: int
    title: str
    content: str
    category: str
    image_url: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}

# Auth sheme
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=150)
    email: EmailStr
    password: str = Field(min_length=6)

class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: str  # username
