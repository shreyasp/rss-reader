# builtin import
from typing import Annotated
import uuid
from datetime import datetime

# external imports
from annotated_types import Ge, Lt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlmodel import select, Session
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

# internal imports
from ...database.models import Users as UserModel
from ...utils.database import get_db_connection

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
def create_user(
    user: CreateUser,
    conn: Session = Depends(get_db_connection),
):
    now = datetime.now()

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
            detail="user with email {email_id} already exists".format(
                email_id=user.email
            ),
        )

    try:
        conn.add(user)
    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="failed to create user",
        )
    else:
        conn.commit()
        conn.refresh(user)

    finally:
        conn.close()

    return user


@users_router.get(
    path="/",
    description="gets user by uuid or email",
    status_code=status.HTTP_200_OK,
)
def get_user_by_id(
    uuid: uuid.UUID | None = None,
    email: EmailStr | None = None,
    conn: Session = Depends(get_db_connection),
):
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
            detail="user with {uuid} not found".format(uuid=uuid),
        )
    except MultipleResultsFound:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="multiple user object exists with given {email} or {uuid}".format(
                uuid=uuid, email=email
            ),
        )
    finally:
        conn.close()

    return user


@users_router.patch(
    path="/{uuid}/activate",
    description="activates a deactivated user profile",
    status_code=status.HTTP_200_OK,
)
def activate_user(
    uuid: str,
    conn: Session = Depends(get_db_connection),
):
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
            detail="user with {uuid} not found".format(uuid=uuid),
        )
    except MultipleResultsFound:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="multiple user object exists with given {uuid}".format(uuid=uuid),
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
def deactivate_user(
    uuid: str,
    conn: Session = Depends(get_db_connection),
):
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
            detail="user with {uuid} not found".format(uuid=uuid),
        )
    except MultipleResultsFound:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="multiple user object exists with given {uuid}".format(uuid=uuid),
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
def delete_user(
    uuid: str,
    conn: Session = Depends(get_db_connection),
):
    query = select(UserModel).where(UserModel.uuid == str(uuid))
    try:
        user = conn.exec(query).one()

        # delete user
        conn.delete(user)

    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user with {uuid} not found".format(uuid=uuid),
        )
    except MultipleResultsFound:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="multiple user object exists with given {uuid}".format(uuid=uuid),
        )
    else:
        conn.commit()
    finally:
        conn.close()


@users_router.get(
    path="/all",
    description="get all the users in the system in paginated fashion",
    status_code=status.HTTP_200_OK,
)
def get_all_active_users(
    only_active: bool = False,
    offset: Annotated[int, Ge(0)] = 0,
    limit: Annotated[int, Lt(50)] = _MAX_QUERY_LIMIT,
    conn: Session = Depends(get_db_connection),
):
    query = select(UserModel)
    if only_active:
        query = query.where(UserModel.is_active == only_active)

    # apply if offset is provided
    if offset:
        query = query.offset(offset=offset)

    # apply default limit if nothing was provided
    if limit > 0 and limit < _MAX_QUERY_LIMIT:
        query = query.limit(limit=limit)

    try:
        users = conn.exec(query).all()
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="failed to get all active users {ex}".format(ex=str(ex)),
        )

    finally:
        conn.close()

    return {"users": users}
