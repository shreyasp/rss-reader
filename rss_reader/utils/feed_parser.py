from ast import Not
from mailbox import Message
import os
from datetime import datetime, timedelta
import uuid

# external imports
import feedparser
from feedparser import FeedParserDict
from rq import Queue
from rq.job import Job
from sqlalchemy import Engine
from sqlmodel import Session, select
from fastapi import status

from rss_reader.utils.cache import Cache
from rss_reader.utils.database import Database
from rss_reader.database.models import (
    Posts as PostModel,
    Feeds as FeedModel,
    User_Feed_Post_Link as UserFeedPostLink,
)
from rss_reader.utils.message_queue import MessageQueue
from rss_reader.utils.singleton import Singleton
from rss_reader.config.config import Config


class Parser(metaclass=Singleton):
    _session: Session
    _cache: Cache
    _queue: Queue

    def __init__(self) -> None:
        pass

    def setup(self):
        self._setup_db_session()

    def _setup_db_session(self):
        app_mode = os.getenv("APP_MODE")

        # get config
        _c: Config = Config(mode=app_mode)

        # setup database
        d: Database = Database()
        d.setup(_c.db_config)
        self._session = Session(d.get_engine())

        # setup cache and message queue
        c: Cache = Cache()
        c.setup(_c.cache_config)
        self._cache = c

        mq: MessageQueue = MessageQueue()
        mq.setup()
        self._queue = mq.get_queue()

    def get_session(self) -> Engine:
        return self._session

    def get_message_queue(self) -> Queue:
        return self._queue

    def get_cache(self) -> Cache:
        return self._cache


def with_db_q_connection(func):
    p: Parser = Parser()
    p.setup()

    session: Session = p.get_session()
    mq: Queue = p.get_message_queue()
    cache: Cache = p.get_cache()

    def wrapper_func(*args, **kwargs):
        return func(session, cache, mq, *args, **kwargs)

    return wrapper_func


@with_db_q_connection
def scheduled_parse(
    conn: Session,
    cache: Cache,
    mq: Queue,
    url: str,
    feed_id: int,
    latest_item_published: datetime,
) -> bool:
    return True


@with_db_q_connection
def parse(
    conn: Session,
    cache: Cache,
    mq: Queue,
    user_id: int,
    feed_id: int,
    url: str,
    should_parse: bool,
) -> bool:

    posts: list[PostModel] = []
    only_link: bool = False
    _: datetime = None

    if should_parse:
        fd, _, err = _parse_feed_and_last_published_date(url)
        if err is not None:
            pass

        for item in fd:
            # published as time struct
            p_ts = item.get("published_parsed")
            published = datetime(*p_ts[:6])

            post = PostModel(
                uuid=uuid.uuid4(),
                url=item.get("link"),
                title=item.get("title"),
                published_at=published,
                feed_id=feed_id,
            )
            posts.append(post)

    # feed and posts exists; collect and create link
    else:
        only_link = True
        q = select(PostModel).join(FeedModel).where(PostModel.feed_id == feed_id)

        try:
            posts = conn.exec(q).all()
        except Exception:
            pass

    sorted_posts = sorted(posts, key=lambda p: p.published_at, reverse=True)
    _ = sorted_posts[0].published_at
    _create_posts_add_links(
        conn=conn,
        posts=posts,
        user_id=user_id,
        feed_id=feed_id,
        only_link=only_link,
    )

    return True


def _parse_feed_and_last_published_date(url) -> tuple[FeedParserDict, datetime, any]:
    f = feedparser.parse(url)

    # check for exceptions in the feed and return early
    if f.get("status") != status.HTTP_200_OK and f.get("bozo"):

        # check if feed is permanently moved to different URL or
        if f.get("status") == status.HTTP_301_MOVED_PERMANENTLY:
            pass

        # or check if feed is permanently gone or discontinued
        elif f.get("status") == status.HTTP_410_GONE:
            pass

        # handle everything else here, wrong url, server exception
        else:
            pass

    fd: list["FeedParserDict"] = f.get("entries")

    if len(fd) != 0:
        # sort the feed with reverse chronological order
        sorted_fd = sorted(fd, key=lambda i: i.get("published_parsed"), reverse=True)

        parsed_published_latest = sorted_fd[0].get("published_parsed")
        _ = datetime(*parsed_published_latest[:6])

        return (sorted_fd, _, None)

    else:
        return (fd, _, None)


def _create_posts_add_links(
    conn: Session,
    posts: list[PostModel],
    user_id: int,
    feed_id: int,
    only_link: bool,
):
    for post in posts:

        # create posts and then link
        if not only_link:
            try:
                conn.add(post)
            except Exception:
                conn.rollback()

            else:
                conn.commit()
                conn.refresh(post)

        _create_links(conn, user_id=user_id, feed_id=feed_id, post_id=post.id)


def _create_links(
    conn: Session,
    user_id: int,
    feed_id: int,
    post_id: int,
):
    link = UserFeedPostLink(
        user_id=user_id,
        feed_id=feed_id,
        post_id=post_id,
    )

    try:
        conn.add(link)
    except Exception:
        conn.rollback()

    else:
        conn.commit()
