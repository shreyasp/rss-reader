# external imports
from fastapi import APIRouter
from pydantic import BaseModel

# builtin imports
from datetime import datetime


rss_feeds_router = APIRouter("/v1/feeds", tags=["rss-feeds"])

