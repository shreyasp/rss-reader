import datetime

from pydantic import EmailStr
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, mapped_column

Base = declarative_base()

class User(Base):
    """Defines DB model for users"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, nullable=False)
    email = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.now())
    updated_at = Column(DateTime, default=datetime.datetime.now())
    feeds = relationship("Feed", back_populates="user")

class Feed(Base):
    """Defines DB model for a single rss feeds linked with a user"""

    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    has_sync_failed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.now())
    updated_at = Column(DateTime, default=datetime.datetime.now())
    last_successful_sync = Column(DateTime, default=datetime.datetime.now())

    user_id = mapped_column(ForeignKey("users.id"))
    user = relationship("User", back_populates="feeds")

    feed_items = relationship("FeedItem", back_populates="feed")


class FeedItem(Base):
    """Defines DB model for a single feed item linked with a feed"""


    __tablename__ = "feed_items"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, nullable=False)
    is_read = Column(Boolean, default=True)
    read_at = Column(DateTime, default=datetime.datetime.now())

    feed_id = mapped_column(ForeignKey("feeds.id"))
    feed = relationship("Feed", back_populates="feed_items")