import uuid
from datetime import datetime

from pydantic import HttpUrl
from sqlalchemy import null
from sqlmodel import Field, Relationship, SQLModel


class User_Feed_Post_Link(SQLModel, table=True):
    user_id: int | None = Field(default=None, foreign_key="users.id", primary_key=True)
    feed_id: int | None = Field(default=None, foreign_key="feeds.id", primary_key=True)
    post_id: int | None = Field(default=None, foreign_key="posts.id", primary_key=True)

    is_read: bool = Field(default=False, nullable=True)
    read_at: datetime = Field(default=datetime.min, nullable=True)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())

    user: "Users" = Relationship(back_populates="user_links")
    feed: "Feeds" = Relationship(back_populates="feed_links")
    post: "Posts" = Relationship(back_populates="post_links")


class Users(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    uuid: str = Field(default=str(uuid.uuid4()), max_length=36)
    email: str = Field(max_length=320)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())

    user_links: list[User_Feed_Post_Link] = Relationship(back_populates="user")


class Feeds(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    uuid: str = Field(default=str(uuid.uuid4()), max_length=36)
    url: str
    is_active: bool = Field(default=True)
    has_sync_failed: bool = Field(default=False)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())
    last_successful_sync: datetime = Field(default=None, nullable=True)

    feed_links: list[User_Feed_Post_Link] = Relationship(back_populates="feed")

    posts: list["Posts"] = Relationship(back_populates="feed")


class Posts(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    url: str
    uuid: str = Field(default=str(uuid.uuid4()), max_length=36)
    published_at: datetime
    feed_id: int = Field(default=None, foreign_key="feeds.id")

    post_links: list[User_Feed_Post_Link] = Relationship(back_populates="post")
    feed: Feeds = Relationship(back_populates="posts")
