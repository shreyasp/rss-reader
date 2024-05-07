# external imports
from fastapi import APIRouter


rss_feeds_router = APIRouter("/v1/feeds", tags=["rss-feeds"])
