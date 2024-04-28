# external imports
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# builtin imports
from datetime import datetime

# defines user router
users_router = APIRouter(prefix="/v1/users", tags=["users"])

# defines user object
class Users(BaseModel):
    id: int
    uuid: str
    email: str
    is_active: bool
    created_at: datetime

@users_router.post(
    path="/",
    description="creates a new user and returns user uuid"
)
def create_user(user:Users):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@users_router.get(
    path="/{uuid}",
    description="gets user by id"
)
def get_user_by_id(uuid:str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@users_router.patch(
    path="/{uuid}/activate",
    description="activates a deactivated user profile"
)
def activate_user(uuid:str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@users_router.patch(
    path="/{uuid}/deactivate",
    description="deactivates an active user"
)
def deactivate_user(uuid:str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@users_router.delete(
    path="/{uuid}",
    description="deletes a user profile"
)
def delete_user(uuid:str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)