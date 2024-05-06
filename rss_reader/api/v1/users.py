# builtin import
from typing import Annotated
import uuid
from datetime import datetime

# external imports
from annotated_types import Ge, Lt
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlmodel import select
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

# internal imports
from ...database.models import Users as UserModel
from ...utils.database import Database

# defines user router
users_router = APIRouter(prefix="/v1/users", tags=["users"])

_MAX_QUERY_LIMIT = 50

class CreateUser(BaseModel):
    email: EmailStr

    class Config:
        from_attributes = True


@users_router.post(
    path="/",
    description="creates a new user and returns user uuid",
    status_code=status.HTTP_201_CREATED,
)
def create_user(user: CreateUser):
    now = datetime.now()

    conn = Database().get_db_connection()

    user = UserModel(
        email=user.email,
        uuid=str(uuid.uuid4()),
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    # check if user already exists
    q = select(UserModel).where(UserModel.email == user.email)
    u = conn.exec(q).one_or_none()
    if u is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user with email {} already exists".format(user.email)
        )

    try:
        conn.add(user)
    except:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="failed to create user"
        )
    else:
        conn.commit()

        # refersh the object to be in sync with database
        conn.refresh(user)
    finally:
        conn.close()
    
    return user


@users_router.get(
    path="/",
    description="gets user by uuid or email",
    status_code=status.HTTP_200_OK,
)
def get_user_by_id(uuid: uuid.UUID | None = None, email: EmailStr | None = None):
    conn = Database().get_db_connection()

    query = select(UserModel)
    if uuid is not None:
        query = query.where(UserModel.uuid == str(uuid))
    elif email is not None:
        query = query.where(UserModel.email == email)
    
    try:
        user = conn.exec(query).one()
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user with {} not found".format(uuid),
        )
    except MultipleResultsFound:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="multiple user object exists with given {} or {}".format(
                uuid, email
            )
        )
    finally:
        conn.close()

    return user


@users_router.patch(
    path="/{uuid}/activate",
    description="activates a deactivated user profile",
    status_code=status.HTTP_200_OK,
)
def activate_user(uuid:str):
    conn = Database().get_db_connection()

    query = select(UserModel).where(UserModel.uuid == str(uuid))
    try:
        user = conn.exec(query).one()
        
        if not user.is_active:
            user.is_active = True
            user.updated_at = datetime.now()
        else:
            return user

        # update user
        conn.add(user)
        
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user with {} not found".format(uuid),
        )
    except MultipleResultsFound:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="multiple user object exists with given {} or {}".format(uuid)
        )
    else:
        conn.commit()
        conn.refresh(user)
    finally:
        conn.close()
    
    return user


@users_router.patch(
    path="/{uuid}/deactivate",
    description="deactivates an active user",
    status_code=status.HTTP_200_OK,
)
def deactivate_user(uuid:str):
    conn = Database().get_db_connection()

    query = select(UserModel).where(UserModel.uuid == str(uuid))
    try:
        user = conn.exec(query).one()
        
        if user.is_active:
            user.is_active = False
            user.updated_at = datetime.now()
        else:
            return user
        
        # update user
        conn.add(user)
        
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user with {} not found".format(uuid),
        )
    except MultipleResultsFound:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="multiple user object exists with given {} or {}".format(uuid)
        )
    else:
        conn.commit()
        conn.refresh(user)
    finally:
        conn.close()
    
    return user


@users_router.delete(
    path="/{uuid}",
    description="deletes a user profile",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(uuid:str):
    conn = Database().get_db_connection()

    query = select(UserModel).where(UserModel.uuid == str(uuid))
    try:
        user = conn.exec(query).one()      
        
        # delete user
        conn.delete(user)
        
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user with {} not found".format(uuid),
        )
    except MultipleResultsFound:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="multiple user object exists with given {} or {}".format(uuid)
        )
    else:
        conn.commit()
    finally:
        conn.close()


@users_router.get(
    path="/all-active-users",
    description="get all the users in the system in paginated fashion",
    status_code=status.HTTP_200_OK,
)
def get_all_active_users(
        offset: Annotated[int, Ge(0)] = 0, 
        limit: Annotated[int, Lt(50)] = 1
):
    conn = Database().get_db_connection()

    query = select(UserModel).where(
        UserModel.is_active == True
    )

    if not offset:
        query.offset(offset=offset)

    if not limit:
        query.limit(limit=_MAX_QUERY_LIMIT)

    try:
        users = conn.exec(query).all()
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="failed to get all active users {}".format(ex),
        )
    
    finally:
        conn.close()

    return users
