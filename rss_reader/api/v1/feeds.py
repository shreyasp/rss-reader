from ast import Tuple
from datetime import datetime
from typing import Sequence
import uuid

# external imports
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, HttpUrl
from sqlmodel import Session, select
from rq import Queue
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from rss_reader.utils.cache import get_cache, Cache
from rss_reader.utils.database import get_db_connection
from rss_reader.database.models import (
    User_Feed_Post_Link as UserFeedPostLink,
    Users as UserModel,
    Feeds as FeedModel,
    Posts as PostModel,
)
from rss_reader.utils.message_queue import get_queue_conn

feeds_router = APIRouter(prefix="/v1/feeds", tags=["rss-feeds"])


class CreateFeed(BaseModel):
    user_id: int
    urls: list[HttpUrl]

    class Config:
        from_attributes = True


class DeleteFeed(BaseModel):
    user_id: int
    feed_ids: list[int]

    class Config:
        from_attributes = True


class MarkPost(BaseModel):
    user_id: int
    feed_id: int


class UserFeedPostResponse(BaseModel):
    post: PostModel
    is_read: bool
    read_at: datetime


@feeds_router.post(
    path="/",
    description="creates or follow multiple feeds for a given user",
    status_code=status.HTTP_200_OK,
)
def create_feed(
    feed_payload: CreateFeed,
    conn: Session = Depends(get_db_connection),
    cache: Cache = Depends(get_cache),
    mq: Queue = Depends(get_queue_conn),
):
    """creates multiple feeds for the user"""
    now = datetime.now()

    # check if user exists
    _check_if_user_exists(conn, feed_payload.user_id)

    # check if feed exists
    feeds: list[FeedModel] = []
    feed: FeedModel = None
    for feed_url in feed_payload.urls:
        q = select(FeedModel).where(FeedModel.url == str(feed_url))
        feed = conn.exec(q).one_or_none()

        # feed doesn't exist create a new one and parse to
        # create posts and links
        if feed is None:
            feed = FeedModel(
                uuid=uuid.uuid4(),
                url=str(feed_url),
                created_at=now,
                updated_at=now,
            )

            try:
                conn.add(feed)

            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="failed to create a new feed with {url}".format(
                        url=str(feed_url)
                    ),
                )

            else:
                conn.commit()
                conn.refresh(feed)

            finally:
                conn.close()

            # parse the feed and create links
            mq.enqueue(
                "rss_reader.utils.feed_parser.parse",
                feed_payload.user_id,
                feed.id,
                feed.url,
                True,  # should parse the feed
            )

        # feed already present, just create the links
        else:
            mq.enqueue(
                "rss_reader.utils.feed_parser.parse",
                feed_payload.user_id,
                feed.id,
                feed.url,
                False,  # should not parse the feed
            )

        feeds.append(feed)

    return {"feeds": feeds}


@feeds_router.delete(
    path="/",
    description="unfollow multiple feeds for a given user",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_feed_link(
    feed_payload: DeleteFeed,
    conn: Session = Depends(get_db_connection),
    cache: Cache = Depends(get_cache),
):
    """unfollow multiple feeds for the user"""
    _check_if_user_exists(conn, feed_payload.user_id)

    for feed_id in feed_payload.feed_ids:
        q = (
            select(UserFeedPostLink)
            .where(UserFeedPostLink.user_id == feed_payload.user_id)
            .where(UserFeedPostLink.feed_id == feed_id)
        )

        links: list[UserFeedPostLink] = []
        try:
            links = conn.exec(q).all()
        except Exception:
            conn.rollback()

        # delete the links
        for link in links:
            try:
                conn.delete(link)

            except:
                conn.rollback()

            else:
                conn.commit()

            finally:
                conn.close()


@feeds_router.post(
    path="/{post_id}",
    description="marks post as read or unread",
    status_code=status.HTTP_200_OK,
)
def mark_post_as_read_or_unread(
    post_id: int,
    payload: MarkPost,
    conn: Session = Depends(get_db_connection),
):
    q = (
        select(UserFeedPostLink)
        .where(UserFeedPostLink.post_id == post_id)
        .where(UserFeedPostLink.user_id == payload.user_id)
        .where(UserFeedPostLink.feed_id == payload.feed_id)
    )

    link: UserFeedPostLink = conn.exec(q).one_or_none()
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="post with {post_id} in feed {feed_id} for user {user_id} not found".format(
                post_id=post_id,
                feed_id=payload.feed_id,
                user_id=payload.user_id,
            ),
        )

    # flip
    link.is_read = not link.is_read

    # is read
    if link.is_read:
        link.read_at = datetime.now()

    # marking as unread
    else:
        link.read_at = None

    try:
        conn.add(link)

    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="failed to update read status for the post {id}".format(id=post_id),
        )

    else:
        conn.commit()
        conn.refresh(link)

    finally:
        conn.close()

    return {"link": link}


@feeds_router.post(
    path="/{feed_id}/mark-all-read",
    description="marks all posts related to a feed for the given user as read",
    status_code=status.HTTP_204_NO_CONTENT,
)
def mark_all_posts_as_read(
    feed_id: int,
    user_id: int,
    conn: Session = Depends(get_db_connection),
):
    q = (
        select(UserFeedPostLink)
        .where(UserFeedPostLink.user_id == user_id)
        .where(UserFeedPostLink.feed_id == feed_id)
    )

    try:
        links = conn.exec(q).all()

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="failed to retrieve posts related to feed {feed_id} for the user {user_id}".format(
                feed_id=feed_id, user_id=user_id
            ),
        )

    finally:
        conn.close()

    for link in links:
        link.is_read = True
        link.read_at = datetime.now()

        try:
            conn.add(link)

        except Exception as exc:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="failed to mark all posts as read related to feed {feed_id} for user {user_id} with {exc}".format(
                    feed_id=feed_id,
                    user_id=user_id,
                    exc=exc,
                ),
            )

        else:
            conn.commit()

    conn.close()


@feeds_router.get(
    path="/{feed_id}",
    description="Lists all posts from a feed for the given user",
    status_code=status.HTTP_200_OK,
)
def get_all_feeds_for_user(
    feed_id: int,
    user_id: int,
    is_read: bool = None,
    conn: Session = Depends(get_db_connection),
):
    q = (
        select(PostModel, UserFeedPostLink)
        .join(PostModel)
        .where(UserFeedPostLink.feed_id == feed_id)
        .where(UserFeedPostLink.user_id == user_id)
    )

    # only list read / unread posts
    if is_read is not None:
        q = q.where(UserFeedPostLink.is_read == is_read)

    try:
        posts_n_links = conn.exec(q).all()

    except Exception as exc:
        raise HTTPException(detail=exc)

    # using item [1] as that is second element of the data returned
    posts_n_links = sorted(
        posts_n_links, key=lambda item: item[1].read_at, reverse=True
    )

    resp: list[UserFeedPostResponse] = []
    for post_n_link in posts_n_links:
        # only append posts
        resp.append(
            UserFeedPostResponse(
                post=post_n_link[0],
                is_read=post_n_link[1].is_read,
                read_at=post_n_link[1].read_at,
            )
        )

    return {"posts": resp}


#### add helper functions here
def _check_if_user_exists(conn: Session, user_id: int):
    q = select(UserModel).where(UserModel.id == user_id)
    try:
        conn.exec(q).one()

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
