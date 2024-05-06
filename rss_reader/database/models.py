import uuid
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


class Users(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    uuid: str = Field(default=str(uuid.uuid4()), max_length=36)
    email: str = Field(max_length=320)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())

    feeds: list["Feeds"] = Relationship(back_populates="user")


class Feeds(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    uuid: str = Field(default=str(uuid.uuid4()), max_length=36)
    is_active: bool = Field(default=True)
    has_sync_failed: bool = Field(default=False)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())
    last_successful_sync: datetime = Field(default=None)

    user_id: int | None = Field(default=None, foreign_key="users.id")
    user: Users | None = Relationship(back_populates="feeds")

    feed_items: list["FeedItems"] = Relationship(back_populates="feed")


class FeedItems(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    uuid: str = Field(default=str(uuid.uuid4()), max_length=36)
    is_read: bool = Field(default=False)
    read_at: datetime = Field(default=None)

    feed_id: int | None = Field(default=None, foreign_key="feeds.id")
    feed: Feeds | None = Relationship(back_populates="feed_items")
