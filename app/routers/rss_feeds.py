# external imports
from fastapi import APIRouter
from pydantic import BaseModel

# builtin imports
from datetime import datetime


rss_feeds_router = APIRouter("/v1/feeds", tags=["rss-feeds"])


class RSSFeeds(BaseModel):
    id: id
    uuid: str
    user_uuid: str
    is_active: bool
    is_failed: bool
    created_at: datetime
    last_successfully_synced_at: datetime

