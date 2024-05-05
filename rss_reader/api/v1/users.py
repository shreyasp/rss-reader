# external imports
from fastapi import APIRouter, HTTPException, status

# defines user router
users_router = APIRouter(prefix="/v1/users", tags=["users"])

@users_router.post(
    path="/",
    description="creates a new user and returns user uuid",
    status_code=status.HTTP_201_CREATED,
)
def create_user():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@users_router.get(
    path="/{uuid}",
    description="gets user by id",
    status_code=status.HTTP_200_OK,
)
def get_user_by_id(uuid:str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@users_router.patch(
    path="/{uuid}/activate",
    description="activates a deactivated user profile",
    status_code=status.HTTP_200_OK,
)
def activate_user(uuid:str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@users_router.patch(
    path="/{uuid}/deactivate",
    description="deactivates an active user",
    status_code=status.HTTP_200_OK,
)
def deactivate_user(uuid:str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@users_router.delete(
    path="/{uuid}",
    description="deletes a user profile",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(uuid:str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)