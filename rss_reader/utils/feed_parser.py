from calendar import c
import os
from datetime import datetime, timezone, timedelta
import uuid

# external imports
import feedparser
from feedparser import FeedParserDict
from rq import Queue
from rq.job import Job
from rq_scheduler import Scheduler
from sqlalchemy import Engine
from sqlmodel import Session, select
from fastapi import status

from rss_reader.utils.cache import Cache
from rss_reader.utils.database import Database
from rss_reader.database.models import (
    Posts as PostModel,
    Feeds as FeedModel,
    Users as UserModel,
    User_Feed_Post_Link as UserFeedPostLink,
)
from rss_reader.utils.message_queue import BackgroundScheduler, MessageQueue
from rss_reader.utils.singleton import Singleton
from rss_reader.config.config import Config


class Parser(metaclass=Singleton):
    _session: Session
    _cache: Cache
    _queue: Queue
    _scheduler: Scheduler

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

        # setup scheduler
        scheduler: BackgroundScheduler = BackgroundScheduler()
        scheduler.setup(mq.get_queue(), c.get_redis_connection())
        self._scheduler = scheduler.get_scheduler()

    def get_session(self) -> Engine:
        return self._session

    def get_message_queue(self) -> Queue:
        return self._queue

    def get_cache(self) -> Cache:
        return self._cache

    def get_scheduler(self) -> Scheduler:
        return self._scheduler

    def requeue_jobs(self):
        requeue_all_jobs()


def with_db_q_connection(func):
    p: Parser = Parser()
    p.setup()

    session: Session = p.get_session()
    mq: Queue = p.get_message_queue()
    cache: Cache = p.get_cache()
    scheduler: Scheduler = p.get_scheduler()

    def wrapper_func(*args, **kwargs):
        return func(session, cache, mq, scheduler, *args, **kwargs)

    return wrapper_func


def scheduled_sync_failure_handler(job: Job, queue_conn, _, value, traceback):
    scheduler = BackgroundScheduler().get_scheduler()

    # we encountered our first failure for the job, we will need to set the
    # backoff intervals and number of retries on the job
    if job.retries_left is None and job.retry_intervals is None:
        backoff_intervals = [
            (2 * 60),  # 2 mins
            (5 * 60),  # 5 mins
            (8 * 60),  # 8 mins
        ]  # backoff intervals in seconds

        job.retry_intervals = backoff_intervals
        job.retries_left = len(backoff_intervals)
        job.save(include_meta=True)

    # if there retries left then utilize the backoff computed by the
    # get_retry_interval() method and update the execution time for
    # the subsequent try
    if job.retries_left != 0:
        d = job.ended_at.replace(tzinfo=timezone.utc)
        scheduler.change_execution_time(
            job, d + timedelta(seconds=job.get_retry_interval())
        )
        job.save(include_meta=True)

    # if number of retries_left is zero, we need to remove the job from
    # the processing queue.
    else:
        scheduler.cancel(job)


def scheduled_sync_success_handler(job: Job, connection, result, *args, **kwargs):
    scheduler = BackgroundScheduler().get_scheduler()

    # if the job has been resurrected from the previous failure, retries
    # would be set to a finite value. but, after resurrection we should
    # reset the retries to max value, so we can apply backoff mechanism
    # properly for next occurrence of the failure.
    if job.retries_left is not None:
        d = job.ended_at.replace(tzinfo=timezone.utc)
        scheduler.change_execution_time(
            job,
            d + timedelta(seconds=job.meta["interval"]),
        )
        job.retries_left = len(job.retry_intervals)
        job.save(include_meta=True, include_result=True)


#### Add queue handlers in here ####
@with_db_q_connection
def requeue_all_jobs(
    conn: Session,
    cache: Cache,
    mq: Queue,
    scheduler: Scheduler,
):

    # remove any job previously queued in and start afresh
    for job in scheduler.get_jobs():
        scheduler.cancel(job)

    # for a good measure call empty queue as well
    mq.empty()

    # requeue all feeds
    _requeue_feeds(conn=conn, scheduler=scheduler, feed_id=None)
    return True


@with_db_q_connection
def requeue_jobs_for_user_feed(
    conn: Session,
    cache: Cache,
    mq: Queue,
    scheduler: Scheduler,
    feed_id: int,
):
    _requeue_feeds(conn=conn, scheduler=scheduler, feed_id=feed_id)
    return True


@with_db_q_connection
def scheduled_sync(
    conn: Session,
    cache: Cache,
    mq: Queue,
    scheduler: Scheduler,
    url: str,
    feed_id: int,
    latest_item_published: datetime,
) -> bool:

    posts_in_feed, _ = _parse_feed_and_last_published_date(url)
    filtered_posts = [
        post
        for post in posts_in_feed
        if datetime(*post.get("published_parsed")[:6]) > latest_item_published
    ]

    posts: list[PostModel] = []
    for item in filtered_posts:
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

    q = (
        select(UserFeedPostLink.user_id)
        .distinct(UserFeedPostLink.user_id)
        .where(UserFeedPostLink.feed_id == feed_id)
    )

    try:
        user_ids = conn.exec(q).all()
    except Exception as exc:
        conn.rollback()
        raise exc.with_traceback()

    if len(user_ids) != 0:
        for user_id in user_ids:
            _create_posts_add_links(
                conn=conn,
                posts=posts,
                user_id=user_id,
                feed_id=feed_id,
                only_link=False,
            )

    # update last successful sync date
    _update_feed_last_successful_sync(conn=conn, feed_id=feed_id)

    return True


@with_db_q_connection
def parse(
    conn: Session,
    cache: Cache,
    mq: Queue,
    scheduler: Scheduler,
    user_id: int,
    feed_id: int,
    url: str,
    should_parse: bool,
) -> bool:

    posts: list[PostModel] = []
    only_link: bool = False
    latest_item_published: datetime = None

    if should_parse:
        fd, latest_item_published = _parse_feed_and_last_published_date(url)
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

        # schedule the job
        first_run_time = datetime.now(tz=timezone.utc) + timedelta(seconds=5)
        _ = scheduler.schedule(
            scheduled_time=first_run_time,
            description="synchronizes feed in scheduled fashion for {feed_url}".format(
                feed_url=url
            ),
            func="rss_reader.utils.feed_parser.scheduled_sync",
            interval=(5 * 60),  # in seconds ~ 5 mins
            queue_name="rss_reader.feeds.sync",
            kwargs={
                "url": url,
                "feed_id": feed_id,
                "latest_item_published": latest_item_published,
            },
            result_ttl=(10 * 60),  # in seconds ~ 10 mins
            on_success="rss_reader.utils.feed_parser.scheduled_sync_success_handler",
            on_failure="rss_reader.utils.feed_parser.scheduled_sync_failure_handler",
        )

    # feed and posts exists; collect and create link
    else:
        only_link = True
        q = select(PostModel).join(FeedModel).where(PostModel.feed_id == feed_id)

        try:
            posts = conn.exec(q).all()
        except Exception:
            conn.rollback()

        sorted_posts = sorted(posts, key=lambda p: p.published_at, reverse=True)
        latest_item_published = (
            datetime.now() if len(sorted_posts) == 0 else sorted_posts[0].published_at
        )

    _create_posts_add_links(
        conn=conn,
        posts=posts,
        user_id=user_id,
        feed_id=feed_id,
        only_link=only_link,
    )

    # update last successful sync date
    _update_feed_last_successful_sync(conn=conn, feed_id=feed_id)

    return True


#### add helper functions here ####


def _requeue_feeds(
    conn: Session,
    scheduler: Scheduler,
    feed_id: int | None,
):
    q = select(FeedModel.id, FeedModel.url).where(FeedModel.is_active == True)

    if feed_id is not None:
        q = q.where(FeedModel.id == feed_id)

    try:
        feeds: list[FeedModel] = conn.exec(q).all()

    except Exception as exc:
        conn.rollback()

    else:
        for feed in feeds:
            # schedule the job
            first_run_time = datetime.now(tz=timezone.utc)
            _ = scheduler.schedule(
                scheduled_time=first_run_time,
                description="synchronizes feed in scheduled fashion for {feed_url}".format(
                    feed_url=feed.url
                ),
                func="rss_reader.utils.feed_parser.scheduled_sync",
                interval=(5 * 60),  # in seconds ~ 5 mins
                queue_name="rss_reader.feeds.sync",
                kwargs={
                    "url": feed.url,
                    "feed_id": feed.id,
                    "latest_item_published": datetime.now(),
                },
                result_ttl=(10 * 60),  # in seconds ~ 10 mins
                on_success="rss_reader.utils.feed_parser.scheduled_sync_success_handler",
                on_failure="rss_reader.utils.feed_parser.scheduled_sync_failure_handler",
            )

    finally:
        conn.close()


def _update_feed_last_successful_sync(conn: Session, feed_id: int):
    q = select(FeedModel).where(FeedModel.id == feed_id)

    try:
        f = conn.exec(q).one_or_none()

    except Exception as exc:
        conn.rollback()

    # update last successful sync for the feed
    f.last_successful_sync = datetime.now()

    try:
        conn.add(f)

    except Exception as exc:
        conn.rollback()

    finally:
        conn.close()


def _parse_feed_and_last_published_date(url) -> tuple[FeedParserDict, datetime]:
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
            raise f.get("bozo_exception")

    fd: list["FeedParserDict"] = f.get("entries")

    if len(fd) != 0:
        # sort the feed with reverse chronological order
        sorted_fd = sorted(fd, key=lambda i: i.get("published_parsed"), reverse=True)

        parsed_published_latest = sorted_fd[0].get("published_parsed")
        latest_item_pub_date = datetime(*parsed_published_latest[:6])

        return (sorted_fd, latest_item_pub_date)

    else:
        return (fd, datetime.min)


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
