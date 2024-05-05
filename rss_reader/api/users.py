# built in imports
import uuid
from datetime import datetime


# external imports
from pydantic import BaseModel, Field, EmailStr


class Users(BaseModel):
    """User Model"""


    id: int
    uuid: uuid.UUID
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True


class CreateUserModel(BaseModel):
    """Model to create a new app user"""
    email: EmailStr = Field(title="user email address")


class UpdateUserModel(BaseModel):
    """Model to update user is active or not"""
    is_active: bool = Field()