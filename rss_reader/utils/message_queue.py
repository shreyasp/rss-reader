# externa imports
from rq import Queue

from rss_reader.utils.singleton import Singleton

# internal imports
from .cache import Cache


def get_queue_conn():
    mq: MessageQueue = MessageQueue()
    yield mq.get_queue()


class MessageQueue(metaclass=Singleton):
    _q: Queue

    def __init__(self):
        pass

    def setup(self) -> None:
        redis_conn = Cache().get_redis_connection()

        self._q = Queue(
            connection=redis_conn,
            name="rss_reader.feeds.sync",
            default_timeout=10,
        )

    def get_queue(self) -> Queue:
        return self._q
